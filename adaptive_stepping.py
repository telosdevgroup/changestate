#!/usr/bin/env python3
"""
adaptive_stepping.py - Prototype for Prime-Based Elastic Capacity Scaling.

Core Principle:
- User input is the ONLY judge of activity.
- Starting at Prime P, wait P minutes.
- If user input occurred during the window: step UP to next prime (new window = next P min).
- If no user input occurred (idle throughout): step DOWN to prev prime (new window = prev P min).

Flags:
  --dry-run (default): Simulates state changes without changing hardware.
  --live: Applies actual changestate calls via sudo/pkexec.
  --fast <N>: 1 prime minute = N seconds (default: 1.0 for rapid testing, 60.0 for real time).
  --start <P>: Starting prime (default: 13).
"""

import sys
import os
import time
import argparse
import ctypes
from datetime import datetime

PRIME_LADDER = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]

# Ctypes binding to X11 XScreenSaver to query user idle milliseconds directly (zero CLI dependencies)
class XScreenSaverInfo(ctypes.Structure):
    _fields_ = [
        ('window', ctypes.c_ulong),
        ('state', ctypes.c_int),
        ('kind', ctypes.c_int),
        ('til_or_since', ctypes.c_ulong),
        ('idle', ctypes.c_ulong),
        ('eventMask', ctypes.c_ulong)
    ]

class UserActivityDetector:
    def __init__(self):
        self._available = False
        try:
            self._x11 = ctypes.cdll.LoadLibrary('libX11.so.6')
            self._xss = ctypes.cdll.LoadLibrary('libXss.so.1')
            self._available = True
        except Exception:
            self._available = False

    def get_idle_seconds(self) -> float:
        """Returns seconds since the user last touched keyboard or mouse."""
        if not self._available:
            return 0.0
        display = self._x11.XOpenDisplay(None)
        if not display:
            return 0.0
        try:
            root = self._x11.XDefaultRootWindow(display)
            info = self._xss.XScreenSaverAllocInfo()
            self._xss.XScreenSaverQueryInfo(display, root, info)
            idle_ms = XScreenSaverInfo.from_address(info).idle
            self._x11.XFree(info)
            return idle_ms / 1000.0
        finally:
            self._x11.XCloseDisplay(display)

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def apply_tier(prime: int, live: bool):
    tier_id = f"p{prime}"
    if live:
        log(f"⚡ [LIVE] Applying hardware shift to {tier_id.upper()}...")
        # Rule: Use changestate entrypoint
        os.system(f"pkexec /usr/local/bin/changestate {tier_id}")
    else:
        log(f"🔍 [SIMULATION] Would apply hardware shift: changestate {tier_id}")

