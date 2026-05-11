#!/usr/bin/env python3
"""
ECM Health Report — System Status Snapshot with Microsecond Precision

Captures comprehensive ECM 002 health metrics every run.
Stores as pipe-delimited JSON for trend analysis and graphing.
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DB_PATH = "/mnt/ecm-ram/ecm-hot.db"
SSD_BACKUP_PATH = "/var/www/html/PQ/0510/ecm-archive-ssd.db"
HEALTH_LOG = "/tmp/ecm-health-log.jsonl"

def get_microsecond_timestamp():
    """Return ISO 8601 timestamp with microsecond precision (3 decimal places)."""
    now = datetime.now()
    return now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

def get_database_stats():
    """Collect statistics from both databases."""
    stats = {
        'timestamp': get_microsecond_timestamp(),
        'status': 'GREEN'
    }

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Total record count
        cursor.execute("SELECT COUNT(*) FROM ecm_actions_details")
        stats['total_actions'] = cursor.fetchone()[0]

        # Action type breakdown
        cursor.execute("""
            SELECT action_type, COUNT(*) as count
            FROM ecm_actions_details
            GROUP BY action_type
            ORDER BY count DESC
        """)
        stats['by_action_type'] = {row[0]: row[1] for row in cursor.fetchall()}

        # Most recent action
        cursor.execute("""
            SELECT timestamp_iso FROM ecm_actions_details
            ORDER BY timestamp_iso DESC LIMIT 1
        """)
        latest = cursor.fetchone()
        stats['latest_action_timestamp'] = latest[0] if latest else None

        # Data freshness (seconds since last action)
        cursor.execute("""
            SELECT MAX(created_at) FROM ecm_actions_details
        """)
        last_created = cursor.fetchone()[0]
        if last_created:
            last_dt = datetime.fromisoformat(last_created)
            now = datetime.now()
            age_seconds = (now - last_dt).total_seconds()
            stats['freshness_seconds'] = int(age_seconds)
        else:
            stats['freshness_seconds'] = None

        # Timestamp integrity check
        cursor.execute("""
            SELECT COUNT(*) FROM ecm_actions_details
            WHERE timestamp_iso IS NULL OR timestamp_iso = '' OR timestamp_iso = 'Z'
        """)
        corrupt_count = cursor.fetchone()[0]
        stats['corrupt_timestamps'] = corrupt_count
        stats['timestamp_integrity_percent'] = round(
            ((stats['total_actions'] - corrupt_count) / stats['total_actions'] * 100)
            if stats['total_actions'] > 0 else 100, 1
        )

        # Database file sizes
        try:
            ram_size = Path(DB_PATH).stat().st_size / (1024**2)
            stats['ram_db_size_mb'] = round(ram_size, 1)
        except:
            stats['ram_db_size_mb'] = None

        try:
            ssd_size = Path(SSD_BACKUP_PATH).stat().st_size / (1024**2)
            stats['ssd_db_size_mb'] = round(ssd_size, 1)
        except:
            stats['ssd_db_size_mb'] = None

        # Database sync status
        if stats['ram_db_size_mb'] and stats['ssd_db_size_mb']:
            size_diff = abs(stats['ram_db_size_mb'] - stats['ssd_db_size_mb'])
            stats['databases_in_sync'] = size_diff < 0.1  # Allow 0.1MB tolerance
        else:
            stats['databases_in_sync'] = False

        # Deduplication stats (content_hash uniqueness)
        cursor.execute("""
            SELECT COUNT(DISTINCT content_hash), COUNT(*)
            FROM ecm_actions_details
            WHERE content_hash IS NOT NULL
        """)
        unique_hashes, total_with_hash = cursor.fetchone()
        if total_with_hash > 0:
            dedup_ratio = (total_with_hash - unique_hashes) / total_with_hash * 100
            stats['deduplication_percent'] = round(dedup_ratio, 1)
            stats['deduplicated_records'] = total_with_hash - unique_hashes
        else:
            stats['deduplication_percent'] = 0
            stats['deduplicated_records'] = 0

        conn.close()

    except sqlite3.Error as e:
        stats['status'] = 'RED'
        stats['error'] = str(e)
        return stats

    # Health status determination
    if stats['corrupt_timestamps'] > 10:
        stats['status'] = 'YELLOW'
    if stats['freshness_seconds'] and stats['freshness_seconds'] > 300:
        stats['status'] = 'YELLOW'
    if not stats['databases_in_sync']:
        stats['status'] = 'YELLOW'
    if stats['total_actions'] == 0:
        stats['status'] = 'RED'

    return stats

def log_health_report(stats):
    """Append health report to pipe-delimited JSONL log."""
    try:
        json_str = json.dumps(stats)
        log_entry = f"{stats['timestamp']}|{json_str}\n"

        with open(HEALTH_LOG, 'a') as f:
            f.write(log_entry)

        return True
    except IOError as e:
        print(f"✗ Error writing to health log: {e}")
        return False

def display_report(stats):
    """Pretty-print health report to stdout."""
    print(f"\n{'='*60}")
    print(f"ECM 002 HEALTH REPORT")
    print(f"{'='*60}")
    print(f"Timestamp:     {stats['timestamp']}")
    print(f"Status:        {stats['status']}")
    print(f"\nACTION COUNTS:")
    print(f"  Total:       {stats.get('total_actions', 'N/A'):,} actions")

    if 'by_action_type' in stats:
        for action_type in sorted(stats['by_action_type'].keys()):
            count = stats['by_action_type'][action_type]
            print(f"  {action_type:10s} {count:,}")

    print(f"\nDATA FRESHNESS:")
    freshness = stats.get('freshness_seconds', -1)
    if freshness >= 0:
        print(f"  Age:         {freshness} seconds")
        freshness_status = "✓ FRESH" if freshness < 120 else "⚠ STALE" if freshness < 300 else "✗ OLD"
        print(f"  Status:      {freshness_status}")
    else:
        print(f"  Age:         N/A")

    print(f"\nTIMESTAMP INTEGRITY:")
    print(f"  Valid:       {stats.get('timestamp_integrity_percent', 0)}%")
    print(f"  Corrupt:     {stats.get('corrupt_timestamps', 0)} records")

    print(f"\nDATABASE STATUS:")
    print(f"  RAM:         {stats.get('ram_db_size_mb', 'N/A')} MB")
    print(f"  SSD Backup:  {stats.get('ssd_db_size_mb', 'N/A')} MB")
    sync_status = "✓ SYNCED" if stats.get('databases_in_sync') else "✗ OUT OF SYNC"
    print(f"  Sync:        {sync_status}")

    print(f"\nDEDUPLICATION:")
    print(f"  Ratio:       {stats.get('deduplication_percent', 0)}%")
    print(f"  Filtered:    {stats.get('deduplicated_records', 0)} records")

    if 'latest_action_timestamp' in stats and stats['latest_action_timestamp']:
        print(f"\nLATEST ACTION:")
        print(f"  Timestamp:   {stats['latest_action_timestamp']}")

    print(f"{'='*60}\n")

if __name__ == "__main__":
    stats = get_database_stats()

    if log_health_report(stats):
        print("✓ Health report logged")

    display_report(stats)

    if stats['status'] == 'RED':
        sys.exit(1)
