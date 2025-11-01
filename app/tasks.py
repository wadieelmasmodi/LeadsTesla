import os
import logging
from logger import get_logger
from app_factory import create_app

# Try to import scraper
try:
    from scraper_selenium import scrape_tesla_leads
    SCRAPER_AVAILABLE = True
except Exception as e:
    SCRAPER_AVAILABLE = False
    print(f"⚠️ Scraper import failed in tasks.py: {e}")
    def scrape_tesla_leads():
        return {'status': 'failed', 'message': 'Scraper not available', 'leads_count': 0, 'leads': []}

logger = get_logger(__name__)

def run_fetch_task():
    """Wrapper to run scraper in a task worker environment.

    This function is suitable to be enqueued into RQ. It creates an app
    context and runs the simplified scraper.
    """
    app = create_app()
    with app.app_context():
        try:
            result = scrape_tesla_leads()
            logger.info(f"Scraper finished: {result['status']} - {result['message']}")
        except Exception as e:
            logger.error(f"Task run_fetch_task failed: {e}")
