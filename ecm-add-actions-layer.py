#!/usr/bin/env python3
"""
ECM Phase 1: Add ecm_actions layer to existing FTS5 database.

Creates two new tables:
- ecm_actions (FTS5): Full-text searchable action summaries
- ecm_actions_details: JSON metadata for each action

Idempotent: Safe to run multiple times (CREATE TABLE IF NOT EXISTS).
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = "/mnt/ecm-ram/ecm-hot.db"
BACKUP_PATH = "/var/www/html/PQ/0510/ecm-archive-ssd.db"

def create_actions_layer():
    """Create FTS5 ecm_actions table and supporting structures."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # FTS5 table for full-text searchable action summaries
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS ecm_actions USING fts5(
                action_type,
                timestamp_iso,
                actor,
                target,
                exit_code,
                indexable_text,
                tokenize = 'porter'
            )
        """)

        # Regular table for full JSON details (FTS5 can't store arbitrary data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ecm_actions_details (
                action_id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                timestamp_iso TEXT NOT NULL,
                actor TEXT,
                target TEXT,
                exit_code INTEGER,
                details_json TEXT,
                content_hash TEXT UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Index for fast lookups by timestamp and action_type
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_actions_timestamp
            ON ecm_actions_details(timestamp_iso DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_actions_type
            ON ecm_actions_details(action_type)
        """)

        conn.commit()
        print(f"✓ Created ecm_actions FTS5 layer in {DB_PATH}")
        print("  - FTS5 table: ecm_actions")
        print("  - Details table: ecm_actions_details")
        print("  - Indexes: timestamp, action_type")

    except sqlite3.Error as e:
        print(f"✗ Error creating tables: {e}")
        sys.exit(1)
    finally:
        conn.close()

def verify_schema():
    """Verify tables exist and are accessible."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM ecm_actions")
        count = cursor.fetchone()[0]
        print(f"✓ Schema verified: ecm_actions table exists ({count} rows)")

        cursor.execute("SELECT COUNT(*) FROM ecm_actions_details")
        count = cursor.fetchone()[0]
        print(f"✓ Schema verified: ecm_actions_details table exists ({count} rows)")

    except sqlite3.Error as e:
        print(f"✗ Schema verification failed: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    print("ECM Phase 1: Adding ecm_actions layer...")
    print(f"Database: {DB_PATH}\n")

    if not Path(DB_PATH).exists():
        print(f"✗ Database not found: {DB_PATH}")
        print(f"  Run this first: /var/www/html/PQ/0510/create-ecm-fts5-multitier.py")
        sys.exit(1)

    create_actions_layer()
    verify_schema()
    print("\n✓ Phase 1 schema ready for ingest")
