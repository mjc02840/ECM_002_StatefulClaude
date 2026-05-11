# The 5 Phases of ECM_002_StatefulClaude

**Deep dive into how each phase captures and stores your activity**

---

## Phase 1: Bash Command Capture

### What Gets Captured

Every bash command you run:
```bash
$ git commit -m "fix bug"
$ ls -la /var/www
$ python3 script.py --option value
```

All logged with:
- Timestamp (microsecond precision)
- Exit code (0 = success, non-zero = error)
- Working directory (where you were)
- Full command text

### How It Works

**Installation:**
```bash
chmod +x /var/www/html/PQ/0510/ecm-bash-trap-setup.sh
/var/www/html/PQ/0510/ecm-bash-trap-setup.sh
```

Adds to `~/.bashrc`:
```bash
ecm_bash_log_command() {
  local exit_code=$?
  local cmd="$BASH_COMMAND"
  local dir="$(pwd)"
  local ts="$(date -u +'%Y-%m-%dT%H:%M:%S.%3NZ')"
  echo "$ts|$exit_code|$dir|$$|$cmd" >> /tmp/ecm-bash-commands.log
}
trap ecm_bash_log_command RETURN
```

**Trigger:** After every command

**Log format:**
```
2026-05-11T10:30:45.123Z|0|/var/www/html|12345|git commit -m "fix bug"
2026-05-11T10:30:46.456Z|1|/var/www/html|12345|ls invalid-directory
2026-05-11T10:30:47.789Z|0|/home/user|12345|echo "hello"
```

### Data Storage

**Table:** `ecm_actions_details` (action_type = 'bash')

**Fields:**
- `timestamp_iso` — When command was run
- `target` — Command summary (first 100 chars)
- `exit_code` — 0 (success) or non-zero (failure)
- `details_json` — Full JSON with:
  - `command` — Complete command text
  - `working_directory` — Where you were
  - `shell_pid` — Shell instance ID
  - `exit_code` — Result

### Query Examples

**Find all failed commands:**
```sql
SELECT timestamp_iso, target FROM ecm_actions_details 
WHERE action_type='bash' AND exit_code != 0;
```

**Find commands in a directory:**
```sql
SELECT timestamp_iso, target FROM ecm_actions_details 
WHERE action_type='bash' 
  AND details_json LIKE '%/var/www%';
```

**Find long-running command sequences:**
```sql
SELECT COUNT(*) as count, 
       MIN(timestamp_iso) as start,
       MAX(timestamp_iso) as end
FROM ecm_actions_details 
WHERE action_type='bash' 
  AND timestamp_iso BETWEEN '2026-05-11T10:00:00Z' AND '2026-05-11T10:10:00Z';
```

---

## Phase 2: SSH Connection Logging

### What Gets Captured

Every SSH connection:
- Successful logins (via key or password)
- Failed authentication attempts
- Invalid user attempts
- Connection close events
- Connection resets

### How It Works

**Source:** Parses `/var/log/auth.log`

**Detection patterns:**
```
Accepted publickey → successful key authentication
Accepted password → successful password authentication
Failed password → authentication failed
Invalid user → user doesn't exist
Connection closed → normal close
Connection reset → abnormal close
```

**Log format:**
```
2026-05-11T10:30:45.123Z|accepted_key|192.168.1.100|aaa|22|key
2026-05-11T10:30:50.456Z|failed_auth|192.168.1.101|root|22|password
2026-05-11T10:31:00.789Z|connection_closed|192.168.1.100|aaa|22|key
```

### Data Storage

**Table:** `ecm_actions_details` (action_type = 'ssh')

**Fields in JSON:**
- `host` — IP address or hostname
- `user` — Username used
- `port` — SSH port (usually 22)
- `auth_method` — "key" or "password"
- `result` — 0 (success) or 1 (failure)
- `operation` — accepted_key, accepted_password, failed_auth, etc.

### Query Examples

**Find all successful logins:**
```sql
SELECT timestamp_iso, json_extract(details_json, '$.host') as host
FROM ecm_actions_details 
WHERE action_type='ssh' AND exit_code=0;
```

