"""Web scraper for Tesla Partner Portal leads - Using Selenium."""
import os
import sys
import time
import json
from datetime import datetime
from typing import Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from models import db, ScraperRun, Lead
from config import PORTAL_URL
from cookies_manager import load_cookies, cookies_exist
from logger import get_logger

# Use unified logger
logger = get_logger('SCRAPER')

def scrape_tesla_leads() -> Dict:
    """
    Scrape Tesla Partner Portal for leads using Selenium.
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
    logger.info("🚀 DÉMARRAGE DU SCRAPER TESLA (SELENIUM)")
    logger.info("="*80)
    
    driver = None
    try:
        # Configure Chrome options
        logger.info("🌐 Configuration de Chrome avec anti-détection...")
        run.phase_connexion = "Configuration du navigateur"
        db.session.commit()
        
        chrome_options = Options()
        
        # Check if we should run in headless mode
        headless_mode = os.getenv('SCRAPER_HEADLESS', 'true').lower() == 'true'
        
        if headless_mode:
            logger.info("🕶️ Mode headless activé")
            chrome_options.add_argument('--headless')
        else:
            logger.info("👁️ Mode visible activé (pour résolution manuelle du captcha)")
            
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Launch Chrome
        logger.info("🚀 Lancement de Chrome...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.set_page_load_timeout(60)
        
        # Get credentials (needed if cookies fail)
        email = os.getenv('TESLA_EMAIL')
        password = os.getenv('TESLA_PASS')
        
        logger.info(f"📧 Email configuré: {'✅ Oui' if email else '❌ Non'}")
        logger.info(f"🔑 Password configuré: {'✅ Oui' if password else '❌ Non'}")
        
        # Check if we have saved cookies
        has_cookies = cookies_exist()
        logger.info(f"🍪 Cookies sauvegardés: {'✅ Oui' if has_cookies else '❌ Non'}")
        
        if has_cookies:
            logger.info("🍪 Chargement des cookies pour authentification automatique...")
            run.phase_connexion = "Chargement cookies"
            db.session.commit()
            
            # First, navigate to domain to set cookies
            logger.info("🔗 Navigation initiale vers auth.tesla.com...")
            driver.get("https://auth.tesla.com")
            time.sleep(2)
            
            # Load and inject cookies
            cookies = load_cookies()
            if cookies:
                logger.info(f"📦 {len(cookies)} cookies chargés depuis le fichier")
                
                # Filter cookies - only keep Tesla domains
                tesla_cookies = [c for c in cookies if 'tesla.com' in c.get('domain', '').lower()]
                
                if not tesla_cookies:
                    logger.warning("⚠️ AUCUN COOKIE TESLA DÉTECTÉ!")
                    logger.warning("Les cookies chargés proviennent d'autres domaines (ex: api2.energum.earth)")
                    logger.warning("Le scraper va fallback au login classique")
                    should_login = True
                elif len(tesla_cookies) < len(cookies):
                    non_tesla = len(cookies) - len(tesla_cookies)
                    logger.warning(f"⚠️ {non_tesla} cookies ignorés (domaines non-Tesla)")
                    logger.info(f"✅ {len(tesla_cookies)} cookies Tesla détectés")
                
                if tesla_cookies:
                    # Group Tesla cookies by domain
                    cookies_by_domain = {}
                    for cookie in tesla_cookies:
                        domain = cookie.get('domain', '')
                        if domain not in cookies_by_domain:
                            cookies_by_domain[domain] = []
                        cookies_by_domain[domain].append(cookie)
                    
                    logger.info(f"🌐 Domaines Tesla trouvés: {list(cookies_by_domain.keys())}")
                    
                    # Inject cookies for each domain
                    injected_count = 0
                    failed_count = 0
                    
                    for domain, domain_cookies in cookies_by_domain.items():
                        # Navigate to the appropriate Tesla domain
                        if domain.startswith('.'):
                            domain_clean = domain[1:]  # Remove leading dot
                        else:
                            domain_clean = domain
                        
                        # Use https for navigation
                        nav_url = f"https://{domain_clean}"
                        logger.info(f"🔗 Navigation vers {nav_url} pour injecter {len(domain_cookies)} cookies...")
                        
                        try:
                            driver.get(nav_url)
                            time.sleep(2)
                            
                            # Inject cookies for this domain
                            for cookie in domain_cookies:
                                try:
                                    # Clean cookie: keep only essential fields
                                    cookie_clean = {
                                        'name': cookie['name'],
                                        'value': cookie['value'],
                                        'domain': cookie.get('domain', domain_clean),
                                        'path': cookie.get('path', '/'),
                                        'secure': cookie.get('secure', True),
                                        'httpOnly': cookie.get('httpOnly', False)
                                    }
                                    
                                    # Remove None values
                                    cookie_clean = {k: v for k, v in cookie_clean.items() if v is not None}
                                    
                                    driver.add_cookie(cookie_clean)
                                    injected_count += 1
                                    logger.debug(f"   ✅ Cookie '{cookie['name']}' injecté")
                                    
                                except Exception as e:
                                    failed_count += 1
                                    logger.warning(f"   ⚠️ Échec injection cookie '{cookie.get('name', '?')}': {str(e)[:100]}")
                        
                        except Exception as e:
                            logger.error(f"❌ Erreur navigation vers {nav_url}: {e}")
                            failed_count += len(domain_cookies)
                    
                    logger.info(f"📊 Résultat injection: {injected_count} réussis, {failed_count} échoués")
                    if injected_count > 0:
                        run.phase_connexion = f"Cookies: {injected_count} injectés ✅"
                        should_login = False
                    else:
                        logger.warning("⚠️ Aucun cookie injecté, passage au login classique")
                        should_login = True
                    db.session.commit()
                else:
                    should_login = True
            
            # Now navigate to portal with cookies
            logger.info(f"🔗 Navigation vers {PORTAL_URL} avec cookies...")
            driver.get(PORTAL_URL)
            time.sleep(5)
            
            current_url = driver.current_url
            logger.info(f"📍 URL après cookies: {current_url}")
            
            # Check if we're authenticated
            if 'auth' not in current_url.lower() and 'login' not in current_url.lower():
                logger.info("✅ Authentification par cookies réussie!")
                run.phase_connexion = "Authentifié via cookies"
                db.session.commit()
                # Skip login process
                should_login = False
            else:
                logger.warning("⚠️ Cookies expirés ou invalides, passage au login classique...")
                run.phase_connexion = "Cookies invalides - login requis"
                db.session.commit()
                should_login = True
        else:
            # No cookies, need to login
            logger.info("🔐 Pas de cookies - login requis")
            should_login = True
            
            # Navigate to Tesla portal
            logger.info(f"🔗 Navigation vers {PORTAL_URL}")
            run.phase_connexion = "Navigation vers le portail"
            db.session.commit()
            
            driver.get(PORTAL_URL)
            logger.info("⏳ Attente du chargement de la page (10 secondes)...")
            time.sleep(10)  # Give the page time to fully load
        
        # If we used cookies and are authenticated, skip login
        if has_cookies and not should_login:
            logger.info("✅ Authentification par cookies - skip login")
        else:
            current_url = driver.current_url
            logger.info(f"📍 URL actuelle: {current_url}")
            
            if not email or not password:
                raise Exception("Credentials TESLA_EMAIL et TESLA_PASS requis pour le login")
        
        # Check if we're on login/auth page
        if should_login and ('auth' in current_url.lower() or 'login' in current_url.lower() or 'signin' in current_url.lower()):
            logger.info("🔐 Page d'authentification détectée")
            run.phase_connexion = "Sur la page de login"
            db.session.commit()
            
            # Take screenshot of login page for debugging
            login_screenshot = f"scraper_run_{run.id}_login_page.png"
            login_screenshot_path = f"/app/static/{login_screenshot}"
            os.makedirs('/app/static', exist_ok=True)
            driver.save_screenshot(login_screenshot_path)
            logger.info(f"📸 Screenshot de la page de login: {login_screenshot}")
            
            # STEP 1: Enter email with identity field
            logger.info("📧 Étape 1: Recherche du champ identity...")
            logger.info("⏳ Attente de 5 secondes pour le formulaire...")
            time.sleep(5)
            
            try:
                wait = WebDriverWait(driver, 20)
                
                # Use only the identity selector (confirmed working)
                logger.info("🔍 Recherche du champ: input[name='identity']")
                email_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[name="identity"]')))
                logger.info("✅ Champ identity trouvé!")
                
                # Fill the email field
                email_field.clear()
                email_field.send_keys(email)
                logger.info("✅ Email renseigné")
                time.sleep(2)
                
                # Look for Next button
                try:
                    next_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Next') or contains(text(), 'Suivant') or contains(text(), 'Continue') or @type='submit']")
                    logger.info("⏭️ Clic sur le bouton Suivant...")
                    next_button.click()
                    time.sleep(3)
                except NoSuchElementException:
                    logger.warning("⚠️ Bouton 'Suivant' non trouvé, on continue...")
                
                # STEP 2: Enter password
                logger.info("🔑 Étape 2: Recherche du champ password...")
                password_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"], input[name="password"]')))
                logger.info("✅ Champ password trouvé")
                
                password_field.clear()
                password_field.send_keys(password)
                logger.info("✅ Password renseigné")
                time.sleep(1)
                
                # Click Sign In button
                try:
                    signin_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Sign In') or contains(text(), 'Connexion') or contains(text(), 'Log In') or @type='submit']")
                    logger.info("🔐 Clic sur le bouton de connexion...")
                    signin_button.click()
                    time.sleep(5)
                    
                    final_url = driver.current_url
                    logger.info(f"📍 URL après login: {final_url}")
                    
                    if 'leads' in final_url or 'home' in final_url:
                        logger.info("✅ Authentification réussie!")
                        run.phase_connexion = "Authentification réussie"
                    else:
                        logger.warning(f"⚠️ Authentification incertaine, URL: {final_url}")
                        run.phase_connexion = f"Auth incertaine"
                        
                except NoSuchElementException:
                    logger.error("❌ Bouton 'Sign In' non trouvé")
                    run.phase_connexion = "Erreur: bouton signin introuvable"
                    
            except TimeoutException:
                logger.error("❌ Timeout: champs de formulaire non trouvés")
                run.phase_connexion = "Erreur: timeout formulaire"
        else:
            logger.info("✅ Déjà authentifié")
            run.phase_connexion = "Déjà authentifié"
        
        db.session.commit()
        
        # Take screenshot
        screenshot_filename = f"scraper_run_{run.id}_page.png"
        screenshot_full_path = f"/app/static/{screenshot_filename}"
        os.makedirs('/app/static', exist_ok=True)
        
        logger.info(f"💾 Sauvegarde screenshot...")
        driver.save_screenshot(screenshot_full_path)
        run.screenshot_path = screenshot_filename
        db.session.commit()
        logger.info(f"✅ Screenshot sauvegardé: {screenshot_filename}")
        
        # Wait for content
        logger.info("⏳ Attente du chargement du contenu (5 secondes pour Angular)...")
        run.phase_extraction = "Attente du contenu"
        db.session.commit()
        time.sleep(5)
        
        # Extract content
        logger.info("🔍 Analyse du contenu de la page...")
        run.phase_extraction = "Analyse du contenu"
        db.session.commit()
        
        page_text = driver.find_element(By.TAG_NAME, 'body').text
        logger.info(f"📄 Longueur du contenu texte: {len(page_text)} caractères")
        logger.info(f"📄 Aperçu: {page_text[:100]}")
        
        # Find tables
        tables = driver.find_elements(By.TAG_NAME, 'table')
        logger.info(f"📊 Nombre de tableaux trouvés: {len(tables)}")
        
        leads_data = []
        
        for idx, table in enumerate(tables):
            logger.info(f"📊 Traitement du tableau {idx + 1}/{len(tables)}...")
            
            try:
                rows = table.find_elements(By.TAG_NAME, 'tr')
                logger.info(f"   ↳ Nombre de lignes: {len(rows)}")
                
                if len(rows) > 0:
                    # Extract headers
                    headers = []
                    first_row = rows[0]
                    header_cells = first_row.find_elements(By.TAG_NAME, 'th') or first_row.find_elements(By.TAG_NAME, 'td')
                    
                    for cell in header_cells:
                        headers.append(cell.text.strip())
                    
                    logger.info(f"   ↳ En-têtes: {headers}")
                    
                    # Extract data rows
                    for row_idx, row in enumerate(rows[1:], 1):
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        
                        if len(cells) > 0:
                            row_data = {}
                            for cell_idx, cell in enumerate(cells):
                                header = headers[cell_idx] if cell_idx < len(headers) else f"column_{cell_idx}"
                                row_data[header] = cell.text.strip()
                            
                            leads_data.append({
                                'table': idx,
                                'row': row_idx,
                                'data': row_data
                            })
                    
                    logger.info(f"   ✅ {len(rows)-1} lignes extraites")
                    
            except Exception as e:
                logger.error(f"   ❌ Erreur tableau {idx + 1}: {e}")
        
        # Save leads
        logger.info(f"💾 Sauvegarde de {len(leads_data)} leads...")
        run.phase_extraction = f"Extraction: {len(leads_data)} leads trouvés"
        
        saved_count = 0
        for lead_data in leads_data:
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
        if driver:
            try:
                driver.quit()
                logger.info("🔒 Navigateur fermé")
            except:
                pass
    
    return result
