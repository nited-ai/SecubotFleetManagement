# Strafe (Left/Right) Movement — How It Works

> **Status:** Implemented and tested (asymmetric deceleration fix applied)
> **Branch:** `feature/Strafe-adjustments`
> **Input:** Keyboard A/D keys (digital ±1)
> **Approach:** Exponential curve + jump-start + asymmetric backend slew rate limiter

## Overview

Strafe (lateral movement) converts A/D key presses into left/right robot velocity. Unlike mouse rotation (unbounded analog deltas), strafe input is **digital** — the key is either pressed (1) or not (0). The speed slider determines the effective input magnitude, and an exponential curve (`x^alpha`) shapes how that maps to velocity.

The system uses **single-layer smoothing** — the backend's asymmetric slew rate limiter is the sole smoother. Frontend smoothing was removed (see "Smoothing Architecture" section below).

## Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│ FRONTEND  (keyboard-mouse-control.js)                                   │
│                                                                         │
│  Step 1: Key Input → Digital Value                                      │
│  ─────────────────────────────────                                      │
│  A key pressed → strafe = -1   (left)                                   │
│  D key pressed → strafe = +1   (right)                                  │
│  Both/neither  → strafe =  0   (stop)                                   │
│                                                                         │
│  Step 2: Speed Slider Applied                                           │
│  ────────────────────────────                                           │
│  speedMultiplier = speedPercentage / 100    (0.0 to 1.0)               │
│  strafe *= speedMultiplier                                              │
│  Result: strafe = ±speedMultiplier  (e.g., ±0.5 at 50% speed)         │
│                                                                         │
│  Step 3: Exponential Curve                                              │
│  ─────────────────────────                                              │
│  input = abs(strafe)            (0.0 to 1.0)                           │
│  if input < deadzone → output = 0                                       │
│  normalized = (input - deadzone) / (1 - deadzone)                      │
│  curved = normalized ^ strafeAlpha                                      │
│  targetStrafe = curved × maxStrafe × sign(strafe)                      │
│                                                                         │
│  Step 4: Direct Assignment (Option B)                                   │
│  ────────────────────────────────────                                   │
│  if |targetStrafe| > 0.001 → currentStrafe = targetStrafe              │
│  else → currentStrafe = 0   (instant stop on key release)              │
│  No frontend ramping — backend handles all smoothing.                  │
│                                                                         │
│  Step 5: Inversion + Normalization → WebSocket                         │
│  ─────────────────────────────────────────────                          │
│  vy = -currentVelocities.strafe   (invert for backend convention)      │
│  lx = -vy / maxStrafe             (normalize to [-1, 1])               │
│  Send {lx, max_strafe, strafe_ramp_time, ...} via WebSocket            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓  WebSocket
┌─────────────────────────────────────────────────────────────────────────┐
│ BACKEND  (app/services/control.py)                                      │
│                                                                         │
│  Step 7: De-normalize → Physical Velocity                               │
│  ────────────────────────────────────────                               │
│  raw_target_vy = -lx × max_strafe     (back to m/s)                   │
│                                                                         │
│  Step 8: Asymmetric Slew Rate Limiter                                   │
│  ─────────────────────────────────────                                  │
│  if |target| < |current|  →  current = target  (INSTANT deceleration)  │
│  else:                                                                  │
│    MAX_STRAFE_ACCEL = max_strafe / strafe_ramp_time                    │
│    max_step = MAX_STRAFE_ACCEL × dt                                    │
│    current += clamp(delta, -max_step, +max_step)  (smooth acceleration)│
│                                                                         │
│  Step 9: Final Safety Clamp                                             │
│  ───────────────────────────                                            │
│  vy = clamp(current_vy, -max_strafe, +max_strafe)                     │
│                                                                         │
│  Step 10: Re-normalize → Robot (using HARDWARE LIMITS)                  │
│  ──────────────────────────────────────────────────────                 │
│  lx_norm = clamp(-vy / HARDWARE_LIMIT_STRAFE, -1.0, 1.0)             │
│  Publish to WirelessController topic: {"lx": lx_norm, ...}            │
│  NOTE: Divides by hardware limit (1.0 m/s), NOT slider value.         │
│  This preserves the slider's speed-limiting effect.                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## The Formula

