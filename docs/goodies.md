# 🎁 Goodies & Extras: TL;DR

ChangeState is built around a lean core, but ships with a collection of focused, zero-dependency companion utilities in `extras/`.

Like ChangeState itself, all goodies adhere to strict principles:
- **Zero bloat:** No pip packages, no external runtimes, no background daemons unless strictly required.
- **Native kernel sysfs:** Direct manipulation of Linux `/sys` and `/proc` hardware interfaces.
- **Hardware preservation:** Purpose-built to extend hardware longevity and operational stability.
- **No liabilities:** Never touch system logs, journals, or personal user state.

---

## 🧰 The Goodies Roster

| Tool | Status | Purpose | Quick Command | Deep Dive |
| :--- | :--- | :--- | :--- | :--- |
| **BatteryGuard** | Available | Caps battery charge (default 80%) to stop lithium degradation on AC power. | `battery-guard status`<br>`sudo battery-guard 80` | [Deep Dive](battery-guard.md) |

---

## 🚀 Quick Usage

Goodies are automatically placed in `/usr/local/bin` when you run `./install.sh`. You can also execute them directly from `extras/` in the repository clone:

```bash
# Check current battery limit & status
battery-guard status

# Keep battery healthy while plugged into dock or AC (caps at 80%)
sudo battery-guard 80

# Restore full capacity before traveling
sudo battery-guard 100
```

---

## 📖 Deep Dives

- 🔋 **[BatteryGuard Deep Dive](battery-guard.md):** The science of lithium cell voltage saturation, kernel ACPI charge thresholds, and vendor support matrix (standard Linux kernel, ThinkPad, Lenovo IdeaPad).
