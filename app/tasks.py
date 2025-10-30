import os
import logging
from logger import get_logger
from app_factory import create_app
from scraper import fetch_leads
from scraper_status import add_message, set_running

logger = get_logger(__name__)

def run_fetch_task():
    """Wrapper to run fetch_leads in a task worker environment.

    This function is suitable to be enqueued into RQ. It creates an app
    context, runs the scraper and records progress via messages.
    """
    app = create_app()
    with app.app_context():
        set_running(True)
        try:
            fetch_leads(logger)
        except Exception as e:
            logger.error(f"Task run_fetch_task failed: {e}")
            add_message(f"Task error: {e}")
        finally:
            set_running(False)
