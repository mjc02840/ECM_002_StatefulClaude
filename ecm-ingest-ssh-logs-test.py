#!/usr/bin/env python3
"""
ECM Phase 2 Test wrapper - uses sample auth.log from /tmp
"""

import sys
sys.path.insert(0, '/var/www/html/PQ/0510')

# Monkey-patch the LOG_FILE before importing
import ecm_ingest_ssh_logs as ssh_module
ssh_module.LOG_FILE = "/tmp/sample-auth.log"

ssh_module.ingest_ssh_logs()
ssh_module.show_recent()