End-to-end from key press to target velocity (before ramping):

```
normalized = (speedMultiplier - deadzone) / (1 - deadzone)
targetStrafe = normalized^strafeAlpha × maxStrafe × sign(key)
```

| Variable | Source | Default | Description |
|---|---|---|---|
| `speedMultiplier` | Speed slider (0–100%) | 1.0 | `speedPercentage / 100` — acts as the curve input |
| `deadzone` | Settings panel | 0.10 | Inputs below this produce zero output |
| `strafeAlpha` | Settings panel | 1.0 | Exponential curve factor (see analysis below) |
| `maxStrafe` | Settings panel | 0.6 m/s | Maximum strafe velocity (normal preset; hardware limit = 1.0 m/s) |
| `sign(key)` | A=-1, D=+1 | — | Direction of strafe |

**Key insight:** For keyboard input, the speed slider value **IS** the curve input (since key press = 1.0, multiplied by speedMultiplier). Alpha controls how the speed slider maps to velocity — it's a "speed profile" for the slider.


## Alpha Curve Behavior Analysis

**User observation:** "At `strafe_alpha = 0.1` and `strafe_ramp_time = 0.1s`, strafe feels responsive but alpha seems to have no effect."

**Root cause:** The user was testing at **100% speed slider**, where alpha has mathematically zero effect.

### Why Alpha Vanishes at 100% Speed

With key pressed, `strafeInput = speedMultiplier`. At 100% speed, `strafeInput = 1.0`:

```
normalized = (1.0 - 0.10) / (1.0 - 0.10) = 1.0
curved = 1.0 ^ alpha = 1.0    ← for ANY alpha value
output = 1.0 × 0.6 = 0.6 m/s  ← always the same
```

Raising 1.0 to any power always gives 1.0. **Alpha only shapes the middle range of the speed slider.**

### Alpha Effect at Different Speed Slider Values

With `deadzone = 0.10`, `maxStrafe = 0.6 m/s`:

| Speed Slider | Alpha 0.1 | Alpha 0.5 | Alpha 1.0 | Alpha 1.2 (default) | Alpha 2.0 |
|---|---|---|---|---|---|
| **100%** | 0.600 | 0.600 | 0.600 | 0.600 | 0.600 |
| **75%** | 0.577 | 0.516 | 0.433 | 0.403 | 0.313 |
| **50%** | 0.553 | 0.400 | 0.267 | 0.225 | 0.119 |
| **25%** | 0.503 | 0.245 | 0.100 | 0.071 | 0.017 |
| **15%** | 0.444 | 0.141 | 0.033 | 0.020 | 0.002 |

*(All values in m/s)*

### What Alpha Does (Intuitively)

- **Alpha < 1.0** (concave): Speed slider feels "responsive" — small slider movements give big velocity jumps. The slider's lower range produces higher speeds.
- **Alpha = 1.0** (linear): Speed slider maps linearly to velocity. 50% slider = 50% max velocity.
- **Alpha > 1.0** (convex): Speed slider feels "gradual" — you need to push the slider higher before velocity ramps up. Good for precision at lower speeds.
- **Alpha = 1.2** (default): Slight convex curve. At 50% speed you get 0.225 m/s (37.5% of max) instead of 0.267 m/s (44.4% linear). Subtle precision boost.

### Verdict

Alpha works correctly but is **imperceptible at 100% speed slider** because `1.0^alpha = 1.0` for all alpha. It becomes meaningful when the speed slider is below ~75%. At the default `strafeAlpha = 1.2`, the effect is subtle — consider higher values (2.0+) if you want a more pronounced precision zone at lower speeds.

