# The Inverted Prime Cadence (TL;DR)

> **The Quick Summary:** Why reversing the prime numbers creates an elastic "rubber band" that keeps your computer cool, quiet, and fast without you ever touching a setting.

---

## 1. The Core Idea: An Elastic Rubber Band

Most power governors make a fatal mistake: **the higher you go, the longer they keep you there.**
If a heavy task kicks your machine to maximum power, it stays hot and loud for 30 minutes even after you've finished.

ChangeState does the exact opposite by **inverting the prime numbers**:

```
      [ HIGH TIERS (P23 - P29) ]
        Short Leash (2 to 3 min)
             │
             ▼ (Fast cool-down gravity)
  ═══► [ THE BALANCED SWEET SPOT ] ◄═══
        P11 - P13 - P17 (11 to 13 min)
        Stable, calm, daily work
             ▲
             │ (Instant wake-up snap)
       [ LOW TIERS (P2 - P7) ]
        Long Holding Hold (17 to 29 min)
```

Think of it like an **elastic rubber band** anchored in the middle:
- **Cranked up high?** You’re on a short leash. The moment you pause, gravity pulls you right back down to normal.
- **Idling low?** The machine rests peacefully for 20+ minutes without constantly thrashing clocks.
- **Touch the mouse?** It snaps right back to the sweet spot instantly.

---

## 2. The Inversion Table: Power vs. Waiting Time

We take the 10 prime capacity tiers and match them against their **exact reverse**:

| Capacity Tier | Power | Timer Window | What Actually Happens |
| :---: | :---: | :---: | :--- |
| **P:2** | 6% | **29 min** | **Deep sleep:** Holds quietly while you're away so fans stay off. |
| **P:3** | 10% | **23 min** | Low idle holding state. |
| **P:5** | 16% | **19 min** | Light idle holding state. |
| **P:7** | 23% | **17 min** | Baseline holding state. |
| **P:11** | 35% | **13 min** | **The Wakeup Snap:** Instant desktop responsiveness the second you return. |
| **P:13** | 42% | **11 min** | **Daily Driver Center:** Smooth, balanced writing, coding, and web browsing. |
| **P:17** | 55% | **7 min** | Active compute: re-checked every 7 minutes. |
| **P:19** | 61% | **5 min** | Heavy workload: short 5-minute leash. |
| **P:23** | 75% | **3 min** | Near-peak burst: checked every 3 minutes so the chassis never cooks. |
| **P:29** | 93% | **2 min** | Maximum burst: 2-minute limit before pulling back toward the center. |

---

## 3. The 3 Simple Rules of the Engine

### Rule 1: The Short Leash (Cool Down Fast)
Heavy work (rendering a video, compiling code) is a **temporary burst**.
- When you ramp up to **P:23** or **P:29**, the timer is only **2 to 3 minutes**.
- As long as you keep hammering away, it stays high.
- The second you get up to grab a coffee, it steps down in 180 seconds. Your fans never scream into an empty room.

### Rule 2: The Steady Center (Stable Focus)
In the middle (**P:11, P:13, P:17**), the timers are **11 to 13 minutes**.
- This is where 90% of your day happens: typing, reading, thinking, chatting.
- The 11–13 minute window means the hardware doesn't bounce around every 30 seconds while you stop to read an article.

### Rule 3: The Wakeup Snap (Zero Lag)
If the computer was resting down at **P:2, P:3, or P:5** while you were away:
- It **does NOT** make you wait or crawl out slowly ($P2 \rightarrow P3 \rightarrow P5$).
- The first millisecond you touch a key or nudge the mouse, it **snaps straight to P:11** (~35% capacity).
- Your screen and apps are instantly crisp and snappy with zero lag.

---

## 4. Protected Extremes (Manual Only)

The autonomous loop strictly lives between **P:2 and P:29**. Two extreme tiers are locked out of the auto loop and require explicit human opt-in:

- **P:0 (MOM):** Total radio silence, airgap firewall, heavy processes killed. Shuts everything down.
- **P:31 (Max Cap):** 80% ceiling broken, full boost on, factory power limit. Unlocks everything.

The result is a self-centering, self-cooling machine that effortlessly matches your human rhythm.
