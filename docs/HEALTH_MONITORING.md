# Health Monitoring

**Understand and monitor your ECM_002_StatefulClaude system**

---

## What is Health Monitoring?

Every 5 minutes, `ecm-health-report.py` captures a snapshot of your system's status:
- How many actions have been captured
- How fresh the data is
- Whether databases are synced
- Any problems that need attention

---

## Checking Health

### View Latest Health Report

```bash
python3 /var/www/html/PQ/0510/ecm-health-report.py
```

Output:
```
============================================================
ECM 002 HEALTH REPORT
============================================================
Timestamp:     2026-05-11T10:30:45.123Z
Status:        GREEN

ACTION COUNTS:
  Total:       10,321 actions
  bash         8
  file         10,298
  fossil       5
  ssh          9
  system       1

DATA FRESHNESS:
  Age:         5 seconds
  Status:      ✓ FRESH

TIMESTAMP INTEGRITY:
  Valid:       100.0%
  Corrupt:     0 records

DATABASE STATUS:
  RAM:         14.0 MB
  SSD Backup:  14.0 MB
  Sync:        ✓ SYNCED

DEDUPLICATION:
  Ratio:       0.0%
  Filtered:    0 records
```

### Watch in Real-Time

```bash
tail -f /tmp/ecm-health.log
```

### Health History

All health reports stored in: `/tmp/ecm-health-log.jsonl`

Each line is pipe-delimited JSON:
```
2026-05-11T10:30:45.123Z|{"status":"GREEN","total_actions":10321,...}
```

---

## Health Status Meanings

### GREEN ✅
- All systems working
- Data is fresh (captured within 2 minutes)
- Databases synced
- Zero corruption
- Safe to use

### YELLOW ⚠️
- One or more issues detected
- Data might be slightly stale (5+ minutes old)
- Databases slightly out of sync
- Minor corruption (<10 records)
- Still functional, but investigate

### RED 🔴
- Critical problems
- No data captured
- Database failures
- Major corruption
- **Stop and investigate immediately**

---

## Key Metrics Explained

### Action Counts
Total actions captured across all 5 phases:
- **bash** — Shell commands
- **ssh** — Network connections
- **file** — File modifications
- **fossil** — Repository commits
- **system** — System snapshots

### Data Freshness
How old is the newest record?
- **Fresh:** <2 minutes (cron running normally)
- **Stale:** 2-5 minutes (possible delay)
- **Old:** >5 minutes (capture might have stopped)

### Timestamp Integrity
What percentage of records have valid timestamps?
- **100%:** Perfect
- **99%+:** Good
- **<99%:** Investigation needed
- **Corrupt records:** Count of invalid timestamps

### Database Status
Are your databases healthy?
- **RAM size:** Memory used (should grow slowly)
- **SSD size:** Backup size (should match RAM)
- **Sync status:** Do they match? (should be ✓ SYNCED)

### Deduplication Ratio
How many duplicate entries were filtered?
- **0%:** No duplicates (first run or good diversity)
- **1-5%:** Normal (some repeated activities)
- **>10%:** High duplication (same commands repeated)

---

## Common Health Scenarios

### Scenario 1: Fresh System
```
Status: GREEN
Total actions: 100
Data Freshness: 1 minute (Fresh)
Timestamp Integrity: 100%
```
**Meaning:** System just started, working perfectly

### Scenario 2: Running Smoothly
```
Status: GREEN
Total actions: 10,321
Data Freshness: 3 seconds (Fresh)
Timestamp Integrity: 100%
Database Sync: SYNCED
```
**Meaning:** All systems operational, data current

### Scenario 3: Slightly Delayed
```
Status: YELLOW
Total actions: 10,321
Data Freshness: 6 minutes (Stale)
Timestamp Integrity: 100%
Database Sync: SYNCED
```
**Meaning:** Capture delayed (cron might be busy), but databases OK

### Scenario 4: Sync Issues
```
Status: YELLOW
Total actions: 10,321
Database Status:
  RAM: 14.0 MB
  SSD: 13.8 MB
  Sync: OUT OF SYNC (size difference)
```
**Meaning:** RAM and SSD getting out of sync, sync job might be failing

### Scenario 5: Corruption Detected
```
Status: YELLOW
Timestamp Integrity: 97%
Corrupt: 309 records
```
**Meaning:** Some old records have bad timestamps (might be from Phase 4), but system is working

