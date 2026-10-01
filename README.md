# changestate

**System persona and hardware profile switcher for Linux laptops (Lenovo / AMD Ryzen).**

`changestate` reprofiles your entire system state on the fly—adjusting CPU cores, clocks, GPU DPM power tiers, audio power saving, PCIe link states, sensors, background services, and firewall posture.

---

## Personas

| Persona | CPU Cores & Frequency | GPU Clock | Radios / Sensors | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **`MOM`** *(Metal Over Moss)* | 1 Core (0 only) @ ~1.1 GHz | Lowest (200 MHz) | All RF cut (`rfkill block all`), webcam sensor OFF, mic MUTED, mDNS stopped, incoming firewall locked | Emergency defense / air-gapped / stealth |
| **`LowLow`** | 4 Cores @ 1.6 GHz cap (Boost OFF) | Lowest (200 MHz) | Wi-Fi ON, Bluetooth OFF, audio codec sleep, PCIe ASPM `powersupersave`, bloat daemons paused | Extreme battery sipping, silent fanless daily driver |
| **`WebDev`** | 6 Cores (Half) with Boost | Lowest (200 MHz) | Wi-Fi ON, balanced profile, MongoDB & Ollama services started | Minimal power dev workstation |
| **`Inferencing`** | 12 Cores (All) uncapped @ 4.6 GHz (Boost ON) | Unlocked Auto | Wi-Fi ON, performance profile, full AI stack running | Heavy local LLMs, AI workloads, and compiles |

*Note: Keyboard backlight is locked at 100% across all states. Antigravity AI assistant is preserved across all states.*

---

## CLI Usage

```bash
sudo ./changestate <persona>
```

Examples:
```bash
sudo ./changestate lowlow
sudo ./changestate webdev
sudo ./changestate inferencing
sudo ./changestate mom
```

### Check Current Hardware State
```bash
./changestate status
```

---

## Desktop Launchers
The repo includes `.desktop` launchers for Linux desktop environments (Cinnamon, GNOME, etc.) to trigger state changes via `pkexec` directly from your desktop.
