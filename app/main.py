"""Main entry point for Tesla leads scraper."""
import sys
from typing import Dict, List, Set
from datetime import datetime
from flask import Flask
from logger import get_logger
from scraper import fetch_leads
from state import load_state, save_state
from notifier import post_to_n8n, NotificationError
from readme import generate_readme
from auth import AuthenticationError
from config import README_FILE
from models import db, Lead
from web import app as web_app

def main() -> None:
    """Main execution flow."""
    # Initialize logger
    logger = get_logger(__name__)
    
    # Start run
    logger.info("Tentative de connexion...")
    
    try:
        # Fetch leads
        leads = fetch_leads(logger)
        logger.info("Connexion réussie et page chargée.")
        
        # Load seen keys
        state = load_state()
        seen_keys: Set[str] = set(state.get('seen_keys', []))
        new_leads_count = 0
        
        # Process leads
        for lead in leads:
            # Log all leads
            logger.info(
                f"Lead détecté [{lead['source']}] (row {lead['row_index']}) "
                f"key={lead['key']} -> {lead['row']}"
            )

            # Send new leads to webhook
            if lead['key'] not in seen_keys:
                try:
                    post_to_n8n(lead, logger)
                    seen_keys.add(lead['key'])
                    new_leads_count += 1
                except NotificationError as e:
                    logger.error(str(e))

        # Save updated state and store leads in database
        state['seen_keys'] = list(seen_keys)
        save_state(state)

        with web_app.app_context():
            for lead_data in leads:
                existing_lead = Lead.query.filter_by(key=lead_data['key']).first()
                if not existing_lead:
                    lead = Lead(
                        source=lead_data['source'],
                        key=lead_data['key'],
                        fetched_at=datetime.fromisoformat(lead_data['fetched_at']),
                        data=lead_data
                    )
                    db.session.add(lead)
            db.session.commit()

        # Generate/update README if we have leads
        if leads:
            generate_readme(leads[0], README_FILE, logger)

        logger.info(f"Run terminé. Nouveaux leads envoyés : {new_leads_count}")

    except AuthenticationError as e:
        logger.error(f"Échec de connexion: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erreur inattendue: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()