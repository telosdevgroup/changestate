# ChangeState Architecture Overview

`changestate` scales Linux compute capacity through discrete prime-ratio steps, balancing acoustics, thermal dissipation, and electrical efficiency.

The system is structured around **5 core architectural pillars**:

```
┌────────────────────────────────────────────────────────┐
│ 5. CLIENT SURFACES (Human Interaction & Controls)      │
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
│ 1. HARDWARE CORE ENGINE   │ │ 3. TELEMETRY RECORDER    │
│    - `changestate_core/`  │ │    - `telemetry_logger`  │
│    - Cores/clocks/boost   │ │    - High-density JSONL  │
│    - GPU clamp & DPM      │ │    - CPU, GPU, NVMe temp │
│    - Kernel swappiness    │ │    - Watts, load, freq   │
└──────────────┬────────────┘ └────────────┬─────────────┘
               │                           │
┌──────────────▼───────────────────────────▼─────────────┐
│ 4. EVENT / HTTP SERVER (Distribution & Integration)    │
│    - [TBD / Planned]: Micro HTTP API (Zero deps)       │
│    - Outbound Webhooks (POST state transitions)        │
│    - Content Negotiation: JSON, Prometheus, SSE, MD    │
│    - Inbound control & cluster fleet orchestration     │
└────────────────────────────────────────────────────────┘
```

---

## The 5 Pillars in Detail

### 1. Hardware Core Engine (`changestate` + `changestate_core/`)
The authoritative hardware stepping layer:
- Manipulates sysfs nodes (`cpufreq`, `online`, `platform_profile`, `pcie_aspm`).
- Clamps GPU clocks and power limits dynamically via vendor tools (`nvidia-smi`, `amdgpu` sysfs).
- Applies proportional kernel memory tunables (`vm.swappiness`, `vm.dirty_background_ratio`).
- Enforces strict safety rules: CPU 0 is never offlined, fans remain under firmware control, and network connectivity is preserved.

### 2. Autonomous Timing Daemon (`changestate-auto`)
The adaptive governor managing dynamic elastic scaling:
- **Prime-Indexed Timing:** Tier $P$ defines an evaluation window of $P$ minutes ($P13 \iff 13$m).
- **Zero-Dependency Activity Detection:** Uses native X11 XScreenSaver idle hooks (`libXss.so.1`) via ctypes.
- **Proportional Decay:** Gradually steps down across prime tiers when the user is away ($P17 \rightarrow P13 \rightarrow P11 \rightarrow P7 \dots$).
- **Wakeup Snap:** Instantly wakes up and snaps straight to **P:11** (~35% capacity, balanced governor) on first keypress or mouse movement.
- **Sustained Work Climb:** Steps up to higher rungs ($P13 \rightarrow P17 \rightarrow P23$) when continuous user activity is detected across an evaluation window.

### 3. Device Heartbeat Recorder (`telemetry_logger.py`)
A minimal local recorder:
- A simple heartbeat for the local machine: records timestamp, active prime tier, temperature, and CPU clock/load.
- No heavy fleet dependencies: just a compact log showing how the machine is doing and confirming that `changestate-auto` is working as expected.

### 4. Event / HTTP Server (Planned / TBD)
Lightweight micro-server using Python's standard library:
- **Outbound Webhooks:** Dispatches POST payloads to home automation, Slack, or monitoring webhooks on tier transitions.
- **Content Negotiation:** Serves status in multiple formats via a single endpoint:
  - `GET /status` (JSON)
  - `GET /metrics` (Prometheus)
  - `GET /status.md` (Markdown MOTD / CLI)
  - `GET /events` (Server-Sent Events streaming)
- **Fleet Orchestration:** Optional authenticated control endpoint for compute cluster scaling.

### 5. Client Surfaces (CLI & Controls)
Visibility and manual interaction:
- **CLI & Launchers:** Direct commands (`changestate status`, `changestate p<N>`) and `.desktop` terminal spawners for manual inspection and tier stepping.
- **MOTD / Shell Prompt:** Lightweight passive indicators (e.g. `changestate status --short` or prompt badges).
