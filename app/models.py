"""Database models for the web interface."""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class ScraperAttempt(db.Model):
    """Model to track scraper connection attempts to Tesla."""
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(45))
    error = db.Column(db.Text, nullable=True)

class User(UserMixin, db.Model):
    """User model for authentication."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_validated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LoginAttempt(db.Model):
    """Model to track login attempts."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    success = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))


class ScraperRun(db.Model):
    """Model to store each execution of the Tesla scraper with phase details and screenshot."""
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    phase_connexion = db.Column(db.String(120))
    phase_extraction = db.Column(db.String(120))
    screenshot_path = db.Column(db.String(256), nullable=True)
    status = db.Column(db.String(32), default='pending')  # success, failed, pending
    details = db.Column(db.Text, nullable=True)