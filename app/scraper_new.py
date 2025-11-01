"""Web scraper for Tesla Partner Portal leads - Simplified version."""
import os
import time
from datetime import datetime
from typing import Dict, List
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from models import db, ScraperRun, Lead
from config import PORTAL_URL

logger = logging.getLogger(__name__)

def scrape_tesla_leads() -> Dict:
    """
    Scrape Tesla Partner Portal for leads.
    Returns a dict with status, message, and leads data.
    """
    result = {
        'status': 'pending',
        'message': '',
        'leads_count': 0,
        'leads': []
    }
    
    # Create ScraperRun record
    run = ScraperRun(
        timestamp=datetime.utcnow(),
        phase_connexion="Démarrage",
        phase_extraction="En attente",
        status="pending"
    )
    db.session.add(run)
    db.session.commit()
    
    logger.info("Starting Tesla scraper")
    
    with sync_playwright() as p:
        try:
            # Launch browser
            logger.info("Launching browser...")
            run.phase_connexion = "Lancement du navigateur"
            db.session.commit()
            
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = context.new_page()
            
            # Navigate to Tesla portal
            logger.info(f"Navigating to {PORTAL_URL}")
            run.phase_connexion = "Navigation vers le portail"
            db.session.commit()
            
            page.goto(PORTAL_URL, wait_until='domcontentloaded', timeout=60000)
            
            # Wait for page to be interactive
            page.wait_for_load_state('networkidle', timeout=30000)
            
            # Check if login is needed
            logger.info("Checking authentication...")
            run.phase_connexion = "Vérification authentification"
            db.session.commit()
            
            # Try to login if credentials are available
            email = os.getenv('TESLA_EMAIL')
            password = os.getenv('TESLA_PASSWORD')
            
            if email and password:
                try:
                    # Look for email input
                    if page.locator('input[type="email"]').count() > 0:
                        logger.info("Login form detected, attempting login...")
                        page.fill('input[type="email"]', email)
                        page.fill('input[type="password"]', password)
                        page.click('button[type="submit"]')
                        page.wait_for_load_state('networkidle', timeout=30000)
                        run.phase_connexion = "Authentification réussie"
                    else:
                        run.phase_connexion = "Déjà authentifié"
                except Exception as e:
                    logger.warning(f"Login attempt failed: {e}")
                    run.phase_connexion = f"Erreur login: {str(e)[:50]}"
            else:
                logger.warning("No credentials provided, assuming already logged in")
                run.phase_connexion = "Pas de credentials (session existante?)"
            
            db.session.commit()
            
            # Take screenshot for debugging
            screenshot_path = f"scraper_run_{run.id}_page.png"
            page.screenshot(path=f"app/static/{screenshot_path}", full_page=True)
            run.screenshot_path = screenshot_path
            db.session.commit()
            
            logger.info("Screenshot saved")
            
            # Wait for content to load
            logger.info("Waiting for page content...")
            run.phase_extraction = "Attente du contenu"
            db.session.commit()
            
            time.sleep(5)  # Give Angular time to render
            
            # Extract page content
            logger.info("Analyzing page content...")
            run.phase_extraction = "Analyse du contenu"
            db.session.commit()
            
            # Get all text content
            page_text = page.inner_text('body')
            
            # Look for tables
            tables = page.locator('table').all()
            logger.info(f"Found {len(tables)} tables on page")
            
            # Extract data from tables
            leads_data = []
            
            for idx, table in enumerate(tables):
                logger.info(f"Processing table {idx + 1}")
                
                try:
                    # Get all rows
                    rows = table.locator('tr').all()
                    
                    if len(rows) > 0:
                        # First row might be headers
                        headers = []
                        first_row = rows[0]
                        header_cells = first_row.locator('th, td').all()
                        
                        for cell in header_cells:
                            headers.append(cell.inner_text().strip())
                        
                        logger.info(f"Table {idx + 1} headers: {headers}")
                        
                        # Process data rows
                        for row_idx, row in enumerate(rows[1:], 1):
                            cells = row.locator('td').all()
                            
                            if len(cells) > 0:
                                row_data = {}
                                for cell_idx, cell in enumerate(cells):
                                    header = headers[cell_idx] if cell_idx < len(headers) else f"column_{cell_idx}"
                                    row_data[header] = cell.inner_text().strip()
                                
                                leads_data.append({
                                    'table': idx,
                                    'row': row_idx,
                                    'data': row_data
                                })
                
                except Exception as e:
                    logger.error(f"Error processing table {idx + 1}: {e}")
            
            # Save leads to database
            logger.info(f"Extracted {len(leads_data)} leads")
            run.phase_extraction = f"Extraction: {len(leads_data)} leads trouvés"
            
            for lead_data in leads_data:
                # Create unique key
                key = f"table{lead_data['table']}_row{lead_data['row']}_{int(time.time())}"
                
                try:
                    lead = Lead(
                        source=f"Tesla Table {lead_data['table']}",
                        key=key,
                        fetched_at=datetime.utcnow(),
                        data=lead_data['data']
                    )
                    db.session.add(lead)
                except Exception as e:
                    logger.error(f"Error saving lead: {e}")
            
            db.session.commit()
            
            # Update run status
            run.status = "success"
            run.details = f"Extracted {len(leads_data)} leads from {len(tables)} tables"
            db.session.commit()
            
            result['status'] = 'success'
            result['message'] = f"Successfully extracted {len(leads_data)} leads"
            result['leads_count'] = len(leads_data)
            result['leads'] = leads_data
            
            logger.info("Scraping completed successfully")
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}", exc_info=True)
            run.status = "failed"
            run.phase_extraction = "Échec"
            run.details = str(e)
            db.session.commit()
            
            result['status'] = 'failed'
            result['message'] = str(e)
        
        finally:
            try:
                browser.close()
            except:
                pass
    
    return result
