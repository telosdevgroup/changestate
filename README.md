# ChangeState


> **Support Development:** [Sponsor on GitHub](https://github.com/sponsors/telosdevgroup) · [Tip / Support via Lemon Squeezy](https://avathings.com/changestate#tip)

---

## Quick One-Liner Installation

Install ChangeState and configure the autonomous daemon:

```bash
curl -sSL https://raw.githubusercontent.com/telosdevgroup/changestate/main/install.sh | bash
sudo systemctl enable --now changestate-auto
```

*(Installs the CLI to `/usr/local/bin/changestate` and enables the autonomous prime-stepping daemon.)*

---

## What It Is

`changestate` is an unbloated, proportional hardware governor and autonomous scaling daemon for Linux. It auto-discovers your machine's hardware capabilities and maps overall system throughput to standardized prime capacity tiers (`P:2` through `P:31`), coordinating active CPU cores, clock ceilings, GPU frequencies, and memory caches.

---

## Terminal Status & Hardware Inspection

### ASCII Terminal Status Readout
Instant hardware telemetry and capacity state inspected via `changestate status`:

```text
================================================================
  CHANGESTATE  •  Active Level: P:13 (~42% Capacity)
  [██████████░░░░░░░░░░░░░░] ~42%
================================================================
CPU (Processor):
  • Active Cores   : 13 of 32 cores running (19 powered down asleep)
  • Speed Ceiling  : 1203 MHz (Clamped from factory 2200 MHz to stop heat)
  • Turbo Boost    : Off (Enforced - stops sudden fan spikes)

GPU (Graphics):
  • Real-Time Draw : 20.72 W (Running at 270 MHz)
  • Power Ceiling  : Factory 115W base, dynamic boost spikes clamped

Memory & Cooling:
  • Swappiness     : 6 (Keeps active data in RAM, avoids disk thrash)
  • Cooling Fans   : BIOS Automatic (Quiet baseline, safe thermal curve)
  • Battery        : 97% (Not charging)
================================================================
```

---

## Universal Prime Capacity Reference Table ($P:2 \dots P:31$)

Every prime gear corresponds to a calibrated universal capacity ratio that dynamically dictates active cores, clock limits, and power targets:

| Prime Tier | Universal % | Active Cores (8-Thread Rig) | Active Cores (16-Thread Laptop) | Active Cores (32-Thread Workstation) | Subsystem Profile & Behavior |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`P:2`** | **6%** | 1 core | 1 core | 2 cores | Minimum floor capacity, extreme battery sipping. Codec power save, low-power ACPI profile. |
| **`P:3`** | **10%** | 1 core | 2 cores | 3 cores | Ultra-light background terminal, sensor monitoring, minimal background thermal footprint. |
| **`P:5`** | **16%** | 1 core | 3 cores | 5 cores | Quiet browsing and light documentation reading without cooling fan spinup. |
| **`P:7`** | **23%** | 2 cores | 4 cores | 7 cores | Smooth typing, background audio playback, completely cool thermals. |
| **`P:11`** | **35%** | 3 cores | 6 cores | 11 cores | Whispering cool server operation & steady background local LLM inferencing. |
| **`P:13`** | **42%** | 3 cores | 7 cores | 13 cores | Steady development workflow, clean responsive editor, balanced battery drain. |
| **`P:17`** | **55%** | 4 cores | 9 cores | 18 cores | Multi-service containers, active compiling, fluid desktop responsiveness. |
| **`P:19`** | **61%** | 5 cores | 10 cores | 20 cores | Heavy local developer builds with concurrent IDE and browser multitasking. |
| **`P:23`** | **75%** | 6 cores | 12 cores | 24 cores | **The Balanced Sweet Spot** — Full gaming & heavy development with zero fan panic loops. |
| **`P:29`** | **93%** | 7 cores | 15 cores | 30 cores | High-throughput data ingestion, fast local compilation, and heavy batch runs. |
| **`P:31`** | **100%** | 8 cores | 16 cores | 32 cores | **Full Throttle** — All clamps released, uncapped factory turbo boost, and maximum GPU TGP. |

---

## Autonomous Scaling Daemon (`changestate-auto`)

In addition to manual CLI and applet control, ChangeState includes an autonomous background timing daemon (`changestate-auto.service`) that adaptively scales your system capacity without manual intervention or intrusive telemetry.

### The Inverted Harmonic Cadence
Traditional auto-scalers measure CPU load percentages, which spike chaotically during brief tasks. ChangeState monitors **user input activity** (keyboard, mouse, trackpad via X11 XScreenSaver) across **discrete prime time windows**.

Under our **Inverted Harmonic Cadence**, high-power tiers operate on short leashes, while low-power tiers hold patiently before stepping down:

| Capacity Tier | Evaluation Window | Decay Behavior |
| :--- | :---: | :--- |
| **`P:29`** (~93%) | **2 min** | Extremely short leash. Steps down rapidly if user load ceases. |
| **`P:23`** (~75%) | **3 min** | Balanced peak window. Steps down to P:19 after 3m of inactivity. |
| **`P:19`** (~61%) | **5 min** | Work session cooldown. |
| **`P:17`** (~55%) | **7 min** | Medium active window. |
| **`P:13`** (~42%) | **11 min** | Steady state holding pattern. |
| **`P:11`** (~35%) | **13 min** | **The Wake Baseline** — Default landing tier on user return. |
| **`P:7`** (~23%) | **17 min** | Deep idle buffer. |
| **`P:5`** (~16%) | **19 min** | Quiet idle buffer. |
| **`P:3`** (~10%) | **23 min** | Near-floor background hold. |
| **`P:2`** (~6%) | **29 min** | Minimum capacity floor. Patiently holds for nearly half an hour. |

### Core Autonomous Behaviors:
1. **Autonomous Envelope (`[P:2 — P:29]`)**: The daemon strictly operates between `P:2` (floor) and `P:29` (ceiling). Extreme edge states—`P:0` (MOM Airgap) and `P:31` (Uncapped Turbo Boost)—are **strictly manual opt-in** and are never entered autonomously.
2. **Wakeup Snap**: When idling below the baseline ($P < \text{P:11}$), any user input immediately breaks the idle window and **snaps straight to P:11**, restoring instant desktop responsiveness without sluggish stepping.
3. **Sustained Activity Climb**: If user activity continues uninterrupted through an active evaluation window, the daemon steps up to the next prime tier ($P_{i+1}$) until reaching the ceiling at `P:29`.
4. **Decay Gravity**: When you step away from the machine, upper tiers step down within 2–5 minutes. After extended inactivity, the machine settles into silent low-power tiers.

```bash
# Enable the background daemon
sudo systemctl enable --now changestate-auto

# Inspect live daemon decisions & remaining window countdown
journalctl -u changestate-auto -f

# Run simulation / dry run in fast-forward mode (1 prime minute = 1 second)
./changestate-auto --dry-run --fast 1.0
```

---

## The Philosophy: Elastic Scaling without Auto-Boost Chaos

Modern laptop processors and GPUs are tuned aggressively out of the box—frequently triggering 5.5 GHz micro-bursts for trivial background tasks, drawing triple their baseline wattage, and sending cooling fans into audible panic loops.

`changestate` eliminates this behavior with clear, deterministic principles:

1. **Pure Dynamic Auto-Discovery (Zero Hardcoded Topology)**:
   - Probes the host system dynamically on launch:
     - CPU logical thread topology (`/sys/devices/system/cpu/cpu[0-9]*`)
     - Physical CPU frequency ranges (`cpuinfo_min_freq` to `cpuinfo_max_freq`)
     - Total RAM and Swap capacity (`/proc/meminfo`)
     - GPU hardware clocks and power bounds via driver sysfs / `nvidia-smi`
   - Dynamically scales active online cores to host topology:
     $$\text{Active Cores} = \max\left(1, \min\left(\text{round}\left(\frac{\text{Capacity \%}}{100} \times \text{Total Threads}\right), \text{Total Threads}\right)\right)$$

2. **The 80% Silicon Safety Ceiling & Turbo Clamp**:
   - On sub-100% tiers (`P:2` through `P:29`), clocks scale smoothly across the range:
     $$\text{Target Clock} = \text{Min} + \left(\frac{\text{Capacity \%}}{100}\right) \times \left(0.80 \times \text{Max} - \text{Min}\right)$$
   - Turbo Boost and dynamic GPU boosts are strictly disabled across intermediate tiers to eliminate sudden thermal spikes.
   - At `P:31` (100%), all clamps are released: full turbo boost enabled, uncapped clock limits, and factory GPU TGP.

3. **BIOS Thermal Safety Preserved**:
   - Cooling fans remain governed by hardware automatic ACPI curves. Because clock and voltage spikes are eliminated on intermediate tiers, the system purrs quietly without any risk of stalling fans or overheating.

4. **Session & Process Protection**:
   - Core 0 is permanently pinned online to guarantee kernel timer stability. Background services (such as local LLM inference engines and databases) remain fully intact across capacity transitions.

---

## Command Line Usage

Inspect hardware specs, discovered tiers, or current active levels:
```bash
# View discovered specs and available capacity tiers
changestate

# Check current active hardware state
changestate status

# Scale to a capacity tier (requires sudo/pkexec)
sudo changestate p11
sudo changestate p23
sudo changestate p31
```

---

## Remote Fleet, Lab & Headless Operations

`changestate` is designed from the ground up to orchestrate bare-metal infrastructure, compute labs, and remote headless servers without any desktop or GUI requirement.

- 🚀 **[Ansible Fleet Orchestration Guide](docs/ansible-fleet-orchestration.md)** — Deploy across dozens of Linux nodes and coordinate capacity with ready-to-run Ansible playbooks:
  - Playbook: [Deploy & Baseline Capacity](docs/recipes/ansible/changestate-deploy.yml)
  - Playbook: [On-Demand Fleet Capacity Shifter](docs/recipes/ansible/changestate-tier-switch.yml)
- ⏱️ **[Scheduled Capacity with Cron & Systemd](docs/cron-and-scheduled-capacity.md)** — Automate day/night compute shifts, power-rate savings, and scheduled cooldown cycles:
  - Crontab recipe: [/etc/cron.d/changestate-schedule](docs/recipes/cron/changestate-schedule.cron)
  - Systemd units: [changestate@.service](docs/recipes/systemd/changestate@.service), [Day Timer](docs/recipes/systemd/changestate-day.timer), [Night Timer](docs/recipes/systemd/changestate-night.timer)
- 🖥️ **[Headless Server & Lab Deployment](docs/headless-server-deployment.md)** — Zero desktop dependencies, remote SSH telemetry, and non-interactive sudoers rules:
  - Security recipe: [Passwordless /etc/sudoers.d snippet](docs/recipes/sudoers/changestate.sudoers)
  - CI/CD recipe: [GitLab CI Runner Capacity Stepper](docs/recipes/ci-cd/gitlab-ci-changestate.yml)

---

## License

Free and open source under the MIT License. See [LICENSE](LICENSE) for details.