**Find failed authentication attempts:**
```sql
SELECT timestamp_iso, json_extract(details_json, '$.host') as host
FROM ecm_actions_details 
WHERE action_type='ssh' AND exit_code=1;
```

**Find connections to specific host:**
```sql
SELECT timestamp_iso, json_extract(details_json, '$.auth_method') as method
FROM ecm_actions_details 
WHERE action_type='ssh' 
  AND details_json LIKE '%192.168.1.100%';
```

---

## Phase 3: Fossil Commit Logging

### What Gets Captured

Every Fossil commit in your repositories:
- Commit hash
- Author
- Commit message
- Files changed (count)
- Repository path

### How It Works

**Installation:**
1. Run setup script in each Fossil repository:
   ```bash
   /var/www/html/PQ/0510/ecm-fossil-setup.sh
   ```

2. Installs post-commit hook in `.fossil-settings/hook-commit-begin`

3. Hook runs after every `fossil commit`:
   ```bash
   fossil log --format json | 
     /var/www/html/PQ/0510/ecm-capture-fossil-commit.py
   ```

**Log format:**
```
2026-05-11T10:30:45.123Z|abc123def456|aaa|fix authentication bug|12|/var/www/html/PQ/0510
2026-05-11T10:35:00.456Z|def456abc123|aaa|update documentation|5|/var/www/html/PQ/0510
```

### Data Storage

**Table:** `ecm_actions_details` (action_type = 'fossil')

**Fields in JSON:**
- `commit_hash` — Unique commit ID
- `author` — Who committed
- `message` — Commit message
- `files_changed` — Count of modified files
- `repository_path` — Where repository is located

### Query Examples

**Find all commits by you:**
```sql
SELECT timestamp_iso, json_extract(details_json, '$.message') as message
FROM ecm_actions_details 
WHERE action_type='fossil';
```

**Find commits with "bug" in message:**
```sql
SELECT timestamp_iso, json_extract(details_json, '$.message') as message
FROM ecm_actions_details 
WHERE action_type='fossil' 
  AND details_json LIKE '%bug%';
```

**Find commits to specific repository:**
```sql
SELECT timestamp_iso, json_extract(details_json, '$.message') as message
FROM ecm_actions_details 
WHERE action_type='fossil' 
  AND details_json LIKE '%0510%';
```

**Commits per day:**
```sql
SELECT DATE(timestamp_iso) as date, COUNT(*) as commits
FROM ecm_actions_details 
WHERE action_type='fossil'
GROUP BY DATE(timestamp_iso);
```

---

## Phase 4: File Operation Monitoring

### What Gets Captured

File modifications in watched directories:
- New files created
- Existing files modified
- File metadata (size, user, permissions)

### How It Works

**Configuration:**
Create `~/.ecm-watched-dirs`:
```
/var/www/html
/home/aaa
/path/to/project
```

**Monitoring:**
Every 1 minute, `ecm-monitor-file-operations.sh` runs:
```bash
find /var/www/html -type f -mmin -2 -exec stat {} \;
```

**Detection logic:**
- mtime < 10 seconds → CREATE
- mtime < 2 minutes → WRITE

**Log format:**
```
2026-05-11T10:30:45.123Z|create|/var/www/html/index.html|4096|aaa|644
2026-05-11T10:30:50.456Z|write|/var/www/html/style.css|2048|aaa|644
```

### Data Storage

**Table:** `ecm_actions_details` (action_type = 'file')

**Fields in JSON:**
- `path` — Full file path
- `operation` — "create" or "write"
- `size` — File size in bytes
- `user` — File owner
- `permissions` — rwxrwxrwx format
- `directory` — Parent directory

### Query Examples

**Find all files created:**
```sql
SELECT timestamp_iso, json_extract(details_json, '$.path') as path
FROM ecm_actions_details 
WHERE action_type='file' AND target LIKE '%create%';
```

