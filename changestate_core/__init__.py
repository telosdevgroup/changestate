"""
changestate_core package initialization.
"""

from .hal import run_cmd, write_sysfs, is_intel_cpu, has_nvidia_gpu
from .discovery import UNIVERSAL_PRIME_PCT, discover_hardware, get_capacity_tiers_metadata
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
    set_aux_services,
    start_dev_stack
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
    "set_aux_services",
    "start_dev_stack",
    "STATE_FILE",
    "TELEMETRY_LOG",
    "collect_telemetry_snapshot",
    "save_active_state",
    "show_status"
]
