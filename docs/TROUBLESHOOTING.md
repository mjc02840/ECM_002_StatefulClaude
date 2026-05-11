# Troubleshooting Guide

**Solutions for common problems with ECM_002_StatefulClaude**

---

## Installation Issues

### "Python not found" or "Python version too old"

**Error:** `python3: command not found` or `Python 3.7+ required`

**Solution:**
```bash
# Check Python version
python3 --version

# Install Python 3.7+
sudo apt-get update
sudo apt-get install python3 python3-pip
```

### "SQLite3 FTS5 not supported"

**Error:** `FTS5 extension not available`

**Solution:**
```bash
# Check SQLite version
sqlite3 --version

# SQLite 3.9.0+ required for FTS5
sudo apt-get install sqlite3
```

### "Bash version too old"

**Error:** `RETURN trap not supported`

**Solution:**
```bash
# Check Bash version
bash --version

# Need Bash 4.0+
sudo apt-get install bash
```

---

## Capture Issues

### "No system state log yet"

**Error:** `ls: cannot access /tmp/ecm-system-state.log`

**Solution:**
```bash
# Run capture manually
python3 /var/www/html/PQ/0510/ecm-capture-system-state.py

# Check if it created the log
ls -la /tmp/ecm-system-state.log

# Verify /proc is readable
ls -la /proc/loadavg /proc/meminfo
```

### "Bash trap not capturing commands"

**Error:** Commands not appearing in `/tmp/ecm-bash-commands.log`

**Solution:**
```bash
# Check trap is installed in ~/.bashrc
grep -n "ecm_bash_log_command" ~/.bashrc

# Reinstall if missing
./ecm-bash-trap-setup.sh

# Reload shell
source ~/.bashrc

# Test
echo "test command" > /dev/null
cat /tmp/ecm-bash-commands.log
```

### "Permissions denied reading /var/log/auth.log"

**Error:** `Permission denied: /var/log/auth.log`

**Solution:**
```bash
# Check permissions
ls -la /var/log/auth.log

# Your user should be in adm group
sudo usermod -aG adm $USER

# Verify
groups $USER

# Log out and back in, then try again
python3 /var/www/html/PQ/0510/ecm-ingest-ssh-logs.py
```

---

## Database Issues

### "Database is locked"

**Error:** `database is locked`

**Solution:**
```bash
# Check for running processes
lsof /mnt/ecm-ram/ecm-hot.db

# Kill any stuck queries
pkill -f "sqlite3"

# Try again
sqlite3 /mnt/ecm-ram/ecm-hot.db "SELECT COUNT(*) FROM ecm_actions_details;"
```

### "RAM disk not mounted"

**Error:** `Cannot access /mnt/ecm-ram/ecm-hot.db`

**Solution:**
```bash
# Check if mounted
mount | grep ecm-ram

# If not mounted, mount it
sudo mkdir -p /mnt/ecm-ram
sudo mount -t tmpfs -o size=4G ecm-ram /mnt/ecm-ram

# Make persistent by adding to /etc/fstab
echo "ecm-ram /mnt/ecm-ram tmpfs size=4G 0 0" | sudo tee -a /etc/fstab
```

### "No data in database after running capture"

**Error:** `SELECT COUNT(*) returns 0`

**Solution:**
```bash
# Run capture manually
python3 /var/www/html/PQ/0510/ecm-capture-system-state.py

# Check log was created
cat /tmp/ecm-system-state.log

# Run ingest manually
python3 /var/www/html/PQ/0510/ecm-ingest-system-state.py

# Check database
sqlite3 /mnt/ecm-ram/ecm-hot.db "SELECT COUNT(*) FROM ecm_actions_details;"
```

---

## Cron Issues

### "Cron jobs not running"

**Error:** No new data appearing, `crontab -l` shows jobs

**Solution:**
```bash
# Check cron is running
sudo service cron status

# Start if stopped
sudo service cron start

# Check cron logs
sudo tail -f /var/log/syslog | grep CRON

# Verify jobs exist
crontab -l | grep ecm

# Test cron environment
env -i /home/aaa/bin/python3 /var/www/html/PQ/0510/ecm-capture-system-state.py
```

### "Cron job produces errors"

**Error:** `Error: ... (from /tmp/ecm-ingest.log)`

**Solution:**
```bash
# Check the error logs
cat /tmp/ecm-*.log

# Run the job manually to see full error
python3 /var/www/html/PQ/0510/ecm-ingest-bash-commands.py

# Common issues:
# - Missing Python module (install: pip3 install X)
# - File permissions (chmod +x script.py)
# - Python path (which python3)
```

### "Cron not finding Python"

**Error:** `python3: command not found (from CRON)`

**Solution:**
```bash
# Find Python path
which python3

# Add to crontab
crontab -e

# Change:
# */5 * * * * /var/www/html/PQ/0510/ecm-capture-system-state.py
# To:
# */5 * * * * /usr/bin/python3 /var/www/html/PQ/0510/ecm-capture-system-state.py
```

---

## Data Issues

### "Timestamps are corrupted (showing 'Z')"

**Error:** `SELECT timestamp_iso FROM ecm_actions_details LIMIT 1;` returns `Z`

