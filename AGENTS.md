# AGENTS.md — ChangeState Developer & Agent Guide

> **Core Purpose:** `changestate` provides discrete prime-core stepping and proportional hardware power / thermal / acoustic profiling for Linux systems (supporting AMD & Intel CPUs, Radeon & NVIDIA GPUs, and Lenovo EC platforms).

---

## 1. Prime Directives & Architectural Rules

1. **The 500-Line Prime Directive (<500 lines per file):**
   - **STRICT MAXIMUM:** No source code file may exceed 500 lines of code.
   - If a file approaches or exceeds this threshold, atomize it immediately: micronize into focused submodules within `changestate_core/` and import cleanly.
   - Cruft, dead code, and obsolete legacy routines must be excised rather than preserved.

2. **Universal Capacity Scaling (Standardized Prime Percentages):**
   - Hardware capacity is scaled dynamically using universal prime capacity percentages:
     - `P:2` = 6% (Floor), `P:3` = 10%, `P:5` = 16%, `P:7` = 23%, `P:11` = 35%, `P:13` = 42%, `P:17` = 55%, `P:19` = 61%, `P:23` = 75% (Balanced sweet spot), `P:29` = 93%, `P:31` = 100% (Uncapped full throttle).
   - Core allocations scale per machine: `active_cores = max(1, min(round((pct / 100) * total_cores), total_cores))`.
   - Core 0 is permanently pinned online; cores `1` through `N-1` are hotplugged via `/sys/devices/system/cpu/cpu*/online`.

3. **80% Safety Ceiling & Turbo Clamp:**
   - On sub-100% tiers (P:2 through P:29), CPU and GPU frequencies are strictly clamped within an 80% ceiling:
     `Target Freq = min + ratio * (0.80 * max - min)`.
   - CPU Turbo Boost and GPU Dynamic Boost are disabled on all clamped tiers to prevent sudden thermal/fan spikes.
   - On `P:31` (100%), all clamps are released: full turbo boost enabled, uncapped clock limits, and factory GPU TGP.

4. **Multi-Vendor Fallbacks & Resiliency:**
   - Always guard sysfs and vendor-specific paths with `glob.glob()`, `os.path.exists()`, or `try/except`.
   - Check `is_intel_cpu()` and `has_nvidia_gpu()` dynamically. Never assume vendor hardware presence.
   - When writing to sysfs, catch `PermissionError` and fall back gracefully to `echo <val> | sudo tee <path>`. Ignore `EBUSY` (errno 16).

---

## 2. Codebase Map & Atomized Architecture

```
changestate/
├── changestate                       # CLI executable entrypoint (< 250 lines)
├── changestate_core/                 # Micronized core engine modules (< 500 lines each)
│   ├── __init__.py                   # Package exports and public interface
│   ├── hal.py                        # Hardware abstraction, sysfs read/write, vendor checks
│   ├── discovery.py                  # Dynamic machine hardware auto-discovery & prime metadata
│   ├── controllers.py                # CPU hotplug, frequency caps, boost, GPU clamp, swappiness
│   └── status.py                     # State persistence, telemetry snapshots, diagnostic status
├── telemetry_logger.py               # High-density JSONL telemetry recorder agent (~150 lines)
├── changestate-*.desktop             # Desktop shortcuts
├── cinnamon-applet/                  # Desktop environment integration
│   └── changestate@avathings.com/    # Cinnamon extension with continuous popup slider
├── README.md                         # Public documentation and theory
└── AGENTS.md                         # (This document) Engineering blueprint & prime directives
```

