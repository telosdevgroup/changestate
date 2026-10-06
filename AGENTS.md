# AGENTS.md — ChangeState Developer & Agent Guide

> **Architecture:**
> - **P:0 (MOM - Metal Over Moss):** Airgap defensive posture (rfkill block all, inbound firewall DROP, heavy background processes culled, 2 cores at min clock floor).
> - **P:2 – P:29 (Capacity Curve):** Multi-dimensional scaling (cores, clocks, swappiness, GPU) under a strict 80% acoustic/thermal ceiling with boost off.
> - **P:31 (Max Cap):** Recovery & raw compute (80% ceiling broken, full boost, uncapped clocks, factory TGP, metal posture cleared).

> **Core Purpose:** `changestate` steps a Linux machine through discrete "prime" capacity tiers, proportionally scaling CPU cores, clocks, boost, GPU limits, and kernel memory tunables to control power, heat, and fan noise. Supports AMD & Intel CPUs, AMD (amdgpu) & NVIDIA GPUs, and Lenovo IdeaPad ACPI (`VPC2004`) peripherals.

### The 5 Architectural Pillars

```
┌────────────────────────────────────────────────────────┐
│ 5. CLIENT SURFACES (Human Interaction & Cockpit)       │
│    - CLI Entrypoint (`changestate status / p<N>`)      │
│    - .desktop Launchers & Terminal Spawners            │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 2. AUTONOMOUS TIMING DAEMON (Adaptive Decision Plane)  │
│    - `changestate-auto` (Systemd background daemon)    │
│    - Prime-interval evaluation windows (P13 <-> 13m)   │
│    - User input activity monitor (XScreenSaver libXss) │
│    - Wake snap to baseline (P:11) & Idle ladder decay  │
└──────────────┬───────────────────────────┬─────────────┘
               │                           │
┌──────────────▼────────────┐ ┌────────────▼─────────────┐
│ 1. HARDWARE CORE ENGINE   │ │ 3. DEVICE HEARTBEAT      │
│    - `changestate_core/`  │ │    - `telemetry_logger`  │
│    - Cores/clocks/boost   │ │    - Local heartbeat log │
│    - GPU clamp & DPM      │ │    - Temp, load, MHz     │
│    - Kernel swappiness    │ │    - Tracks daemon health│
└──────────────┬────────────┘ └────────────┬─────────────┘
               │                           │
┌──────────────▼───────────────────────────▼─────────────┐
│ 4. EVENT / HTTP SERVER (Distribution & Integration)    │
│    - [TBD / Planned]: Micro HTTP API (Zero deps)       │
│    - Outbound Webhooks (POST state transitions)        │
│    - Content Negotiation: JSON, Prometheus, SSE, MD    │
│    - Inbound control & small group orchestration       │
└────────────────────────────────────────────────────────┘
```

**Precedence:** The rules in §0 and §1 are invariants. If code conflicts with them, the code is wrong. If this document conflicts with the code anywhere else, verify the code and update this document in the same change.

---

## 0. Agent Safety Rules (Read First)

1. **Never change live hardware state without explicit user approval.** Do not run `sudo changestate p<N>`, `pkexec changestate …`, `install.sh`, or any command that writes to `/sys`, `/proc/sys`, `rfkill`, `nvidia-smi` (setters), or `systemctl`, unless the user asked for it in the current request.
2. **Safe to run anytime (read-only):** `changestate --help`, `changestate status`, `changestate tiers-json`, `telemetry_logger.py --once`, `python3 -m py_compile <file>`, `wc -l`, `grep`.
3. **Never write fan, EC, or thermal-trip registers.** Cooling is always left to the BIOS/firmware automatic curve. Do not add fan control.
4. **Never offline CPU 0.** Never write to `/sys/devices/system/cpu/cpu0/online`. On most x86 systems the file doesn't exist, and where it does, offlining the boot CPU is unsupported or destabilizing.
5. **Never sever the user's working environment.** No tier may block Wi-Fi, stop NetworkManager / network services, kill the desktop session, or turn off the keyboard backlight. The Antigravity AI assistant depends on network connectivity.
6. **Never commit build artifacts.** `__pycache__/` and `*.tar.gz` release bundles are not source.

