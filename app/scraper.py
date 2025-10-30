"""Web scraper for Tesla Partner Portal leads."""
import hashlib
import json
import random
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging
import socket
from playwright.sync_api import sync_playwright
from config import PORTAL_URL, PAGE_TIMEOUT, TABLE_SOURCES
from utils_text import normalize_key
from auth import login_if_needed
from models import db, ScraperAttempt

def extract_headers(table) -> List[str]:
    """Extract and normalize table headers."""
    # Try thead first
    headers = table.query_selector_all('thead th')
    if not headers:
        # Fallback to first row
        headers = table.query_selector_all('tr:first-child th')
    
    return [normalize_key(header.text_content().strip()) for header in headers]

def extract_rows(table, headers: List[str]) -> List[Dict]:
    """Extract rows from table and map to headers."""
    rows = []
    for tr in table.query_selector_all('tbody tr'):
        cells = tr.query_selector_all('td')
        if len(cells) == len(headers):
            row = {
                headers[i]: cells[i].text_content().strip()
                for i in range(len(headers))
            }
            rows.append(row)
    return rows

def guess_primary_key(row: Dict) -> str:
    """Determine primary key for a lead row."""
    # Try preferred fields in order
    for field in ['numero_d_installation', 'numero_de_confirmation', 'id']:
        if field in row and row[field]:
            return row[field]
            
    # Fallback: create stable hash of sorted row items
    row_str = json.dumps(dict(sorted(row.items())), ensure_ascii=False)
    return hashlib.sha256(row_str.encode()).hexdigest()[:8]

def log_scraper_attempt(success: bool, error: str = None):
    """Log a scraper connection attempt."""
    attempt = ScraperAttempt(
        success=success,
        ip_address=socket.gethostbyname(socket.gethostname()),
        error=error
    )
    db.session.add(attempt)
    db.session.commit()

def random_delay():
    """Wait for a random time between 5 and 20 minutes."""
    delay = random.randint(5 * 60, 20 * 60)  # Convert to seconds
    time.sleep(delay)

def fetch_leads(logger: logging.Logger) -> List[Dict]:
    """Fetch all leads from Tesla Partner Portal.

    Logs progress at key steps so callers can follow what happened.
    Raises exceptions on critical failures so callers can record attempt status.
    """
    leads: List[Dict] = []
    logger.info("Scraper: starting new run")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            logger.info(f"Scraper: navigating to {PORTAL_URL}")
            page.goto(PORTAL_URL, timeout=PAGE_TIMEOUT * 1000)
            logger.info("Scraper: page loaded, performing login if needed")
            try:
                login_if_needed(page)
                logger.info("Scraper: login check complete")
            except Exception as e:
                logger.error(f"Scraper: login failed or raised: {e}")
                raise

            logger.info("Scraper: waiting for leads tables to appear")
            page.wait_for_selector('table', timeout=PAGE_TIMEOUT * 1000)

            tables = page.query_selector_all('table')
            logger.info(f"Scraper: found {len(tables)} table(s) on the page")
            if not tables:
                logger.warning("Scraper: no tables found — returning empty list")
                return []

            for i, table in enumerate(tables):
                if i >= len(TABLE_SOURCES):
                    logger.debug(f"Scraper: skipping table index {i} beyond configured sources")
                    break

                source = TABLE_SOURCES[i]
                headers = extract_headers(table)
                logger.debug(f"Scraper: table {i} headers: {headers}")
                rows = extract_rows(table, headers)
                logger.info(f"Scraper: extracted {len(rows)} rows from table {i} (source={source})")

                for row_index, row in enumerate(rows):
                    lead = {
                        "source": source,
                        "key": guess_primary_key(row),
                        "fetched_at": datetime.now(),
                        "url": PORTAL_URL,
                        "row_index": row_index,
                        "row": row
                    }
                    leads.append(lead)

            logger.info(f"Scraper: total leads extracted: {len(leads)}")

        except Exception as e:
            logger.error(f"Scraper: unexpected error during fetch_leads: {e}")
            raise
        finally:
            try:
                context.close()
            except Exception:
                pass
            try:
                browser.close()
            except Exception:
                pass

    return leads