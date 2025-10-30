"""Web interface for Tesla Leads dashboard."""
import os
from datetime import datetime
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer
import requests
from models import db, User, LoginAttempt, Lead
from logger import get_logger
from config import N8N_WEBHOOK_URL

# Configuration
DOMAIN = "https://api2.energum.earth"
ADMIN_EMAIL = "contact@energum.earth"
SECRET_KEY = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')

app = Flask(__name__)
app.config.update(
    SECRET_KEY=SECRET_KEY,
    SQLALCHEMY_DATABASE_URI=SQLALCHEMY_DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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
    """Dashboard principal avec les 3 tableaux."""
    successful_logins = LoginAttempt.query.filter_by(success=True)\
        .order_by(LoginAttempt.timestamp.desc()).limit(10).all()
        
    failed_logins = LoginAttempt.query.filter_by(success=False)\
        .order_by(LoginAttempt.timestamp.desc()).limit(10).all()
        
    latest_leads = Lead.query.order_by(Lead.fetched_at.desc()).limit(10).all()
    
    return render_template('dashboard.html',
                         successful_logins=successful_logins,
                         failed_logins=failed_logins,
                         latest_leads=latest_leads)

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
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé')
            return redirect(url_for('register'))
            
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        user = User(
            email=email,
            password_hash=password_hash,
            validation_token=os.urandom(32).hex()
        )
        
        db.session.add(user)
        db.session.commit()
        
        send_validation_email(user)
        flash('Inscription réussie. Attendez la validation par email.')
        return redirect(url_for('login'))
        
    return render_template('register.html')

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

@app.route('/health')
def health_check():
    """Health check endpoint for Coolify."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

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
    database_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    _ensure_db_dir(database_uri)
    with app.app_context():
        try:
            logger.info(f"Initializing database at {database_uri}")
            db.create_all()
        except Exception as e:
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
    app.run(host='0.0.0.0', port=8000)


if __name__ == '__main__':
    init_db_and_run()