"""Text utilities for normalizing headers and strings."""
import re
import unicodedata

def strip_accents(s: str) -> str:
    """Remove accents from string while preserving base characters."""
    return ''.join(c for c in unicodedata.normalize('NFKD', s)
                  if not unicodedata.combining(c))

def normalize_key(header: str) -> str:
    """Convert header to normalized key format.
    
    Converts to lowercase, removes accents, replaces spaces/punctuation with underscore,
    and compacts multiple underscores.
    """
    # Convert to lowercase and strip accents
    text = strip_accents(header.lower())
    
    # Replace spaces and punctuation with underscore
    text = re.sub(r'[^\w\s]', '_', text)
    text = re.sub(r'\s+', '_', text)
    
    # Compact multiple underscores
    text = re.sub(r'_+', '_', text)
    
    # Remove leading/trailing underscores
    return text.strip('_')