## The 1.0 m/s Hardware Limit

### Investigation Results

The strafe velocity limit is **NOT** in official Unitree Go2 specifications:

- Official specs document forward speed (2.5–5.0 m/s depending on model variant)
- No lateral/strafe velocity limit is mentioned anywhere in Unitree documentation
- The WirelessController interface uses normalized values (-1 to 1) — the firmware applies its own internal limits

### Where 1.0 Is Enforced

| Location | File | Value |
|---|---|---|
| Frontend hardware limit | `curve-utils.js` | `HARDWARE_LIMITS.strafe = 1.0` |
| Backend hardware limit | `control.py` | `HARDWARE_LIMIT_STRAFE = 1.0` |
| Default settings | `keyboard-mouse-control.js` | `maxStrafe: 1.0` |
| Normal preset slider | `settings-manager.js` | `kb_max_strafe_velocity: 0.6` |
| Sport preset slider | `settings-manager.js` | `kb_max_strafe_velocity: 1.0` |
| Backend safety clamp | `control.py` | `vy = clamp(vy, -max_strafe, max_strafe)` |

### Origin

The original conservative limit was 0.6 m/s, chosen empirically. After testing showed the Go2 handles higher lateral velocities on flat ground, the hardware limit was raised to 1.0 m/s. Presets now offer a range from 0.5 m/s (beginner) to 1.0 m/s (sport).

### Notes

- The Go2's lateral stability is lower than its forward stability (quadrupeds are naturally more stable in the sagittal plane)
- Higher lateral velocities may cause stumbling on uneven terrain
- The WirelessController accepts any value in [-1, 1], and the firmware applies its own internal limits


## The Deceleration Problem & Fix

### The Problem

When `strafe_ramp_time = 2.0s`, the robot takes ~2 seconds to stop after releasing the strafe key. Users expect **instant stop** on key release (FPS game convention).

### Root Cause: Symmetric Slew Rate Limiter

The backend slew rate limiter **previously** used the same acceleration limit for both speeding up and slowing down:

```python
# OLD CODE (symmetric — same rate for accel and decel)
delta_vy = raw_target_vy - self.current_vy
max_step_vy = MAX_STRAFE_ACCEL * dt
safe_delta_vy = clamp(delta_vy, -max_step_vy, +max_step_vy)
self.current_vy += safe_delta_vy
```

With `strafe_ramp_time = 2.0s`:
- `MAX_STRAFE_ACCEL = 0.6 / 2.0 = 0.3 m/s²`
- At 30Hz polling: `max_step = 0.3 × 0.033 = 0.0099 m/s per frame`
- To decelerate from 0.6 → 0: `0.6 / 0.0099 ≈ 60 frames = 2.0 seconds`

The backend couldn't decelerate any faster than it accelerated, even though the frontend was sending rapidly decaying target values.

### The Fix: Asymmetric Ramping

The slew rate limiter now uses **asymmetric ramping** — slow acceleration, instant deceleration:

```python
# NEW CODE (asymmetric — instant decel, ramped accel)
if abs(raw_target_vy) < abs(self.current_vy):
    # Decelerating (target closer to zero): instant response
    self.current_vy = raw_target_vy
else:
    # Accelerating (target further from zero): apply slew rate limiter
    delta_vy = raw_target_vy - self.current_vy
    max_step_vy = MAX_STRAFE_ACCEL * dt
    self.current_vy += clamp(delta_vy, -max_step_vy, +max_step_vy)
```

**Detection logic:** When `|target| < |current|`, the velocity magnitude is decreasing (moving toward zero). In this case, bypass the limiter and follow the frontend's target directly.

This fix is applied to **all three movement axes** (linear, strafe, rotation) for consistent behavior.

### Result

