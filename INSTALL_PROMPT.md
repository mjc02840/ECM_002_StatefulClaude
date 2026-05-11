# ECM_002_StatefulClaude Installation Prompt

*Created and Produced by Claude Haiku 4.5*

**Copy this entire prompt and paste it into Claude Code CLI on your machine.**

Claude Code will read this prompt, understand what StatefulClaude is, and automatically build and install the complete system for you.

This installation prompt itself was written by Claude Haiku 4.5 to guide you through setting up external context memory—a system that was also designed and built entirely by Haiku.

---

```
You are about to install ECM_002_StatefulClaude: Infinite External Persistence of Memory for Claude Code CLI.

StatefulClaude is an open-source system that captures everything you do in your terminal 
and makes it searchable and persistent across Claude Code sessions. It records:
- Every bash command you run
- Every SSH connection
- Every Fossil commit
- Every file you modify
- System metrics (CPU, memory, disk)

All data is stored locally on your machine (RAM disk + SSD backup). Nothing is sent 
to the cloud. You own your data.

This is a prompt-based installer. I (Claude Code) will:
1. Check your system for required dependencies
2. Build the complete 5-phase action capture system
3. Set up cron automation
4. Activate health monitoring
5. Test everything to make sure it works

IMPORTANT: This system requires:
- Linux (with /proc filesystem)
- Python 3.7+
- SQLite3 with FTS5 support
- Bash 4.0+
- sudo access (for RAM disk mounting)
- cron daemon
- At least 10 GB of free disk space for SSD backup

If your system doesn't have these, I'll tell you what's missing and how to install it.

---

STEP 0: SYSTEM DETECTION & PREREQUISITES

Before we begin, let me check your system:

1. Detect OS and Linux distribution
2. Check Python version (need 3.7+)
3. Check SQLite version and FTS5 support
4. Check Bash version (need 4.0+)
5. Check for cron daemon
6. Check available disk space
7. Ask about RAM disk size (default 4GB, user can customize)
8. Ask about backup location (default /var/www/html, user can customize)
9. Ask about installation directory base

If anything is missing, offer to install it or explain the limitation.

Once all prerequisites are met, ask for user confirmation to proceed.

---

STEP 1: BUILD PHASE 1 - BASH COMMAND CAPTURE

Phase 1 captures every bash command you run. It uses a RETURN trap in .bashrc 
to log commands automatically with timestamps, exit codes, and working directories.

What you'll get:
- Every command logged with: timestamp (microsecond precision) | exit_code | working_dir | command
- Logged to: /tmp/ecm-bash-commands.log
- Ingested every 1 minute automatically via cron
- Searchable in the database with action_type='bash'

Build the following:
1. Create: ecm-bash-trap-setup.sh (installs RETURN trap in ~/.bashrc)
2. Create: ecm-ingest-bash-commands.py (parses log, deduplicates, inserts into DB)
3. Run setup script to install the trap
4. Test: Run a few bash commands and verify they appear in /tmp/ecm-bash-commands.log
5. Test: Verify ingest script can parse the log

Verify Phase 1:
- Check that ~/.bashrc has the ecm_bash_log_command function
- Run: cat /tmp/ecm-bash-commands.log (should show recent commands)
- If working, display: "✓ Phase 1 Complete: Bash command capture active"

---

STEP 2: BUILD PHASE 2 - SSH CONNECTION LOGGING

Phase 2 captures SSH connection attempts and successes from /var/log/auth.log.
It detects patterns: accepted (key/password), failed auth, invalid user, connection events.

What you'll get:
- Every SSH event: timestamp | operation | host | user | port | auth_method | result
- Logged to: /tmp/ecm-ssh-events.log
- Ingested every 1 minute automatically via cron
- Searchable in the database with action_type='ssh'

Build the following:
1. Create: ecm-ingest-ssh-logs.py (parses /var/log/auth.log with regex)
2. Test: Run ingest script, should find SSH events
3. Verify regex patterns work correctly on sample auth.log lines

Verify Phase 2:
- Run ingest script
- Query database: SELECT COUNT(*) FROM ecm_actions_details WHERE action_type='ssh'
- If count > 0, display: "✓ Phase 2 Complete: SSH event logging active"

---

STEP 3: BUILD PHASE 3 - FOSSIL COMMIT LOGGING

Phase 3 captures commits from Fossil repositories on your machine.
Each commit is logged with: timestamp | commit_hash | author | message | files_changed | repo_path

What you'll get:
- Every Fossil commit logged with full metadata
- Logged to: /tmp/ecm-fossil-commits.log
- Ingested every 1 minute automatically via cron
- Searchable in the database with action_type='fossil'

Build the following:
1. Create: ecm-fossil-post-commit-hook.sh (post-commit hook template)
2. Create: ecm-ingest-fossil-commits.py (parses commit log, inserts into DB)
3. Create: ecm-fossil-setup.sh (installs hook in .fossil-settings/hook-commit-begin for each repo)
4. Explain to user: User must run ecm-fossil-setup.sh in each Fossil repository they want to monitor
5. For testing: Suggest user run setup script in at least one Fossil repo, make a test commit

Verify Phase 3:
- Ask user if they have Fossil repos set up
- If yes, verify hook is installed and make a test commit
- Query database: SELECT COUNT(*) FROM ecm_actions_details WHERE action_type='fossil'
- Display: "✓ Phase 3 Complete: Fossil commit logging active (or ready to activate)"

---

STEP 4: BUILD PHASE 4 - FILE OPERATION MONITORING

Phase 4 captures file modifications in watched directories.
It scans directories every 1 minute using find -mmin to detect creates and writes.

What you'll get:
- Every file created or modified in watched directories
- Logged with: timestamp | operation (create/write) | path | size | user | permissions
- Logged to: /tmp/ecm-file-operations.log
- Ingested every 1 minute automatically via cron
- Searchable in the database with action_type='file'

Build the following:
1. Create: ecm-monitor-file-operations.sh (finds modified files in watched dirs)
2. Create: ecm-ingest-file-operations.py (parses file log, deduplicates, inserts into DB)
3. Create: ecm-file-operations-setup.sh (creates ~/.ecm-watched-dirs config)
4. Ask user: Which directories to monitor? (suggest: /var/www/html, /home/aaa, or user's choice)
5. Run setup script to create config
6. Test: Modify a file in a watched directory, verify it appears in log

Verify Phase 4:
- Check ~/.ecm-watched-dirs exists with user's chosen directories
- Run monitoring script, verify files appear in /tmp/ecm-file-operations.log
- Query database: SELECT COUNT(*) FROM ecm_actions_details WHERE action_type='file'
- If count > 0, display: "✓ Phase 4 Complete: File operation monitoring active"

---

STEP 5: BUILD PHASE 5 - SYSTEM STATE MONITORING

Phase 5 captures system metrics every 5 minutes: CPU load, memory, disk, network, processes.
This lets you correlate your work with system performance.

What you'll get:
- System snapshots with: CPU (1/5/15min load), Memory (total/used/available/percent), 
  Disk (total/used/available/percent), Network (RX/TX bytes), Process count
- Logged to: /tmp/ecm-system-state.log
- Ingested every 5 minutes automatically via cron
- Searchable in the database with action_type='system'

Build the following:
1. Create: ecm-capture-system-state.py (reads /proc, df, ps for metrics)
2. Create: ecm-ingest-system-state.py (parses metrics, deduplicates, inserts into DB)
3. Test: Run capture script, verify metrics are collected
4. Test: Run ingest script, verify data enters database

Verify Phase 5:
- Run capture script: python3 ecm-capture-system-state.py
- Should display: CPU load, memory, disk, network, process count
- Query database: SELECT COUNT(*) FROM ecm_actions_details WHERE action_type='system'
- Display: "✓ Phase 5 Complete: System state monitoring active"

---

STEP 6: SET UP CORE DATABASE & BACKUP

Build the foundational infrastructure:

1. Create RAM disk (4GB default, user can customize):
   - Mount at: /mnt/ecm-ram
   - Size: User configurable (default 4GB = 4194304 KB)
   - Type: tmpfs (RAM-based, ultra-fast)

2. Create SQLite FTS5 database on RAM disk:
   - Location: /mnt/ecm-ram/ecm-hot.db
   - Schema: ecm_actions (FTS5 virtual table), ecm_actions_details (with JSON)
   - Indexes on: action_type, timestamp_iso

3. Create SSD backup directory:
   - Location: User configurable (default /var/www/html/PQ/0510/)
   - File: ecm-archive-ssd.db (synced from RAM every 5 minutes)

4. Create state tracking directory:
   - Location: /tmp
   - Files: ecm-bash-ingest-state.json, ecm-ssh-ingest-state.json, etc.
   - Purpose: Track which lines have been ingested (for resume capability)

Verify:
- RAM disk mounted: mount | grep ecm-ram
- Database exists: ls -lh /mnt/ecm-ram/ecm-hot.db
- Display: "✓ Core infrastructure ready"

---

STEP 7: INSTALL CRON AUTOMATION

Set up 9 cron jobs that run automatically (user doesn't have to do anything):

Every 1 minute (6 jobs):
- Bash command ingest
- SSH log ingest
- Fossil commit ingest
- File operation monitor
- File operation ingest

Every 5 minutes (3 jobs):
- RAM to SSD sync
- System state capture
- System state ingest
- Health report

Build the following:
1. Create: ecm-sync-ram-to-ssd.sh (copies /mnt/ecm-ram/ecm-hot.db to backup)
2. Install all scripts into crontab with proper error handling
3. Verify crontab installation: crontab -l | grep ecm

Each cron job should:
- Log output to /tmp/ecm-*.log files
- Run silently on success (no output unless error)
- Handle errors gracefully (don't crash if a file is missing)

Display results:
- Show all cron jobs installed
- Explain that user can monitor with: tail -f /tmp/ecm-*.log
- Display: "✓ Cron automation installed (9 jobs, all running)"

---

STEP 8: ACTIVATE HEALTH MONITORING

Build the health report system:

1. Create: ecm-health-report.py (captures system health snapshot every run)
   - Measures: total actions, action breakdown, data freshness, timestamp integrity,
     DB size, sync status, deduplication ratio
   - Uses microsecond-precision timestamps (YYYY-MM-DDTHH:MM:SS.fffZ)
   - Outputs both human-readable report and JSON data
   - Logs to: /tmp/ecm-health-log.jsonl (pipe-delimited for easy parsing)

2. Install health report to cron: */5 * * * *
3. Run once to verify it works
4. Show user a sample health report with all metrics

Display:
- Sample health report output
- Explain where logs are: /tmp/ecm-health-log.jsonl
- Suggest: tail -f /tmp/ecm-health.log to watch health updates
- Display: "✓ Health monitoring active"

---

STEP 9: INITIALIZE DATABASE & RUN FIRST INGEST

Now that all capture and ingest scripts are ready:

1. Run each capture script once to generate initial data:
   - ecm-capture-system-state.py (creates /tmp/ecm-system-state.log)
   - If Fossil repo exists, make a test commit
   - Modify a watched file to test file operations

2. Run all ingest scripts to populate database:
   - ecm-ingest-bash-commands.py
   - ecm-ingest-ssh-logs.py
   - ecm-ingest-fossil-commits.py (if applicable)
   - ecm-ingest-file-operations.py
   - ecm-ingest-system-state.py

3. Query database to verify data:
   - SELECT action_type, COUNT(*) FROM ecm_actions_details GROUP BY action_type
   - Show user the breakdown

Display:
- "Database initialized with X total actions"
- Show action type breakdown
- Display: "✓ First ingest complete"

---

STEP 10: VERIFICATION & TESTING

Run comprehensive verification to ensure everything works:

1. Check all prerequisites one more time
2. Verify all scripts exist and are executable
3. Verify RAM disk is mounted and has correct size
4. Verify database exists and has correct schema
5. Verify cron jobs are installed
6. Run a test workflow:
   - Run a bash command
   - Check /tmp/ecm-bash-commands.log for entry
   - Wait for cron to ingest (or run ingest manually)
   - Query database and verify command appears
7. Verify each action type:
   - bash: Count should be > 0
   - file: Count should be > 0 (from setup and test files)
   - system: Count should be > 0
   - ssh: Count depends on user's SSH activity
   - fossil: Count depends on user's Fossil activity

Success criteria:
- All 9 cron jobs installed and running
- Database has at least 1 action for each phase
- Health report runs and produces output
- User can query: SELECT * FROM ecm_actions_details LIMIT 1

Display final verification report:
```
ECM 002 INSTALLATION COMPLETE ✓

