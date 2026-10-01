# changestate

**Universal system persona and hardware power tier switcher for Linux laptops (AMD & Intel, Radeon & NVIDIA).**

`changestate` reprofiles your entire system state on the fly—adjusting CPU cores, clocks, GPU power tiers, audio codec sleep, PCIe ASPM link states, sensors, background services, and firewall posture.

---

## Universal Tiers

| Tier | Cores & Clocks | GPU Clock | Radios / Sensors | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **`server`** | 2–4 Cores base @ 2.8 GHz cap (Boost OFF) | Floor (200 MHz) | Wi-Fi/Eth ON, BT OFF, mic MUTED, camera OFF, bloat paused | Ultra low-wattage server mode. Fluid XFCE/Cinnamon terminal log viewing with prime core spike scaling loop (`--loop`) |
| **`mom`** *(Metal Over Moss)* | 1 Core (Core 0 only) @ ~1.1 GHz | Floor (200 MHz / 300 MHz) | All RF cut (`rfkill block all`), webcam sensor OFF, mic MUTED, mDNS stopped, incoming firewall locked | Emergency defense / air-gapped / absolute stealth |
| **`lowlow`** | 4 Cores @ 1.6 GHz cap (Boost OFF) | Floor | Wi-Fi ON, Bluetooth OFF, audio codec sleep, PCIe ASPM `powersupersave`, bloat daemons paused | Extreme battery sipping, silent fanless daily driver |
| **`mid`** | 50% of available cores with Boost | Floor | Wi-Fi ON, balanced profile, dev stack started | Snappy balanced daily workload |
| **`eleven`** | 100% of cores uncapped (Boost ON) | Unlocked Auto | Wi-Fi ON, performance profile, full stack running | Cranked to 11 / maximum throughput / full blast |

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