def run_adaptive_loop(start_prime=13, seconds_per_prime_minute=60.0, floor_prime=2, ceiling_prime=31, wake_prime=11, live=False):
    if start_prime not in PRIME_LADDER:
        sys.exit(f"Error: Start prime {start_prime} is not in PRIME_LADDER: {PRIME_LADDER}")
    if floor_prime not in PRIME_LADDER or ceiling_prime not in PRIME_LADDER or wake_prime not in PRIME_LADDER:
        sys.exit(f"Error: Floor/Ceiling/Wake primes must be in {PRIME_LADDER}")
    if floor_prime > ceiling_prime:
        sys.exit(f"Error: Floor P{floor_prime} cannot be higher than Ceiling P{ceiling_prime}")

    detector = UserActivityDetector()
    current_prime = max(floor_prime, min(start_prime, ceiling_prime))
    current_idx = PRIME_LADDER.index(current_prime)
    floor_idx = PRIME_LADDER.index(floor_prime)
    ceiling_idx = PRIME_LADDER.index(ceiling_prime)
    wake_idx = PRIME_LADDER.index(wake_prime)

    log("=" * 65)
    log(" ChangeState: Prime-Based Elastic Capacity Scaling")
    log(f" Mode: {'⚡ LIVE HARDWARE' if live else '🔍 DRY RUN / SIMULATION'}")
    log(f" Operating Bounds: [Floor: P{floor_prime} ── Ceiling: P{ceiling_prime}]")
    log(f" Wakeup Baseline: P{wake_prime} (Snaps here immediately on wake)")
    log(f" Active Tier: P{current_prime}")
    log(f" Time Scale: 1 prime minute = {seconds_per_prime_minute}s ({'real minutes' if seconds_per_prime_minute == 60.0 else 'scaled'})")
    log(" Activity Rule: User input (mouse/keyboard) is the sole metric.")
    log("=" * 65)

    apply_tier(current_prime, live)
    is_idling = False

    while True:
        current_prime = PRIME_LADDER[current_idx]
        window_duration_sec = current_prime * seconds_per_prime_minute
        log(f"⏳ Monitoring window started: P{current_prime} (Window: {current_prime}m -> {window_duration_sec:.1f}s)")

        window_start = time.time()
        activity_detected = False
        prev_idle = detector.get_idle_seconds()

        tick_interval = 0.5 if seconds_per_prime_minute < 5 else 2.0
        while (time.time() - window_start) < window_duration_sec:
            time.sleep(tick_interval)
            current_idle = detector.get_idle_seconds()

            # Activity detected: user pressed key or moved mouse
            if current_idle < prev_idle or current_idle < 1.0:
                activity_detected = True
                # If recovering from idle, wake up immediately without stalling
                if is_idling:
                    break
            prev_idle = current_idle

        # Evaluate window outcome
        if activity_detected:
            # If waking up while below wake baseline, snap directly to wake tier
            if is_idling and current_idx < wake_idx:
                next_idx = min(ceiling_idx, max(floor_idx, wake_idx))
                log(f"🟢 User wake detected! Snapping directly to Wake Baseline: P{current_prime} -> P{PRIME_LADDER[next_idx]}")
            else:
                next_idx = min(ceiling_idx, current_idx + 1)
                if next_idx > current_idx:
                    log(f"🟢 User activity sustained! Stepping UP: P{current_prime} -> P{PRIME_LADDER[next_idx]}")
                else:
                    log(f"🟢 User activity sustained, already at ceiling P{current_prime}. Maintaining tier.")

            is_idling = False
            if next_idx != current_idx:
                current_idx = next_idx
                apply_tier(PRIME_LADDER[current_idx], live)
        else:
            is_idling = True
            if current_idx > floor_idx:
                next_idx = current_idx - 1
                log(f"💤 No user activity detected ({current_prime}m idle). Stepping DOWN: P{current_prime} -> P{PRIME_LADDER[next_idx]}")
                current_idx = next_idx
                apply_tier(PRIME_LADDER[current_idx], live)
            else:
                log(f"💤 No user activity detected, already at floor P{current_prime}. Maintaining tier.")

def main():
    parser = argparse.ArgumentParser(description="Prime-based adaptive capacity scaling.")
    parser.add_argument("--start", type=int, default=13, help="Starting prime tier (default: 13)")
    parser.add_argument("--floor", type=int, default=2, help="Lower prime boundary (default: 2)")
    parser.add_argument("--ceiling", type=int, default=31, help="Upper prime boundary (default: 31)")
    parser.add_argument("--wake", type=int, default=11, help="Wake baseline prime (default: 11)")
    parser.add_argument("--fast", type=float, default=60.0, help="Seconds per prime-minute (default: 60.0 for real minutes; use 1.0 for testing)")
    parser.add_argument("--live", action="store_true", help="Apply actual hardware changes (default: dry run)")
    args = parser.parse_args()

    try:
        run_adaptive_loop(
            start_prime=args.start,
            seconds_per_prime_minute=args.fast,
            floor_prime=args.floor,
            ceiling_prime=args.ceiling,
            wake_prime=args.wake,
            live=args.live
        )
    except KeyboardInterrupt:
        log("\nAdaptive loop stopped by user.")

if __name__ == "__main__":
    main()
