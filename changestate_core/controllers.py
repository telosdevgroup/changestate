"""
Hardware scaling controllers: CPU core hotplugging, clock caps,
governors/EPP, GPU clamping, memory swappiness, radios, and services.
"""

from .hal import run_cmd, write_sysfs, is_intel_cpu
from .discovery import discover_hardware

def set_cpu_cores(target_count):
    """Dynamically set the number of active CPU cores (Core 0 always online)."""
    total = discover_hardware()["total_cores"]
    target = min(max(target_count, 1), total)
    for i in range(1, total):
        state = 1 if i < target else 0
        write_sysfs(f"/sys/devices/system/cpu/cpu{i}/online", state)

def set_cpu_boost(enabled):
    """Enable or disable CPU turbo/boost across AMD and Intel CPUs."""
    if is_intel_cpu():
        write_sysfs("/sys/devices/system/cpu/intel_pstate/no_turbo", 0 if enabled else 1)
    else:
        write_sysfs("/sys/devices/system/cpu/cpufreq/boost", 1 if enabled else 0)

def set_cpu_freq_cap(max_khz):
    """Cap max CPU frequency across all online cores."""
    write_sysfs("/sys/devices/system/cpu/cpufreq/policy*/scaling_max_freq", max_khz)

def set_cpu_governor(governor, epp=None):
    """Set CPU frequency scaling governor and energy_performance_preference."""
    write_sysfs("/sys/devices/system/cpu/cpufreq/policy*/scaling_governor", governor)
    epp_map = {
        "powersave": "power",
        "performance": "performance",
        "balanced": "balance_performance",
        "balance_power": "balance_power"
    }
    epp_val = epp if epp is not None else epp_map.get(governor, "default")
    write_sysfs("/sys/devices/system/cpu/cpufreq/policy*/energy_performance_preference", epp_val)

def set_gpu_clamp(ratio, hw):
    """
    Clamp GPU clocks proportionally to capacity ratio, locked under 80% ceiling.
    Auto-boost / Dynamic Boost strictly disabled on low/mid tiers.
    At 100% capacity (ratio >= 1.0, e.g. P:31), all clamps are released:
    full factory power limit, full clock range, and auto-boost restored.
    """
    if ratio <= 0.25:
        write_sysfs("/sys/class/drm/card*/device/power_dpm_force_performance_level", "low")
    else:
        write_sysfs("/sys/class/drm/card*/device/power_dpm_force_performance_level", "auto")

    if hw["gpu"]["vendor"] == "nvidia":
        if ratio >= 1.0:
            # 100% Full Open Throttle: Reset clocks, restore factory power, enable auto-boost
            run_cmd("nvidia-smi -rgc")
            p_def = hw["gpu"].get("power_default_w") or 115
            run_cmd(f"nvidia-smi -pl {p_def}")
            run_cmd("nvidia-smi --auto-boost-permission=1")
        else:
            # Always revoke auto-boost permission on clamped tiers (no unexpected surges)
            run_cmd("nvidia-smi --auto-boost-permission=0")
            
            g_min = hw["gpu"]["min_clk_mhz"]
            g_max = hw["gpu"]["max_clk_mhz"]
            if g_max > g_min:
                # 80% maximum glass ceiling multiplier
                g_ceiling = int(g_min + ratio * (0.80 * g_max - g_min))
                run_cmd(f"nvidia-smi -lgc {g_min},{g_ceiling}")
            else:
                run_cmd("nvidia-smi -rgc")

def set_memory_swappiness(ratio):
    """
    Dynamically tune swappiness and dirty cache ratio:
    Low ratio: Aggressive flushing (cool RAM), low swappiness (minimize disk thrash).
    High ratio: Generous page caching for fast batch tensor loading without swapping.
    """
    target_swap = max(1, int(10 - ratio * 9))
    write_sysfs("/proc/sys/vm/swappiness", target_swap)

    target_dirty = int(10 + ratio * 10)
    write_sysfs("/proc/sys/vm/dirty_background_ratio", target_dirty)

def set_radios(wifi=True, bluetooth=False):
    """Control Wi-Fi and Bluetooth using rfkill."""
    run_cmd(f"rfkill {'unblock' if wifi else 'block'} wifi")
    run_cmd(f"rfkill {'unblock' if bluetooth else 'block'} bluetooth")

def set_camera_power(enabled=True):
    write_sysfs("/sys/devices/pci*/**/VPC2004:00/camera_power", 1 if enabled else 0)

def set_mic_mute(mute=False):
    run_cmd(f"amixer set Capture {'mute' if mute else 'unmute'}")

def set_aux_services(enable=True):
    services = ["cups", "cups-browsed", "ModemManager"]
    action = "start" if enable else "stop"
    for s in services:
        run_cmd(f"sudo systemctl {action} {s}")

def start_dev_stack():
    """Ensure developmental databases and LLM servers stay alive."""
    for s in ["mongod", "mongodb", "ollama"]:
        run_cmd(f"sudo systemctl start {s}")
