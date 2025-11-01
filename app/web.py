"""Web interface for Tesla Leads dashboard."""
import os
from datetime import datetime
import bcrypt
import socket
import secrets
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer
from flask_cors import CORS
import requests
from models import db, User, LoginAttempt, Lead, ScraperAttempt, ScraperRun
import threading
from config import PORTAL_URL
from logger import get_logger

# Try to import scraper - log error if it fails
try:
    from scraper_selenium import scrape_tesla_leads
    SCRAPER_AVAILABLE = True
    print("✅ Scraper Selenium imported successfully")
except Exception as e:
    SCRAPER_AVAILABLE = False
    print(f"⚠️ Scraper import failed: {e}")
    print("Le scraper ne sera pas disponible")
    # Define a dummy function
    def scrape_tesla_leads():
        return {'status': 'failed', 'message': 'Scraper not available - Selenium not installed', 'leads_count': 0, 'leads': []}
from config import N8N_WEBHOOK_URL
from app_factory import create_app
from scraper_status import get_messages, is_running
# Optional: support Redis + RQ if REDIS_URL is provided in environment
try:
    from redis import Redis
    from rq import Queue
    REDIS_AVAILABLE = True
except Exception:
    REDIS_AVAILABLE = False

# Configuration
DOMAIN = os.getenv('DOMAIN', 'https://api2.energum.earth')
ADMIN_EMAIL = "contact@energum.earth"

# Create Flask application
app = create_app()
CORS(app)
SECRET_KEY = app.config['SECRET_KEY']
logger = get_logger(__name__)

# Initialize extensions
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize serializer for email tokens
serializer = URLSafeTimedSerializer(SECRET_KEY)

logger = get_logger(__name__)
serializer = URLSafeTimedSerializer(SECRET_KEY)

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.query.get(int(user_id))

def send_validation_email(user):
    """Send validation email with token."""
    token = serializer.dumps(user.email, salt='email-validation')
    validation_url = f"{DOMAIN}/validate/{token}"
    
    # Envoi vers webhook n8n pour l'email
    payload = {
        "to": ADMIN_EMAIL,
        "subject": "Nouvelle demande d'accès au dashboard Tesla Leads",
        "text": f"Un nouvel utilisateur demande l'accès:\nEmail: {user.email}\n\nPour valider: {validation_url}",
        "html": render_template('email/validation.html', 
                              user=user,
                              validation_url=validation_url)
    }
    
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            logger.info(f"Email de validation envoyé pour {user.email}")
        else:
            logger.error(f"Échec envoi email pour {user.email}: {response.status_code}")
    except Exception as e:
        logger.error(f"Erreur envoi email: {str(e)}")

@app.route('/')
@login_required
def dashboard():
    """Dashboard principal avec les 3 tableaux et pagination."""
    # Determine pages from query params
    try:
        leads_page = int(request.args.get('leads_page', 1))
    except ValueError:
        leads_page = 1

    try:
        success_page = int(request.args.get('success_page', 1))
    except ValueError:
        success_page = 1

    try:
        failed_page = int(request.args.get('failed_page', 1))
    except ValueError:
        failed_page = 1

    # Which tab should be active
    active_tab = request.args.get('tab', 'leads')

    latest_leads = Lead.query.order_by(Lead.fetched_at.desc()).paginate(page=leads_page, per_page=10, error_out=False)
    scraper_page = int(request.args.get('scraper_page', 1))
    scraper_runs = ScraperRun.query.order_by(ScraperRun.timestamp.desc()).paginate(page=scraper_page, per_page=10, error_out=False)

    return render_template('dashboard.html',
                         latest_leads=latest_leads,
                         scraper_runs=scraper_runs,
                         active_tab=active_tab,
                         portal_url=PORTAL_URL)


