#!/usr/bin/env python3
"""
ECM Search Test - Verify multi-tier FTS5 is working and fast
"""

import sqlite3
import time

db_path = "/mnt/ecm-ram/ecm-hot.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

test_queries = [
    ("external context memory", "ecm_content"),
    ("Fossil", "ecm_content"),
    ("ingest", "ecm_content"),
    ("memory", "ecm_content"),
    ("database", "ecm_metadata"),
]

print("=== ECM FTS5 SEARCH TEST ===\n")

for query, table in test_queries:
    start = time.time()
    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {table} MATCH ?", (query,))
    count = cursor.fetchone()[0]
    elapsed_ms = (time.time() - start) * 1000
    
    print(f"Query: '{query}'")
    print(f"  Results: {count}")
    print(f"  Time: {elapsed_ms:.3f} ms")
    print()

# Show size
import os
size_mb = os.path.getsize(db_path) / (1024*1024)
print(f"Database size: {size_mb:.1f} MB")
print(f"Mounted on: /mnt/ecm-ram/ (RAM disk)")

conn.close()