---

## Monitoring Best Practices

### Daily Check
```bash
python3 /var/www/html/PQ/0510/ecm-health-report.py | grep "Status:"
```

Should show: `Status: GREEN`

### Weekly Review
```bash
sqlite3 /mnt/ecm-ram/ecm-hot.db \
  "SELECT DATE(timestamp_iso) as date, COUNT(*) as actions 
   FROM ecm_actions_details 
   WHERE timestamp_iso > datetime('now', '-7 days')
   GROUP BY date"
```

Should show consistent daily action counts

### Monthly Summary
```bash
python3 /var/www/html/PQ/0510/ecm-health-report.py
```

Check overall health and growth

---

## Troubleshooting Health Issues

### Data is Stale (age > 5 minutes)

**Check if cron jobs are running:**
```bash
crontab -l | grep ecm
```

**Verify cron logs:**
```bash
tail -f /tmp/ecm-capture.log
tail -f /tmp/ecm-ingest.log
```

**Manually run capture:**
```bash
python3 /var/www/html/PQ/0510/ecm-capture-system-state.py
```

### Databases Out of Sync

**Check sync log:**
```bash
tail -f /tmp/ecm-sync.log
```

**Manually sync:**
```bash
/var/www/html/PQ/0510/ecm-sync-ram-to-ssd.sh
```

**Verify sizes match:**
```bash
ls -lh /mnt/ecm-ram/ecm-hot.db /var/www/html/PQ/0510/ecm-archive-ssd.db
```

### Corrupt Timestamps

**See which records are corrupt:**
```bash
sqlite3 /mnt/ecm-ram/ecm-hot.db \
  "SELECT action_type, COUNT(*) FROM ecm_actions_details 
   WHERE timestamp_iso IS NULL OR timestamp_iso = 'Z' 
   GROUP BY action_type"
```

**Fix corrupt timestamps (if minimal):**
```bash
sqlite3 /mnt/ecm-ram/ecm-hot.db \
  "UPDATE ecm_actions_details 
   SET timestamp_iso = strftime('%Y-%m-%dT%H:%M:%f', created_at) || 'Z' 
   WHERE timestamp_iso IS NULL OR timestamp_iso = 'Z'"
```

### Zero Actions Captured

**Verify capture scripts exist:**
```bash
ls -la /var/www/html/PQ/0510/ecm-*.py
```

**Check if cron job exists:**
```bash
crontab -l | grep "ecm-capture"
```

**Run capture manually:**
```bash
python3 /var/www/html/PQ/0510/ecm-capture-system-state.py
```

**Check /tmp logs:**
```bash
ls -la /tmp/ecm-*.log
```

---

## Health Metrics Over Time

Track how your system grows:

```sql
-- Daily action count
SELECT DATE(timestamp_iso) as date, COUNT(*) as actions
FROM ecm_actions_details 
GROUP BY DATE(timestamp_iso)
ORDER BY date DESC;

-- Actions per type per day
SELECT DATE(timestamp_iso) as date, 
       action_type,
       COUNT(*) as count
FROM ecm_actions_details 
GROUP BY date, action_type
ORDER BY date DESC;

-- Database size growth (query health log)
SELECT timestamp_iso, 
       json_extract(json_data, '$.ram_db_size_mb') as ram_mb
FROM health_snapshots
ORDER BY timestamp_iso DESC LIMIT 30;
```

---

## Setting Up Alerts

### Alert on stale data

```bash
# Check health every 5 minutes, alert if stale
while true; do
  age=$(sqlite3 /mnt/ecm-ram/ecm-hot.db \
    "SELECT (julianday('now') - julianday(MAX(timestamp_iso))) * 86400 
     FROM ecm_actions_details")
  if [ "${age%.*}" -gt 300 ]; then
    echo "⚠️ WARNING: Data is stale (${age} seconds old)"
  fi
  sleep 300
done
```

### Alert on low disk space

```bash
# Check SSD backup space
ssd_size=$(du -sb /var/www/html/PQ/0510/ecm-archive-ssd.db | cut -f1)
if [ $ssd_size -gt $((5 * 1024 * 1024 * 1024)) ]; then
  echo "⚠️ WARNING: SSD backup is growing large ($(numfmt --to=iec $ssd_size))"
fi
```

---

**Health monitoring keeps your external memory reliable and transparent.**

*Created by Claude Haiku 4.5*
