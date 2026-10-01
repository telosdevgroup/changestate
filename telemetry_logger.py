#!/usr/bin/env python3
"""
telemetry_logger.py - High-density hardware telemetry logger for changestate.
Outputs JSONL formatted records ideal for AI ingestion and trend analysis.
Logs CPU cores/freqs/load, package temp, GPU power/temp, NVMe temp, battery, and web latency.
"""

import os
import sys
import time
import json
import urllib.request
from datetime import datetime, timezone

LOG_DIR = "/var/log/changestate"
LOG_FILE = os.path.join(LOG_DIR, "telemetry.jsonl")

def read_file(path, default=""):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return default

def get_cpu_utilization():
    try:
        def read_stat():
            with open("/proc/stat", "r") as f:
                fields = [float(x) for x in f.readline().strip().split()[1:8]]
            idle = fields[3] + fields[4]
            total = sum(fields)
            return idle, total
        idle1, total1 = read_stat()
        time.sleep(0.15)
        idle2, total2 = read_stat()
        diff_idle = idle2 - idle1
        diff_total = total2 - total1
        if diff_total <= 0:
            return 0.0
        return round(max(0.0, min(100.0, 100.0 * (1.0 - (diff_idle / diff_total)))), 2)
    except Exception:
        return 0.0

def measure_web_latency():
    # Measure latency to local web server port 8006
    t0 = time.time()
    try:
        req = urllib.request.Request("http://127.0.0.1:8006/", headers={"User-Agent": "TelemetryBot/1.0"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            status = resp.status
        latency_ms = round((time.time() - t0) * 1000.0, 2)
        return {"status": status, "latency_ms": latency_ms}
    except Exception as e:
        return {"status": 0, "error": str(e), "latency_ms": -1}

def get_snapshot():
    now_iso = datetime.now(timezone.utc).isoformat()

    # Active persona
    persona = read_file("/var/run/changestate.state", default="untracked")

    # CPU online cores & frequencies
    online_cores = read_file("/sys/devices/system/cpu/online", default="unknown")
    epp = read_file("/sys/devices/system/cpu/cpufreq/policy0/energy_performance_preference", default="unknown")
    governor = read_file("/sys/devices/system/cpu/cpufreq/policy0/scaling_governor", default="unknown")
    boost = read_file("/sys/devices/system/cpu/cpufreq/boost", default="unknown")

    # Sample frequencies of core 0 and 1
    freq0 = int(read_file("/sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq", default="0"))
    freq1 = int(read_file("/sys/devices/system/cpu/cpufreq/policy1/scaling_cur_freq", default="0"))

    # Temperatures (in Celsius)
    temp_cpu_raw = read_file("/sys/class/hwmon/hwmon3/temp1_input", default="0")
    temp_gpu_raw = read_file("/sys/class/hwmon/hwmon4/temp1_input", default="0")
    temp_nvme_raw = read_file("/sys/class/hwmon/hwmon2/temp1_input", default="0")

    temp_cpu_c = round(float(temp_cpu_raw) / 1000.0, 1) if temp_cpu_raw.isdigit() else None
    temp_gpu_c = round(float(temp_gpu_raw) / 1000.0, 1) if temp_gpu_raw.isdigit() else None
    temp_nvme_c = round(float(temp_nvme_raw) / 1000.0, 1) if temp_nvme_raw.isdigit() else None

    # GPU Power & DPM level
    gpu_power_raw = read_file("/sys/class/hwmon/hwmon4/power1_input", default="0")
    gpu_power_w = round(float(gpu_power_raw) / 1000000.0, 2) if gpu_power_raw.isdigit() else None
    gpu_dpm = read_file("/sys/class/drm/card1/device/power_dpm_force_performance_level", default="unknown")

    # Battery
    battery_pct = int(read_file("/sys/class/power_supply/BAT0/capacity", default="-1"))
    battery_status = read_file("/sys/class/power_supply/BAT0/status", default="unknown")

    # Load & Latency
    cpu_load = get_cpu_utilization()
    web_stat = measure_web_latency()

    record = {
        "timestamp": now_iso,
        "persona": persona,
        "cpu": {
            "online": online_cores,
            "load_percent": cpu_load,
            "governor": governor,
            "epp": epp,
            "boost": boost == "1",
            "freq_core0_khz": freq0,
            "freq_core1_khz": freq1,
        },
        "gpu": {
            "dpm_level": gpu_dpm,
            "power_watts": gpu_power_w,
        },
        "thermals_c": {
            "cpu_tctl": temp_cpu_c,
            "gpu_edge": temp_gpu_c,
            "nvme": temp_nvme_c,
        },
        "battery": {
            "percent": battery_pct,
            "status": battery_status,
        },
        "web": web_stat
    }
    return record

def main():
    interval = 10.0  # Log every 10 seconds by default
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        rec = get_snapshot()
        print(json.dumps(rec, indent=2))
        return

    # Check if target log directory exists, otherwise fallback to local
    target_path = LOG_FILE
    if not os.path.exists(LOG_DIR):
        try:
            os.makedirs(LOG_DIR, exist_ok=True)
        except PermissionError:
            target_path = os.path.expanduser("~/changestate-telemetry.jsonl")

    print(f"[*] Telemetry logger started. Appending records to {target_path} (every {interval}s).")
    try:
        while True:
            rec = get_snapshot()
            line = json.dumps(rec)
            try:
                with open(target_path, "a") as f:
                    f.write(line + "\n")
            except Exception as e:
                print(f"[!] Log write error: {e}", file=sys.stderr)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[*] Telemetry logger stopped.")

if __name__ == "__main__":
    main()