System Status:
- Total actions captured: X
- Action types: bash, SSH, fossil, file, system
- RAM database: /mnt/ecm-ram/ecm-hot.db (Y MB)
- SSD backup: /path/to/ecm-archive-ssd.db (Y MB)
- Cron jobs: 9 installed and running
- Health monitoring: Active

Next Steps:
1. Read documentation: github.com/username/ecm-002
2. Try example queries (see USAGE.md)
3. Monitor with: tail -f /tmp/ecm-health.log
4. Check logs: /tmp/ecm-*.log

Your work is now being captured and searchable.
```

---

STEP 11: PROVIDE DOCUMENTATION & RESOURCES

Before finishing, give user:

1. Quick reference for common queries:
   - Find all commands from today
   - Find system metrics when CPU spiked
   - Find all SSH connections
   - Find files modified with pattern
   - Correlate work with system load

2. Troubleshooting guide:
   - RAM disk not mounting → (solution)
   - Database not created → (solution)
   - Cron jobs not running → (solution)
   - Timestamps corrupted → (solution)
   - No data appearing → (solution)

3. Links to documentation:
   - GitHub repo for full docs
   - Architecture guide
   - SQL query examples
   - Issue tracker for bugs/features

4. Suggestions for what to do next:
   - Let it run for a few days to collect data
   - Try the example queries
   - Check health report trends
   - Consider archiving old data

---

IMPORTANT NOTES FOR THIS INSTALLATION:

1. **Safety First**
   - Ask for confirmation before mounting RAM disk (destructive operation)
   - Backup existing crontab before modifying
   - Verify no name conflicts with existing files
   - Save installation log for troubleshooting

2. **Error Handling**
   - If any step fails, explain why and suggest fix
   - Don't proceed to next step until current step succeeds
   - Offer rollback option if user wants to uninstall

3. **Customization**
   - Ask about RAM disk size (default 4GB)
   - Ask about backup location (default /var/www/html)
   - Ask about watched directories (default ~/., /var/www/html)
   - Ask about ingest frequency (default 1-5 minutes)

4. **Long-Term Sustainability**
   - Explain that cron jobs run forever (until uninstalled)
   - Suggest checking health report weekly
   - Mention that old data can be archived after 30 days
   - Point to documentation for advanced queries

5. **Future Extensibility**
   - Explain that ECM 002 is currently Claude Code CLI only
   - Note that it's open source and can be extended
   - Mention future plans for ChatGPT, other AI systems

---

This is the complete ECM 002 installation prompt. Once you have read and understood 
all of the above, please proceed with building and installing the system. Ask for 
confirmation at each major step, and provide detailed output so the user knows 
what's happening at each stage.

The goal is: User runs one prompt, and walks away with a fully functioning, 
automatically-updating, searchable action capture system on their machine.

Good luck building ECM 002. This is the future of stateful AI assistants.
```