| Scenario | Before (symmetric) | After (asymmetric) |
|---|---|---|
| Key release at `ramp_time = 0.2s` | ~0.2s to stop | ~0.3s (frontend decay) |
| Key release at `ramp_time = 2.0s` | **~2.0s to stop** | **~0.3s (frontend decay)** |
| Key press at `ramp_time = 2.0s` | ~2.0s to max speed | ~2.0s to max speed (unchanged) |

After the fix, deceleration time is determined by the **frontend's exponential decay** (`deceleration = 0.2`, reaching 10% in ~10 frames / 0.33s), regardless of the `ramp_time` setting. The `ramp_time` setting now only controls acceleration.

## Smoothing Architecture (Option B: Direct Assignment)

> **Update:** Frontend smoothing (Layer 1) was **removed** for keyboard axes (linear, strafe).
> The backend's asymmetric slew rate limiter is now the **sole** smoothing layer.

### Why Frontend Smoothing Was Removed

The original system had **two layers of smoothing** that fought each other:

| Layer | What it did | Time constant | Problem |
|---|---|---|---|
| ~~Frontend~~ | `current += (target - current) × 0.05` | **~2.0s** to 95% | Hard-coded, not tunable |
| Backend | Slew rate limiter (`strafe_ramp_time`) | **Tunable** (0.1s–2.0s) | Never got a chance to limit |

The frontend's `ACCEL_FACTOR = 0.05` was a **2-second anchor** — it slowly ramped the signal before the backend ever saw it. Setting `strafe_ramp_time = 0.1s` in the UI had no effect because the frontend was already throttling the signal to ~2.0s.

Users compensated by setting `alpha = 0.1` (logarithmic curve) to force the output to hit max speed immediately, fighting the lag. This made alpha feel broken.

### Current Architecture: Single Layer

```
Key Press → Exponential Curve → Direct Assignment → WebSocket → Backend Slew Rate Limiter → Robot
                                (no frontend ramp)              (sole smoothing layer)
```

The frontend now sends the **raw curve output** directly to the backend. The backend's asymmetric slew rate limiter handles all physics:
- **Acceleration:** Smooth ramp controlled by `strafe_ramp_time` setting (actually works now!)
- **Deceleration:** Instant (FPS convention)

### Backend Slew Rate Limiter (The Only Smoother)

```python
MAX_STRAFE_ACCEL = max_strafe / strafe_ramp_time    # 0.6 / 0.2 = 3.0 m/s²
max_step = MAX_STRAFE_ACCEL × dt                     # 3.0 × 0.033 = 0.099 m/s/frame
```

At `strafe_ramp_time = 0.2s`: full ramp in ~6 frames (0.2s). At `0.1s`: ~3 frames (0.1s). At `0.05s`: nearly instant.

### Removed Components

- **`ACCEL_FACTOR`** (was 0.05): Frontend exponential ramping constant — removed
- **`MIN_START_SPEED`** (was 0.15): Jump-start logic — no longer needed since there's no slow ramp to overcome
- **`deceleration`** (was 0.2): Frontend decay rate — removed (backend handles instant decel)
- **Jump-start logic**: Was a workaround for the slow frontend ramp + deadzone conflict. With direct assignment, key press → immediate full target velocity → backend ramps smoothly

## Tuning Guide

| Parameter | UI Location | Effect | Recommendation |
|---|---|---|---|
| **Speed Slider** | Main control bar | Primary input to the curve. Determines strafe velocity. | 100% for open areas, lower for precision |
| **Strafe Alpha** | Settings → Strafe | Shapes how speed slider maps to velocity. Higher = more precision at low speeds. | 1.0 default (linear). Try 1.2+ for a gentle precision curve |
| **Max Strafe** | Settings → Strafe | Hard velocity cap (m/s). Range: 0.1–1.0. | Normal: 0.6. Sport: 1.0 (hardware limit) |
| **Strafe Ramp Time** | Settings → Strafe | Backend acceleration time (seconds). Only affects ramp-up, not stop. | 0.20s default. Range: 0.01–0.50s |

### Preset Comparison

