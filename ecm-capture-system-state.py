#!/usr/bin/env python3
"""
ECM Phase 5: System State Capture
Captures CPU, memory, disk, and network metrics periodically.

Reads from /proc and system commands, logs to /tmp/ecm-system-state.log
Monitors system health to correlate with activity in Phases 1-4.
"""

import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime

LOG_FILE = "/tmp/ecm-system-state.log"

def get_cpu_metrics():
    """Get CPU usage, load average."""
    try:
        with open("/proc/loadavg") as f:
            load_data = f.read().split()
            return {
                'load_1min': float(load_data[0]),
                'load_5min': float(load_data[1]),
                'load_15min': float(load_data[2])
            }
    except:
        return {}

def get_memory_metrics():
    """Get memory usage (total, used, free, percent)."""
    try:
        with open("/proc/meminfo") as f:
            mem = {}
            for line in f:
                if line.startswith(("MemTotal", "MemAvailable")):
                    key, value = line.split(":")
                    mem[key.strip()] = int(value.split()[0])

        if mem:
            total = mem.get('MemTotal', 0)
            avail = mem.get('MemAvailable', 0)
            used = total - avail
            percent = (used / total * 100) if total > 0 else 0
            return {
                'total_mb': total // 1024,
                'available_mb': avail // 1024,
                'used_mb': used // 1024,
                'percent_used': round(percent, 1)
            }
    except:
        pass
    return {}

def get_disk_metrics():
    """Get disk usage for root filesystem."""
    try:
        result = subprocess.run(
            ["df", "-B1", "/"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                total = int(parts[1])
                used = int(parts[2])
                avail = int(parts[3])
                percent = (used / total * 100) if total > 0 else 0
                return {
                    'total_gb': total // (1024**3),
                    'used_gb': used // (1024**3),
                    'available_gb': avail // (1024**3),
                    'percent_used': round(percent, 1)
                }
    except:
        pass
    return {}

def get_network_metrics():
    """Get network interface stats."""
    try:
        with open("/proc/net/dev") as f:
            lines = f.readlines()
            total_rx = 0
            total_tx = 0
            for line in lines[2:]:  # Skip header lines
                if ':' not in line:
                    continue
                parts = line.split()
                if len(parts) >= 10:
                    total_rx += int(parts[1])
                    total_tx += int(parts[9])
            return {
                'bytes_received': total_rx,
                'bytes_sent': total_tx,
                'bytes_received_mb': total_rx // (1024**2),
                'bytes_sent_mb': total_tx // (1024**2)
            }
    except:
        pass
    return {}

def get_process_count():
    """Get total running process count."""
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return len(result.stdout.strip().split('\n')) - 1
    except:
        pass
    return 0

def capture_system_state():
    """Capture all system metrics."""
    timestamp = datetime.now().isoformat() + "Z"

    metrics = {
        'timestamp': timestamp,
        'cpu': get_cpu_metrics(),
        'memory': get_memory_metrics(),
        'disk': get_disk_metrics(),
        'network': get_network_metrics(),
        'processes': get_process_count()
    }

    # Log as pipe-delimited: timestamp|json_metrics
    json_str = json.dumps(metrics)
    log_entry = f"{timestamp}|{json_str}"

    try:
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry + '\n')
    except IOError as e:
        print(f"✗ Error writing to log: {e}")
        return False

    return True

def show_current_state():
    """Display current system state."""
    metrics = {
        'cpu': get_cpu_metrics(),
        'memory': get_memory_metrics(),
        'disk': get_disk_metrics(),
        'network': get_network_metrics(),
        'processes': get_process_count()
    }

    print("\nCurrent System State:")
    print("─────────────────────────────────")

    if metrics['cpu']:
        print(f"CPU Load:  1m={metrics['cpu']['load_1min']:.2f} " +
              f"5m={metrics['cpu']['load_5min']:.2f} " +
              f"15m={metrics['cpu']['load_15min']:.2f}")

    if metrics['memory']:
        print(f"Memory:    {metrics['memory']['used_mb']}MB / " +
              f"{metrics['memory']['total_mb']}MB " +
              f"({metrics['memory']['percent_used']:.1f}%)")

    if metrics['disk']:
        print(f"Disk:      {metrics['disk']['used_gb']}GB / " +
              f"{metrics['disk']['total_gb']}GB " +
              f"({metrics['disk']['percent_used']:.1f}%)")

    if metrics['network']:
        print(f"Network:   RX {metrics['network']['bytes_received_mb']}MB " +
              f"TX {metrics['network']['bytes_sent_mb']}MB")

    if metrics['processes']:
        print(f"Processes: {metrics['processes']}")

if __name__ == "__main__":
    success = capture_system_state()

    if success:
        show_current_state()
        print("\n✓ System state captured")
    else:
        print("✗ Failed to capture system state")
        sys.exit(1)
