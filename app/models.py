"""Database models for the web interface."""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_validated = db.Column(db.Boolean, default=False)
    validation_token = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LoginAttempt(db.Model):
    """Model to track login attempts."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    success = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))

class Lead(db.Model):
    """Model to store leads from Tesla Portal."""
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50))
    key = db.Column(db.String(50), unique=True)
    fetched_at = db.Column(db.DateTime)
    data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)