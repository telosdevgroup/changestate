"""
changestate_core package initialization.
"""

from .hal import run_cmd, write_sysfs, is_intel_cpu, has_nvidia_gpu, scaled_cap
from .discovery import (
    UNIVERSAL_PRIME_PCT,
    discover_hardware,
    discover_cpu_topology_order,
    get_capacity_tiers_metadata
)
from .controllers import (
    set_cpu_cores,
    set_cpu_boost,
    set_cpu_freq_cap,
    set_cpu_governor,
    set_gpu_clamp,
    set_memory_swappiness,
    set_radios,
    set_camera_power,
    set_mic_mute,
    engage_metal_posture
)
from .status import (
    STATE_FILE,
    TELEMETRY_LOG,
    collect_telemetry_snapshot,
    save_active_state,
    show_status
)

__all__ = [
    "run_cmd",
    "write_sysfs",
    "is_intel_cpu",
    "has_nvidia_gpu",
    "scaled_cap",
    "UNIVERSAL_PRIME_PCT",
    "discover_hardware",
    "get_capacity_tiers_metadata",
    "set_cpu_cores",
    "set_cpu_boost",
    "set_cpu_freq_cap",
    "set_cpu_governor",
    "set_gpu_clamp",
    "set_memory_swappiness",
    "set_radios",
    "set_camera_power",
    "set_mic_mute",
    "engage_metal_posture",
    "STATE_FILE",
    "TELEMETRY_LOG",
    "collect_telemetry_snapshot",
    "save_active_state",
    "show_status"
]
