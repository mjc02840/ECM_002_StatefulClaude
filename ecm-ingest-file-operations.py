#!/usr/bin/env python3
"""
ECM Phase 4 Ingest: Parse file operations log and populate ecm_actions.

Reads /tmp/ecm-file-operations.log, parses pipe-delimited format:
  ISO8601_timestamp|operation|path|size|user|permissions

Deduplicates by content-hash (operation + path + timestamp + size).
Inserts into ecm_actions layer (same as Bash, SSH, Fossil).

Tracks ingest state in /tmp/ecm-file-ingest-state.json.
"""

import sqlite3
import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime

DB_PATH = "/mnt/ecm-ram/ecm-hot.db"
LOG_FILE = "/tmp/ecm-file-operations.log"
STATE_FILE = "/tmp/ecm-file-ingest-state.json"

def load_state():
    """Load previous ingest state."""
    if Path(STATE_FILE).exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_line": 0, "last_timestamp": None, "entries_processed": 0}

def save_state(state):
    """Save ingest state for next run."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def parse_file_ops_line(line):
    """
    Parse pipe-delimited file operations log line.
    Format: timestamp|operation|path|size|user|permissions

    Returns dict or None if parsing fails.
    """
    try:
        parts = line.strip().split('|', 5)
        if len(parts) < 6:
            return None

        return {
            'timestamp_iso': parts[0],
            'operation': parts[1],
            'path': parts[2],
            'size': int(parts[3]) if parts[3].isdigit() else 0,
            'user': parts[4],
            'permissions': parts[5]
        }
    except (ValueError, IndexError):
        return None

def compute_content_hash(file_op):
    """Hash the essential file operation content."""
    content = f"{file_op['operation']}|{file_op['path']}|{file_op['timestamp_iso']}|{file_op['size']}"
    return hashlib.md5(content.encode()).hexdigest()

def file_op_exists(cursor, content_hash):
    """Check if this file operation already exists."""
    cursor.execute(
        "SELECT action_id FROM ecm_actions_details WHERE content_hash = ?",
        (content_hash,)
    )
    return cursor.fetchone() is not None

def insert_file_operation(cursor, file_op):
    """Insert file operation into ecm_actions."""
    content_hash = compute_content_hash(file_op)

    # Skip if duplicate
    if file_op_exists(cursor, content_hash):
        return False

    # Build indexable text for FTS5
    # Include path for full-text search
    indexable = f"file {file_op['operation']} {file_op['path']} {file_op['user']}"

    # Build target summary
    op_shortname = file_op['operation'][:6]  # "create", "write", etc.
    target = f"file-{op_shortname} {Path(file_op['path']).name}"

    # Full details as JSON
    details = {
        'operation': file_op['operation'],
        'path': file_op['path'],
        'size_bytes': file_op['size'],
        'user': file_op['user'],
        'permissions': file_op['permissions']
    }

    # Exit code: 0 for all file operations (they happened)
    # Could be: 0 = successful, 1 = error (if we detect errors)
    exit_code = 0

    try:
        # Insert into FTS5 table
        cursor.execute(
            """
            INSERT INTO ecm_actions(
                action_type, timestamp_iso, actor, target, exit_code, indexable_text
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                'file',
                file_op['timestamp_iso'],
                file_op['user'],
                target,
                exit_code,
                indexable
            )
        )

        # Insert into details table
        cursor.execute(
            """
            INSERT INTO ecm_actions_details(
                action_type, timestamp_iso, actor, target, exit_code,
                details_json, content_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                'file',
                file_op['timestamp_iso'],
                file_op['user'],
                target,
                exit_code,
                json.dumps(details),
                content_hash
            )
        )

        return True
    except sqlite3.Error as e:
        print(f"✗ Error inserting file operation: {e}")
        return False

def ingest_file_operations():
    """Main ingest logic."""
    if not Path(LOG_FILE).exists():
        print(f"ℹ No file operations log yet: {LOG_FILE}")
        print("  File monitor may not have run yet (waits for files to be modified)")
        return

    state = load_state()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    new_count = 0

    try:
        with open(LOG_FILE) as f:
            lines = f.readlines()

        # Process only new lines since last ingest
        for i, line in enumerate(lines[state['last_line']:], start=state['last_line']):
            file_op = parse_file_ops_line(line)
            if file_op and insert_file_operation(cursor, file_op):
                new_count += 1

        state['last_line'] = len(lines)
        state['entries_processed'] += new_count
        state['last_timestamp'] = datetime.now().isoformat()

        conn.commit()

        if new_count > 0:
            print(f"✓ Ingested {new_count} new file operations")
            print(f"  Total processed: {state['entries_processed']}")
            print(f"  Timestamp: {state['last_timestamp']}")
        else:
            if len(lines) > 0:
                print(f"ℹ Found {len(lines)} file operations, all previously ingested")
            else:
                print("ℹ No file operations since last ingest")

        save_state(state)

    except sqlite3.Error as e:
        print(f"✗ Database error: {e}")
        sys.exit(1)
    finally:
        conn.close()

def show_recent():
    """Show last 5 ingested file operations."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT timestamp_iso, target, json_extract(details_json, '$.size_bytes') FROM ecm_actions_details
            WHERE action_type = 'file'
            ORDER BY created_at DESC
            LIMIT 5
            """
        )
        rows = cursor.fetchall()
        if rows:
            print("\nRecent file operations in ECM:")
            for ts, target, size in rows:
                size_kb = int(size) // 1024 if size else 0
                print(f"  {ts} {target} ({size_kb} KB)")
    except sqlite3.Error:
        pass
    finally:
        conn.close()

if __name__ == "__main__":
    print("ECM Phase 4 File Operations Ingest")
    print(f"Log: {LOG_FILE}")
    print(f"Database: {DB_PATH}\n")

    ingest_file_operations()
    show_recent()