@app.route('/scrape-now', methods=['POST'])
@login_required
def scrape_now():
    """Trigger a scraping run in background and return immediately.

    If REDIS_URL is configured and RQ is available, enqueue the task into RQ.
    Otherwise, fall back to a local background thread.
    """
    redis_url = os.getenv('REDIS_URL')
    if redis_url and REDIS_AVAILABLE:
        try:
            conn = Redis.from_url(redis_url)
            q = Queue(connection=conn)
            q.enqueue('app.tasks.run_fetch_task')
            flash("Scrape en file d'attente (Redis/RQ).", 'info')
        except Exception as e:
            logger.error(f"Failed to enqueue job to RQ: {e}")
            flash("Impossible d'enregistrer le job RQ — exécution locale.", 'warning')
            def _background():
                with app.app_context():
                    try:
                        scrape_tesla_leads()
                    except Exception as e:
                        logger.error(f"Background scrape failed: {e}")

            thread = threading.Thread(target=_background, daemon=True)
            thread.start()
    else:
        def _background():
            with app.app_context():
                try:
                    scrape_tesla_leads()
                except Exception as e:
                    logger.error(f"Background scrape failed: {e}")

        thread = threading.Thread(target=_background, daemon=True)
        thread.start()
        flash('Scrape lancé en tâche de fond — vérifiez les logs ou le tableau pour les résultats.', 'info')

    # keep the user on the same tab if provided
    tab = request.args.get('tab', 'leads')
    return redirect(url_for('dashboard', tab=tab))


@app.route('/upload-cookies', methods=['POST'])
@login_required
def upload_cookies():
    """Upload Tesla cookies to bypass captcha."""
    try:
        from cookies_manager import save_cookies
        
        cookies_json = request.json
        if not cookies_json:
            return jsonify({'status': 'error', 'message': 'No cookies provided'}), 400
        
        save_cookies(cookies_json)
        logger.info(f"Cookies uploaded by {current_user.email}")
        
        return jsonify({
            'status': 'success',
            'message': f'{len(cookies_json)} cookies saved successfully',
            'count': len(cookies_json)
        })
        
    except Exception as e:
        logger.error(f"Error uploading cookies: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/cookies-status')
@login_required
def cookies_status():
    """Check if cookies are available."""
    try:
        from cookies_manager import cookies_exist
        exists = cookies_exist()
        return jsonify({'exists': exists})
    except Exception as e:
        return jsonify({'exists': False, 'error': str(e)})


@app.route('/cookies-export')
@login_required
def cookies_export_page():
    """Page to export and upload cookies."""
    return render_template('cookies_export.html')


@app.route('/scrape-status')
@login_required
def scrape_status():
    """Return recent scraper progress messages and running flag as JSON."""
    return jsonify({'running': is_running(), 'messages': get_messages()})

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de login."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        attempt = LoginAttempt(
            email=email,
            ip_address=request.remote_addr
        )
        
        if user and bcrypt.checkpw(password.encode(), user.password_hash):
            if not user.is_validated:
                flash("Votre compte n'est pas encore validé.")
                attempt.success = False
                db.session.add(attempt)
                db.session.commit()
                return redirect(url_for('login'))
                
            attempt.success = True
            db.session.add(attempt)
            login_user(user)
            db.session.commit()
            return redirect(url_for('dashboard'))
            
        attempt.success = False
        db.session.add(attempt)
        db.session.commit()
        flash('Email ou mot de passe incorrect')
        
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription."""
    try:
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            admin_key = request.form.get('admin_key')
            
            logger.info(f"Tentative d'inscription pour: {email}")
            
            if User.query.filter_by(email=email).first():
                flash('Cet email est déjà utilisé')
                return redirect(url_for('register'))
                
            # Vérification de la clé admin
            required_key = os.getenv('ADMIN_KEY')
            logger.info(f"État de la clé admin : {'configurée' if required_key else 'non configurée'}")
            
            if not required_key:
                logger.error("ADMIN_KEY environment variable not set!")
                flash('Inscription temporairement désactivée')
                return redirect(url_for('register'))
            
            # Conversion en string pour éviter les problèmes de type
            admin_key = str(admin_key or '')
            required_key = str(required_key)
            
            if not secrets.compare_digest(admin_key, required_key):
                logger.warning(f"Tentative d'inscription avec une clé invalide pour {email}")
                flash('Clé d\'inscription invalide')
                return redirect(url_for('register'))

            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            user = User(
                email=email,
                password_hash=password_hash,
                is_validated=True  # Auto-validation avec la bonne clé admin
            )
            
            try:
                db.session.add(user)
                db.session.commit()
                logger.info(f"Inscription réussie pour {email}")
                flash('Inscription réussie. Vous pouvez maintenant vous connecter.')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                logger.error(f"Erreur lors de l'inscription de {email}: {str(e)}")
                flash('Une erreur est survenue lors de l\'inscription. Veuillez réessayer.')
                return redirect(url_for('register'))
            
        return render_template('register.html')
        
    except Exception as e:
        logger.error(f"Erreur non gérée dans register: {str(e)}")
        flash('Une erreur inattendue est survenue. Veuillez réessayer.')
        return redirect(url_for('register'))



@app.route('/validate/<token>')
def validate_email(token):
    """Validation d'email via token."""
    try:
        email = serializer.loads(token, salt='email-validation', max_age=86400)
        user = User.query.filter_by(email=email).first()
        if user:
            user.is_validated = True
            db.session.commit()
            flash('Compte validé avec succès!')
        else:
            flash('Token invalide')
    except:
        flash('Le lien de validation est invalide ou expiré')
    return redirect(url_for('login'))

