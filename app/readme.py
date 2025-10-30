"""README generator for webhook documentation."""
import json
import os
from typing import Dict
import logging

def generate_readme(example_payload: Dict, path: str, logger: logging.Logger) -> None:
    """Generate README file documenting webhook payload format.
    
    Args:
        example_payload: Example lead data structure
        path: Path where to save the README
        logger: Logger instance
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    content = """# Tesla Partner Portal Webhook Documentation

## Description
This document describes the JSON payload format sent to the configured n8n webhook for each new lead detected.

## Payload Structure
```json
{}
```

## Field Definitions

### Root Level
- `source`: Source table identifier (tesla.com or shop.tesla.com)
- `key`: Unique identifier for the lead
- `fetched_at`: ISO timestamp when lead was fetched
- `url`: Portal URL where lead was found
- `row_index`: Index of the lead's row in source table
- `row`: Actual lead data (see below)

### Row Fields
{}

## Notes

- Headers are normalized: lowercase, no accents, spaces/punctuation replaced with underscore
- Primary key selection:
  1. `numero_d_installation` if present
  2. `numero_de_confirmation` if present
  3. `id` if present
  4. SHA-256 hash (first 8 chars) of sorted row data if no other key available
""".format(
        json.dumps(example_payload, indent=2, ensure_ascii=False),
        '\n'.join(f"- `{k}`: {v if v else 'Empty string'}" 
                 for k, v in example_payload['row'].items())
    )
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    logger.info(f"README generated at {path}")