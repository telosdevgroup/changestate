# Hardware Actuation & Linux Kernel Interfaces

> **Target Audience:** LLMs, systems engineers, and Linux kernel hackers.  
> **Key Objective:** Exact breakdown of how ChangeState interfaces with Linux sysfs, procfs, ACPI, and GPU drivers.

---

## 1. CPU Core Orchestration

ChangeState calculates the active logical thread allocation using:
$$\text{active\_cores} = \max(1, \min(\text{round}(\text{ratio} \times \text{total\_cpus}), \text{total\_cpus}))$$

### Topologically-Aware Allocation
Instead of sequentially offlining cores (`cpu1`, `cpu2`...), `discover_cpu_topology_order()` analyzes `/sys/devices/system/cpu/cpu*/topology/thread_siblings_list`:
1. **Primary Threads First:** Real physical cores (prioritizing P-cores before E-cores on hybrid architectures).
2. **SMT Siblings Second:** Hyper-threading / secondary logical threads.
3. **Core 0 Invariant:** `/sys/devices/system/cpu/cpu0/online` is **never written**. CPU 0 remains perpetually online.

### Core Online/Offline Control
```python
# changestate_core/controllers.py
for cpu_id in target_cpus_to_offline:
    write_sysfs(f"/sys/devices/system/cpu/cpu{cpu_id}/online", 0)

for cpu_id in target_cpus_to_online:
    write_sysfs(f"/sys/devices/system/cpu/cpu{cpu_id}/online", 1)
```

---

## 2. Frequency Scaling & Thermal Ceilings

### Clamping Formula (Ratio < 1.0)
To eliminate abrupt fan screaming, tiers below `P:31` enforce an 80% ceiling between hardware minimum and hardware maximum:
$$\text{cap\_khz} = \text{min\_khz} + \text{ratio} \times (0.80 \times \text{max\_khz} - \text{min\_khz})$$
- `min_khz` and `max_khz` are read from hardware limits (`cpuinfo_min_freq` / `cpuinfo_max_freq`), **not** transient `scaling_*` nodes.
- Applied per policy across `/sys/devices/system/cpu/cpufreq/policy*/scaling_max_freq`.

### Turbo / Boost Invariant
- **Ratio < 1.0:** CPU Boost is explicitly disabled (`/sys/devices/system/cpu/cpufreq/boost` $\rightarrow$ `0` or vendor `no_turbo` $\rightarrow$ `1`).
- **Ratio == 1.0 (P:31):** CPU Boost enabled (`1`), frequency ceiling restored to `cpuinfo_max_freq`.

---

## 3. ACPI Profiles & Kernel Governors

| Ratio Band | Tiers | ACPI Profile | Scaling Governor | EPP Preference | PCIe ASPM |
| :--- | :--- | :--- | :--- | :--- | :--- |
| $\text{ratio} \le 0.25$ | P:2–P:7 | `low-power` | `powersave` | `power` | `powersupersave` |
| $0.25 < \text{ratio} \le 0.65$ | P:11–P:19 | `balanced` | `powersave` | `balance_power` | `default` |
| $0.65 < \text{ratio} < 1.0$ | P:23–P:29 | `balanced` | `powersave` | `balance_performance` | `default` |
| $\text{ratio} == 1.0$ | P:31 | `performance` | `performance` | `performance` | `performance` |

- ACPI Platform Profile: `/sys/firmware/acpi/platform_profile`
- Energy Performance Preference (EPP): `/sys/devices/system/cpu/cpufreq/policy*/energy_performance_preference`
- PCIe ASPM: `/sys/module/pcie_aspm/parameters/policy`

---

## 4. GPU Clamping & Memory Tunables

### NVIDIA (via `nvidia-smi`)
- **Ratio < 1.0:** Clamps maximum graphics clock ceiling via `nvidia-smi -lgc <min>,<target_mhz>` and resets auto-boost permission to 0.
- **Ratio == 1.0 (P:31):** Restores factory power limit (`-pl <default_w>`) and resets clocks (`nvidia-smi -rgc`).

### AMDGPU (via sysfs)
- Scales DPM performance level in `/sys/class/drm/card*/device/power_dpm_force_performance_level`:
  - $\text{ratio} \le 0.25 \implies \text{"low"}$
  - $\text{ratio} > 0.25 \implies \text{"auto"}$

### Kernel Memory Tunables
Dynamic VM aggressiveness:
- **`vm.swappiness`:** Scales inversely with capacity ($10 \rightarrow 1$):
  $$\text{swappiness} = \max(1, \text{int}(10 - 9 \times \text{ratio}))$$
- **`vm.dirty_background_ratio`:** Scales directly with capacity ($10 \rightarrow 20$):
  $$\text{dirty\_ratio} = \text{int}(10 + 10 \times \text{ratio})$$
