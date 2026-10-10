"""
Hardware abstraction layer and sysfs / shell command helpers.
"""

import os
import glob
import subprocess
import shutil

def run_cmd(cmd):
    """Run a shell command silently; ignore non-fatal errors."""
    try:
        subprocess.run(cmd, shell=True, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def write_sysfs(path_pattern, value):
    """Write value to every sysfs file matching path_pattern.

    Globbing is non-recursive on purpose: `**` in /sys can follow symlink
    cycles. Use stable paths (e.g. /sys/bus/*/devices/...) instead.
    Never escalates privileges: the tool is expected to run as root. EBUSY,
    ENOENT, and ENODEV (common on offline CPU cores) are ignored; any other
    failure is reported and the caller continues.
    """
    for path in glob.glob(path_pattern):
        if os.path.exists(path):
            try:
                with open(path, "w") as f:
                    f.write(str(value))
            except OSError as e:
                # 16 = EBUSY, 2 = ENOENT, 19 = ENODEV (offline cores return busy/no-such-device)
                if e.errno in (16, 2, 19):
                    continue
                print(f"[!] Warning writing to {path}: {e}")
            except Exception as e:
                print(f"[!] Warning writing to {path}: {e}")

def scaled_cap(lo, hi, ratio):
    """Proportional clock cap clamped to [lo, 0.80 * hi] (AGENTS.md §1.3)."""
    ceiling = max(lo, 0.80 * hi)
    return int(min(max(lo + ratio * (0.80 * hi - lo), lo), ceiling))

def get_cpu_driver():
    """Detect active cpufreq scaling driver (e.g. 'intel_pstate', 'amd-pstate-epp', 'acpi-cpufreq')."""
    driver_path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver"
    if os.path.exists(driver_path):
        try:
            with open(driver_path, "r") as f:
                driver = f.read().strip()
                if driver:
                    return driver
        except Exception:
            pass
    if os.path.exists("/sys/devices/system/cpu/intel_pstate"):
        return "intel_pstate"
    return "generic"

def is_intel_cpu():
    """Detect if running on an Intel CPU with intel_pstate."""
    driver = get_cpu_driver()
    return driver == "intel_pstate" or os.path.exists("/sys/devices/system/cpu/intel_pstate")

def has_nvidia_gpu():
    """Detect if NVIDIA GPU and driver tools are present."""
    return shutil.which("nvidia-smi") is not None

