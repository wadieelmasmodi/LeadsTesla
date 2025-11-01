"""Web scraper for Tesla Partner Portal leads - Simplified version."""
import os
import sys
import time
from datetime import datetime
from typing import Dict, List
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from models import db, ScraperRun, Lead
from config import PORTAL_URL

# Configure logging to stdout for visibility
logging.basicConfig(
    level=logging.INFO,
    format='[SCRAPER] %(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
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
    
    logger.info("="*80)
    logger.info("🚀 DÉMARRAGE DU SCRAPER TESLA")
    logger.info("="*80)
    
    with sync_playwright() as p:
        try:
            # Launch browser
            logger.info("🌐 Lancement du navigateur Chromium...")
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
            logger.info(f"🔗 Navigation vers {PORTAL_URL}")
            run.phase_connexion = "Navigation vers le portail"
            db.session.commit()
            
            page.goto(PORTAL_URL, wait_until='domcontentloaded', timeout=60000)
            logger.info("✅ Page chargée (DOM ready)")
            
            # Wait for page to be interactive
            page.wait_for_load_state('networkidle', timeout=30000)
            logger.info("✅ Page interactive (network idle)")
            
            # Check if login is needed
            logger.info("🔐 Vérification de l'authentification...")
            run.phase_connexion = "Vérification authentification"
            db.session.commit()
            
            # Try to login if credentials are available
            email = os.getenv('TESLA_EMAIL')
            password = os.getenv('TESLA_PASS')
            
            logger.info(f"📧 Email configuré: {'✅ Oui' if email else '❌ Non'}")
            logger.info(f"🔑 Password configuré: {'✅ Oui' if password else '❌ Non'}")
            
            if email and password:
                try:
                    # Look for email input
                    email_inputs = page.locator('input[type="email"]').count()
                    logger.info(f"🔍 Champs email trouvés: {email_inputs}")
                    
                    if email_inputs > 0:
                        logger.info("🔐 Formulaire de login détecté, authentification en cours...")
                        page.fill('input[type="email"]', email)
                        logger.info("✅ Email renseigné")
                        
                        page.fill('input[type="password"]', password)
                        logger.info("✅ Password renseigné")
                        
                        page.click('button[type="submit"]')
                        logger.info("⏳ Clic sur le bouton de connexion, attente de la réponse...")
                        
                        page.wait_for_load_state('networkidle', timeout=30000)
                        logger.info("✅ Authentification réussie!")
                        run.phase_connexion = "Authentification réussie"
                    else:
                        logger.info("✅ Déjà authentifié (pas de formulaire de login)")
                        run.phase_connexion = "Déjà authentifié"
                except Exception as e:
                    logger.error(f"❌ Erreur lors du login: {e}")
                    run.phase_connexion = f"Erreur login: {str(e)[:50]}"
            else:
                logger.warning("⚠️ Pas de credentials fournis, on suppose être déjà connecté")
                run.phase_connexion = "Pas de credentials (session existante?)"
            
            db.session.commit()
            
            # Take screenshot for debugging
            screenshot_filename = f"scraper_run_{run.id}_page.png"
            screenshot_full_path = os.path.join('/app/static', screenshot_filename)
            
            # Ensure static directory exists
            os.makedirs('/app/static', exist_ok=True)
            
            logger.info(f"💾 Saving screenshot to {screenshot_full_path}")
            page.screenshot(path=screenshot_full_path, full_page=True)
            run.screenshot_path = screenshot_filename
            db.session.commit()
            
            logger.info(f"✅ Screenshot saved successfully: {screenshot_filename}")
            
            # Wait for content to load
            logger.info("⏳ Attente du chargement du contenu (5 secondes pour Angular)...")
            run.phase_extraction = "Attente du contenu"
            db.session.commit()
            
            time.sleep(5)  # Give Angular time to render
            
            # Extract page content
            logger.info("🔍 Analyse du contenu de la page...")
            run.phase_extraction = "Analyse du contenu"
            db.session.commit()
            
            # Get all text content
            page_text = page.inner_text('body')
            logger.info(f"📄 Longueur du contenu texte: {len(page_text)} caractères")
            logger.info(f"📄 Aperçu du contenu (100 premiers caractères): {page_text[:100]}")
            
            # Look for tables
            tables = page.locator('table').all()
            logger.info(f"📊 Nombre de tableaux trouvés: {len(tables)}")
            
            # Extract data from tables
            leads_data = []
            
            for idx, table in enumerate(tables):
                logger.info(f"📊 Traitement du tableau {idx + 1}/{len(tables)}...")
                
                try:
                    # Get all rows
                    rows = table.locator('tr').all()
                    logger.info(f"   ↳ Nombre de lignes: {len(rows)}")
                    
                    if len(rows) > 0:
                        # First row might be headers
                        headers = []
                        first_row = rows[0]
                        header_cells = first_row.locator('th, td').all()
                        
                        for cell in header_cells:
                            headers.append(cell.inner_text().strip())
                        
                        logger.info(f"   ↳ En-têtes: {headers}")
                        
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
                                
                        logger.info(f"   ✅ {len(rows)-1} lignes de données extraites")
                
                except Exception as e:
                    logger.error(f"   ❌ Erreur traitement tableau {idx + 1}: {e}")
            
            # Save leads to database
            logger.info(f"💾 Sauvegarde de {len(leads_data)} leads dans la base de données...")
            run.phase_extraction = f"Extraction: {len(leads_data)} leads trouvés"
            
            saved_count = 0
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
                    saved_count += 1
                except Exception as e:
                    logger.error(f"❌ Erreur sauvegarde lead: {e}")
            
            logger.info(f"✅ {saved_count}/{len(leads_data)} leads sauvegardés")
            
            db.session.commit()
            
            # Update run status
            run.status = "success"
            run.details = f"Extracted {len(leads_data)} leads from {len(tables)} tables"
            db.session.commit()
            
            result['status'] = 'success'
            result['message'] = f"Successfully extracted {len(leads_data)} leads"
            result['leads_count'] = len(leads_data)
            result['leads'] = leads_data
            
            logger.info("="*80)
            logger.info("✅ SCRAPING TERMINÉ AVEC SUCCÈS")
            logger.info(f"📊 {len(tables)} tableaux analysés")
            logger.info(f"💾 {len(leads_data)} leads extraits")
            logger.info("="*80)
            
        except Exception as e:
            logger.error("="*80)
            logger.error(f"❌ ÉCHEC DU SCRAPING: {e}")
            logger.error("="*80)
            logger.error("Stack trace:", exc_info=True)
            
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
