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
    """Write value to one or more sysfs files matching path_pattern."""
    for path in glob.glob(path_pattern):
        if os.path.exists(path):
            try:
                with open(path, "w") as f:
                    f.write(str(value))
            except PermissionError:
                subprocess.run(f"echo {value} | sudo tee {path} > /dev/null", shell=True, check=False)
            except Exception as e:
                if getattr(e, "errno", None) != 16:
                    print(f"[!] Warning writing to {path}: {e}")

def is_intel_cpu():
    """Detect if running on an Intel CPU with intel_pstate."""
    return os.path.exists("/sys/devices/system/cpu/intel_pstate")

def has_nvidia_gpu():
    """Detect if NVIDIA GPU and driver tools are present."""
    return shutil.which("nvidia-smi") is not None
