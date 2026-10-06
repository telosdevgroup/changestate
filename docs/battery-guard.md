# 🔋 BatteryGuard Deep Dive

> *Native Linux battery lifespan preservation & hardware charge threshold control.*

Most laptops plugged into wall chargers or docking stations stay pegged at 100% state of charge (SoC). For Lithium-ion and Lithium-polymer chemistries, prolonged high-voltage saturation (4.2V–4.35V per cell) combined with internal laptop heat accelerates chemical breakdown, causing permanent capacity loss and cell swelling.

`BatteryGuard` (`extras/battery-guard`) allows you to cap battery charging at 80% (or any threshold from 50–100%) directly using native Linux kernel interfaces, without installing heavy power suites like TLP.

---

## 🔬 How It Works (Kernel Interfaces)

Linux exposes battery charging thresholds through standardized and vendor-specific sysfs nodes. When configured, the embedded controller (EC) stops drawing power into the battery when the ceiling is reached, running the laptop purely off AC pass-through power.

`BatteryGuard` automatically detects and actuates the appropriate sysfs nodes in order of precedence:

### 1. Standard Linux Kernel Power Supply Interface
Standardized in mainline Linux kernel (v5.4+):
```bash
/sys/class/power_supply/BAT*/charge_control_end_threshold
/sys/class/power_supply/BAT*/charge_control_start_threshold
```
Writing `80` to `charge_control_end_threshold` commands the charge controller to halt charging at 80%. When supported, `BatteryGuard` also sets `charge_control_start_threshold` to `75%` to prevent micro-cycling between 79% and 80%.

### 2. Legacy ThinkPad ACPI (`tp_smapi` / `thinkpad_acpi`)
```bash
/sys/class/power_supply/BAT*/charge_stop_threshold
/sys/class/power_supply/BAT*/charge_start_threshold
```

### 3. Lenovo IdeaPad ACPI (`VPC2004`)
For modern Lenovo IdeaPad, Legion, and Yoga laptops that govern conservation mode via the platform driver:
```bash
/sys/bus/platform/devices/VPC2004:*/conservation_mode
```
- Writing `1` activates conservation mode (hardwired in firmware to stop charging at 75–80%).
- Writing `0` deactivates conservation mode (charges to 100%).

---

## ⌨️ Command Reference

```bash
# Query current status, charge level, and active limits
battery-guard status

# Cap charge at 80% (recommended for desk / dock usage)
sudo battery-guard 80
# or:
sudo battery-guard on

# Restore full charging to 100% (before going mobile)
sudo battery-guard 100
# or:
sudo battery-guard off

# Custom threshold (50-100%)
sudo battery-guard 60
```

---

## 🧰 Behavior Details

- **Already above the threshold?** If your battery is currently at 95% and you set `battery-guard 80`, charging immediately halts (`Not charging`). The laptop will run on battery or pass-through until natural drain brings it down to 80%, where it will settle.
- **Persistence across reboots:** Most modern laptop ECs persist charge thresholds in NVRAM across reboots. On machines where firmware resets thresholds on cold boot, you can call `battery-guard 80` in `/etc/rc.local` or a simple systemd one-shot service.
- **Zero dependencies:** Written in pure, POSIX-friendly Bash. No Python runtime required, no pip packages, no background daemon.
