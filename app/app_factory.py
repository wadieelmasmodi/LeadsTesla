"""Flask application factory."""
import os
from datetime import datetime
import socket
from flask import Flask
from models import db

def create_app():
    """Create Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.config.update(
        SECRET_KEY=os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex()),
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///app.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    
    # Initialize extensions
    db.init_app(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return {
            'status': 'ok',
            'timestamp': datetime.now().isoformat()
        }
    
    # Debug info endpoint
    @app.route('/debug')
    def debug_info():
        """Return debug information."""
        from flask import jsonify
        return jsonify({
            'hostname': socket.gethostname(),
            'environment': dict(os.environ),
            'working_directory': os.getcwd(),
            'database_url': app.config['SQLALCHEMY_DATABASE_URI']
        })
        
    return app