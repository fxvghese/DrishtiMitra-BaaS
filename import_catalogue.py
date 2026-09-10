#!/usr/bin/env python

from dotenv import load_dotenv

load_dotenv()

"""Import catalogue data into Supabase/PostgreSQL database.

This script imports Open Food Facts and Flipkart catalogue data into the
reference_products table using the existing importer functions.

Usage:
    # For local development (SQLite)
    python import_catalogue.py

    # For production (Supabase PostgreSQL) - set DATABASE_URL in .env first
    DATABASE_URL="postgresql://..." python import_catalogue.py

The script uses the DATABASE_URL from the project's .env file.
"""

import os
import sys
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database.client import SessionLocal
from backend.services.catalogue import import_open_food_facts, import_flipkart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for catalogue import."""
    logger.info("Starting catalogue import...")
    
    # Verify environment
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not set in environment. Please check your .env file.")
        sys.exit(1)
    
    logger.info(f"Using database: {database_url.split('@')[-1] if '@' in database_url else database_url}")
    
    db = SessionLocal()
    try:
        logger.info("Starting Open Food Facts import...")
        off_metrics = import_open_food_facts(db)
        logger.info(f"Open Food Facts import completed: {off_metrics}")

        logger.info("Starting Flipkart import...")
        fk_metrics = import_flipkart(db)
        logger.info(f"Flipkart import completed: {fk_metrics}")

        # Summary
        total_inserted = off_metrics.get("inserted", 0) + fk_metrics.get("inserted", 0)
        total_updated = off_metrics.get("updated", 0) + fk_metrics.get("updated", 0)
        total_errors = off_metrics.get("errors", 0) + fk_metrics.get("errors", 0)
        
        logger.info("=" * 50)
        logger.info("IMPORT SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total records inserted: {total_inserted}")
        logger.info(f"Total records updated: {total_updated}")
        logger.info(f"Total errors: {total_errors}")
        logger.info(f"Open Food Facts: {off_metrics}")
        logger.info(f"Flipkart: {fk_metrics}")
        
        if total_errors > 0:
            logger.warning(f"Import completed with {total_errors} errors. Check logs for details.")
            sys.exit(1)
        else:
            logger.info("Import completed successfully!")
            
    except Exception as exc:
        logger.error(f"Import failed: {exc}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    import os
    import sys
    main()