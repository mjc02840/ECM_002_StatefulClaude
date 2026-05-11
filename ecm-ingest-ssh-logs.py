#!/usr/bin/env python3
"""
ECM Phase 2 Ingest: Parse /var/log/auth.log for SSH events.

Extracts:
- SSH login attempts (successful and failed)
- User, host, timestamp, authentication method
- Connection events (opened, closed)
- Port forwarding, key-based auth details

Inserts into ecm_actions layer (same schema as Phase 1).
Deduplicates by content-hash (event fingerprint).

Tracks state in /tmp/ecm-ssh-ingest-state.json to avoid re-processing.
"""

import sqlite3
import json
import hashlib
import sys
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DB_PATH = "/mnt/ecm-ram/ecm-hot.db"
LOG_FILE = "/var/log/auth.log"
STATE_FILE = "/tmp/ecm-ssh-ingest-state.json"

# SSH-related patterns to capture
SSH_PATTERNS = {
    'accepted_key': r'sshd\[\d+\]:\s+Accepted publickey for (\S+) from ([\d.]+) port (\d+)',
    'accepted_password': r'sshd\[\d+\]:\s+Accepted password for (\S+) from ([\d.]+) port (\d+)',
    'failed_auth': r'sshd\[\d+\]:\s+Failed password for (\S+) from ([\d.]+) port (\d+)',
    'invalid_user': r'sshd\[\d+\]:\s+Invalid user (\S+) from ([\d.]+)',
    'connection_closed': r'sshd\[\d+\]:\s+Connection closed by authenticating user (\S+) ([\d.]+)',
    'connection_reset': r'sshd\[\d+\]:\s+Connection reset by ([\d.]+)',
    'disconnected': r'sshd\[\d+\]:\s+Disconnected from (\S+) port (\d+) \[([\w]+)\]',
}

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

def parse_auth_log_line(line):
    """
    Parse auth.log line into structured format.
    Typical format: May 11 01:07:43 hostname sshd[1234]: message

    Returns dict with: timestamp_iso, raw_message, source
    """
    try:
        # Auth.log format: Month Day HH:MM:SS hostname service[pid]: message
        match = re.match(
            r'(\w+\s+\d+\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(sshd)\[(\d+)\]:\s+(.*)',
            line
        )
        if not match:
            return None

        time_str, hostname, service, pid, message = match.groups()

        return {
            'timestamp_str': time_str,
            'hostname': hostname,
            'service': service,
            'pid': pid,
            'message': message,
            'raw_line': line.strip()
        }
    except Exception:
        return None

def extract_ssh_event(parsed_line):
    """
    Extract SSH event from parsed log line.
    Returns: (event_type, details) or (None, None) if not an SSH event.
    """
    message = parsed_line['message']

    for event_type, pattern in SSH_PATTERNS.items():
        match = re.search(pattern, message)
        if match:
            return event_type, match.groups()

    return None, None

def compute_event_hash(event_type, details, hostname):
    """Hash event content to deduplicate."""
    content = f"{event_type}|{hostname}|{details}"
    return hashlib.md5(content.encode()).hexdigest()

def event_exists(cursor, content_hash):
    """Check if event already ingested."""
    cursor.execute(
        "SELECT action_id FROM ecm_actions_details WHERE content_hash = ?",
        (content_hash,)
    )
    return cursor.fetchone() is not None

