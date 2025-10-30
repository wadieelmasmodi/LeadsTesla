"""State management for tracking processed leads."""
import json
import os
from typing import Dict, List, Set
from config import STATE_FILE

def load_state() -> dict:
    """Load seen keys from state file."""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        return {"seen_keys": []}
    except Exception as e:
        # If any error occurs, return empty state
        return {"seen_keys": []}

def save_state(state: dict) -> None:
    """Save seen keys to state file."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)