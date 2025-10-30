"""Authentication module for Tesla Partner Portal."""
from typing import Optional
import pyotp
from playwright.sync_api import Page
from config import (
    TESLA_EMAIL, TESLA_PASS, TOTP_SECRET,
    SEL_EMAIL_INPUT, SEL_NEXT_BTN, SEL_PASS_INPUT,
    SEL_SIGNIN_BTN, SEL_2FA_INPUT, SEL_VERIFY_BTN,
    AUTH_TIMEOUT
)

class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass

def login_if_needed(page: Page) -> None:
    """Handle login flow if login page is detected.
    
    Raises:
        AuthenticationError: If login fails or required credentials are missing
    """
    # Check if email input is present
    email_input = page.query_selector(SEL_EMAIL_INPUT)
    if not email_input:
        return  # Already logged in
        
    if not all([TESLA_EMAIL, TESLA_PASS, TOTP_SECRET]):
        raise AuthenticationError("Missing required credentials in environment variables")
    
    try:
        # Enter email
        page.fill(SEL_EMAIL_INPUT, TESLA_EMAIL, timeout=AUTH_TIMEOUT * 1000)
        page.click(SEL_NEXT_BTN, timeout=AUTH_TIMEOUT * 1000)
        
        # Enter password
        page.fill(SEL_PASS_INPUT, TESLA_PASS, timeout=AUTH_TIMEOUT * 1000)
        page.click(SEL_SIGNIN_BTN, timeout=AUTH_TIMEOUT * 1000)
        
        # Handle 2FA
        if page.query_selector(SEL_2FA_INPUT):
            totp = pyotp.TOTP(TOTP_SECRET)
            code = totp.now()
            page.fill(SEL_2FA_INPUT, code, timeout=AUTH_TIMEOUT * 1000)
            page.click(SEL_VERIFY_BTN, timeout=AUTH_TIMEOUT * 1000)
            
        # Wait for navigation to complete
        page.wait_for_load_state('networkidle', timeout=AUTH_TIMEOUT * 1000)
        
    except Exception as e:
        raise AuthenticationError(f"Login failed: {str(e)}")