**Solution:**
```bash
# Count corrupted records
sqlite3 /mnt/ecm-ram/ecm-hot.db \
  "SELECT COUNT(*) FROM ecm_actions_details WHERE timestamp_iso = 'Z' OR timestamp_iso IS NULL;"

# Fix by using created_at
sqlite3 /mnt/ecm-ram/ecm-hot.db \
  "UPDATE ecm_actions_details 
   SET timestamp_iso = strftime('%Y-%m-%dT%H:%M:%f', created_at) || 'Z' 
   WHERE timestamp_iso = 'Z' OR timestamp_iso IS NULL;"

# Verify fix
sqlite3 /mnt/ecm-ram/ecm-hot.db \
  "SELECT COUNT(*) FROM ecm_actions_details WHERE timestamp_iso = 'Z';"
```

### "Duplicate records in database"

**Error:** Same command/action appears multiple times

**Solution:**
```bash
# This is normal for file operations (small timestamp differences)
# But check if massive duplication

# Count by content_hash
sqlite3 /mnt/ecm-ram/ecm-hot.db \
  "SELECT COUNT(DISTINCT content_hash), COUNT(*) FROM ecm_actions_details;"

# If huge duplication, check deduplication in ingest scripts
cat /tmp/ecm-system-ingest-state.json
```

### "FTS5 search not returning results"

**Error:** Full-text search returns 0 rows even though data exists

**Solution:**
```bash
# FTS5 searches the FTS5 virtual table, not the details table
# Use this instead:
sqlite3 /mnt/ecm-ram/ecm-hot.db \
  "SELECT * FROM ecm_actions_details WHERE indexable_text LIKE '%search term%';"

# Or use proper SQL search:
sqlite3 /mnt/ecm-ram/ecm-hot.db \
  "SELECT * FROM ecm_actions_details WHERE target LIKE '%git%' OR details_json LIKE '%git%';"
```

---

## Performance Issues

### "Queries are slow"

**Error:** SQLite queries take seconds instead of milliseconds

**Solution:**
```bash
# Check database size
du -h /mnt/ecm-ram/ecm-hot.db

# Analyze and optimize
sqlite3 /mnt/ecm-ram/ecm-hot.db "ANALYZE;"

# Rebuild indexes
sqlite3 /mnt/ecm-ram/ecm-hot.db ".rebuild"

# Check table stats
sqlite3 /mnt/ecm-ram/ecm-hot.db "SELECT COUNT(*) FROM ecm_actions_details;"
```

### "RAM disk running out of space"

**Error:** `No space left on device` when inserting

**Solution:**
```bash
# Check RAM disk usage
df /mnt/ecm-ram

# Archive old data to SSD
sqlite3 /mnt/ecm-ram/ecm-hot.db \
  "SELECT COUNT(*) FROM ecm_actions_details WHERE timestamp_iso < datetime('now', '-30 days');"

# Option 1: Delete old records
# sqlite3 /mnt/ecm-ram/ecm-hot.db "DELETE FROM ecm_actions_details WHERE timestamp_iso < datetime('now', '-90 days');"

# Option 2: Increase RAM disk size
# sudo umount /mnt/ecm-ram
# sudo mount -t tmpfs -o size=8G ecm-ram /mnt/ecm-ram
```

---

## Health Monitoring Issues

### "Health report shows YELLOW or RED"

**Error:** Health status is not GREEN

**Solution:**
```bash
# Run health report to see details
python3 /var/www/html/PQ/0510/ecm-health-report.py

# Check specific issue:
# - Data is stale: verify cron jobs running
# - Databases out of sync: run sync script manually
# - Corrupt timestamps: fix as shown above
# - Zero actions: run capture manually

/var/www/html/PQ/0510/ecm-sync-ram-to-ssd.sh
python3 /var/www/html/PQ/0510/ecm-capture-system-state.py
```

---

## Getting Help

### Before asking for help, collect this info:

```bash
# System info
uname -a
python3 --version
sqlite3 --version
bash --version

# Check logs
tail -20 /tmp/ecm-*.log

# Run health check
python3 /var/www/html/PQ/0510/ecm-health-report.py

# Database state
sqlite3 /mnt/ecm-ram/ecm-hot.db "SELECT COUNT(*) FROM ecm_actions_details; SELECT action_type, COUNT(*) FROM ecm_actions_details GROUP BY action_type;"

# Cron jobs
crontab -l | grep ecm

# Mount status
mount | grep ecm
df -h /mnt/ecm-ram
```

---

## Known Limitations

### Issue: "No SSH events captured"

**Cause:** `/var/log/auth.log` isn't readable or no SSH activity

**Workaround:** Grant group permissions to auth.log, or generate SSH events

### Issue: "File operations missing some files"

**Cause:** Scanning only captures files with recent `mtime`, symlinks not followed

**Workaround:** Ensure watched directories have actual files, not just symlinks

### Issue: "Process count seems wrong"

**Cause:** `ps aux` output varies by system, includes defunct processes

**Workaround:** Query count is approximate, good for trends not exact numbers

---

**Still stuck? Run the health report and check the logs first.**

*Created by Claude Haiku 4.5*
