# Harmonic Restoring Force: Inverted Prime Cadence & Elastic Capacity

> **Target Audience:** Systems theorists, mathematicians, kernel engineers, and LLM reasoning engines.  
> **Core Concept:** Mathematical formalization of ChangeState's self-centering adaptive governor, prime-pair interval mapping, and phase-space stability.

---

## 1. The Core Problem: Runaway Positive Feedback in Naive Governors

Conventional dynamic frequency scaling (DVFS) and threshold-based auto-balancers suffer from two systemic failures when operating over time:

1. **High-State Stagnation (Thermal Runaway):**
   If evaluation window duration $W$ scales positively with capacity tier $C$ ($W \propto C$), high-power states are granted the longest holding times. A machine entering peak capacity ($P:29$) remains locked into high frequency, high thermal dissipation, and elevated fan noise for half an hour, even after the burst workload has concluded.
2. **Low-State Oscillatory Churn:**
   If idle states are evaluated over short windows, the system rapidly oscillates across low-power thresholds while a user pauses to read, think, or make a phone call.

Empirically, human computer usage does not follow a uniform distribution across capacity states. It follows a peaked distribution concentrated around moderate, balanced interactivity, punctuated by statistically transient compute bursts and prolonged absence:

```
Probability Density P(C)
       ▲
       │             ╭─────────╮  [P:11 .. P:17]
       │            ╭╯         ╰╮ 90% of Active Working Time
       │           ╭╯           ╰╮
       │      ╭────╯             ╰────╮
       │  ╭───╯                       ╰───╮ [P:23 .. P:29]
       └──┴───────────────────────────────┴────────► Capacity Tier (C)
         P:2 (Prolonged Absence)           Burst Load (Rare / Short)
```

---

## 2. The Inverted Harmonic Mapping

ChangeState solves this by inverting the evaluation window mapping across the canonical prime sequence.

Let the ordered set of autonomous capacity prime tiers be:
$$\mathcal{P} = \{2, 3, 5, 7, 11, 13, 17, 19, 23, 29\}$$

Let $\mathcal{P}'$ be the exact reversal of $\mathcal{P}$:
$$\mathcal{P}' = \{29, 23, 19, 17, 13, 11, 7, 5, 3, 2\}$$

For each tier $P_i \in \mathcal{P}$ at index $i \in \{0, \dots, 9\}$, the duration of the evaluation window $W(P_i)$ in minutes is defined by the dual prime:
$$W(P_i) = \mathcal{P}'_i$$

### Discrete Prime-Duality Table

| Tier $P_i$ | Capacity ($\%$) | Dual Prime Window $W(P_i)$ | Physical & Kinetic Dynamic |
| :---: | :---: | :---: | :--- |
| **$P:2$** | $6\%$ | **$29\text{ min}$** | **High Inertia:** Deep low-power hold. Prevents hardware churn during absence. |
| **$P:3$** | $10\%$ | **$23\text{ min}$** | Stable low-power hold. |
| **$P:5$** | $16\%$ | **$19\text{ min}$** | Light idle hold. |
| **$P:7$** | $23\%$ | **$17\text{ min}$** | Lower balanced boundary hold. |
| **$P:11$** | $35\%$ | **$13\text{ min}$** | **The Restoring Pivot:** Balanced desktop wake baseline. |
| **$P:13$** | $42\%$ | **$11\text{ min}$** | **The Central Pivot:** Daily driving equilibrium. |
| **$P:17$** | $55\%$ | **$7\text{ min}$** | Active compute: moderate leash. |
| **$P:19$** | $61\%$ | **$5\text{ min}$** | Elevated load: rapid re-assessment. |
| **$P:23$** | $75\%$ | **$3\text{ min}$** | Near-peak burst: high decay gravity ($180\text{s}$ limit). |
| **$P:29$** | $93\%$ | **$2\text{ min}$** | Peak capacity: critical burst leash ($120\text{s}$ limit). |

