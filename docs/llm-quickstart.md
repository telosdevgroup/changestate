# LLM Quickstart & System Onboarding

> **Target Audience:** LLM agents, automated coding assistants, and autonomous dev-ops bots.  
> **Key Objective:** Rapidly understand ChangeState's system design, invocation semantics, safety rules, and execution models without context hallucination.

---

## 1. What is ChangeState?

ChangeState is a Linux hardware capacity coordinator and autonomous elastic governor. It proportionally scales silicon throughput across discrete prime tiers:
- **Tiers:** `P:2` (Floor, ~6%) up to `P:31` (Max Uncapped, 100%).
- **Hardware Controlled:** Active CPU logical cores (`online`), CPU clock ceilings (`scaling_max_freq`), turbo/boost, PCIe ASPM, kernel memory caches (`vm.swappiness`), and GPU frequencies/clocks (`amdgpu` and `nvidia-smi`).
- **Acoustic Guard:** All tiers from `P:2` to `P:29` enforce an **80% acoustic/thermal ceiling** with CPU boost disabled. Only `P:31` unlocks full uncapped compute.

---

## 2. The Core Components

```
┌────────────────────────────────────────────────────────┐
│ 1. HARDWARE CORE ENGINE (`changestate` & `_core/`)     │
│    Deterministic actuation layer (pure mechanism)      │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 2. ADAPTIVE DAEMON (`changestate-auto` & systemd)      │
│    Decision plane: prime timers & user activity loop   │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 3. DEVICE HEARTBEAT LOG (`/run/changestate*.state`)    │
│    Local state files for real-time status query        │
└────────────────────────────────────────────────────────┘
```

1. **`changestate` (CLI Entrypoint):** Python script at `/usr/local/bin/changestate`. Stateless actuator.
2. **`changestate_core/` (Package):**
   - `hal.py`: Low-level sysfs writers (`write_sysfs`), command execution (`run_cmd`), clock scaling formulas.
   - `discovery.py`: Host topology probing (`discover_hardware()`), thread sibling prioritization, tier percentage mappings (`UNIVERSAL_PRIME_PCT`).
   - `controllers.py`: Cores onlining/offlining, boost toggling, governors (`powersave` vs `performance`), GPU clamping.
   - `status.py`: Formats ASCII diagnostics and persists `/run/changestate.state`.
3. **`changestate-auto` (Daemon):** Autonomous prime-interval scaling daemon (`systemd/system/changestate-auto.service`).

---

## 3. The Prime Adaptive Algorithm (How `changestate-auto` Thinks)

The adaptive daemon maps tier $P$ to an evaluation window of $P$ minutes ($P13 \iff 13$m):

```
                   [ Activity Detected ] ──► Step Up (e.g. P13 -> P17) & Wait 17m
                  /
[ P13 for 13 min ]
                  \
                   [ 13m Total Inactivity ] ──► Step Down (e.g. P13 -> P11) & Wait 11m
```

### Deterministic Rules:
1. **Activity Metric:** Strictly user input (keyboard, mouse, trackpad) queried via `ctypes` -> `libXss.so.1` (X11 XScreenSaver idle milliseconds). Background CPU load is **NOT** activity.
2. **Idle Decay:** If 0 user input occurs during the entire $P$-minute window, step down to previous prime:
   $$\dots \rightarrow P17 \rightarrow P13 \rightarrow P11 \rightarrow P7 \rightarrow P5 \rightarrow P3 \rightarrow P2$$
3. **Wakeup Snap:** If the machine was idling below baseline ($P < 11$) and user input is detected, it immediately breaks out of the idle window and **snaps directly to P:11** (starts an 11m timer).
4. **Sustained Activity:** If active during the window, steps up by 1 prime tier until ceiling ($P31$).

---

## 4. State & Interface Contracts

| File / Command | Format | Purpose |
| :--- | :--- | :--- |
| `/run/changestate.state` | Plaintext string (e.g. `P:17`) | Canonical active tier for the machine |
| `/run/changestate-auto.json` | JSON | Daemon heartbeat: `{"tier": "p17", "prime": 17, "remaining_seconds": 450.2, "status": "active"}` |
| `changestate status` | Terminal text | Human-readable ASCII hardware status readout |
| `changestate tiers-json` | JSON array | Dynamic metadata for all tiers on this specific host |
| `changestate p<N>` | Command (requires root) | Sets tier immediately (e.g. `sudo changestate p17`) |

---

## 5. Critical Invariants for LLMs

When modifying, generating, or debugging ChangeState code:

1. **Safety First:**
   - **NEVER offline CPU 0** (`/sys/devices/system/cpu/cpu0/online`).
   - **NEVER control fans directly.** Cooling is strictly delegated to firmware/BIOS.
   - **NEVER sever networking or Wi-Fi.**
2. **Hard File Size Limit:**
   - Every source file (`.py`, `.sh`, extensionless scripts) **MUST remain under 500 lines (`wc -l < 500`)**.
   - Entrypoint `changestate` targets $\le 250$ lines.
3. **No External Python Dependencies:**
   - ChangeState uses pure Python standard library (`ctypes`, `json`, `os`, `sys`, `time`, `glob`). Never introduce pip packages.
