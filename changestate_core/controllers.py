"""
Hardware scaling controllers: CPU core hotplugging, clock caps,
governors/EPP, GPU clamping, memory swappiness, radios, and MOM defensive posture.
"""

import subprocess
import sys
from .hal import run_cmd, write_sysfs, is_intel_cpu, scaled_cap
from .discovery import discover_hardware, discover_cpu_topology_order

def set_cpu_cores(target_count):
    """
    Dynamically set the number of active CPU cores using topology-aware ordering:
    - Primary physical threads (and P-cores) are kept online first for max IPC/watt.
    - SMT secondary threads are brought online only when scaling up, and offlined first.
    - Core 0 is permanently pinned online.
    """
    order = discover_cpu_topology_order()
    total = len(order)
    target = min(max(target_count, 1), total)

    active_set = set(order[:target])
    # Core 0 is permanently online; hotplug remaining cores
    for cpu_id in order:
        if cpu_id == 0:
            continue
        state = 1 if cpu_id in active_set else 0
        write_sysfs(f"/sys/devices/system/cpu/cpu{cpu_id}/online", state)

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
        # Always reset clock locks (-rgc) to prevent nvidia-modeset kernel driver hangs
        run_cmd("nvidia-smi -rgc")
        if ratio >= 1.0:
            p_def = hw["gpu"].get("power_default_w")
            if p_def:  # Unknown default: leave the power limit untouched
                run_cmd(f"nvidia-smi -pl {int(p_def)}")
            run_cmd("nvidia-smi --auto-boost-permission=1")
        else:
            # Revoke auto-boost permission to prevent power surges without starving display modeset
            run_cmd("nvidia-smi --auto-boost-permission=0")

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
    """Lenovo IdeaPad ACPI camera power (stable platform-bus path)."""
    write_sysfs("/sys/bus/platform/devices/VPC2004:*/camera_power", 1 if enabled else 0)

def set_mic_mute(mute=False):
    run_cmd(f"amixer set Capture {'mute' if mute else 'unmute'}")

def engage_metal_posture(active=True):
    """
    MOM (Metal Over Moss) Defensive Posture:
    - active=True (P:0): Total radio silence (rfkill block all), kill heavy gaming/dev
      processes (steam, mongod, ollama, docker), drop unsolicited inbound network traffic.
    - active=False (P:2..P:31): Restore inbound traffic policy.
    """
    if active:
        # 1. Total Radio Silence (Wired Ethernet untouched)
        run_cmd("rfkill block all")
        # 2. Strict defensive firewall (allow loopback & established sessions, drop unsolicited inbound)
        run_cmd("iptables -C INPUT -i lo -j ACCEPT 2>/dev/null || iptables -A INPUT -i lo -j ACCEPT")
        run_cmd("iptables -C INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT 2>/dev/null || iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT")
        run_cmd("iptables -P INPUT DROP")
        # 3. Kill heavy dev & gaming background loads
        targets = ["steam", "steamwebhelper", "mongod", "ollama", "docker"]
        for t in targets:
            run_cmd(f"pkill -15 -f {t} 2>/dev/null")
    else:
        # Restore standard firewall policy
        run_cmd("iptables -P INPUT ACCEPT")

def confirm_mom(assume_yes=False):
    """
    Guard for P:0 (MOM). Returns True if the user may proceed.
    - assume_yes (--confirm): proceed without a prompt (scripts, launchers).
    - Interactive terminal: the user must type MOM.
    - Otherwise: refuse, since nobody is there to confirm.
    """
    if assume_yes:
        return True
    if not sys.stdin.isatty():
        print("[!] P:0 (MOM) needs confirmation. Re-run with --confirm.")
        return False
    print("[!] P:0 (MOM) blocks ALL radios (Wi-Fi + Bluetooth), drops inbound traffic, and stops steam/docker/ollama/mongod.")
    print("[!] Restore with: sudo changestate p31 (or any other tier).")
    try:
        return input("Type MOM to continue: ").strip().upper() == "MOM"
    except EOFError:
        return False
