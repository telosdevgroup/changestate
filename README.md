# changestate

**System persona and hardware power tier switcher for Linux laptops (Lenovo / AMD Ryzen).**

`changestate` reprofiles your entire system state on the fly—adjusting CPU cores, clocks, GPU DPM power tiers, audio codec sleep, PCIe ASPM link states, sensors, background services, and firewall posture.

---

## The 4 Universal Tiers

| Tier | Cores & Clocks | GPU Clock | Radios / Sensors | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **`mom`** *(Metal Over Moss)* | 1 Core (Core 0 only) @ ~1.1 GHz | Floor (200 MHz) | All RF cut (`rfkill block all`), webcam sensor OFF, mic MUTED, mDNS stopped, incoming firewall locked | Emergency defense / air-gapped / absolute stealth |
| **`lowlow`** | 4 Cores @ 1.6 GHz cap (Boost OFF) | Floor (200 MHz) | Wi-Fi ON, Bluetooth OFF, audio codec sleep, PCIe ASPM `powersupersave`, bloat daemons paused | Extreme battery sipping, silent fanless daily driver |
| **`mid`** | 6 Cores (Half) with Boost enabled | Floor (200 MHz) | Wi-Fi ON, balanced profile, dev stack started | Snappy balanced daily workload |
| **`eleven`** | 12 Cores (All) uncapped @ 4.6 GHz (Boost ON) | Unlocked Auto | Wi-Fi ON, performance profile, full stack running | Cranked to 11 / maximum throughput / full blast |

*Note: Keyboard backlight is locked at 100% across all states. Antigravity AI assistant is preserved across all states.*

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
```

### Check Current Hardware State
```bash
changestate status
```

---

## Desktop Launchers
The repo includes Cinnamon / GNOME `.desktop` launchers to trigger state changes via `pkexec` directly from your desktop.
