# Headless Server and Remote Lab Deployment

The core `changestate` engine is completely headless, dependency-free, and designed to run cleanly over SSH on bare-metal servers, compute rigs, or remote lab machines.

---

## 1. Zero GUI Dependencies

ChangeState’s CLI and core orchestrator rely only on standard Linux kernel interfaces (`/sys`, `/proc`, `cpufreq`, `amdgpu`/`nvidia`) and standard Python 3. It runs seamlessly on headless installs of:
- Ubuntu Server / Debian
- Red Hat Enterprise Linux / Rocky Linux / AlmaLinux
- Fedora Server
- Arch Linux

The Cinnamon applet is completely optional. On a headless machine, you do not need Cinnamon, X11, Wayland, or desktop libraries.

---

## 2. Fast Headless Installation

To deploy the standalone CLI directly:

```bash
# Clone the repository
sudo git clone --depth 1 https://github.com/telosdevgroup/changestate.git /opt/changestate

# Symlink CLI to system PATH
sudo ln -sf /opt/changestate/changestate /usr/local/bin/changestate
sudo chmod +x /usr/local/bin/changestate

# Test installation
changestate status
```

---

## 3. Configuring Sudoers for Unattended Automation

In headless deployments (CI runners, cron, Ansible, or remote scripts), promptless execution is required.

Install the dedicated sudoers snippet from [`docs/recipes/sudoers/changestate.sudoers`](recipes/sudoers/changestate.sudoers):

```bash
sudo cp docs/recipes/sudoers/changestate.sudoers /etc/sudoers.d/changestate
sudo chmod 0440 /etc/sudoers.d/changestate
```

This rule allows administrative users or CI agents to invoke `/usr/local/bin/changestate` with `sudo` without password prompts, while preventing unauthorized access to other root commands.

---

## 4. Headless Remote Inspection Over SSH

When managing remote nodes, you can query capacity, telemetry, and available hardware limits without opening an interactive session:

```bash
# Get ASCII dashboard readout
ssh user@remote-node "changestate status"

# Get machine-readable JSON metadata for scripting or monitoring
ssh user@remote-node "changestate tiers-json"
```

### Feeding Headless Metrics to Monitoring (Prometheus / JSONL)

ChangeState includes a background JSONL telemetry logger ([`telemetry_logger.py`](../telemetry_logger.py)). Run once to emit structured system telemetry directly to stdout:

```bash
python3 /opt/changestate/telemetry_logger.py --once
```

Example JSON output:
```json
{"timestamp":"2026-10-04T23:30:00Z","active_tier":"P:13","active_cores":13,"total_cores":32,"cpu_freq_cap_mhz":1203,"gpu_power_w":20.7,"gpu_freq_mhz":270,"swappiness":6,"battery_pct":97}
```

This makes headless node monitoring trivial to ingest into Vector, Fluentbit, or Prometheus node_exporter textfile collectors.
