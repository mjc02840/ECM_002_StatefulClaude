# How to Use Your External Context Memory

**Practical examples and SQL queries to search your captured activity**

---

## Quick Start: Basic Queries

### Connect to your database

```bash
sqlite3 /mnt/ecm-ram/ecm-hot.db
```

### See what's been captured

```sql
-- Count total actions
SELECT COUNT(*) FROM ecm_actions_details;

-- Breakdown by type
SELECT action_type, COUNT(*) as count 
FROM ecm_actions_details 
GROUP BY action_type;
```

---

## Bash Commands

### Find all commands from today

```sql
SELECT timestamp_iso, target 
FROM ecm_actions_details 
WHERE action_type='bash' 
  AND DATE(timestamp_iso) = DATE('now');
```

### Find failed commands

```sql
SELECT timestamp_iso, target 
FROM ecm_actions_details 
WHERE action_type='bash' 
  AND exit_code != 0
ORDER BY timestamp_iso DESC;
```

### Find commands in a specific directory

```sql
SELECT timestamp_iso, target 
FROM ecm_actions_details 
WHERE action_type='bash' 
  AND details_json LIKE '%/var/www%'
ORDER BY timestamp_iso DESC LIMIT 20;
```

### Search command history by keyword

```sql
SELECT timestamp_iso, target 
FROM ecm_actions_details 
WHERE action_type='bash' 
  AND details_json LIKE '%git%'
ORDER BY timestamp_iso DESC;
```

### Find all git commands you ran

```sql
SELECT timestamp_iso, 
       json_extract(details_json, '$.command') as command,
       json_extract(details_json, '$.exit_code') as result
FROM ecm_actions_details 
WHERE action_type='bash' 
  AND details_json LIKE '%git%';
```

### Show your command success rate

```sql
SELECT 
  CASE WHEN exit_code=0 THEN 'Success' ELSE 'Failed' END as status,
  COUNT(*) as count
FROM ecm_actions_details 
WHERE action_type='bash'
GROUP BY exit_code;
```

---

## SSH Connections

### Show all SSH connections today

```sql
SELECT timestamp_iso, 
       json_extract(details_json, '$.host') as host,
       json_extract(details_json, '$.auth_method') as method
FROM ecm_actions_details 
WHERE action_type='ssh' 
  AND DATE(timestamp_iso) = DATE('now');
```

### Find failed SSH attempts

```sql
SELECT timestamp_iso, 
       json_extract(details_json, '$.host') as host,
       json_extract(details_json, '$.user') as user
FROM ecm_actions_details 
WHERE action_type='ssh' 
  AND exit_code=1
ORDER BY timestamp_iso DESC;
```

### Connections to specific host

```sql
SELECT timestamp_iso, 
       json_extract(details_json, '$.auth_method') as method
FROM ecm_actions_details 
WHERE action_type='ssh' 
  AND details_json LIKE '%192.168.1.100%';
```

### SSH activity by host

```sql
SELECT 
  json_extract(details_json, '$.host') as host,
  COUNT(*) as count,
  SUM(CASE WHEN exit_code=0 THEN 1 ELSE 0 END) as successful
FROM ecm_actions_details 
WHERE action_type='ssh'
GROUP BY host
ORDER BY count DESC;
```

---

## Fossil Commits

### Show all commits

```sql
SELECT timestamp_iso, 
       json_extract(details_json, '$.message') as message,
       json_extract(details_json, '$.files_changed') as files
FROM ecm_actions_details 
WHERE action_type='fossil'
ORDER BY timestamp_iso DESC;
```

### Find commits with keyword in message

```sql
SELECT timestamp_iso, 
       json_extract(details_json, '$.message') as message
FROM ecm_actions_details 
WHERE action_type='fossil' 
  AND details_json LIKE '%bug%'
ORDER BY timestamp_iso DESC;
```

### Commits per day

```sql
SELECT DATE(timestamp_iso) as date, 
       COUNT(*) as commits
FROM ecm_actions_details 
WHERE action_type='fossil'
GROUP BY DATE(timestamp_iso)
ORDER BY date DESC;
```

### Most active days

```sql
SELECT DATE(timestamp_iso) as date, 
       COUNT(*) as actions
FROM ecm_actions_details 
WHERE action_type='fossil'
GROUP BY DATE(timestamp_iso)
ORDER BY actions DESC
LIMIT 10;
```

---

## File Operations

### Files created today

```sql
SELECT timestamp_iso, 
       json_extract(details_json, '$.path') as path
FROM ecm_actions_details 
WHERE action_type='file' 
  AND target LIKE '%create%'
  AND DATE(timestamp_iso) = DATE('now');
```

### Files modified in last hour

```sql
SELECT timestamp_iso, 
       json_extract(details_json, '$.path') as path,
       json_extract(details_json, '$.size') as size
FROM ecm_actions_details 
WHERE action_type='file' 
  AND timestamp_iso > datetime('now', '-1 hour')
ORDER BY timestamp_iso DESC;
```

### Find changes to specific file

```sql
SELECT timestamp_iso, 
       json_extract(details_json, '$.operation') as operation,
       json_extract(details_json, '$.size') as size
FROM ecm_actions_details 
WHERE action_type='file' 
  AND details_json LIKE '%README.md%';
```

### Files in directory

```sql
SELECT timestamp_iso, 
       json_extract(details_json, '$.path') as path
FROM ecm_actions_details 
WHERE action_type='file' 
  AND details_json LIKE '%/var/www/html%'
ORDER BY timestamp_iso DESC LIMIT 20;
```

### Create vs write ratio

```sql
SELECT 
  CASE WHEN target LIKE '%create%' THEN 'Created' ELSE 'Modified' END as operation,
  COUNT(*) as count
FROM ecm_actions_details 
WHERE action_type='file'
GROUP BY operation;
```

