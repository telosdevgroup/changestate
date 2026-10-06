# The Inner Workings: TL;DR

> **Why ChangeState Feels Right:** Primes for power, primes in reverse for time. A self-centering rubber band that keeps your computer quiet, cool, and fast.

---

## 1. The Core Idea: An Elastic Rubber Band

Most power managers get it backwards: **the harder you work, the longer they keep your computer screaming.**
If a quick job kicks your machine to max power, it stays hot and loud for half an hour even after you've walked away.

ChangeState uses a simple prime trick: **we reverse the prime numbers for the timers.**

```
      [ HIGH PRIMES (P23, P29) ]
        Short Leash (2 to 3 min)
             │
             ▼ (Cools right down)
  ═══► [ THE BALANCED CENTER ] ◄═══
        P11, P13, P17 (11 to 13 min)
        Calm, quiet, normal daily work
             ▲
             │ (Instant wake-up snap)
       [ LOW PRIMES (P2, P3, P5, P7) ]
        Patient Hold (17 to 29 min)
```

Think of it like an **elastic rubber band** anchored in the balanced sweet spot:
- **Cranked up high?** You’re on a short leash. The moment you pause, it pulls right back down to normal.
- **Resting low?** The machine sits quietly for 20+ minutes without constantly fidgeting with clocks or fans.
- **Touch the mouse?** It snaps right back to a responsive baseline (**P:11**, ~35%) instantly.

---

## 2. The Prime Mirror: Power vs. Minutes

We take the 10 prime capacity tiers and mirror them with the exact same primes in reverse:

| Prime Tier | Power | Waiting Timer | What Actually Happens |
| :---: | :---: | :---: | :--- |
| **P:2** | 6% | **29 min** | **Deep sleep:** Holds quietly while you're away so fans stay completely off. |
| **P:3** | 10% | **23 min** | Low idle holding state. |
| **P:5** | 16% | **19 min** | Light idle holding state. |
| **P:7** | 23% | **17 min** | Baseline holding state. |
| **P:11** | 35% | **13 min** | **The Wakeup Snap:** Instant snap to responsive desktop the second you return. |
| **P:13** | 42% | **11 min** | **Daily Driver Center:** Smooth, quiet writing, coding, and browsing. |
| **P:17** | 55% | **7 min** | Active work: checked every 7 minutes. |
| **P:19** | 61% | **5 min** | Heavy work: short 5-minute leash. |
| **P:23** | 75% | **3 min** | Near-peak burst: checked every 3 minutes so fans never scream needlessly. |
| **P:29** | 93% | **2 min** | Maximum burst: 2-minute limit before pulling back toward the center. |

---

## 3. The 3 Simple Rules

### Rule 1: The Short Leash (Cool Down Fast)
Heavy compute is a **temporary burst**.
- When you ramp up to **P:23** or **P:29**, the timer is only **2 to 3 minutes**.
- Keep typing or working, and it stays fast.
- Get up to grab a drink, and it steps right back down in 180 seconds. Fans never scream into an empty room.

### Rule 2: The Steady Center (Stable Focus)
In the middle (**P:11, P:13, P:17**), the timers are **11 to 13 minutes**.
- This is where 90% of your day happens: typing, reading, thinking.
- The 11–13 minute window gives you steady stability so the hardware doesn't bounce around every 30 seconds while you stop to read.

### Rule 3: The Wakeup Snap (Zero Lag)
If the computer was resting down at **P:2, P:3, or P:5** while you were away:
- It **never** makes you crawl out slowly rung-by-rung.
- The first instant you touch a key or nudge the mouse, it **snaps straight to P:11** (~35% capacity).
- Your screen and apps are instantly crisp and snappy with zero lag.

---

## 4. The Two Extremes (Manual Only)

The auto daemon strictly roams between **P:2 and P:29**. Two extreme tiers are kept completely out of the auto loop:

- **P:0 (MOM):** Shuts everything down (radio silence, firewall drop, background jobs culled).
- **P:31 (Max Cap):** Unlocks everything (100% uncapped, turbo boost on, full factory wattage).

Primes for power, primes in reverse for time. It just balances itself.