---

## 1. Architectural Invariants

### 1.1 File Size Limit
- **Hard limit: 500 physical lines (`wc -l`) per source file**: `.py`, `.js`, `.sh`, and the extensionless `changestate` entrypoint. Markdown, JSON, and `.desktop` files are exempt.
- **Entrypoint `changestate` target: ≤ 250 lines.** Push logic into `changestate_core/`.
- At around 400 lines, split the file into single-responsibility modules under `changestate_core/` and re-export them via `__init__.py`.
- Delete dead code. Don't comment it out and don't keep "legacy" paths.

### 1.2 Tier Table (Single Source of Truth)
- **Canonical source:** `UNIVERSAL_PRIME_PCT` in [`discovery.py`](file:///home/dev/Code/tdg/compstate/changestate_core/discovery.py). The values are hand-picked (roughly `P/31`, rounded). They are **not** computed, and `P:23 = 75` is intentional.

| Tier | P:2 | P:3 | P:5 | P:7 | P:11 | P:13 | P:17 | P:19 | P:23 | P:29 | P:31 |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `pct` | 6 | 10 | 16 | 23 | 35 | 42 | 55 | 61 | **75** (Balanced) | 93 | **100** (Uncapped) |

- Off-table input falls back to: `≤2 → 6`, `≥31 → 100`, otherwise `round(P/31*100)`.
- **Mirrors that must stay in sync:** the hardcoded fallback `TIERS` array in [`applet.js`](file:///home/dev/Code/tdg/compstate/cinnamon-applet/changestate@avathings.com/applet.js), the `.desktop` launchers, and `README.md`.

### 1.3 Scaling Formulas
Let `ratio = pct / 100`.
- **Cores:** `active_cores = max(1, min(round(ratio * total_cpus), total_cpus))`. `total_cpus` counts logical CPUs (`cpu[0-9]*`).
- **Core order** ([`discover_cpu_topology_order`](file:///home/dev/Code/tdg/compstate/changestate_core/discovery.py#L26)): CPU 0 first, then primary threads (P-cores before E-cores), then SMT siblings. Scale-down offlines in reverse order.
- **CPU clock cap (ratio < 1):** `cap = min_khz + ratio * (0.80 * max_khz - min_khz)`. `min_khz` and `max_khz` come from `cpuinfo_min_freq` / `cpuinfo_max_freq` (hardware limits, not `scaling_*`).
  - **Required invariant:** `cap` must be clamped to `[min_khz, 0.80 * max_khz]`. If `0.80 * max_khz < min_khz`, use `min_khz`.
- **GPU clock cap (NVIDIA):** `nvidia-smi -rgc` is kept active on all tiers to protect `nvidia-modeset` and avoid display lockups. Power is governed safely by toggling NVIDIA auto-boost permission (`1` at P:31, `0` at ratio < 1) and restoring factory TGP at P:31. Hard clock clamps (`-lgc`) are prohibited on primary display GPUs.
- **ratio == 1 (P:31):** boost on, `scaling_max_freq = cpuinfo_max_freq`, `nvidia-smi -rgc`, factory power limit, auto-boost permission restored.
- **ratio < 1:** CPU boost **off**, NVIDIA auto-boost permission **off**. No exceptions.

### 1.4 Tier Band Mapping (Exact)

| Band | Tiers | `platform_profile` | Governor / EPP | PCIe ASPM | amdgpu DPM |
|:--|:--|:--|:--|:--|:--|
| `ratio ≤ 0.25` | P:2–P:7 | `low-power` | `powersave` / `power` | `powersupersave` | `low` |
| `0.25 < ratio ≤ 0.65` | P:11–P:19 | `balanced` | `powersave` / `balance_power` | `default` | `auto` |
| `0.65 < ratio < 1` | P:23–P:29 | `balanced` | `powersave` / `balance_performance` | `default` | `auto` |
| `ratio = 1` | P:31 | `performance` | `performance` / `performance` | `performance` | `auto` |

**Memory** (applies to every tier): `vm.swappiness = max(1, int(10 - 9*ratio))` (10 → 1), and `vm.dirty_background_ratio = int(10 + 10*ratio)` (10 → 20).

**Applied on every tier, regardless of band:** Wi-Fi unblocked, Bluetooth **blocked**, keyboard backlight = 2, camera power on, mic unmuted.

**NVIDIA power limit at P:31:** restored to the detected `power_default_w`. If unknown, `-pl` is skipped. Never hardcode a wattage.

### 1.5 Adaptive Scaling Model (changestate-auto)
- **Autonomous Envelope [P:2 ── P:29]:** Autonomous transitions are bounded by a configurable floor and ceiling, which must be on the ladder `2, 3, 5, 7, 11, 13, 17, 19, 23, 29`. **Defaults: floor P:7, ceiling P:23.** P:2 and P:29 are the hard outer limits. Extremes P:0 (MOM) and P:31 (Max Uncapped Turbo) are strictly manual opt-in and are never entered autonomously.
  - **Options:** `--range 7:23` (also `7-23`, `7,23`), `--min`/`--floor`, `--max`/`--ceiling`, `--wake`. `--range` overrides `--min`/`--max`.
  - **Persistent config:** `/etc/changestate/auto.conf` (`range=`, `min=`/`floor=`, `max=`/`ceiling=`), `CHANGESTATE_RANGE` env var, or flags in the service `ExecStart`. CLI flags override the config file.
- **Inverted Harmonic Cadence:** High capacity tiers have short leashes; low tiers hold patiently:
  `P2: 29m, P3: 23m, P5: 19m, P7: 17m, P11: 13m, P13: 11m, P17: 7m, P19: 5m, P23: 3m, P29: 2m`.
- **Sole Metric for Activity:** User input (keyboard, mouse, trackpad) queried via X11 XScreenSaver idle time (`libXss.so.1`). CPU load percentages are intentionally ignored to prevent micro-burst false positives.
- **Evaluation Loop & Transitions:**
  - Evaluates user idle time periodically (`tick_interval = 2.0s` in normal operation).
  - If activity is detected during the active window:
    - If idling below baseline ($P < \text{wake\_prime}$, default **P:11**): immediate **Wakeup Snap** to the wake baseline tier ($P11$).
    - If already at or above baseline: steps up to the next prime tier ($P_{i+1}$) upon window completion, up to ceiling ($P:29$).
  - If no activity is detected throughout the entire window duration:
    - Steps down to the previous prime tier ($P_{i-1}$) under **Decay Gravity**, down to floor ($P:2$).
- **State Export (`/run/changestate-auto.json`):** Atomically written via tmp file with keys: `tier`, `prime`, `window_minutes`, `remaining_seconds`, `status`, and `timestamp`.
- **Simulation & Testing:** Supports non-root simulation with `--dry-run` and time-acceleration `--fast <seconds_per_prime_minute>` (e.g. `--fast 1.0` simulates 1 prime minute per second).

### 1.6 Hardware Access & Resiliency
- **All sysfs writes go through `hal.write_sysfs()`.** Never call `open(..., "w")` on `/sys` or `/proc` directly.
- **All shell calls go through `hal.run_cmd()`.** Build arguments from internal constants only. Never interpolate user input into shell strings.
- Treat every path as optional. Missing files, a missing `nvidia-smi`, or a missing `platform_profile` must be silent no-ops.
- Detect vendors at runtime only: `is_intel_cpu()` (checks for `intel_pstate`) and `has_nvidia_gpu()` (checks for `nvidia-smi` on PATH). Never hardcode vendor, core count, or frequencies.
- Ignore `EBUSY` (errno 16). Log any other write error as `[!] Warning …` and keep going. A tier shift must never abort halfway because of one failed write.
- **Never escalate privileges internally.** The tool runs as root (via `sudo`/`pkexec`). No `sudo` inside code; call `systemctl --no-ask-password`. On permission failure, warn and continue.
- Globs are non-recursive by design. Don't use `**` or `recursive=True` under `/sys` (symlink cycles). Use stable paths such as `/sys/bus/platform/devices/VPC2004:*/…`.
- **Clock caps must use `hal.scaled_cap(lo, hi, ratio)`**, which implements the §1.3 formula and clamp.

---

## 2. Codebase Map

```
compstate/
├── changestate                  # CLI entrypoint: arg parsing, apply_prime_state(), terminal spawn
├── changestate-auto             # Autonomous adaptive daemon: prime-interval timers & wake-snap
├── changestate-auto.service     # Systemd service unit for changestate-auto background daemon
├── changestate_core/
│   ├── __init__.py              # Public re-exports (keep in sync when adding functions)
│   ├── hal.py                   # write_sysfs, run_cmd, scaled_cap, is_intel_cpu, has_nvidia_gpu
│   ├── discovery.py             # UNIVERSAL_PRIME_PCT, topology order, discover_hardware, tiers metadata
│   ├── controllers.py           # cores, boost, freq cap, governor/EPP, GPU clamp, swappiness, radios, camera, mic
│   └── status.py                # state file, telemetry snapshot, `status` rendering
├── telemetry_logger.py          # Standalone JSONL telemetry daemon
├── install.sh                   # Installer (modifies system — requires user approval)
├── changestate-*.desktop        # Desktop launchers
├── assets/, LICENSE, README.md
└── AGENTS.md
```

**Public interface contracts:**
- `changestate tiers-json` outputs JSON from `get_capacity_tiers_metadata()`.
- `changestate p<N> [--terminal]` uses tier ids of the form `p<prime>`.
- **State files:**
  - `STATE_FILE` in `status.py` (`/run/changestate.state`; read by `telemetry_logger.py`).
  - `AUTO_STATE_FILE` (`/run/changestate-auto.json`; exports current tier, window remaining seconds, and status).
- **Telemetry:** `/var/log/changestate_telemetry.jsonl`, one compact JSON object per line (`json.dumps(obj, separators=(",",":"))`, no embedded newlines, no `NaN`).

---

## 3. Workflows

### 3.1 Verify (always safe)
```bash
cd /home/dev/Code/tdg/compstate
python3 -m py_compile changestate changestate-auto changestate_core/*.py telemetry_logger.py
wc -l changestate changestate-auto changestate_core/*.py telemetry_logger.py install.sh   # all < 500
python3 changestate --help
python3 changestate status
python3 changestate tiers-json | python3 -m json.tool > /dev/null && echo OK
python3 telemetry_logger.py --once | python3 -c 'import sys,json;[json.loads(l) for l in sys.stdin];print("JSONL OK")'
```

### 3.2 Apply a Tier (user approval required)
```bash
sudo ./changestate p23            # balanced
sudo ./changestate p31            # full uncapped; also the "restore defaults" path
sudo ./changestate p11 --terminal
```
There is no dry-run mode and no automatic rollback. **`p31` is the recovery tier.** Keep it working at all times.

### 3.3 Adaptive Scaling Daemon (changestate-auto)
- Test dry-run: `./changestate-auto --dry-run --fast 1.0` (1 prime minute = 1 second)
- Real-time service control:
  ```bash
  sudo systemctl status changestate-auto
  journalctl -u changestate-auto -f
  sudo systemctl stop changestate-auto
  ```

---

## 4. Change Checklist (before declaring done)

- [ ] All §3.1 checks pass and every file is under 500 lines.
- [ ] If tiers, ids, or labels changed: `discovery.py`, `.desktop` files, and `README.md` were all updated.
- [ ] If a new public function was added: exported in `changestate_core/__init__.py`.
- [ ] No new direct `/sys` writes, hardcoded hardware values, or vendor assumptions.
- [ ] §0 safety rules respected: no fan/EC writes, CPU 0 untouched, Wi-Fi and network preserved.
- [ ] This document updated if behavior in §1.3–§1.5 or §2 changed.

---

## 5. Known Issues / Tech Debt (fix when touching these areas)

When you find one, add it here as a numbered item (problem, location, intended fix) and remove it in the change that fixes it.

1. **Stale frequency limits when scaling up:** `discover_hardware()` runs before `set_cpu_cores()`, and offline CPUs don't expose their `cpufreq` policy. Going from a low tier to `p31` can therefore cap every core at a lower core's max (seen: 2200 MHz instead of 5500 MHz). A second `p31` run fixes it. Fix: bring cores online first and re-read the limits, or write each policy's own `cpuinfo_max_freq` at P:31.