def insert_ssh_event(cursor, parsed, event_type, event_details):
    """Insert SSH event into ecm_actions."""
    content_hash = compute_event_hash(event_type, event_details, parsed['hostname'])

    if event_exists(cursor, content_hash):
        return False

    # Convert May 11 01:07:43 to ISO format (add year and timezone)
    ts_str = parsed['timestamp_str']
    try:
        dt = datetime.strptime(f"2026 {ts_str}", "%Y %b %d %H:%M:%S")
        timestamp_iso = dt.isoformat() + "Z"
    except:
        timestamp_iso = datetime.now().isoformat() + "Z"

    # Build indexable text and details based on event type
    if event_type == 'accepted_key':
        user, host, port = event_details
        indexable = f"SSH accepted publickey {user} from {host} port {port}"
        target = f"ssh-key-auth {user}@{host}:{port}"
        details = {
            'auth_method': 'publickey',
            'user': user,
            'remote_host': host,
            'remote_port': port,
            'local_host': parsed['hostname']
        }
        exit_code = 0

    elif event_type == 'accepted_password':
        user, host, port = event_details
        indexable = f"SSH accepted password {user} from {host} port {port}"
        target = f"ssh-password-auth {user}@{host}:{port}"
        details = {
            'auth_method': 'password',
            'user': user,
            'remote_host': host,
            'remote_port': port,
            'local_host': parsed['hostname']
        }
        exit_code = 0

    elif event_type == 'failed_auth':
        user, host, port = event_details
        indexable = f"SSH failed password {user} from {host} port {port}"
        target = f"ssh-failed-auth {user}@{host}:{port}"
        details = {
            'auth_method': 'password',
            'user': user,
            'remote_host': host,
            'remote_port': port,
            'local_host': parsed['hostname'],
            'status': 'failed'
        }
        exit_code = 1

    elif event_type == 'invalid_user':
        user, host = event_details
        indexable = f"SSH invalid user {user} from {host}"
        target = f"ssh-invalid-user {user}@{host}"
        details = {
            'user': user,
            'remote_host': host,
            'local_host': parsed['hostname'],
            'status': 'invalid_user'
        }
        exit_code = 1

    elif event_type == 'connection_closed':
        user, host = event_details
        indexable = f"SSH connection closed {user} from {host}"
        target = f"ssh-conn-closed {user}@{host}"
        details = {
            'user': user,
            'remote_host': host,
            'local_host': parsed['hostname'],
            'reason': 'authentication_complete'
        }
        exit_code = 0

    elif event_type == 'connection_reset':
        host = event_details[0]
        indexable = f"SSH connection reset from {host}"
        target = f"ssh-conn-reset {host}"
        details = {
            'remote_host': host,
            'local_host': parsed['hostname'],
            'reason': 'connection_reset'
        }
        exit_code = 1

    elif event_type == 'disconnected':
        user, port, reason = event_details
        indexable = f"SSH disconnected {user} port {port} {reason}"
        target = f"ssh-disconnected {user}:{port}"
        details = {
            'user': user,
            'port': port,
            'reason': reason,
            'local_host': parsed['hostname']
        }
        exit_code = 0

    else:
        return False

    try:
        # Insert into FTS5 table
        cursor.execute(
            """
            INSERT INTO ecm_actions(
                action_type, timestamp_iso, actor, target, exit_code, indexable_text
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ('ssh', timestamp_iso, 'system', target, exit_code, indexable)
        )

        # Insert into details table
        cursor.execute(
            """
            INSERT INTO ecm_actions_details(
                action_type, timestamp_iso, actor, target, exit_code,
                details_json, content_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ('ssh', timestamp_iso, 'system', target, exit_code,
             json.dumps(details), content_hash)
        )

        return True
    except sqlite3.Error as e:
        print(f"✗ Error inserting SSH event: {e}")
        return False

def ingest_ssh_logs():
    """Main ingest logic for SSH events."""
    if not Path(LOG_FILE).exists():
        print(f"ℹ No auth log: {LOG_FILE}")
        return

    state = load_state()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    new_count = 0
    ssh_count = 0

    try:
        with open(LOG_FILE) as f:
            lines = f.readlines()

        # Process new lines since last ingest
        for i, line in enumerate(lines[state['last_line']:], start=state['last_line']):
            parsed = parse_auth_log_line(line)
            if parsed and 'sshd' in parsed['service']:
                ssh_count += 1
                event_type, event_details = extract_ssh_event(parsed)
                if event_type and insert_ssh_event(cursor, parsed, event_type, event_details):
                    new_count += 1

        state['last_line'] = len(lines)
        state['entries_processed'] += new_count
        state['last_timestamp'] = datetime.now().isoformat()

        conn.commit()

        if new_count > 0:
            print(f"✓ Ingested {new_count} new SSH events")
            print(f"  (Scanned {ssh_count} SSH-related lines)")
            print(f"  Total processed: {state['entries_processed']}")
        else:
            if ssh_count > 0:
                print(f"ℹ Found {ssh_count} SSH events, all previously ingested")
            else:
                print("ℹ No new SSH events since last ingest")

        save_state(state)

    except sqlite3.Error as e:
        print(f"✗ Database error: {e}")
        sys.exit(1)
    finally:
        conn.close()

def show_recent():
    """Show last 5 ingested SSH events."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT timestamp_iso, target, exit_code FROM ecm_actions_details
            WHERE action_type = 'ssh'
            ORDER BY created_at DESC
            LIMIT 5
            """
        )
        rows = cursor.fetchall()
        if rows:
            print("\nRecent SSH events in ECM:")
            for ts, target, code in rows:
                code_str = "✓" if code == 0 else f"✗({code})"
                print(f"  {ts} {code_str} {target}")
    except sqlite3.Error:
        pass
    finally:
        conn.close()

if __name__ == "__main__":
    print("ECM Phase 2 SSH Event Ingest")
    print(f"Source: {LOG_FILE}")
    print(f"Database: {DB_PATH}\n")

    ingest_ssh_logs()
    show_recent()
