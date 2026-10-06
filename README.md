# 🎚️ ChangeState

**A volume knob for your Linux machine.**

Turn it down and your computer runs cooler, quieter, and sips power 🔋. Turn it up and it stretches its legs 🚀. ChangeState does this by steering your CPU, GPU, and memory settings to match the level you pick.

Works with AMD and Intel processors, and with AMD and NVIDIA graphics.

---

## ⚡ Quick start

```bash
# install
curl -sSL https://raw.githubusercontent.com/telosdevgroup/changestate/main/install.sh | bash

# see how your machine is doing
changestate status

# pick a level
sudo changestate p23     # a good everyday balance
sudo changestate p31     # everything wide open
```

Want it to adjust itself while you work? Turn on automatic mode:

```bash
sudo systemctl enable --now changestate-auto
```

---

## 📦 Install

**The easy way:**

```bash
curl -sSL https://raw.githubusercontent.com/telosdevgroup/changestate/main/install.sh | bash
```

**Or from a clone:**

```bash
git clone https://github.com/telosdevgroup/changestate.git
cd changestate
./install.sh
```

You need Linux, Python 3, and `sudo` to change levels. Looking at status doesn't need it.

---

## 🕹️ Using it

```bash
changestate                # what hardware you have and what levels exist
changestate status         # where things stand right now
sudo changestate p11       # move to a level
sudo changestate p31       # back to full power, always works
```

`status` gives you a readable snapshot:

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

## 🔢 The levels

The levels are named after prime numbers: **2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31**.

Why primes? Because it's cool, and because they give the numbers a spine. They're odd, a little irregular, and they don't line up with anything else. A level like `P:13` has its own personality. It isn't just "about half".

Low numbers are quiet and cool 🧊. High numbers are fast and loud 🔥. Here's how they feel:

| Level | Feels like |
| :--- | :--- |
| 😴 `P:2` | Asleep. Maximum battery, almost no heat. |
| 🌙 `P:3` | Barely awake. A terminal and a few monitors. |
| 📖 `P:5` | Reading and light browsing, fans stay off. |
| 🎧 `P:7` | Typing and music, cool to the touch. |
| 🤖 `P:11` | Quiet background work, even a local AI model ticking along. |
| ⌨️ `P:13` | A normal day of coding. |
| 🐳 `P:17` | Containers and compiling. |
| 🧱 `P:19` | Builds, editor and a pile of browser tabs. |
| 🎯 **`P:23`** | **The sweet spot. Games and heavy work without the fans freaking out.** |
| 🏎️ `P:29` | Big jobs, fast. |
| 🚀 **`P:31`** | **Wide open. No limits, full turbo, full GPU power.** |

Your machine decides what each level means in practice. On a 32-thread desktop, `P:23` keeps 24 threads running. On a laptop with fewer, it keeps proportionally fewer.

The two ends of the dial, `P:0` and `P:31`, are special. They're both manual only. Details below.

---

## 🔒 P:0, "MOM" lockdown

**MOM stands for Metal Over Moss.** It's the hunker-down mode: the machine goes quiet, closed off, and bare-bones.

```bash
sudo changestate p0      # or: sudo changestate mom
```

- 📴 Wireless radios are switched off, so you'll lose Wi-Fi and Bluetooth.
- 🧱 Incoming connections are blocked.
- 🪫 Heavy background processes are shut down.
- 🧊 Only 2 cores run, at their lowest speed.

**Getting out:** run `sudo changestate p31` (or any other level) from the machine itself. P:31 clears the lockdown and restores full power.

> [!NOTE]
> Since P:0 turns off Wi-Fi, don't use it over SSH or on a machine you can't touch. You'd lock yourself out.

---

## 🚀 P:31, wide open

Everything ChangeState does, undone. Turbo is on, clock limits are gone, and the GPU gets its full factory power back.

```bash
sudo changestate p31
```

It's also the **"fix everything" button**. If something feels off, or you just want your machine back exactly as the factory shipped it, run this one.

It's loud and hot by design. For daily use, `P:23` is usually the better pick.

---


## 🤖 Automatic mode

If you'd rather not think about it, `changestate-auto` runs in the background and moves the level for you.

It pays attention to one thing: **are you there?** 👀 It checks for keyboard, mouse, and trackpad activity. It ignores CPU load, so a brief spike doesn't make it jump around.

- 🚶 **Walk away** and it slowly steps down. Busy levels give up fast, and sleepy levels are patient.
- 👋 **Come back** and it snaps straight to `P:11` (see below).
- 💪 **Keep working** and it climbs one level at a time, as high as `P:29`.
- 🛑 It never goes to `P:0` or `P:31` on its own. Those are yours to choose.

> ### 👋 The `P:11` wake-up snap
> Let the machine drift down to the quiet levels (`P:2` through `P:7`), then touch the keyboard or mouse: it resets straight to **`P:11`**. It doesn't creep back up one step at a time, so you never sit waiting on a sleepy machine.
>
> `P:11` is your wake-up baseline. If you're already at `P:11` or higher, nothing snaps. It just keeps climbing as you work.

How long it waits before stepping down:

| Level | Waits |
| :--- | :---: |
| `P:29` | 2 min |
| `P:23` | 3 min |
| `P:19` | 5 min |
| `P:17` | 7 min |
| `P:13` | 11 min |
| `P:11` | 13 min |
| `P:7` | 17 min |
| `P:5` | 19 min |
| `P:3` | 23 min |
| `P:2` | 29 min |

The waits get shorter as you go up because high power is expensive to leave running. The low levels are cheap, so they can wait.

```bash
journalctl -u changestate-auto -f          # watch it make decisions
./changestate-auto --dry-run --fast 1.0    # try it without touching anything
sudo systemctl stop changestate-auto       # turn it off
```

---

## ✨ What it does for you

Modern chips burst to top speed for trivial tasks, pull a lot of power, and send the fans into a panic. ChangeState calms that down:

- 🧮 **Fewer cores and a lower speed limit** as you move down the levels.
- 🚫 **No turbo** on any level below `P:31`, so there are no sudden spikes.
- 🎮 **GPU boost off** below `P:31`, with full power restored at `P:31`.
- 🧠 **Memory settings** tuned for each level.
- 🔍 **It finds your hardware itself.** Nothing is hardcoded for your machine.

---

## 🛡️ What it won't do

- 🌀 **It never touches your fans.** Your BIOS keeps control of them.
- 🧷 **It never turns off your first CPU core.**
- 📶 **It never cuts your Wi-Fi or kills your desktop** (outside the opt-in `P:0` lockdown).
- 🤐 **It skips anything your machine doesn't have,** without complaining.
- 🆘 **`sudo changestate p31` always puts everything back.**

---

## 🖥️ Servers, labs, and fleets

It works fine without a desktop too:

- 🧰 [Ansible fleet guide](docs/ansible-fleet-orchestration.md): [deploy playbook](docs/recipes/ansible/changestate-deploy.yml), [tier switcher](docs/recipes/ansible/changestate-tier-switch.yml)
- ⏰ [Cron and systemd schedules](docs/cron-and-scheduled-capacity.md): quieter at night, faster by day
- 🗄️ [Headless server setup](docs/headless-server-deployment.md): [sudoers snippet](docs/recipes/sudoers/changestate.sudoers), [GitLab CI recipe](docs/recipes/ci-cd/gitlab-ci-changestate.yml)

---

## 💛 Support

If it's useful to you, you can [sponsor on GitHub](https://github.com/sponsors/telosdevgroup) or [leave a tip](https://avathings.com/changestate#tip).

## 📜 License

MIT. See [LICENSE](LICENSE).
