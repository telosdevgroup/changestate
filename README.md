# changestate

**Universal system persona and hardware power tier switcher for Linux laptops (AMD & Intel, Radeon & NVIDIA).**

`changestate` reprofiles your entire system state on the fly—adjusting CPU cores, clocks, GPU power tiers, audio codec sleep, PCIe ASPM link states, sensors, background services, and firewall posture.

---

## Universal Tiers & The "1, 2, 5 Law"

The tier hierarchy follows the **1, 2, 5 Law** of proportional envelopes (similar to standard electronic decade steps) combined with **Prime Number Core Allocation** (`cores > threads`, rounded to the nearest prime):

* **Avoiding Hyperthreading Contention:** Allocating physical cores cleanly avoids cache thrashing and sibling thread contention.
* **Breaking Harmonic Resonance:** Typical power-of-two thread pools (2, 4, 8, 16) create lock-step scheduling bottlenecks when concurrent workers compete on hash rings or I/O queues. Prime allocations break harmonic CPU contention naturally.
* **Preserving Dedicated Services:** Low-power states maintain non-negotiable responsiveness for network services (e.g. HTTP servers on port 8004, terminal loops, Cinnamon event loop) without dropping packets or stalling.

| Tier | Level / Ratio | Physical Cores (Formula) | Clocks & Thermals | Radios & Services | Target Behavior |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`mom`** *(Metal Over Moss)* | **`0`** (Floor / ~10%) | Floor prime: **2** (or 3) cores | ~800MHz floor, Boost OFF, EPP `power` | All RF cut/air-gapped, mic MUTED, mDNS stopped, incoming locked | Shrink to moss, encased in metal. Absolute floor, silent, terminal + net alive, Cinnamon idle. |
| **`lowlow`** | **`1`** (~20% envelope) | 20% capped prime: **5** cores | 1.6 GHz cap, Boost OFF | Wi-Fi ON, Bluetooth OFF, audio codec sleep, PCIe ASPM `powersupersave` | Extreme battery sipping, silent fanless daily driver. |
| **`server`** | **`2`** (~40% envelope) | 40% target prime: **11** cores | 2.8 GHz cap, Boost OFF | Wi-Fi/Eth ON, BT OFF, mic MUTED, camera OFF, bloat paused | Ultra low-wattage sustained throughput. Fluid terminal log viewing with prime core spike scaling loop. |
| **`mid`** *(Power Eco)* | **`3.5–4`** (~70–80%) | High-efficiency prime: **17** or **19** cores | Boost ON, EPP `balance_power` | Wi-Fi ON, balanced profile, dev stack active | "Flash High" mode: all capabilities (AVX, turbo) active, but biased strictly at the voltage efficiency sweet-spot. |
| **`eleven`** | **`5`** (100% envelope) | Full unconstrained: **23** cores / 100% | Boost ON, max governor, auto fan ramp | Full stack running, uninhibited throughput | Cranked to 11. Full unconstrained hardware capacity. |

*Note: Keyboard backlight is locked at 100% across all states. Antigravity AI assistant is preserved across all states.*

---

## Native Cinnamon Panel Applet

`changestate` includes a native **Cinnamon Panel Applet** (`cinnamon-applet/changestate@telosdevgroup`).

It sits right in your taskbar next to the clock/battery:
* **Live status badge:** Shows `[ MOM ]`, `[ LOW ]`, `[ MID ]`, or `[ 11 ]`.
* **Click menu:** Click anytime to switch power states without opening a terminal or minimizing windows.

### Installing the Applet on a New Machine:
```bash
mkdir -p ~/.local/share/cinnamon/applets/
cp -r cinnamon-applet/changestate@telosdevgroup ~/.local/share/cinnamon/applets/
```
Then right-click your panel $\to$ **Applets** $\to$ Enable **ChangeState**.

---

## CLI Usage

```bash
sudo changestate <persona>
```

Examples:
```bash
sudo changestate lowlow
sudo changestate mid
sudo changestate eleven
sudo changestate mom
sudo changestate server
```

### Check Current Hardware State
```bash
changestate status
```