---

## System Metrics

### CPU load over time

```sql
SELECT timestamp_iso, 
       json_extract(details_json, '$.cpu.load_1min') as cpu_1m,
       json_extract(details_json, '$.cpu.load_5min') as cpu_5m
FROM ecm_actions_details 
WHERE action_type='system'
ORDER BY timestamp_iso DESC
LIMIT 20;
```

### Memory usage trend

```sql
SELECT timestamp_iso, 
       json_extract(details_json, '$.memory.percent_used') as mem_pct,
       json_extract(details_json, '$.memory.used_mb') as used_mb
FROM ecm_actions_details 
WHERE action_type='system'
ORDER BY timestamp_iso DESC
LIMIT 20;
```

### Highest CPU load

```sql
SELECT timestamp_iso, 
       json_extract(details_json, '$.cpu.load_1min') as cpu
FROM ecm_actions_details 
WHERE action_type='system'
ORDER BY json_extract(details_json, '$.cpu.load_1min') DESC
LIMIT 5;
```

### Highest memory usage

```sql
SELECT timestamp_iso, 
       json_extract(details_json, '$.memory.percent_used') as mem_pct
FROM ecm_actions_details 
WHERE action_type='system'
ORDER BY json_extract(details_json, '$.memory.percent_used') DESC
LIMIT 5;
```

### Disk usage

```sql
SELECT timestamp_iso, 
       json_extract(details_json, '$.disk.percent_used') as disk_pct,
       json_extract(details_json, '$.disk.used_gb') as used_gb
FROM ecm_actions_details 
WHERE action_type='system'
ORDER BY timestamp_iso DESC LIMIT 10;
```

### Network activity

```sql
SELECT timestamp_iso, 
       json_extract(details_json, '$.network.bytes_received_mb') as rx_mb,
       json_extract(details_json, '$.network.bytes_sent_mb') as tx_mb
FROM ecm_actions_details 
WHERE action_type='system'
ORDER BY timestamp_iso DESC
LIMIT 10;
```

---

## Advanced: Correlating Activities

### What were you doing during peak CPU?

```sql
SELECT action_type, COUNT(*) as count
FROM ecm_actions_details 
WHERE timestamp_iso BETWEEN 
  (SELECT timestamp_iso FROM ecm_actions_details 
   WHERE action_type='system' 
     AND json_extract(details_json, '$.cpu.load_1min') > 3.0
   ORDER BY json_extract(details_json, '$.cpu.load_1min') DESC
   LIMIT 1)
  AND datetime((SELECT timestamp_iso FROM ecm_actions_details 
               WHERE action_type='system' 
                 AND json_extract(details_json, '$.cpu.load_1min') > 3.0
               ORDER BY json_extract(details_json, '$.cpu.load_1min') DESC
               LIMIT 1), '+5 minutes')
GROUP BY action_type;
```

### Commands run during memory spike

```sql
SELECT target 
FROM ecm_actions_details 
WHERE action_type='bash'
  AND timestamp_iso BETWEEN '2026-05-11T10:00:00Z' AND '2026-05-11T10:05:00Z'
ORDER BY timestamp_iso;
```

### Timeline: All activity in time window

```sql
SELECT timestamp_iso, action_type, target
FROM ecm_actions_details 
WHERE timestamp_iso BETWEEN '2026-05-11T09:00:00Z' AND '2026-05-11T10:00:00Z'
ORDER BY timestamp_iso;
```

### Activity breakdown by hour

```sql
SELECT 
  strftime('%Y-%m-%d %H:00', timestamp_iso) as hour,
  action_type,
  COUNT(*) as count
FROM ecm_actions_details 
WHERE DATE(timestamp_iso) = DATE('now')
GROUP BY hour, action_type
ORDER BY hour, action_type;
```

---

## Saving Results to File

### Export query results

```bash
sqlite3 /mnt/ecm-ram/ecm-hot.db ".mode csv" \
  "SELECT timestamp_iso, action_type, target FROM ecm_actions_details" \
  > activity.csv
```

### Export with headers

```bash
sqlite3 /mnt/ecm-ram/ecm-hot.db ".headers on" \
  "SELECT timestamp_iso, action_type, target FROM ecm_actions_details" \
  > activity.txt
```

---

## Tips & Tricks

### Make queries shorter

Create a shell alias:

```bash
alias ecm='sqlite3 /mnt/ecm-ram/ecm-hot.db'
```

Then:

```bash
ecm "SELECT COUNT(*) FROM ecm_actions_details;"
```

### Use jq to parse JSON

```bash
sqlite3 /mnt/ecm-ram/ecm-hot.db \
  "SELECT details_json FROM ecm_actions_details WHERE action_type='system' LIMIT 1" \
  | jq '.cpu'
```

### Watch for new entries

```bash
watch -n 5 'sqlite3 /mnt/ecm-ram/ecm-hot.db "SELECT COUNT(*) FROM ecm_actions_details;"'
```

### Export daily report

```bash
sqlite3 /mnt/ecm-ram/ecm-hot.db << EOF
.mode markdown
.headers on
SELECT DATE(timestamp_iso) as date, 
       action_type, 
       COUNT(*) as count
FROM ecm_actions_details 
WHERE DATE(timestamp_iso) = DATE('now')
GROUP BY date, action_type;
EOF
```

---

## Your Data, Your Queries

These are just examples. You can write any SQL query against:
- `ecm_actions` — Full-text searchable index
- `ecm_actions_details` — Detailed records with JSON

The data is yours. Explore it. Build reports. Discover patterns.

**Your external memory. Your rules.**

*Created by Claude Haiku 4.5*
