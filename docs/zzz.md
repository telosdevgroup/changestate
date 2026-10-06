# zzz.md — Random TODOs & What-Nexts

## Ideas / Backlog

- [ ] **Console Status API Endpoint (Later):**
  - Expose a minimal API call to retrieve the exact data currently rendered on the console status screen (`changestate status`).
  - No vanity telemetry graphs or raw temperatures that nobody acts on—just the real operational state:
    - Active Prime Tier ($P$)
    - Active cores / Total threads
    - CPU/GPU frequency ceilings & clamp state
    - Daemon window state (remaining minutes, idle vs. awake)
  - Keep it lightweight, zero-dependency, and on-demand.
