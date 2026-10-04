# ChangeState

**Elastic Capacity Controller — Dynamic Hardware Resource Scaling for Linux**

`changestate` is an unbloated, proportional hardware governor and native Linux Mint / Cinnamon panel applet. It auto-discovers your machine's hardware capabilities and maps overall system throughput to standardized prime capacity tiers (`P:2` through `P:31`), coordinating active CPU cores, clock ceilings, GPU frequencies, and memory caches with a single slider.

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
     $$\text{Active Cores} = \text{round}\left(\frac{\text{Capacity \%}}{100} \times \text{Total Threads}\right)$$

2. **The 80% Silicon Safety Ceiling**:
   - Clocks scale smoothly across the range:
     $$\text{Target Clock} = \text{Min} + \left(\frac{\text{Capacity \%}}{100}\right) \times \left(0.80 \times \text{Max} - \text{Min}\right)$$
   - Even at 100% capacity (`P:31`), frequencies stop cleanly at 80% of silicon max. The system never redlines.

3. **No Auto-Boost Spikes**:
   - Intel `no_turbo = 1` and NVIDIA `--auto-boost-permission=0` are strictly enforced. Clocks remain steady under load without sudden thermal spikes.

4. **BIOS Thermal Safety Preserved**:
   - Cooling fans remain governed by the hardware's automatic ACPI curves. Because clock and voltage spikes are impossible, the system naturally purrs quietly without any risk of board overheating.

5. **Session & Process Protection**:
   - Local LLM inferencing (`ollama`) and local databases (`mongod`, `mongodb`) are kept alive across every capacity transition.

---

## Universal Capacity Tiers

Every prime notch represents an identical, universal capacity percentage for any machine:

| Tier | Universal % | Active Cores (8-Core Laptop) | Active Cores (16-Core Laptop) | Active Cores (32-Thread Workstation) | Behavior |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`P:2`** | **6%** | 1 core | 1 core | 2 cores | Minimum floor capacity, extreme battery sipping. |
| **`P:3`** | **10%** | 1 core | 2 cores | 3 cores | Ultra-light background terminal / sensor monitoring. |
| **`P:5`** | **16%** | 1 core | 3 cores | 5 cores | Quiet browsing and light documentation. |
| **`P:7`** | **23%** | 2 cores | 4 cores | 7 cores | Smooth typing, background music, cool thermals. |
| **`P:11`** | **35%** | 3 cores | 6 cores | 11 cores | Whispering cool server & background LLM inferencing. |
| **`P:13`** | **42%** | 3 cores | 7 cores | 13 cores | Steady development, clean responsive editor. |
| **`P:17`** | **55%** | 4 cores | 9 cores | 18 cores | Multi-service containers, active compiling. |
| **`P:19`** | **61%** | 5 cores | 10 cores | 20 cores | Heavy local dev with fluid multitasking. |
| **`P:23`** | **75%** | 6 cores | 12 cores | 24 cores | **The Balanced Sweet Spot** — Full gaming & dev with zero fan panic. |
| **`P:29`** | **93%** | 7 cores | 15 cores | 30 cores | High-throughput data builds and heavy batch runs. |
| **`P:31`** | **100%** | 8 cores | 16 cores | 32 cores | Full capacity stride (locked cleanly under 80% silicon max). |

---

## Cinnamon Panel Applet

`changestate` includes a native Linux Mint / Cinnamon panel applet (`cinnamon-applet/changestate@telosdevgroup`):

- **Real-Time Badge**: Displays current capacity on your taskbar (e.g. `P:11`, `P:23`).
- **Elastic Capacity Slider**: Click the applet to smoothly dial between `P:2` and `P:31`.
- **Current Hardware State**: Click to inspect active cores, exact clock ceilings, real-time GPU draw, and swappiness in a clean human-readable readout.
- **Dynamic Host Query**: Automatically invokes `changestate tiers-json` on startup to adapt slider notches and core counts to whatever machine it is running on.

### Quick Symlink Setup:
```bash
# 1. Symlink CLI to PATH
sudo ln -sf /path/to/changestate /usr/local/bin/changestate

# 2. Symlink Applet to Cinnamon
ln -sf /path/to/cinnamon-applet/changestate@telosdevgroup ~/.local/share/cinnamon/applets/changestate@telosdevgroup

# 3. Reload Cinnamon (Alt+F2 -> r -> Enter)
```

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

## Licensing: The Honorable Dual Model

ChangeState is built with zero DRM, zero activation keys, zero telemetry, and zero nag screens. The codebase is 100% identical for everyone. We operate under a transparent, fair-use honor system:

```
┌───────────────────────────────────────┬───────────────────────────────────────┐
│              PERSONAL                 │              COMMERCIAL               │
├───────────────────────────────────────┼───────────────────────────────────────┤
│ For personal laptops, rigs, & labs.   │ For corporate & commercial hardware.  │
│                                       │                                       │
│ Free & Open (Voluntary Tip Jar)       │ $25 / seat (One-time flat fee)        │
│ [ Drop a Tip ($1 - $5) ]              │ [ Purchase Commercial Registration ]  │
│                                       │ Includes instant tax invoice & PDF    │
└───────────────────────────────────────┴───────────────────────────────────────┘
```

- **Personal Use**: 100% free and open for individual rigs, hobbyists, students, and home labs. If it saved your laptop battery or kept your workspace quiet, voluntary contributions can be dropped into the [Personal Tip Jar](https://avathings.com/changestate#tip).
- **Commercial Use**: If you or your team use ChangeState on hardware owned, leased, or reimbursed by a commercial entity, please support ongoing development by purchasing a [Commercial Seat ($25 flat / seat)](https://avathings.com/changestate#commercial). Checkout automatically generates an official tax invoice and downloadable PDF license certificate for corporate expense accounting.
