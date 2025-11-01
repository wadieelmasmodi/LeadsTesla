"""Web scraper for Tesla Partner Portal leads."""
import hashlib
import json
import random
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging
import socket
from playwright.sync_api import sync_playwright
from config import PORTAL_URL, PAGE_TIMEOUT, TABLE_SOURCES
from utils_text import normalize_key
from auth import login_if_needed
from models import db, ScraperAttempt, ScraperRun
from scraper_status import add_message, set_running

def extract_headers(table) -> List[str]:
    """Extract and normalize table headers."""
    # Try thead first
    headers = table.query_selector_all('thead th')
    if not headers:
        # Fallback to first row
        headers = table.query_selector_all('tr:first-child th')
    
    return [normalize_key(header.text_content().strip()) for header in headers]

def extract_rows(table, headers: List[str]) -> List[Dict]:
    """Extract rows from table and map to headers."""
    rows = []
    for tr in table.query_selector_all('tbody tr'):
        cells = tr.query_selector_all('td')
        if len(cells) == len(headers):
            row = {
                headers[i]: cells[i].text_content().strip()
                for i in range(len(headers))
            }
            rows.append(row)
    return rows

def guess_primary_key(row: Dict) -> str:
    """Determine primary key for a lead row."""
    # Try preferred fields in order
    for field in ['numero_d_installation', 'numero_de_confirmation', 'id']:
        if field in row and row[field]:
            return row[field]
            
    # Fallback: create stable hash of sorted row items
    row_str = json.dumps(dict(sorted(row.items())), ensure_ascii=False)
    return hashlib.sha256(row_str.encode()).hexdigest()[:8]

def log_scraper_attempt(success: bool, error: str = None):
    """Log a scraper connection attempt."""
    attempt = ScraperAttempt(
        success=success,
        ip_address=socket.gethostbyname(socket.gethostname()),
        error=error
    )
    db.session.add(attempt)
    db.session.commit()

def random_delay():
    """Wait for a random time between 5 and 20 minutes."""
    delay = random.randint(5 * 60, 20 * 60)  # Convert to seconds
    time.sleep(delay)

