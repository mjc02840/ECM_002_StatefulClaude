#!/usr/bin/env python3
"""
ECM Phase 1 Ingest: Parse Bash trap log and populate ecm_actions.

Reads /tmp/ecm-bash-commands.log, parses pipe-delimited format:
  ISO8601_timestamp|exit_code|working_dir|shell_pid|command

Deduplicates by content-hash (ignores timestamp variations of same command).
Inserts into ecm_actions (FTS5) and ecm_actions_details (metadata + JSON).

Tracks ingest state to avoid re-processing:
  /tmp/ecm-bash-ingest-state.json

Idempotent: Safe to run multiple times (deduplication handles it).
"""

import sqlite3
import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime

DB_PATH = "/mnt/ecm-ram/ecm-hot.db"
LOG_FILE = "/tmp/ecm-bash-commands.log"
STATE_FILE = "/tmp/ecm-bash-ingest-state.json"

def load_state():
    """Load previous ingest state (line count, last timestamp)."""
    if Path(STATE_FILE).exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_line": 0, "last_timestamp": None, "entries_processed": 0}

def save_state(state):
    """Save ingest state for next run."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def parse_bash_log_line(line):
    """
    Parse pipe-delimited Bash trap log line.
    Format: timestamp|exit_code|working_dir|shell_pid|command

    Returns dict or None if parsing fails.
    """
    try:
        parts = line.strip().split('|', 4)
        if len(parts) < 5:
            return None

        return {
            'timestamp_iso': parts[0],
            'exit_code': int(parts[1]),
            'working_dir': parts[2],
            'shell_pid': parts[3],
            'command': parts[4]
        }
    except (ValueError, IndexError):
        return None

def compute_content_hash(action_dict):
    """Hash the essential command content (ignore timestamp)."""
    content = f"{action_dict['command']}|{action_dict['working_dir']}"
    return hashlib.md5(content.encode()).hexdigest()

def action_exists(cursor, content_hash):
    """Check if this action (by content) already exists."""
    cursor.execute(
        "SELECT action_id FROM ecm_actions_details WHERE content_hash = ?",
        (content_hash,)
    )
    return cursor.fetchone() is not None

def insert_bash_action(cursor, action):
    """Insert bash command into ecm_actions + ecm_actions_details."""
    content_hash = compute_content_hash(action)

    # Skip if duplicate
    if action_exists(cursor, content_hash):
        return False

    # Build indexable text for FTS5
    indexable = f"{action['command']} {action['working_dir']}"

    # Full details as JSON
    details = {
        'working_dir': action['working_dir'],
        'shell_pid': action['shell_pid'],
        'duration_ms': None  # Could measure if we had two timestamps
    }

    # Insert into FTS5 table
    cursor.execute(
        """
        INSERT INTO ecm_actions(
            action_type, timestamp_iso, actor, target, exit_code, indexable_text
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            'bash',
            action['timestamp_iso'],
            'cli_user',  # Could extract from shell context
            action['command'],
            action['exit_code'],
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
            'bash',
            action['timestamp_iso'],
            'cli_user',
            action['command'],
            action['exit_code'],
            json.dumps(details),
            content_hash
        )
    )

    return True

def ingest_bash_log():
    """Main ingest logic."""
    if not Path(LOG_FILE).exists():
        print(f"ℹ No log file yet: {LOG_FILE}")
        print("  Run: source ~/.bashrc")
        print("  Then: Execute some commands")
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
            action = parse_bash_log_line(line)
            if action and insert_bash_action(cursor, action):
                new_count += 1

        state['last_line'] = len(lines)
        state['entries_processed'] += new_count
        state['last_timestamp'] = datetime.now().isoformat()

        conn.commit()

        if new_count > 0:
            print(f"✓ Ingested {new_count} new bash commands")
            print(f"  Total processed: {state['entries_processed']}")
            print(f"  Timestamp: {state['last_timestamp']}")
        else:
            print("ℹ No new commands since last ingest")

        save_state(state)

    except sqlite3.Error as e:
        print(f"✗ Database error: {e}")
        sys.exit(1)
    finally:
        conn.close()

def show_recent():
    """Show last 5 ingested commands."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT timestamp_iso, target, exit_code FROM ecm_actions_details
            WHERE action_type = 'bash'
            ORDER BY created_at DESC
            LIMIT 5
            """
        )
        rows = cursor.fetchall()
        if rows:
            print("\nRecent commands in ECM:")
            for ts, cmd, code in rows:
                code_str = "✓" if code == 0 else f"✗({code})"
                print(f"  {ts} {code_str} {cmd[:60]}")
    except sqlite3.Error:
        pass
    finally:
        conn.close()

if __name__ == "__main__":
    print("ECM Phase 1 Bash Command Ingest")
    print(f"Log: {LOG_FILE}")
    print(f"Database: {DB_PATH}\n")

    ingest_bash_log()
    show_recent()