@app.route('/webhook/account-validation', methods=['POST'])
def account_validation_webhook():
    """Webhook pour la validation des comptes."""
    data = request.json
    if not data or 'email' not in data:
        return jsonify({'error': 'Invalid payload'}), 400
        
    user = User.query.filter_by(email=data['email']).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    user.is_validated = True
    db.session.commit()
    logger.info(f"Compte validé via webhook: {user.email}")
    
    return jsonify({'status': 'success'})

@app.route('/logout')
@login_required
def logout():
    """Déconnexion."""
    logout_user()
    return redirect(url_for('login'))



def _ensure_db_dir(database_uri: str) -> None:
    """Ensure the directory for the SQLite database exists.

    Accepts DATABASE_URL values like:
      - sqlite:////absolute/path/to/db.db
      - sqlite:///relative/path.db
    """
    db_path = None
    if database_uri.startswith('sqlite:////'):
        # absolute path: sqlite:////data/app.db -> /data/app.db
        db_path = database_uri.replace('sqlite:////', '/')
    elif database_uri.startswith('sqlite:///'):
        # relative path: sqlite:///data/app.db -> data/app.db (relative to CWD)
        db_path = database_uri.replace('sqlite:///', '')

    if db_path:
        dirpath = os.path.dirname(db_path)
        if dirpath:
            try:
                os.makedirs(dirpath, exist_ok=True)
            except Exception as e:
                logger.error(f"Impossible de créer le répertoire de la DB {dirpath}: {e}")

def init_db_and_run():
    """Initialize DB and run the Flask app."""
    logger.info("Starting application initialization...")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Files in current directory: {os.listdir('.')}")
    
    # Log all environment variables
    for key, value in os.environ.items():
        logger.info(f"ENV: {key}={value}")
    
    database_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    logger.info(f"Starting database initialization with URI: {database_uri}")
    
    _ensure_db_dir(database_uri)
    with app.app_context():
        try:
            logger.info(f"Initializing database at {database_uri}")
            # Try to check directory permissions
            if database_uri.startswith('sqlite:////'):
                db_path = database_uri.replace('sqlite:////', '/')
                dir_path = os.path.dirname(db_path)
                logger.info(f"Checking permissions for directory: {dir_path}")
                logger.info(f"Directory exists: {os.path.exists(dir_path)}")
                if os.path.exists(dir_path):
                    logger.info(f"Directory permissions: {oct(os.stat(dir_path).st_mode)[-3:]}")
                    logger.info(f"Directory owner: {os.stat(dir_path).st_uid}")
                    
            db.create_all()
            logger.info("Database initialization successful")
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            # Log detailed diagnostics to help debugging permission/path issues
            try:
                db_path = None
                if database_uri and database_uri.startswith('sqlite:'):
                    if database_uri.startswith('sqlite:////'):
                        db_path = database_uri.replace('sqlite:////', '/')
                    elif database_uri.startswith('sqlite:///'):
                        db_path = database_uri.replace('sqlite:///', '')
                dirpath = os.path.dirname(db_path) if db_path else None
                exists = os.path.exists(dirpath) if dirpath else False
                writable = os.access(dirpath, os.W_OK) if dirpath else False
            except Exception:
                exists = False
                writable = False

            logger.error(f"Failed to create DB ({database_uri}): {e}")
            logger.error(f"DB dir: {dirpath}, exists={exists}, writable={writable}")
            logger.error("Continuing to run the web server, but DB operations may fail.")
    # Run the Flask app
    port = int(os.getenv('PORT', 8000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port)


if __name__ == '__main__':
    try:
        init_db_and_run()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise