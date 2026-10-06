# Scheduled Capacity with Cron and Systemd Timers

Hardware workloads are rarely constant. Build servers experience heavy activity during working hours and sit idle all night. In lab environments, keeping 50 workstations running at uncapped frequencies generates unnecessary heat, exhausts cooling infrastructure, and wastes power.

By scheduling ChangeState with standard Linux `cron` or `systemd.timer` units, you can step machines up for workday shifts and step them down into whisper-cool idle tiers during off-hours—completely automatically and without touching the BIOS.

---

## 1. Choosing Between Cron and Systemd Timers

- **Cron (`/etc/cron.d`)**: Simple, familiar, portable across almost any UNIX/Linux system, and quick to set up in a single file.
- **Systemd Timers**: Ideal for modern systemd environments. Supports monotonic timers, handles missed events across reboots via `Persistent=true`, and integrates directly with `journalctl` for audit trails.

---

## 2. Approach A: Cron Schedule

The simplest way to schedule shifts is placing a crontab definition in `/etc/cron.d/changestate-schedule`.

A production-ready schedule is provided at [`docs/recipes/cron/changestate-schedule.cron`](recipes/cron/changestate-schedule.cron):

```cron
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# 06:00 Mon-Fri: Morning warm-up (P:23 - ~75% capacity, balanced compute & quiet fans)
0 6 * * 1-5 root /usr/local/bin/changestate p23 > /var/log/changestate_cron.log 2>&1

# 09:00 Mon-Fri: Peak business/build hours (P:29 - ~93% capacity, high throughput)
0 9 * * 1-5 root /usr/local/bin/changestate p29 > /var/log/changestate_cron.log 2>&1

# 18:00 Mon-Fri: Evening stand-down (P:11 - ~35% capacity, quiet idle, low power)
0 18 * * 1-5 root /usr/local/bin/changestate p11 > /var/log/changestate_cron.log 2>&1

# 23:00 Every day: Deep overnight whisper mode (P:3 - ~10% capacity, minimum thermal footprint)
0 23 * * * root /usr/local/bin/changestate p3 > /var/log/changestate_cron.log 2>&1

# 02:00 Sunday: Scheduled heavy maintenance & batch backups (P:31 - 100% full throttle)
0 2 * * 0 root /usr/local/bin/changestate p31 > /var/log/changestate_cron.log 2>&1
```

### Installation
```bash
sudo cp docs/recipes/cron/changestate-schedule.cron /etc/cron.d/changestate-schedule
sudo chmod 0644 /etc/cron.d/changestate-schedule
```

---

## 3. Approach B: Systemd Timers (Enterprise & Production)

Systemd allows parametric instantiation via `changestate@.service`. You can trigger any tier simply by starting `changestate@<tier>.service`.

### 1. Install the Parameterized Service Unit
Copy [`docs/recipes/systemd/changestate@.service`](recipes/systemd/changestate@.service) to `/etc/systemd/system/`:

```ini
[Unit]
Description=ChangeState Capacity Shift to %I
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/changestate %i
StandardOutput=journal
StandardError=journal
```

### 2. Install the Schedule Timers
Copy the day and night timers to `/etc/systemd/system/`:

- **Day Shift (`changestate-day.timer`)**:
  ```ini
  [Unit]
  Description=ChangeState Day Shift Capacity (P:23)

  [Timer]
  OnCalendar=Mon..Fri *-*-* 08:00:00
  Persistent=true
  Unit=changestate@p23.service

  [Install]
  WantedBy=timers.target
  ```

- **Night Shift (`changestate-night.timer`)**:
  ```ini
  [Unit]
  Description=ChangeState Night Shift Capacity (P:7)

  [Timer]
  OnCalendar=Mon..Fri *-*-* 19:00:00
  Persistent=true
  Unit=changestate@p7.service

  [Install]
  WantedBy=timers.target
  ```

### 3. Activate the Timers
```bash
sudo cp docs/recipes/systemd/changestate@.service /etc/systemd/system/
sudo cp docs/recipes/systemd/changestate-day.timer /etc/systemd/system/
sudo cp docs/recipes/systemd/changestate-night.timer /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now changestate-day.timer changestate-night.timer
```

### 4. Verification and Audit Logs
Check active timers and past transitions:
```bash
# List scheduled timers and next trigger time
systemctl list-timers changestate*

# Inspect recent execution logs
journalctl -u "changestate@*" -n 20 --no-pager
```