---

## How to Use This Prompt

1. **Copy the entire prompt** (the section between the triple backticks above)
2. **Open Claude Code CLI** on your machine
3. **Paste the prompt** into Claude Code and press Enter
4. **Follow the interactive prompts** as Claude Code guides you through installation
5. **Verify each step** as Claude Code tests and confirms functionality
6. **Enjoy your external context memory** — your work is now captured and searchable

---

## What Happens Next

Once Claude Code finishes the installation, you'll have:
- ✅ All 5 phases running (Bash, SSH, Fossil, Files, System)
- ✅ 9 cron jobs capturing and ingesting data automatically
- ✅ Full-text searchable database with all your actions
- ✅ Health monitoring showing system status
- ✅ SSD backup syncing every 5 minutes
- ✅ Documentation and query examples

**Everything runs automatically from that point on.** You don't need to do anything. 
Just use Claude Code normally, and your context grows automatically.

---

## Questions?

- **What is ECM 002?** See [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **How do I query the data?** See [USAGE.md](docs/USAGE.md)
- **Something broke?** See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **I want to extend it?** See [CONTRIBUTING.md](CONTRIBUTING.md)

---

**License:** MIT  
**Repository:** [github.com/your-username/ECM_002_StatefulClaude](https://github.com/your-username/ECM_002_StatefulClaude)  
**Status:** Production Ready | Claude Code CLI Only | v0.1.0
