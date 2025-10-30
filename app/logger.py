"""Logging configuration for the application."""
import logging
import os
from typing import Optional
from config import LOG_FILE

def get_logger(name: str) -> logging.Logger:
    """Configure and return a logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid adding handlers multiple times
    if not logger.handlers:
        # Create formatters and handlers
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger