# Mouse Rotation (Yaw) — How It Works

> **Status:** Implemented and tested
> **File:** `static/js/keyboard-mouse-control.js` (rotation section in `poll()`, lines ~534-563)
> **Approach:** Direct Linear Mapping with Instant Stop (FPS "Call of Duty" style)

## Overview

Mouse rotation (yaw) converts horizontal mouse movement into robot turning velocity. The system uses **direct linear mapping** — mouse pixels translate proportionally to rotation speed in rad/s, with no exponential curves or normalization. When the mouse stops, rotation stops instantly.

This approach **bypasses** the `applyCurve()` function used by keyboard/gamepad controls. Mouse input is fundamentally different from gamepad joysticks (unbounded deltas vs. fixed 0-1 range), so it needs its own pipeline.

## Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│ FRONTEND  (keyboard-mouse-control.js)                                   │
│                                                                         │
│  Step 1: Mouse Hardware → Accumulated Pixels                            │
│  ─────────────────────────────────────────────                          │
│  Browser fires 'mousemove' events (60-1000Hz depending on mouse/OS).    │
│  handleMouseMove() accumulates movementX into this.mouseMovement.x.     │
│  Multiple events may fire between polls.                                │
│                                                                         │
│  Step 2: Poll (every 33ms / 30Hz) → Raw Rotation Value                 │
│  ──────────────────────────────────────────────────                     │
│  rotation = mouseMovement.x × MOUSE_SCALE_FACTOR (0.01)                │
│  mouseMovement.x = 0  (reset after reading)                            │
│                                                                         │
│  Step 3: Speed Slider Applied                                           │
│  ────────────────────────────                                           │
│  speedMultiplier = speedPercentage / 100   (0.0 to 1.0)                │
│  rotation *= speedMultiplier                                            │
│                                                                         │
│  Step 4: Direct Linear Mapping → Target Velocity (rad/s)               │
│  ────────────────────────────────────────────────────────               │
│  targetRadPerSec = rotation × mouseSensitivity × maxRotation            │
│                                                                         │
│  Step 5: Safety Ceiling Clamp                                           │
│  ────────────────────────────                                           │
│  safetyCeiling = maxRotation × speedMultiplier                          │
│  targetRadPerSec = clamp(targetRadPerSec, -safetyCeiling, safetyCeiling)│
│                                                                         │
│  Step 6: Deadzone + Instant Assignment                                  │
│  ─────────────────────────────────────                                  │
│  if |targetRadPerSec| > 0.05 → currentVelocities.rotation = target     │
│  else → currentVelocities.rotation = 0  (instant stop)                 │
│                                                                         │
│  Step 7: Inversion + Normalization → WebSocket                         │
│  ─────────────────────────────────────────────                          │
│  vyaw = -currentVelocities.rotation   (invert for backend convention)   │
│  rx = -vyaw / maxRotation              (normalize to [-1, 1])           │
│  Send {rx, max_rotation, rotation_ramp_time, ...} via WebSocket         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓  WebSocket
┌─────────────────────────────────────────────────────────────────────────┐
│ BACKEND  (app/services/control.py)                                      │
│                                                                         │
│  Step 8: De-normalize → Physical Velocity                               │
│  ────────────────────────────────────────                               │
│  raw_target_vyaw = -rx × max_rotation   (back to rad/s)                │
│                                                                         │
│  Step 9: Slew Rate Limiter                                              │
│  ────────────────────────────                                           │
│  MAX_YAW_ACCEL = max_rotation / rotation_ramp_time                      │
│  max_step = MAX_YAW_ACCEL × dt                                          │
│  delta = raw_target - current_vyaw                                      │
│  current_vyaw += clamp(delta, -max_step, +max_step)                     │
│                                                                         │
│  Step 10: Final Safety Clamp                                            │
│  ───────────────────────────                                            │
│  vyaw = clamp(current_vyaw, -max_rotation, +max_rotation)               │
│                                                                         │
│  Step 11: Re-normalize → Robot                                          │
│  ─────────────────────────────                                          │
│  rx_norm = clamp(-vyaw / max_rotation, -1.0, 1.0)                      │
│  Publish to WirelessController topic: {"rx": rx_norm, ...}              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## The Formula

The full end-to-end formula from mouse pixels to target velocity:

```
targetRadPerSec = rawPixels × MOUSE_SCALE_FACTOR × speedMultiplier × mouseSensitivity × maxRotation
```

| Variable | Source | Default | Description |
|---|---|---|---|
| `rawPixels` | Browser `movementX` | varies | Accumulated horizontal mouse pixels since last poll |
| `MOUSE_SCALE_FACTOR` | Hardcoded constant | 0.01 | Converts pixels to a manageable base unit |
| `speedMultiplier` | Speed slider (0-100%) | 1.0 | `speedPercentage / 100` |
| `mouseSensitivity` | Settings panel slider | 5.0 | User-adjustable sensitivity multiplier |
| `maxRotation` | Settings panel | 3.0 rad/s | Physical maximum rotation velocity |