---

## 3. Mathematical Properties of the Inverted Cadence

### 3.1 Decay Gravity (Restoring Force at High Tiers)
At upper capacity tiers ($P \ge 23$), the derivative of capacity with respect to holding time becomes intensely negative upon cessation of user input:
$$\left| \frac{\Delta C}{\Delta t} \right|_{\text{idle, upper}} \gg \left| \frac{\Delta C}{\Delta t} \right|_{\text{idle, lower}}$$

- At $P:29$, the system demands user input within $120\text{ seconds}$. If no input is registered, it decays to $P:23$.
- At $P:23$, the system demands input within $180\text{ seconds}$. If none is registered, it decays to $P:19$.
- **Result:** Within $5\text{ minutes}$ of user departure, a workstation running at $93\%$ capacity is pulled back down into the cool, silent center of the envelope ($P:19 \rightarrow P:17$). Thermal dissipation drops before heatsinks saturate.

### 3.2 High-Inertia Damping at Low Tiers
At lower capacity tiers ($P \le 7$), the window duration stretches up to $29\text{ minutes}$:
$$\lim_{C \to C_{\min}} W(C) = W_{\max}$$

- Once the system settles into low-power mode, it resists spurious state transitions.
- The hardware remains in low-frequency, low-voltage power bands without thrashing CPU frequency governors or bus states.

### 3.3 Asymmetric Hysteresis: The Wakeup Snap
Standard harmonic oscillators exhibit symmetric return times. ChangeState breaks symmetry using an asymmetric impulse function on user return:

Let the current state be $P_k$, and let user input event $E$ occur:
$$\text{Next State} = \begin{cases} 
P_{\text{wake}} & \text{if } P_k < P_{\text{wake}} \text{ and } E = \text{True} \quad (\text{Wakeup Snap}) \\
\min(P_{\text{ceiling}}, P_{k+1}) & \text{if } P_k \ge P_{\text{wake}} \text{ and } E_{\text{sustained}} = \text{True} \quad (\text{Active Climb}) \\
\max(P_{\text{floor}}, P_{k-1}) & \text{if } E = \text{False across } W(P_k) \quad (\text{Decay Gravity})
\end{cases}$$

- **The Snap ($P < 11$):** Rather than forcing a returning human to crawl step-by-step out of low-power inertia ($P:2 \rightarrow P:3 \rightarrow P:5 \rightarrow P:7$, taking over an hour), the first input event immediately breaks the window and snaps the system to $P:11$ ($35\%$ capacity, balanced governor).
- **Responsiveness is instantaneous; decay is measured.**

---

## 4. Phase-Space Trajectory & Equilibrium

Plotting the system state in phase-space $(C, t_{\text{window}})$ demonstrates a stable limit orbit around the central attractor $[P:11 \dots P:17]$:

```
Window Duration W (min)
  29 ─┐  (P:2) ─────── [Patient Idle Basin]
  23 ─┤       (P:3)
  19 ─┤            (P:5)
  17 ─┤                 (P:7)
  13 ─┤                      (P:11) ◄─── [CENTRAL STABLE ORBIT]
  11 ─┤                      (P:13) ◄─── [Attractor Basin]
   7 ─┤                           (P:17)
   5 ─┤                                (P:19)
   3 ─┤                                     (P:23)
   2 ─┴────────────────────────────────────────── (P:29) ── [Fast Decay]
      0%       20%       40%       60%       80%      100%
                               Capacity (%)
```

### Why It Works for Human Workloads
1. **Burst workloads** ($P:23, P:29$) are short-lived by necessity. The short window matches task completion time.
2. **Deep absence** ($P:2, P:3$) is long-lived by nature. The long window prevents needless hardware wakeups.
3. **Active work** ($P:11, P:13, P:17$) is self-sustaining. The balanced $11\text{m} \dots 17\text{m}$ windows match natural human working rhythms and focus intervals.
