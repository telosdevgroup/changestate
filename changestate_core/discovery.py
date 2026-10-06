"""
Hardware auto-discovery module: dynamically queries CPU topology,
clock boundaries, memory/swap, and GPU capabilities.
"""

import os
import glob
import subprocess
from .hal import has_nvidia_gpu

# Standardized Prime Percentage Map (Universal across all computers)
UNIVERSAL_PRIME_PCT = {
    2:  6,    # Floor (~6%)
    3:  10,   # ~10%
    5:  16,   # ~16%
    7:  23,   # ~23%
    11: 35,   # ~35%
    13: 42,   # ~42%
    17: 55,   # ~55%
    19: 61,   # ~61%
    23: 75,   # ~75% (The universal balanced capacity sweet spot)
    29: 93,   # ~93%
    31: 100   # 100% (Full capacity, completely uncapped)
}

def discover_cpu_topology_order():
    """
    Discover CPU topology and return an allocation priority list:
      1. Primary thread of each physical core (prioritizing P-cores over E-cores on hybrid CPUs)
      2. Secondary SMT/Hyper-Threading threads
      3. Any offline or unmapped CPU IDs
    CPU 0 is always guaranteed at index 0.
    """
    cpu_nodes = glob.glob("/sys/devices/system/cpu/cpu[0-9]*")
    total_cpus = max(len(cpu_nodes), 1)

    atom_cpus, core_cpus = set(), set()
    for pmu, cpu_set in [("cpu_atom", atom_cpus), ("cpu_core", core_cpus)]:
        pmu_path = f"/sys/devices/{pmu}/cpus"
        if os.path.exists(pmu_path):
            try:
                with open(pmu_path) as f:
                    for part in f.read().strip().split(","):
                        if "-" in part:
                            s, e = map(int, part.split("-"))
                            cpu_set.update(range(s, e + 1))
                        elif part.isdigit():
                            cpu_set.add(int(part))
            except Exception:
                pass

    seen_siblings = set()
    primary_cpus, secondary_cpus = [], []
    for i in range(total_cpus):
        top_file = f"/sys/devices/system/cpu/cpu{i}/topology/thread_siblings_list"
        if not os.path.exists(top_file) or i in seen_siblings:
            continue
        s_list = []
        try:
            with open(top_file) as f:
                for part in f.read().strip().split(","):
                    if "-" in part:
                        s, e = map(int, part.split("-"))
                        s_list.extend(range(s, e + 1))
                    elif part.isdigit():
                        s_list.append(int(part))
        except Exception:
            s_list = [i]
        s_list = sorted(set(s_list))
        for sib in s_list:
            seen_siblings.add(sib)
        primary_cpus.append(s_list[0])
        for sib in s_list[1:]:
            secondary_cpus.append(sib)

    remaining = [i for i in range(total_cpus) if i not in seen_siblings]

    if core_cpus or atom_cpus:
        p_primaries = [c for c in primary_cpus if c in core_cpus]
        e_primaries = [c for c in primary_cpus if c in atom_cpus]
        other_primaries = [c for c in primary_cpus if c not in core_cpus and c not in atom_cpus]
        primary_cpus = p_primaries + e_primaries + other_primaries

    alloc_order = []
    for c in primary_cpus + secondary_cpus + remaining:
        if c not in alloc_order:
            alloc_order.append(c)

    if 0 in alloc_order:
        alloc_order.remove(0)
    return [0] + alloc_order

def discover_hardware():
    """
    Dynamically auto-discover hardware specifications of the current machine.
    Zero hardcoded values.
    """
    # 1. Total CPU threads
    cpu_nodes = glob.glob("/sys/devices/system/cpu/cpu[0-9]*")
    total_cores = max(len(cpu_nodes), 1)

    # 2. CPU Frequency Boundaries (kHz)
    min_freqs, max_freqs = [], []
    for p in glob.glob("/sys/devices/system/cpu/cpufreq/policy*"):
        try:
            with open(os.path.join(p, "cpuinfo_min_freq")) as f:
                min_freqs.append(int(f.read().strip()))
            with open(os.path.join(p, "cpuinfo_max_freq")) as f:
                max_freqs.append(int(f.read().strip()))
        except Exception:
            pass
    cpu_min_khz = min(min_freqs) if min_freqs else 800000
    cpu_max_khz = max(max_freqs) if max_freqs else 3000000

    # 3. RAM & Swap (MB)
    mem_total_mb, swap_total_mb = 0, 0
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem_total_mb = int(line.split()[1]) // 1024
                elif line.startswith("SwapTotal:"):
                    swap_total_mb = int(line.split()[1]) // 1024
    except Exception:
        pass

    # 4. GPU Discovery (NVIDIA & AMD)
    gpu = {"vendor": "none", "min_clk_mhz": 0, "max_clk_mhz": 0}
    if has_nvidia_gpu():
        gpu["vendor"] = "nvidia"
        try:
            res = subprocess.run(["nvidia-smi", "-q", "-d", "SUPPORTED_CLOCKS"], capture_output=True, text=True)
            if res.returncode == 0:
                clocks = []
                for l in res.stdout.splitlines():
                    if "Graphics" in l:
                        parts = l.split(":")
                        if len(parts) == 2:
                            clocks.append(int(parts[1].strip().split()[0]))
                if clocks:
                    gpu["min_clk_mhz"] = min(clocks)
                    gpu["max_clk_mhz"] = max(clocks)
        except Exception:
            pass

        # Fallback query if supported_clocks was restricted
        if not gpu["max_clk_mhz"]:
            try:
                res = subprocess.run(["nvidia-smi", "--query-gpu=clocks.max.graphics", "--format=csv,noheader"], capture_output=True, text=True)
                if res.returncode == 0 and res.stdout.strip().isdigit():
                    gpu["max_clk_mhz"] = int(res.stdout.strip())
                    gpu["min_clk_mhz"] = 210
            except Exception:
                pass

        gpu["power_default_w"] = 0
        gpu["power_max_w"] = 0
        try:
            res = subprocess.run(["nvidia-smi", "--query-gpu=power.default_limit,power.max_limit", "--format=csv,noheader"], capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                parts = [p.replace("W", "").strip() for p in res.stdout.strip().split(",")]
                if len(parts) >= 2:
                    gpu["power_default_w"] = int(float(parts[0]))
                    gpu["power_max_w"] = int(float(parts[1]))
        except Exception:
            pass

    return {
        "total_cores": total_cores,
        "cpu_min_khz": cpu_min_khz,
        "cpu_max_khz": cpu_max_khz,
        "mem_total_mb": mem_total_mb,
        "swap_total_mb": swap_total_mb,
        "gpu": gpu
    }

def get_capacity_tiers_metadata():
    """Output universal capacity tiers metadata with machine-specific active core counts."""
    hw = discover_hardware()
    tiers = []
    for p, pct in UNIVERSAL_PRIME_PCT.items():
        cores = max(1, round((pct / 100.0) * hw["total_cores"]))
        if p == 23:
            label = f"P:23 · ~{pct}% (Balanced)"
        elif p == 2:
            label = f"P:2 · ~{pct}% (Floor)"
        elif p == 31:
            label = f"P:31 · {pct}% (Max)"
        else:
            label = f"P:{p} · ~{pct}%"

        tiers.append({
            "id": f"p{p}",
            "prime": p,
            "pct": pct,
            "cores": cores,
            "total_cores": hw["total_cores"],
            "label": label
        })
    return tiers