| Setting | Beginner | Normal | Advanced | Sport |
|---|---|---|---|---|
| `strafe_alpha` | 1.2 | 1.0 | 0.9 | 0.8 |
| `max_strafe` | 0.5 m/s | 0.6 m/s | 0.9 m/s | 1.0 m/s |
| `strafe_ramp_time` | 0.40s | 0.20s | 0.10s | 0.05s |
| **Feel** | Gentle, safe | Linear, balanced | Responsive, fast | Aggressive, instant |

## Comparison with Mouse Rotation

| Aspect | Strafe (keyboard) | Rotation (mouse) |
|---|---|---|
| **Input type** | Digital (0 or 1) | Analog (unbounded pixels) |
| **Uses `applyCurve()`** | Yes | No (bypassed) |
| **Alpha parameter** | Active (shapes speed slider) | Not used |
| **Frontend smoothing** | Exponential ramp + decay | Instant (no momentum) |
| **Backend smoothing** | Asymmetric slew rate limiter | Asymmetric slew rate limiter |
| **Speed slider role** | Curve input (0→1) | Sensitivity scalar + ceiling |
| **Max velocity** | 1.0 m/s | 3.0 rad/s |

The fundamental difference: keyboard is digital (the curve shapes the speed slider), while mouse is analog (the curve was bypassed because [0,1] clamping destroyed dynamic range).

## Max Velocity Slider Bug & Fix

### The Bug

The max velocity sliders (e.g., `kb_max_strafe_velocity`) had **no effect** on actual robot speed. Setting the slider to minimum still resulted in full-speed movement.

### Root Cause: Re-normalization Cancellation

The backend pipeline had a round-trip that perfectly cancelled the slider value:

```
Frontend: curvedStrafe = 0.6 m/s → lx = -0.6 / 0.6 = -1.0   (normalize by slider)
Backend:  raw_target_vy = 1.0 × 0.6 = 0.6                     (de-normalize by slider)
Backend:  lx_norm = -0.6 / 0.6 = -1.0                          (re-normalize by slider) ← BUG
Robot:    receives lx = -1.0 → full speed, regardless of slider
```

The re-normalization step (Step 10) divided by `max_strafe` — the same value used to de-normalize. The slider effect was multiplied in and then divided back out, resulting in `lx = ±1.0` always.

### The Fix: Re-normalize by Hardware Limits

The fix changes re-normalization to divide by the **hardware limit** (the robot's physical maximum) instead of the user's slider value:

```python
# BEFORE (bug): slider cancels out
lx_norm = -vy / max_strafe           # max_strafe = slider value (e.g., 0.6)

# AFTER (fix): slider effect preserved
lx_norm = -vy / HARDWARE_LIMIT_STRAFE  # HARDWARE_LIMIT_STRAFE = 1.0 (constant)
```

### Verification

| Slider Value | Hardware Limit | Robot Receives | Result |
|---|---|---|---|
| 0.5 m/s | 1.0 m/s | `lx = 0.50` | 50% speed ✅ |
| 0.6 m/s | 1.0 m/s | `lx = 0.60` | 60% speed ✅ |
| 1.0 m/s | 1.0 m/s | `lx = 1.00` | Full speed ✅ |

Hardware limit constants are defined in:
- Frontend: `HARDWARE_LIMITS` in `static/js/curve-utils.js`
- Backend: `self.HARDWARE_LIMIT_STRAFE` in `app/services/control.py`

These must always stay in sync.

## Files

- `static/js/keyboard-mouse-control.js` — Strafe input, curve application, direct assignment (lines ~513-533 in `poll()`)
- `static/js/curve-utils.js` — `applyCurve()` and `applyStrafeCurve()` functions, `HARDWARE_LIMITS.strafe`
- `static/js/settings-manager.js` — Preset definitions (`strafeAlpha`, `maxStrafe`, `strafeRampTime`)
- `app/services/control.py` — Backend asymmetric slew rate limiter, hardware limit constants, WirelessController re-normalization