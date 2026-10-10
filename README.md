# 💧 ChangeState

**A prime-based liquid operating-state manager for Linux computers (auto and manual modes).**

*You love your hardware, and so do we. That's why we "conservativize" the operating range: to help maximize the effectiveness, thermal health, and longevity of your machines.*

ChangeState coordinates hardware and system settings across CPU, GPU, memory, storage, and other system subsystems to manage how a Linux computer operates. Its prime-based capacity levels provide a consistent framework for changing the machine's overall operating state, manually or automatically in response to user activity.

The normal operating range, P:2 through P:29, applies a conservative operating model with an 80% maximum clock ceiling for tier calculations, alongside adjustments to CPU core availability, boost behavior, GPU clocks and settings, memory caching, storage settings, and other system controls.

At the extremes, ChangeState offers two special states:

* **P:0 — MOM (Metal Over Moss):** a defensive posture that radically reduces the system to a minimal operating configuration.
* **P:31 — Salt Flats:** an explicit unlock of full performance beyond the normal operating ceiling, including boost.

Automatic mode stays within the more central P:7–P:23 band and never autonomously enters either end.


---

## 🧭 Contents

- [⚡ 1. Rapid Install (One-Liner)](#-1-rapid-install-one-liner)
- [🤖 2. Automatic Mode (Set & Forget)](#-2-automatic-mode-set--forget)
- [🧰 3. Tools & Small Group Deployment](#-3-tools--small-group-deployment)
- [🕹️ 4. Quick Manual Commands](#%EF%B8%8F-4-quick-manual-commands)
- [📬 Holler at Us](#-holler-at-us)
- [📚 Deep Dives & Extra Stuff](#-deep-dives--extra-stuff)
- [📜 License](#-license)

---

## ⚡ 1. Rapid Install (One-Liner)

Install ChangeState and enable the autonomous background daemon on any machine in 5 seconds:

```bash
curl -sSL https://raw.githubusercontent.com/telosdevgroup/changestate/main/install.sh | bash
sudo systemctl enable --now changestate-auto
```

*(Installs the CLI to `/usr/local/bin/changestate` and registers the autonomous systemd service).*

Or install from a local clone / USB:
```bash
git clone https://github.com/telosdevgroup/changestate.git
cd changestate
./install.sh
sudo systemctl enable --now changestate-auto
```

---

## 🤖 2. Automatic Mode (Set & Forget)

Once `changestate-auto` is running, you never have to touch a setting again. It monitors keyboard, mouse, and trackpad activity via X11 idle hooks:

- **Active work:** Climbs dynamically up to **`P:23`** (~75% capacity, quiet acoustics, boost off).
- **Step away:** High tiers have a short 2–3 minute leash. The moment you leave, it pulls right back down to cool the chassis.
- **Come back:** The instant you touch a key or nudge the mouse, it snaps straight to **`P:11`** (~35% capacity) with zero lag.
- **Default Range:** Strictly bounded between **`P:7`** and **`P:23`**. It never touches `P:0` (lockdown) or `P:31` (uncapped boost) on its own.

```bash
journalctl -u changestate-auto -f       # watch it adapt in real time
sudo systemctl stop changestate-auto    # pause or turn off
```

---

## 🧰 3. Tools & Small Group Deployment

Quieter machines and lower power bills across a lab, cluster, or office without babysitting each box:

| Tool / Recipe | What It Does | Links |
| :--- | :--- | :--- |
| 🧰 **Ansible Playbooks** | Roll ChangeState out to every machine at once, set default ranges, or step whole clusters on demand. | [Group Guide](docs/ansible-small-group-orchestration.md) · [Deploy Playbook](docs/recipes/ansible/changestate-deploy.yml) · [Tier Switcher](docs/recipes/ansible/changestate-tier-switch.yml) |
| ⏰ **Schedules & Timers** | High capacity during working hours, deep sleep at night. | [Scheduling Guide](docs/cron-and-scheduled-capacity.md) · [Cron](docs/recipes/cron/changestate-schedule.cron) · [Systemd Timers](docs/recipes/systemd/changestate-day.timer) |
| 🗄️ **Headless Servers** | Runs over SSH on Ubuntu, Debian, RHEL, Rocky, Alma, Fedora, and Arch. Zero GUI libraries. | [Headless Guide](docs/headless-server-deployment.md) |
| 🔐 **Passwordless Sudo** | Clean sudoers snippet so CI runners and automation can step tiers without passwords. | [Sudoers Snippet](docs/recipes/sudoers/changestate.sudoers) |
| 🚦 **CI/CD Runners** | Step a build runner up to P:31 for a compile job, then step back down after. | [GitLab CI Recipe](docs/recipes/ci-cd/gitlab-ci-changestate.yml) |

---

## 🕹️ 4. Quick Manual Commands

```bash
changestate status       # instant hardware diagnostic readout
sudo changestate p11     # battery sweet spot (~35%)
sudo changestate p23     # balanced work sweet spot (~75%)
sudo changestate p31     # Salt Flats: 100% uncapped compute (the "restore defaults" button)
sudo changestate p0      # MOM: Metal Over Moss airgap lockdown (requires typing 'MOM')
```

---

## 📬 Holler at Us

Rolling this out to a school lab, office, or render farm and want a second pair of eyes on your setup? 

Drop an email to **[telosdevgroup@gmail.com](mailto:telosdevgroup@gmail.com?subject=ChangeState%20Help)**. Happy to help you tune your group deployment, no charge.

---

## 📚 Deep Dives & Extra Stuff

For the curious and anyone wanting to peek under the hood:

- 📖 **[The Inner Workings: TL;DR](docs/harmonic-cadence.md):** The quick story on how reversing the primes turns your machine into a self-centering rubber band.
- ⚙️ **[Hardware Actuation & Kernel Interfaces](docs/hardware-actuation.md):** Exact details on CPU topology ordering, clock clamping math, ACPI platform profiles, and safe GPU driver handling.
- 🏗️ **[System Architecture](docs/architecture.md):** The 5 architectural pillars (Core Engine, Timing Daemon, Device Heartbeat, Event Server, Client Surfaces).
- 🤖 **[LLM Quickstart & Onboarding](docs/llm-quickstart.md):** High-density reference written for LLMs and autonomous dev-ops bots.
- 🛡️ **[Developer & Agent Rules](AGENTS.md):** Safety invariants, file size limits, and development guidelines.

---

## 📜 License

MIT License. See [LICENSE](LICENSE) for details.
