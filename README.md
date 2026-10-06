# 🎚️ ChangeState

**A volume knob for your Linux machine.**

Turn it down and your computer runs cooler, quieter, and sips power 🔋. Turn it up and it stretches its legs 🚀. ChangeState does this by steering your CPU, GPU, and memory settings to match the level you pick.

Works with AMD and Intel processors, and with AMD and NVIDIA graphics.

Rolling it out to a small group? Ready-made recipes and free help are below. 👇 [Small Group Toolkit](#-the-small-group-toolkit)

---

## ⚡ Quick start

```bash
# install
curl -sSL https://raw.githubusercontent.com/telosdevgroup/changestate/main/install.sh | bash

# see how your machine is doing
changestate status

# pick a level
sudo changestate p23     # a good everyday balance
sudo changestate p31     # Salt Flats: nothing in your way
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
| 🔋 **`P:11`** | **Sweet spot: great battery life.** Browsing, email, docs. |
| ⌨️ `P:13` | A normal day of coding. |
| 🐳 `P:17` | Containers and compiling. |
| 🧱 `P:19` | Builds, editor and a pile of browser tabs. |
| 🎯 **`P:23`** | **Sweet spot: the all-around efficiency + performance winner.** |
| 🏎️ `P:29` | Big jobs, fast. |
| 🚀 **`P:31`** | **Salt Flats. Flat out, nothing in your way: full turbo, full GPU power.** |

**Two sweet spots to remember:** `P:11` when you want to go easy on the battery, `P:23` when you want real speed without the noise. Most days you'll live between them.

### 🖱️ One-click desktop icons

Grab a launcher, drop it on your desktop or in your app menu, and click to switch. Each one asks for your password the usual way (`pkexec`) and needs ChangeState installed.

| | Launcher |
| :--- | :--- |
| 🔋 **`P:11`** Sweet spot: great battery life | [changestate-p11.desktop](changestate-p11.desktop) |
| 🎯 **`P:23`** Sweet spot: all-around winner | [changestate-p23.desktop](changestate-p23.desktop) |
| 🚀 **`P:31`** Salt Flats, also your "restore defaults" button | [changestate-p31.desktop](changestate-p31.desktop) |

After downloading, right-click the file and choose **Allow Launching** (or run `chmod +x changestate-p*.desktop`).

Your machine decides what each level means in practice. On a 32-thread desktop, `P:23` keeps 24 threads running. On a laptop with fewer, it keeps proportionally fewer.

The two ends of the dial, `P:0` and `P:31`, are special. They're both manual only. Details below.

---

## 🔒 P:0, "MOM" lockdown

**MOM stands for Metal Over Moss.** Shrink the machine down to something as small as moss, then harden it with metal. Tiny footprint, tough shell. 🌱🔩 Everything unnecessary goes quiet, and what's left is sealed up tight.

```bash
sudo changestate p0      # prompts you to type 'MOM' to confirm
sudo changestate p0 --confirm   # skips the confirmation prompt (for scripts / launchers)
```

Because P:0 severs Wi-Fi, drops incoming connections, and halts services, running it interactively will ask you to type `MOM` to confirm. If running in an automation script or launcher, pass `--confirm`.

- 📴 Wireless radios are switched off, so you'll lose Wi-Fi and Bluetooth.
- 🧱 Incoming connections are blocked.
- 🪫 Heavy background processes are shut down.
- 🧊 Only 2 cores run, at their lowest speed.

**Getting out:** run `sudo changestate p31` (or any other level) from the machine itself. P:31 clears the lockdown and restores full power.

> [!NOTE]
> Since P:0 turns off Wi-Fi, don't use it over SSH or on a machine you can't touch. You'd lock yourself out.

---

## 🏁 P:31, Salt Flats

Miles of flat, empty ground and nothing to slow you down. Every limit ChangeState sets is lifted: turbo is on, clock ceilings are gone, and the GPU gets its full factory power back. 🏎️💨

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
- 💪 **Keep working** and it climbs one level at a time, up to your ceiling (`P:23` by default, at most `P:29`; see [below](#%EF%B8%8F-choosing-how-low-and-high-it-may-go)).
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

> 📖 **Want to know why this feels so natural?** Read [The Inner Workings: TL;DR](docs/harmonic-cadence.md) for the quick story on how reversing the primes turns your machine into a self-centering rubber band.

```bash
journalctl -u changestate-auto -f          # watch it make decisions
./changestate-auto --dry-run --fast 1.0    # try it without touching anything
sudo systemctl stop changestate-auto       # turn it off
```

### 🎛️ Choosing how low and high it may go

By default automatic mode stays between **`P:7`** and **`P:23`**. You can change that. The allowed levels are `2, 3, 5, 7, 11, 13, 17, 19, 23, 29`.

```bash
changestate-auto --range 7:23     # floor and ceiling together (7-23 and 7,23 also work)
changestate-auto --min 5 --max 29 # or set them separately (--floor / --ceiling also work)
changestate-auto --wake 11        # the level it snaps to when you come back
```

`--range` wins over `--min` and `--max` if you give both.

To make it permanent, use one of these:

- **Config file** `/etc/changestate/auto.conf`, one `key=value` per line:
  ```ini
  range=7:29
  # or: min=7 / max=29
  ```
- **Environment variable:** `CHANGESTATE_RANGE=7:29`
- **The systemd service:** edit `ExecStart` in `changestate-auto.service`, for example `ExecStart=/usr/local/bin/changestate-auto --range 7:29`. Then run `sudo systemctl daemon-reload && sudo systemctl restart changestate-auto`.

Command-line flags override the config file and environment variable.

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

## 🧰 The Small Group Toolkit

Quieter machines and a lower power bill, without babysitting each box. ChangeState ships with ready-to-run recipes, so you can go from one machine to a handful without writing your own glue. Everything runs headless, with no desktop needed.

| | What you get | Grab it |
| :--- | :--- | :--- |
| 🧰 **Ansible** | Roll ChangeState out to every machine and set a baseline level. Change the whole group's level on demand. | [Group guide](docs/ansible-small-group-orchestration.md) · [deploy playbook](docs/recipes/ansible/changestate-deploy.yml) · [tier switcher](docs/recipes/ansible/changestate-tier-switch.yml) |
| ⏰ **Cron & systemd timers** | Fast by day, whisper-quiet at night, all on a schedule. Pick cron for simple or systemd timers for easy-to-read logs. | [Scheduling guide](docs/cron-and-scheduled-capacity.md) · [cron schedule](docs/recipes/cron/changestate-schedule.cron) · [day timer](docs/recipes/systemd/changestate-day.timer) · [night timer](docs/recipes/systemd/changestate-night.timer) |
| 🗄️ **Headless servers** | Runs over SSH on Ubuntu, Debian, RHEL, Rocky, Alma, Fedora and Arch. No GUI libraries. | [Server setup](docs/headless-server-deployment.md) |
| 🔐 **Passwordless control** | A locked-down sudoers rule so automation can change levels without a password. | [sudoers snippet](docs/recipes/sudoers/changestate.sudoers) |
| 🚦 **Self-hosted CI** | Step a build runner up for the job and back down after. | [GitLab CI recipe](docs/recipes/ci-cd/gitlab-ci-changestate.yml) |

Stuck or want a second pair of eyes on your setup? Email [telosdevgroup@gmail.com](mailto:telosdevgroup@gmail.com?subject=ChangeState%20help). Happy to help, no charge.

---

## 📜 License

MIT. See [LICENSE](LICENSE).
