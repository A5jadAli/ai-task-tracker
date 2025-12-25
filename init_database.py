#!/usr/bin/env python3
"""
Database Initialization Script
Run this to create all database tables
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.database import Base, engine
from app.config import settings
from loguru import logger


def init_database():
    """Initialize database tables"""
    try:
        logger.info("Initializing database...")
        logger.info(f"Database URL: {settings.DATABASE_URL}")

        # Create all tables
        Base.metadata.create_all(bind=engine)

        logger.info("✓ Database tables created successfully!")
        logger.info("Tables created:")
        for table in Base.metadata.tables.keys():
            logger.info(f"  - {table}")

        return True

    except Exception as e:
        logger.error(f"✗ Failed to initialize database: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Database Initialization")
    print("=" * 60 + "\n")

    success = init_database()

    if success:
        print("\n" + "=" * 60)
        print("  ✅ Database initialization complete!")
        print("=" * 60 + "\n")
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("  ❌ Database initialization failed!")
        print("=" * 60 + "\n")
        sys.exit(1)
