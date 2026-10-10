"""
State management, telemetry snapshot recording, and CLI diagnostics.
"""

import os
import glob
import json
import subprocess
from datetime import datetime, timezone
from .hal import run_cmd
from .discovery import discover_hardware, UNIVERSAL_PRIME_PCT

STATE_FILE = "/run/changestate.state"
TELEMETRY_LOG = "/var/log/changestate_telemetry.jsonl"

def collect_telemetry_snapshot(target_tier):
    """Record a point-in-time hardware snapshot as a JSON line."""
    now_iso = datetime.now(timezone.utc).isoformat()
    freqs = []
    for fpath in sorted(glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq")):
        try:
            with open(fpath, "r") as f:
                freqs.append(int(f.read().strip()))
        except Exception:
            pass

    online_cores = "unknown"
    try:
        with open("/sys/devices/system/cpu/online", "r") as f:
            online_cores = f.read().strip()
    except Exception:
        pass

    mem_total_mb, mem_used_mb = 0, 0
    try:
        res = subprocess.run("free -m", shell=True, capture_output=True, text=True)
        for line in res.stdout.splitlines():
            if line.startswith("Mem:"):
                parts = line.split()
                mem_total_mb = int(parts[1])
                mem_used_mb = int(parts[2])
                break
    except Exception:
        pass

    battery = {}
    try:
        with open("/sys/class/power_supply/BAT0/capacity", "r") as f:
            battery["percent"] = int(f.read().strip())
        with open("/sys/class/power_supply/BAT0/status", "r") as f:
            battery["status"] = f.read().strip()
    except Exception:
        pass

    doc = {
        "timestamp": now_iso,
        "tier": target_tier,
        "online_cores": online_cores,
        "cpu_khz": freqs,
        "mem_used_mb": mem_used_mb,
        "mem_total_mb": mem_total_mb,
        "battery": battery
    }

    json_line = json.dumps(doc, separators=(",", ":"), allow_nan=False)
    try:
        with open(TELEMETRY_LOG, "a") as f:
            f.write(json_line + "\n")
    except PermissionError as e:
        print(f"[!] Warning writing telemetry: {e}")
    except Exception:
        pass

def save_active_state(name):
    """Save active tier name to STATE_FILE and log telemetry."""
    try:
        with open(STATE_FILE, "w") as f:
            f.write(name)
    except PermissionError as e:
        print(f"[!] Warning writing state file: {e}")
    except Exception:
        pass
    collect_telemetry_snapshot(name)

def show_status():
    """Print complete diagnostic status of current hardware and state."""
    hw = discover_hardware()
    state = "UNKNOWN"
    try:
        with open(STATE_FILE, "r") as f:
            state = f.read().strip()
    except Exception:
        pass

    # Extract prime number if present
    p_num = None
    if state.startswith("P:"):
        try:
            p_num = int(state.split(":")[1])
        except Exception:
            pass

    pct = UNIVERSAL_PRIME_PCT.get(p_num) if p_num else None

    # Core count
    online_count = hw["total_cores"]
    try:
        with open("/sys/devices/system/cpu/online", "r") as f:
            online_str = f.read().strip()
            count = 0
            for part in online_str.split(","):
                if "-" in part:
                    s, e = part.split("-")
                    count += (int(e) - int(s) + 1)
                else:
                    count += 1
            online_count = count
    except Exception:
        pass

    asleep_count = max(0, hw["total_cores"] - online_count)

    # CPU clock cap
    cur_cpu_cap = hw["cpu_max_khz"] // 1000
    try:
        with open("/sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq", "r") as f:
            cur_cpu_cap = int(f.read().strip()) // 1000
    except Exception:
        pass

    # Turbo boost status
    turbo_disabled = True
    if os.path.exists("/sys/devices/system/cpu/intel_pstate/no_turbo"):
        try:
            with open("/sys/devices/system/cpu/intel_pstate/no_turbo", "r") as f:
                turbo_disabled = (f.read().strip() == "1")
        except Exception:
            pass
    elif os.path.exists("/sys/devices/system/cpu/cpufreq/boost"):
        try:
            with open("/sys/devices/system/cpu/cpufreq/boost", "r") as f:
                turbo_disabled = (f.read().strip() == "0")
        except Exception:
            pass
    elif os.path.exists("/sys/devices/system/cpu/cpufreq/policy0/boost"):
        try:
            with open("/sys/devices/system/cpu/cpufreq/policy0/boost", "r") as f:
                turbo_disabled = (f.read().strip() == "0")
        except Exception:
            pass

    # Swappiness
    swappiness = "60"
    try:
        with open("/proc/sys/vm/swappiness", "r") as f:
            swappiness = f.read().strip()
    except Exception:
        pass

    # Battery
    bat_str = "N/A"
    try:
        with open("/sys/class/power_supply/BAT0/capacity", "r") as f:
            cap = f.read().strip()
        with open("/sys/class/power_supply/BAT0/status", "r") as f:
            stat = f.read().strip()
        bat_str = f"{cap}% ({stat})"
    except Exception:
        pass

    # GPU
    gpu_draw = "Idle / Low"
    gpu_clk = "Default"
    if hw["gpu"]["vendor"] == "nvidia":
        try:
            res = subprocess.run(
                "nvidia-smi --query-gpu=power.draw,clocks.gr --format=csv,noheader",
                shell=True, capture_output=True, text=True
            )
            if res.returncode == 0 and res.stdout.strip():
                parts = [p.strip() for p in res.stdout.strip().split(",")]
                gpu_draw, gpu_clk = parts[0], parts[1]
        except Exception:
            pass

    # Capacity bar
    bar_width = 24
    filled = round((pct / 100) * bar_width) if pct is not None else 0
    bar = "█" * filled + "░" * (bar_width - filled)
    pct_txt = "unknown" if pct is None else (f"{pct}%" if pct >= 100 else f"~{pct}%")

    print("=" * 64)
    print(f"  CHANGESTATE  •  Active Level: {state} ({pct_txt} Capacity)")
    print(f"  [{bar}] {pct_txt}")
    print("=" * 64)
    print("CPU (Processor):")
    print(f"  • Active Cores   : {online_count} of {hw['total_cores']} cores running ({asleep_count} powered down asleep)")
    print(f"  • Speed Ceiling  : {cur_cpu_cap} MHz (Clamped from factory {hw['cpu_max_khz'] // 1000} MHz to stop heat)")
    print(f"  • Turbo Boost    : {'Off (Enforced - stops sudden fan spikes)' if turbo_disabled else 'On'}")
    print()
    print("GPU (Graphics):")
    print(f"  • Real-Time Draw : {gpu_draw} (Running at {gpu_clk})")
    p_def = hw["gpu"].get("power_default_w")
    tgp = f"{p_def}W" if p_def else "factory"
    if pct is None:
        print("  • Power Ceiling  : unknown (no recorded tier)")
    elif pct >= 100:
        print(f"  • Power Ceiling  : Uncapped ({tgp} TGP, Dynamic Boost enabled)")
    else:
        print(f"  • Power Ceiling  : {tgp} TGP, dynamic boost spikes clamped")
    print()
    print("Memory & Cooling:")
    print(f"  • Swappiness     : {swappiness} (Keeps active data in RAM, avoids disk thrash)")
    print("  • Cooling Fans   : BIOS Automatic (Quiet baseline, safe thermal curve)")
    print(f"  • Battery        : {bat_str}")
    print("=" * 64)
