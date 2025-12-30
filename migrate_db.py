#!/usr/bin/env python3
"""
Simple database migration script to add implementation tracking columns.
Run this to update your database schema without alembic.
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env file")
    exit(1)

print(f"🔗 Connecting to database...")

try:
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        print("✅ Connected successfully!")

        # Check if columns already exist
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'tasks'
            AND column_name IN ('files_created', 'files_modified', 'implementation_summary', 'test_results')
        """))

        existing_columns = [row[0] for row in result]

        if len(existing_columns) == 4:
            print("✅ All columns already exist! Database is up to date.")
            exit(0)

        print(f"📊 Found {len(existing_columns)} existing columns: {existing_columns}")
        print("🔨 Adding missing columns...")

        # Add columns if they don't exist
        if 'files_created' not in existing_columns:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN files_created JSONB"))
            print("  ✓ Added files_created column")

        if 'files_modified' not in existing_columns:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN files_modified JSONB"))
            print("  ✓ Added files_modified column")

        if 'implementation_summary' not in existing_columns:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN implementation_summary TEXT"))
            print("  ✓ Added implementation_summary column")

        if 'test_results' not in existing_columns:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN test_results JSONB"))
            print("  ✓ Added test_results column")

        conn.commit()

        print("\n✅ Migration completed successfully!")
        print("🚀 You can now use the new features.")

except Exception as e:
    print(f"\n❌ Migration failed: {e}")
    print("\nTroubleshooting:")
    print("1. Check that PostgreSQL is running")
    print("2. Verify DATABASE_URL in .env file")
    print("3. Ensure the database exists")
    print("4. Check that you have permission to alter tables")
    exit(1)