**Find modifications to specific file:**
```sql
SELECT timestamp_iso, json_extract(details_json, '$.size') as size
FROM ecm_actions_details 
WHERE action_type='file' 
  AND details_json LIKE '%index.html%';
```

**Find files modified in last hour:**
```sql
SELECT timestamp_iso, json_extract(details_json, '$.path') as path
FROM ecm_actions_details 
WHERE action_type='file' 
  AND timestamp_iso > datetime('now', '-1 hour');
```

**Files created vs modified:**
```sql
SELECT 
  CASE WHEN target LIKE '%create%' THEN 'created' ELSE 'modified' END as op,
  COUNT(*) as count
FROM ecm_actions_details 
WHERE action_type='file'
GROUP BY op;
```

---

## Phase 5: System State Monitoring

### What Gets Captured

System metrics every 5 minutes:
- CPU load (1, 5, 15 minute averages)
- Memory usage (total, used, available, percent)
- Disk usage (total, used, available, percent)
- Network (bytes received, bytes sent)
- Process count

### How It Works

**Capture every 5 minutes:**
```bash
python3 ecm-capture-system-state.py
```

Reads from:
- `/proc/loadavg` — CPU load
- `/proc/meminfo` — Memory
- `/proc/net/dev` — Network
- `df` command — Disk
- `ps` command — Processes

**Log format:**
```
2026-05-11T10:30:45.123Z|{"timestamp":"2026-05-11T10:30:45.123Z","cpu":{"load_1min":0.5,"load_5min":0.45,"load_15min":0.40},"memory":{"total_mb":8192,"used_mb":1024,"available_mb":7168,"percent_used":12.5},...}
```

### Data Storage

**Table:** `ecm_actions_details` (action_type = 'system')

**Fields in JSON:**
- `cpu` → `load_1min`, `load_5min`, `load_15min`
- `memory` → `total_mb`, `used_mb`, `available_mb`, `percent_used`
- `disk` → `total_gb`, `used_gb`, `available_gb`, `percent_used`
- `network` → `bytes_received`, `bytes_sent`, `bytes_received_mb`, `bytes_sent_mb`
- `processes` → count of running processes

### Query Examples

**Memory usage over time:**
```sql
SELECT timestamp_iso, 
       json_extract(details_json, '$.memory.percent_used') as mem_pct
FROM ecm_actions_details 
WHERE action_type='system'
ORDER BY timestamp_iso DESC
LIMIT 20;
```

**CPU spikes:**
```sql
SELECT timestamp_iso, 
       json_extract(details_json, '$.cpu.load_1min') as cpu_1m
FROM ecm_actions_details 
WHERE action_type='system' 
  AND json_extract(details_json, '$.cpu.load_1min') > 2.0;
```

**Disk usage trend:**
```sql
SELECT timestamp_iso, 
       json_extract(details_json, '$.disk.percent_used') as disk_pct
FROM ecm_actions_details 
WHERE action_type='system'
ORDER BY timestamp_iso;
```

**When was memory lowest:**
```sql
SELECT timestamp_iso, 
       json_extract(details_json, '$.memory.percent_used') as mem_pct
FROM ecm_actions_details 
WHERE action_type='system'
ORDER BY json_extract(details_json, '$.memory.percent_used') ASC
LIMIT 1;
```

---

## Correlating Phases Together

The real power: correlate activity across all 5 phases:

**"What was I doing when CPU spiked?"**
```sql
SELECT action_type, COUNT(*) as count
FROM ecm_actions_details 
WHERE timestamp_iso BETWEEN 
  (SELECT timestamp_iso FROM ecm_actions_details 
   WHERE action_type='system' AND json_extract(details_json, '$.cpu.load_1min') > 3.0
   LIMIT 1)
  AND datetime((SELECT timestamp_iso FROM ecm_actions_details 
               WHERE action_type='system' AND json_extract(details_json, '$.cpu.load_1min') > 3.0 LIMIT 1), '+5 minutes')
GROUP BY action_type;
```

**Result:** Bash commands, file writes, and commits during high CPU

---

**All 5 phases working together create your complete external context memory.**

*Created by Claude Haiku 4.5*
