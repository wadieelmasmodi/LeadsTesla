"""Logging configuration for the application."""
import logging
import os
import sys
from typing import Optional
from config import LOG_FILE

def get_logger(name: str, log_to_file: bool = True) -> logging.Logger:
    """
    Configure and return a unified logger.
    
    Format: YYYY-MM-DD HH:MM:SS [MODULE] [LEVEL] Message
    Example: 2025-11-01 23:00:58 [SCRAPER] [INFO] Démarrage du scraper
    
    Args:
        name: Module name (e.g., 'SCRAPER', 'WEB', 'COOKIES')
        log_to_file: Whether to log to file (default True)
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid adding handlers multiple times
    if not logger.handlers:
        # Unified format: timestamp [module] [level] message
        formatter = logging.Formatter(
            '%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler (always enabled)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler (optional)
        if log_to_file:
            try:
                os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
                file_handler = logging.FileHandler(LOG_FILE)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.warning(f"Could not create file handler: {e}")
    
    return logger