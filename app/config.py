"""Configuration module for Tesla leads scraper."""
import os
from typing import Optional

# Required environment variables
PORTAL_URL: str = os.getenv('PORTAL_URL', 'https://partners.tesla.com/home/fr-fr/leads')
TESLA_EMAIL: Optional[str] = os.getenv('TESLA_EMAIL')
TESLA_PASS: Optional[str] = os.getenv('TESLA_PASS')
TOTP_SECRET: Optional[str] = os.getenv('TOTP_SECRET')
N8N_WEBHOOK_URL: Optional[str] = os.getenv('N8N_WEBHOOK_URL')

# File paths
STATE_FILE: str = os.getenv('STATE_FILE', '/data/state.json')
LOG_FILE: str = os.getenv('LOG_FILE', '/data/leads.log')
README_FILE: str = os.getenv('README_FILE', '/data/README_webhook.md')

# Table configuration
TABLE_SOURCES: list[str] = os.getenv('TABLE_SOURCES', 'tesla.com,shop.tesla.com').split(',')

# Optional UI selectors with defaults
SEL_EMAIL_INPUT: str = os.getenv('SEL_EMAIL_INPUT', 'input[type="email"]')
SEL_NEXT_BTN: str = os.getenv('SEL_NEXT_BTN', 'button[type="submit"]')
SEL_PASS_INPUT: str = os.getenv('SEL_PASS_INPUT', 'input[type="password"]')
SEL_SIGNIN_BTN: str = os.getenv('SEL_SIGNIN_BTN', 'button[type="submit"]')
SEL_2FA_INPUT: str = os.getenv('SEL_2FA_INPUT', 'input[type="text"]')
SEL_VERIFY_BTN: str = os.getenv('SEL_VERIFY_BTN', 'button:has-text("Verify")')

# Timeouts
PAGE_TIMEOUT: float = 60.0  # seconds
AUTH_TIMEOUT: float = 5.0   # seconds for auth prompts