### Module Breakdown (<500 Line Compliance)
- **[`changestate`](file:///home/dev/Code/tdg/compstate/changestate):** Lightweight executable script (<250 lines) handling CLI argument parsing (`status`, `tiers-json`, `p<N>`), user terminal launching, and orchestrating the prime capacity transition.
- **[`changestate_core/hal.py`](file:///home/dev/Code/tdg/compstate/changestate_core/hal.py):** Low-level hardware abstraction layer (~40 lines). Handles `write_sysfs()`, `run_cmd()`, `is_intel_cpu()`, and `has_nvidia_gpu()`.
- **[`changestate_core/discovery.py`](file:///home/dev/Code/tdg/compstate/changestate_core/discovery.py):** Hardware auto-discovery (~130 lines). Dynamically inspects CPU core counts, frequency limits, RAM/Swap, and GPU clocks without hardcoded values.
- **[`changestate_core/controllers.py`](file:///home/dev/Code/tdg/compstate/changestate_core/controllers.py):** Actuators (~110 lines). Implements `set_cpu_cores()`, `set_cpu_boost()`, `set_cpu_freq_cap()`, `set_cpu_governor()`, `set_gpu_clamp()`, and `set_memory_swappiness()`.
- **[`changestate_core/status.py`](file:///home/dev/Code/tdg/compstate/changestate_core/status.py):** Diagnostics & logging (~190 lines). Writes `/var/run/changestate.state`, generates `/var/log/changestate_telemetry.jsonl` snapshots, and renders ASCII status bars.
- **[`telemetry_logger.py`](file:///home/dev/Code/tdg/compstate/telemetry_logger.py):** Standalone telemetry collector daemon (~150 lines) outputting valid single-line JSONL metrics.

---

## 3. Hardware Subsystems Controlled

| Subsystem | Linux / Hardware Interface | Controlled Behavior |
| :--- | :--- | :--- |
| **CPU Core Hotplug** | `/sys/devices/system/cpu/cpu*/online` | Cores online from 1 up to `active_cores` (Core 0 permanently on) |
| **ACPI Platform Profile** | `/sys/firmware/acpi/platform_profile` | `low-power`, `balanced`, or `performance` based on tier ratio |
| **CPU Governor & EPP** | `/sys/devices/system/cpu/cpufreq/policy*/scaling_governor`, `energy_performance_preference` | `powersave` (with `power`, `balance_power`, `balance_performance`) or `performance` |
| **CPU Turbo / Boost** | Intel: `/sys/devices/system/cpu/intel_pstate/no_turbo`<br>AMD: `/sys/devices/system/cpu/cpufreq/boost` | Disabled on tiers < 100% (stops thermal spikes); enabled on P:31 |
| **CPU Max Frequency** | `/sys/devices/system/cpu/cpufreq/policy*/scaling_max_freq` | Clamped to 80% ceiling on mid tiers; uncapped max on P:31 |
| **GPU Power Profile** | AMD: `/sys/class/drm/card*/device/power_dpm_force_performance_level`<br>NVIDIA: `nvidia-smi -lgc`, `-pl`, `--auto-boost-permission` | Proportional clock ceiling (80% max); auto-boost disabled until 100% tier |
| **Memory Swappiness** | `/proc/sys/vm/swappiness`, `dirty_background_ratio` | Dynamic adjustment: low swappiness on low tiers; high caching on high tiers |
| **Cooling & Fans** | BIOS Automatic Curve | Factory thermal safety curve preserved with zero risk of stalling fans |
| **Radios & Peripherals** | `rfkill`, `/sys/devices/pci*/**/VPC2004:00/camera_power`, ALSA `amixer` | Wi-Fi kept alive, Bluetooth managed, mic/camera power controls |
| **PCIe ASPM & Audio** | `/sys/module/pcie_aspm/parameters/policy`, `/sys/module/snd_hda_intel/parameters/power_save` | `powersupersave` below 25% capacity; codec power saving |

---

## 4. Key Developer & Agent Workflows

### 4.1 Running and Testing
- **Display Available Prime Gears & Hardware Status:**
  ```bash
  python3 /home/dev/Code/tdg/compstate/changestate --help
  python3 /home/dev/Code/tdg/compstate/changestate status
  ```
- **Executing a Capacity Shift (Requires Root Privileges):**
  ```bash
  sudo /home/dev/Code/tdg/compstate/changestate p5
  sudo /home/dev/Code/tdg/compstate/changestate p23
  # With terminal spawn
  sudo /home/dev/Code/tdg/compstate/changestate p11 --terminal
  ```
- **Querying JSON Tiers for Applet / Integrations:**
  ```bash
  python3 /home/dev/Code/tdg/compstate/changestate tiers-json
  ```
- **Running Telemetry Logger:**
  ```bash
  # Single snapshot
  python3 /home/dev/Code/tdg/compstate/telemetry_logger.py --once
  # Continuous logging
  python3 /home/dev/Code/tdg/compstate/telemetry_logger.py
  ```

### 4.2 Cinnamon Applet Development & Sync
- Applet source: `cinnamon-applet/changestate@avathings.com/`
- User installation target: `~/.local/share/cinnamon/applets/changestate@avathings.com/`
- Sync updates to Cinnamon:
  ```bash
  # Restart Cinnamon panel (or press Alt+F2 -> r -> Enter in X11)
  cinnamon --replace &
  ```

---

## 5. Development Principles & Guardrails for Future AI Agents

When modifying or extending this codebase, adhere strictly to these rules:

1. **Maintain the <500 Line File Limit:**
   - Under no circumstances should any single Python or JavaScript file exceed 500 lines.
   - Decompose functionality into modular single-responsibility units under `changestate_core/`.
2. **Never Take CPU Core 0 Offline:**
   - Linux sysfs kernel timers will reject or destabilize if CPU 0 is offlined. Hotplugging logic must always iterate over cores `1` to `total_cores - 1`.
3. **Preserve Persistent Utilities & AI Assistant:**
   - Antigravity AI assistant, core network connections, and keyboard backlight must never be severed in low-power modes.
4. **Format Telemetry as Single-Line Valid JSON:**
   - `telemetry_logger.py` and `collect_telemetry_snapshot` must emit strict JSON lines (one JSON per line).
5. **Synchronize Applet & Engine:**
   - Any modifications to the gear naming or calling conventions in [`changestate`](file:///home/dev/Code/tdg/compstate/changestate) must be mirrored in [`cinnamon-applet/.../applet.js`](file:///home/dev/Code/tdg/compstate/cinnamon-applet/changestate@avathings.com/applet.js).