def fetch_leads(logger: logging.Logger) -> List[Dict]:
    """Fetch all leads from Tesla Partner Portal and log phases in ScraperRun."""
    leads: List[Dict] = []
    run = ScraperRun(
        timestamp=datetime.utcnow(),
        phase_connexion="Démarrage",
        phase_extraction="En attente",
        status="pending"
    )
    db.session.add(run)
    db.session.commit()
    logger.info("Scraper: starting new run")
    add_message("Scraper: starting new run")
    set_running(True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            logger.info(f"Scraper: navigating to {PORTAL_URL}")
            add_message("Navigating to portal")
            run.phase_connexion = "Navigation vers le portail"
            db.session.commit()
            page.goto(PORTAL_URL, timeout=PAGE_TIMEOUT * 1000)
            logger.info("Scraper: page loaded, performing login if needed")
            add_message("Page loaded; checking login")
            try:
                login_if_needed(page)
                logger.info("Scraper: login check complete")
                add_message("Login check complete")
                run.phase_connexion = "Connexion réussie"
                db.session.commit()
            except Exception as e:
                logger.error(f"Scraper: login failed or raised: {e}")
                add_message(f"Login failed: {e}")
                run.phase_connexion = f"Échec connexion: {e}"
                run.status = "failed"
                run.details = str(e)
                db.session.commit()
                raise

            logger.info("Scraper: waiting for page load to complete")
            add_message("Waiting for page load to complete")
            page.wait_for_load_state('networkidle', timeout=PAGE_TIMEOUT * 1000)
            
            # Wait for Angular app to be ready
            run.phase_extraction = "Initialisation Angular"
            db.session.commit()
            logger.info("Scraper: waiting for Angular app to initialize")
            add_message("Waiting for Angular app to initialize")
            try:
                # First wait for app-root to exist
                page.wait_for_selector('app-root', timeout=PAGE_TIMEOUT * 1000, state='attached')
                
                # Then wait for it to be visible and not empty
                page.wait_for_selector('app-root:not(:empty)', timeout=PAGE_TIMEOUT * 1000, state='visible')
                
                # Additional check - wait for Angular to finish bootstrapping
                page.evaluate('''() => {
                    return new Promise((resolve) => {
                        if (window.getAllAngularTestabilities) {
                            const testabilities = window.getAllAngularTestabilities();
                            const callback = () => {
                                if (testabilities.every(t => t.isStable())) resolve();
                            };
                            testabilities.forEach(t => t.whenStable(callback));
                        } else {
                            setTimeout(resolve, 1000);
                        }
                    });
                }''')
                
                logger.info("Angular app initialization complete")
            except Exception as e:
                logger.warning(f"Could not detect Angular app initialization: {e}")
                page.screenshot(path="angular_init_failed.png")
            
            # Wait for global loader to disappear
            run.phase_extraction = "Attente disparition loader"
            db.session.commit()
            logger.info("Scraper: waiting for main loader to disappear")
            add_message("Waiting for loader to disappear")
            try:
                page.wait_for_selector('.tds-loader--show', timeout=PAGE_TIMEOUT * 1000, state='hidden')
            except Exception as e:
                logger.warning(f"Could not detect loader disappearance: {e}")
                
            # Wait a bit for any animations to complete
            page.wait_for_timeout(2000)
            
            # Verify content presence
            run.phase_extraction = "Vérification du contenu"
            db.session.commit()
            logger.info("Scraper: waiting for content to be ready")
            add_message("Waiting for content to be ready")
            
            # Wait for either table, error message, or empty state
            selectors = [
                'table[class*="table"]', 
                '.tds-table',
                'mat-table',
                '.no-results',
                '.empty-state',
                '#main-content table',
                '.table',  # Additional generic table class
                '[role="table"]'  # ARIA role for tables
            ]
            
            try:
                # Take screenshot before looking for content
                screenshot_path = f"scraper_run_{run.id}_pre_content.png"
                page.screenshot(path=f"static/{screenshot_path}")
                run.screenshot_path = screenshot_path
                db.session.commit()
                logger.info("Saved pre-content screenshot")
                
                # Try each selector individually first
                found = False
                for selector in selectors:
                    logger.info(f"Trying selector: {selector}")
                    try:
                        element = page.wait_for_selector(selector, timeout=10000, state='attached')
                        if element:
                            logger.info(f"Found matching element with selector: {selector}")
                            found = True
                            break
                    except:
                        continue
                
                if not found:
                    # If no immediate matches, try waiting for any to appear
                    logger.info("Waiting for any content to appear")
                    # Use state='attached' instead of 'visible' to catch hidden elements
                    page.wait_for_selector(' ,'.join(selectors), timeout=PAGE_TIMEOUT * 1000, state='attached')
                    
                # After finding content, ensure it's visible
                page.wait_for_timeout(2000)  # Give time for any final rendering
                
                # Try evaluating page content
                page_content = page.content()
                if 'table' in page_content.lower():
                    logger.info("Found table in page content")
                else:
                    logger.warning("No table found in page content")
                
            except Exception as e:
                # Take detailed debug screenshots
                try:
                    page.screenshot(path="debug_screenshot_full.png", full_page=True)
                    logger.info("Saved full page debug screenshot")
                    
                    # Also get page HTML for debugging
                    with open("debug_page.html", "w", encoding="utf-8") as f:
                        f.write(page.content())
                    logger.info("Saved page HTML for debugging")
                except:
                    pass
                    
                logger.error(f"Content detection failed: {str(e)}")
                # Continue instead of raising to attempt table extraction anyway
                pass

            tables = page.query_selector_all('table')
            logger.info(f"Scraper: found {len(tables)} table(s) on the page")
            add_message(f"Found {len(tables)} table(s) on the page")
            run.phase_extraction = f"Tables détectées: {len(tables)}"
            db.session.commit()
            if not tables:
                logger.warning("Scraper: no tables found — returning empty list")
                add_message("No tables found — returning empty list")
                run.status = "success"
                db.session.commit()
                return []

            for i, table in enumerate(tables):
                if i >= len(TABLE_SOURCES):
                    logger.debug(f"Scraper: skipping table index {i} beyond configured sources")
                    break

                source = TABLE_SOURCES[i]
                headers = extract_headers(table)
                logger.debug(f"Scraper: table {i} headers: {headers}")
                rows = extract_rows(table, headers)
                logger.info(f"Scraper: extracted {len(rows)} rows from table {i} (source={source})")
                add_message(f"Extracted {len(rows)} rows from table {i} (source={source})")

                for row_index, row in enumerate(rows):
                    lead = {
                        "source": source,
                        "key": guess_primary_key(row),
                        "fetched_at": datetime.now(),
                        "url": PORTAL_URL,
                        "row_index": row_index,
                        "row": row
                    }
                    leads.append(lead)

            logger.info(f"Scraper: total leads extracted: {len(leads)}")
            add_message(f"Total leads extracted: {len(leads)}")
            run.phase_extraction = f"Extraction terminée: {len(leads)} leads"
            run.status = "success"
            db.session.commit()

        except Exception as e:
            logger.error(f"Scraper: unexpected error during fetch_leads: {e}")
            add_message(f"Error during fetch: {e}")
            run.status = "failed"
            run.details = str(e)
            db.session.commit()
            raise
        finally:
            try:
                context.close()
            except Exception:
                pass
            try:
                browser.close()
            except Exception:
                pass
            set_running(False)
            add_message("Scraper: run finished")

    return leads