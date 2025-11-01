import os
import logging
from logger import get_logger
from app_factory import create_app
from scraper_selenium import scrape_tesla_leads

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
