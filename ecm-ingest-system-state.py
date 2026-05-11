#!/usr/bin/env python3
"""
ECM Phase 5 Ingest: Parse system state log and populate ecm_actions.

Reads /tmp/ecm-system-state.log, parses JSON format:
  ISO8601_timestamp|{"cpu": {...}, "memory": {...}, "disk": {...}, ...}

Inserts into ecm_actions layer (same as other phases).
Tracks ingest state in /tmp/ecm-system-ingest-state.json.
"""

import sqlite3
import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime

DB_PATH = "/mnt/ecm-ram/ecm-hot.db"
LOG_FILE = "/tmp/ecm-system-state.log"
STATE_FILE = "/tmp/ecm-system-ingest-state.json"

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

def parse_system_state_line(line):
    """
    Parse pipe-delimited system state log line.
    Format: timestamp|json_metrics

    Returns dict or None if parsing fails.
    """
    try:
        parts = line.strip().split('|', 1)
        if len(parts) < 2:
            return None

        timestamp_iso = parts[0]
        metrics_json = json.loads(parts[1])

        return {
            'timestamp_iso': timestamp_iso,
            'metrics': metrics_json
        }
    except (ValueError, json.JSONDecodeError):
        return None

def compute_content_hash(state_entry):
    """Hash the essential state content (ignore minor fluctuations)."""
    # Round metrics to reduce hash variation from minor changes
    metrics = state_entry['metrics']
    rounded = {
        'cpu_load_1': round(metrics.get('cpu', {}).get('load_1min', 0), 1),
        'mem_percent': round(metrics.get('memory', {}).get('percent_used', 0)),
        'disk_percent': round(metrics.get('disk', {}).get('percent_used', 0))
    }
    content = json.dumps(rounded, sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()

def state_exists(cursor, content_hash):
    """Check if this state already exists (deduplicates similar metrics)."""
    cursor.execute(
        "SELECT action_id FROM ecm_actions_details WHERE content_hash = ?",
        (content_hash,)
    )
    return cursor.fetchone() is not None

def insert_system_state(cursor, state_entry):
    """Insert system state into ecm_actions."""
    content_hash = compute_content_hash(state_entry)

    # Skip if very similar state was recently logged
    if state_exists(cursor, content_hash):
        return False

    metrics = state_entry['metrics']

    # Build indexable text for FTS5
    mem_pct = metrics.get('memory', {}).get('percent_used', 0)
    cpu_load = metrics.get('cpu', {}).get('load_1min', 0)
    disk_pct = metrics.get('disk', {}).get('percent_used', 0)
    procs = metrics.get('processes', 0)

    indexable = (f"system state cpu load disk memory "
                f"mem={mem_pct:.0f}% cpu={cpu_load:.1f} "
                f"disk={disk_pct:.0f}% procs={procs}")

    # Build target summary
    target = f"system-state mem={mem_pct:.0f}% cpu={cpu_load:.1f}"

    # Full details as JSON
    details = {
        'cpu': metrics.get('cpu', {}),
        'memory': metrics.get('memory', {}),
        'disk': metrics.get('disk', {}),
        'network': metrics.get('network', {}),
        'processes': metrics.get('processes', 0)
    }

    # Exit code: 0 for all state snapshots
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
                'system',
                state_entry['timestamp_iso'],
                'monitor',
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
                'system',
                state_entry['timestamp_iso'],
                'monitor',
                target,
                exit_code,
                json.dumps(details),
                content_hash
            )
        )

        return True
    except sqlite3.Error as e:
        print(f"✗ Error inserting system state: {e}")
        return False

def ingest_system_state():
    """Main ingest logic."""
    if not Path(LOG_FILE).exists():
        print(f"ℹ No system state log yet: {LOG_FILE}")
        print("  Phase 5 capture may not have run yet")
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
            state_entry = parse_system_state_line(line)
            if state_entry and insert_system_state(cursor, state_entry):
                new_count += 1

        state['last_line'] = len(lines)
        state['entries_processed'] += new_count
        state['last_timestamp'] = datetime.now().isoformat()

        conn.commit()

        if new_count > 0:
            print(f"✓ Ingested {new_count} new system state snapshots")
            print(f"  Total processed: {state['entries_processed']}")
            print(f"  Timestamp: {state['last_timestamp']}")
        else:
            if len(lines) > 0:
                print(f"ℹ Found {len(lines)} state snapshots, all previously ingested")
            else:
                print("ℹ No system state data since last ingest")

        save_state(state)

    except sqlite3.Error as e:
        print(f"✗ Database error: {e}")
        sys.exit(1)
    finally:
        conn.close()

def show_recent():
    """Show last 5 ingested state snapshots."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT timestamp_iso, target FROM ecm_actions_details
            WHERE action_type = 'system'
            ORDER BY created_at DESC
            LIMIT 5
            """
        )
        rows = cursor.fetchall()
        if rows:
            print("\nRecent system state in ECM:")
            for ts, target in rows:
                print(f"  {ts} {target}")
    except sqlite3.Error:
        pass
    finally:
        conn.close()

if __name__ == "__main__":
    print("ECM Phase 5 System State Ingest")
    print(f"Log: {LOG_FILE}")
    print(f"Database: {DB_PATH}\n")

    ingest_system_state()
    show_recent()