**Safety ceiling** prevents exceeding the physical limit:
```
safetyCeiling = maxRotation × speedMultiplier
output = clamp(targetRadPerSec, -safetyCeiling, +safetyCeiling)
```

### Example Calculations

**Default settings** (sensitivity=5.0, maxRotation=3.0, speed=100%):
| Mouse px/poll | Target (rad/s) | After Ceiling | Feel |
|---|---|---|---|
| 2px | 0.30 | 0.30 | Gentle nudge |
| 5px | 0.75 | 0.75 | Precise adjustment |
| 10px | 1.50 | 1.50 | Steady turn |
| 20px | 3.00 | 3.00 | Max speed |
| 50px | 7.50 | **3.00** | Capped at ceiling |

**At 25% speed** (sensitivity=5.0, maxRotation=3.0, speed=25%):
| Mouse px/poll | Target (rad/s) | After Ceiling | Feel |
|---|---|---|---|
| 2px | 0.075 | 0.075 | Very gentle |
| 10px | 0.375 | 0.375 | Precise |
| 20px | 0.75 | **0.75** | Capped at 25% ceiling |

## Speed Slider = "Global Volume Knob"

The speed slider has a **dual effect** on mouse rotation:

1. **Reduces sensitivity (slope)**: `rotation *= speedMultiplier` — mouse must move further for the same speed
2. **Reduces ceiling (max speed)**: `safetyCeiling = maxRotation × speedMultiplier` — even fast flicks hit a lower limit

This means:
- **At 100% speed:** Full sensitivity, full max velocity. Fast mouse = fast turning.
- **At 10% speed:** 10× less sensitive AND max rotation capped at 10% of maxRotation. Perfect for precision docking or tight spaces.

The speed slider acts like a volume knob on a stereo — it scales everything down proportionally.

## Instant Stop (No Momentum)

When the mouse stops moving, `mouseMovement.x` is zero at the next poll. This produces `rotation = 0`, which produces `targetRadPerSec = 0`, which falls below the 0.05 deadzone threshold and sets `currentVelocities.rotation = 0` instantly.

**Why no momentum/decay?**
- FPS games (Call of Duty, CS:GO) use instant stop — players expect the camera to stop when the mouse stops
- The **backend slew rate limiter** already provides physical smoothing to protect the robot from abrupt velocity changes
- Adding frontend momentum would feel "floaty" and imprecise for a robot controller

## Backend Slew Rate Limiter

The frontend sends crisp velocity targets (0 → max instantly). The backend smooths these for the physical robot:

```python
MAX_YAW_ACCEL = max_rotation / rotation_ramp_time   # e.g., 3.0 / 0.9 = 3.33 rad/s²
max_step = MAX_YAW_ACCEL × dt                        # e.g., 3.33 × 0.033 = 0.11 rad/s per tick
current_vyaw += clamp(delta, -max_step, +max_step)
```

With default `rotation_ramp_time = 0.9s`, the robot takes ~0.9 seconds to ramp from 0 to max rotation. This prevents mechanical jerk without making the mouse feel sluggish — the frontend stays instant, the robot accelerates smoothly.

## Tuning Guide

| Parameter | UI Location | Effect | Recommendation |
|---|---|---|---|
| **Mouse Sensitivity** | Settings → Rotation | Multiplier on mouse input. Higher = faster turns per pixel. | Start at 5.0, increase if turns feel too slow |
| **Max Rotation** | Settings → Rotation | Hard physical limit (rad/s). | Default 3.0 is safe. Up to 9.0 for aggressive turning |
| **Speed Slider** | Main control bar | Global volume knob (sensitivity + ceiling). | 100% for open areas, 20-50% for precision |
| **Rotation Ramp Time** | Settings → Rotation | Backend acceleration time (seconds). | 0.9s default. Lower for snappier, higher for smoother |

## Why Not Use applyCurve()?

The `applyCurve()` function in `curve-utils.js` was designed for **gamepad joystick input** (always 0.0 to 1.0). It hard-clamps input to [0, 1] before applying the exponential curve. This is correct for gamepads but destructive for mouse deltas:

- A gamepad joystick maxes out at 1.0 — the clamp is a no-op
- Mouse deltas are **unbounded** — a fast flick can produce 200+ pixels per poll
- After `× 0.01`, a 200px flick = 2.0, which gets clamped to 1.0 — identical to a 100px movement

Additionally, the exponential curve (`x^alpha`) crushes small mouse movements when alpha > 1.0 (e.g., `0.15^2.5 = 0.003`), making slow precision movements nearly impossible.

By bypassing `applyCurve()` for mouse rotation:
- Fast flicks produce proportionally faster rotation (no [0,1] clamp destroying dynamic range)
- Small movements produce small, usable rotation (no exponential suppression)
- The `rotationAlpha` and `rotationDeadzone` settings have no effect on mouse rotation (they still apply to keyboard/gamepad)

## Files

- `static/js/keyboard-mouse-control.js` — Mouse rotation implementation (lines ~534-563 in `poll()`)
- `static/js/curve-utils.js` — Exponential curve functions (still used for keyboard/gamepad, **not** for mouse rotation)
- `app/services/control.py` — Backend slew rate limiter and WirelessController normalization
