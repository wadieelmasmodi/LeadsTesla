"""Cookie management for Tesla authentication bypass."""
import os
import json
from datetime import datetime
from logger import get_logger

COOKIES_FILE = "/data/tesla_cookies.json"
logger = get_logger('COOKIES')

def save_cookies(cookies_dict):
    """
    Save cookies to file.
    
    Args:
        cookies_dict: Dict or list of cookies from browser
    """
    with open(COOKIES_FILE, 'w') as f:
        json.dump({
            'cookies': cookies_dict,
            'saved_at': datetime.utcnow().isoformat()
        }, f, indent=2)
    logger.info(f"Cookies sauvegardés: {len(cookies_dict)} cookies")

def load_cookies():
    """
    Load cookies from file.
    
    Returns:
        List of cookies or None if file doesn't exist
    """
    if not os.path.exists(COOKIES_FILE):
        logger.warning("Aucun fichier de cookies trouvé")
        return None
    
    try:
        with open(COOKIES_FILE, 'r') as f:
            data = json.load(f)
            cookies = data.get('cookies', [])
            saved_at = data.get('saved_at', 'unknown')
            logger.info(f"Cookies chargés: {len(cookies)} cookies (sauvegardés le {saved_at})")
            return cookies
    except Exception as e:
        logger.error(f"Erreur chargement cookies: {e}")
        return None

def cookies_exist():
    """Check if cookies file exists."""
    exists = os.path.exists(COOKIES_FILE)
    logger.debug(f"Cookies existent: {exists}")
    return exists

def delete_cookies():
    """Delete cookies file."""
    if os.path.exists(COOKIES_FILE):
        os.remove(COOKIES_FILE)
        logger.info("Cookies supprimés")
        return True
    logger.warning("Aucun fichier de cookies à supprimer")
    return False
