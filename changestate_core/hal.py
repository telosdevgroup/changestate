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
    Never escalates privileges: the tool is expected to run as root. EBUSY is
    ignored; any other failure is reported and the caller continues.
    """
    for path in glob.glob(path_pattern):
        if os.path.exists(path):
            try:
                with open(path, "w") as f:
                    f.write(str(value))
            except Exception as e:
                if getattr(e, "errno", None) != 16:
                    print(f"[!] Warning writing to {path}: {e}")

def scaled_cap(lo, hi, ratio):
    """Proportional clock cap clamped to [lo, 0.80 * hi] (AGENTS.md §1.3)."""
    ceiling = max(lo, 0.80 * hi)
    return int(min(max(lo + ratio * (0.80 * hi - lo), lo), ceiling))

def is_intel_cpu():
    """Detect if running on an Intel CPU with intel_pstate."""
    return os.path.exists("/sys/devices/system/cpu/intel_pstate")

def has_nvidia_gpu():
    """Detect if NVIDIA GPU and driver tools are present."""
    return shutil.which("nvidia-smi") is not None
