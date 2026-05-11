#!/usr/bin/env python3
"""
ECM Phase 3 Ingest: Parse Fossil commit log and populate ecm_actions.

Reads /tmp/ecm-fossil-commits.log, parses pipe-delimited format:
  ISO8601_timestamp|commit_hash|user|message|files_changed|repo_path

Deduplicates by content-hash (commit hash + message).
Inserts into ecm_actions layer (same as Bash and SSH phases).

Tracks ingest state in /tmp/ecm-fossil-ingest-state.json.
"""

import sqlite3
import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime

DB_PATH = "/mnt/ecm-ram/ecm-hot.db"
LOG_FILE = "/tmp/ecm-fossil-commits.log"
STATE_FILE = "/tmp/ecm-fossil-ingest-state.json"

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

def parse_fossil_log_line(line):
    """
    Parse pipe-delimited Fossil commit log line.
    Format: timestamp|commit_hash|user|message|files_changed|repo_path

    Returns dict or None if parsing fails.
    """
    try:
        parts = line.strip().split('|', 5)
        if len(parts) < 6:
            return None

        return {
            'timestamp_iso': parts[0],
            'commit_hash': parts[1],
            'user': parts[2],
            'message': parts[3],
            'files_changed': int(parts[4]) if parts[4].isdigit() else 0,
            'repo_path': parts[5]
        }
    except (ValueError, IndexError):
        return None

def compute_content_hash(commit):
    """Hash the essential commit content (ignore timestamp)."""
    content = f"{commit['commit_hash']}|{commit['message']}|{commit['repo_path']}"
    return hashlib.md5(content.encode()).hexdigest()

def commit_exists(cursor, content_hash):
    """Check if this commit already exists."""
    cursor.execute(
        "SELECT action_id FROM ecm_actions_details WHERE content_hash = ?",
        (content_hash,)
    )
    return cursor.fetchone() is not None

def insert_fossil_commit(cursor, commit):
    """Insert Fossil commit into ecm_actions."""
    content_hash = compute_content_hash(commit)

    # Skip if duplicate
    if commit_exists(cursor, content_hash):
        return False

    # Build indexable text for FTS5
    # Include message for full-text search
    indexable = f"fossil commit {commit['commit_hash']} {commit['user']} {commit['message']}"

    # Build target summary
    target = f"fossil-commit {commit['commit_hash']} {commit['user']}"

    # Full details as JSON
    details = {
        'commit_hash': commit['commit_hash'],
        'user': commit['user'],
        'message': commit['message'],
        'files_changed': commit['files_changed'],
        'repository': commit['repo_path']
    }

    # Insert into FTS5 table
    cursor.execute(
        """
        INSERT INTO ecm_actions(
            action_type, timestamp_iso, actor, target, exit_code, indexable_text
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            'fossil',
            commit['timestamp_iso'],
            commit['user'],
            target,
            0,  # Commits always succeed (if they're logged, they committed)
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
            'fossil',
            commit['timestamp_iso'],
            commit['user'],
            target,
            0,
            json.dumps(details),
            content_hash
        )
    )

    return True

def ingest_fossil_log():
    """Main ingest logic."""
    if not Path(LOG_FILE).exists():
        print(f"ℹ No Fossil commit log yet: {LOG_FILE}")
        print("  Install post-commit hook in Fossil repository")
        print("  Then make a commit to generate log entries")
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
            commit = parse_fossil_log_line(line)
            if commit and insert_fossil_commit(cursor, commit):
                new_count += 1

        state['last_line'] = len(lines)
        state['entries_processed'] += new_count
        state['last_timestamp'] = datetime.now().isoformat()

        conn.commit()

        if new_count > 0:
            print(f"✓ Ingested {new_count} new Fossil commits")
            print(f"  Total processed: {state['entries_processed']}")
            print(f"  Timestamp: {state['last_timestamp']}")
        else:
            print("ℹ No new commits since last ingest")

        save_state(state)

    except sqlite3.Error as e:
        print(f"✗ Database error: {e}")
        sys.exit(1)
    finally:
        conn.close()

def show_recent():
    """Show last 5 ingested commits."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT timestamp_iso, actor, target FROM ecm_actions_details
            WHERE action_type = 'fossil'
            ORDER BY created_at DESC
            LIMIT 5
            """
        )
        rows = cursor.fetchall()
        if rows:
            print("\nRecent Fossil commits in ECM:")
            for ts, user, target in rows:
                print(f"  {ts} {user} {target}")
    except sqlite3.Error:
        pass
    finally:
        conn.close()

if __name__ == "__main__":
    print("ECM Phase 3 Fossil Commit Ingest")
    print(f"Log: {LOG_FILE}")
    print(f"Database: {DB_PATH}\n")

    ingest_fossil_log()
    show_recent()
