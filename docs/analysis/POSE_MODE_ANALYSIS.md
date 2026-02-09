# Pose Mode (SPACE Key Hold) — How It Works

> **Status:** Implemented and tested
> **Files:** `static/js/keyboard-mouse-control.js` (Pose Mode section in `poll()`), `app/services/control.py`
> **Approach:** Mixed position/velocity control via WirelessController axis remapping

## Overview

Pose Mode allows the user to control the robot's body orientation (yaw, pitch, roll, height) without moving the robot's legs. It is activated by **holding the SPACE key** and deactivated by releasing it.

The robot enters Pose Mode via **Sport API 1028** (Pose) and exits via **Sport API 1006** (RecoveryStand). While in Pose Mode, the WirelessController axes are remapped from velocity to position control:

| Axis | Normal AI Mode | Pose Mode |
|------|---------------|-----------|
| `lx` | Strafe velocity (m/s) | Roll position (spring-back) |
| `ly` | Forward velocity (m/s) | Height position (spring-back) |
| `rx` | Yaw velocity (rad/s) | Yaw position (accumulated) |
| `ry` | Pitch — disabled (0.0) | Pitch position (accumulated) |

## Input Handling: Two Control Styles

### Mouse (Yaw/Pitch) — Accumulated Position
Mouse movement **accumulates** into `poseAngles.yaw` and `poseAngles.pitch`. When the mouse stops, the accumulated value persists and the robot **holds its orientation**. This prevents the spring-back behavior of the physical joystick.

```
poseAngles.yaw   += mouseMovement.x × POSE_MOUSE_SENSITIVITY × speedMultiplier
poseAngles.pitch += -mouseMovement.y × POSE_MOUSE_SENSITIVITY × speedMultiplier
```

Both values are clamped to [-1, 1] (joystick position limits).

### WASD Keys (Roll/Height) — Velocity (Spring-Back)
A/D and W/S keys produce **instantaneous velocity values** that return to 0 when keys are released. This matches the physical joystick's spring-centered behavior — the robot tilts while the key is held and returns to neutral when released.

```
roll   = (D pressed ? +POSE_KEY_RATE : 0) + (A pressed ? -POSE_KEY_RATE : 0)
height = (W pressed ? +POSE_KEY_RATE : 0) + (S pressed ? -POSE_KEY_RATE : 0)
```

**Why the difference?** Mouse yaw/pitch needs to hold position for precise aiming (like an FPS camera). Roll/height are coarse adjustments where spring-back to neutral is the expected behavior (like tilting a joystick).

## Speed Slider Effect

The speed slider (`speedPercentage / 100`) scales mouse sensitivity in Pose Mode:

```
effectiveSensitivity = POSE_MOUSE_SENSITIVITY × speedMultiplier
```

| Speed Slider | speedMultiplier | Effect |
|-------------|----------------|--------|
| 100% | 1.0 | Full mouse sensitivity |
| 50% | 0.5 | Half sensitivity — more precise |
| 10% | 0.1 | Very precise micro-adjustments |

WASD key rate (`POSE_KEY_RATE`) is **not** affected by the speed slider — it's a fixed velocity value.

## Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│ FRONTEND  (keyboard-mouse-control.js :: poll())                         │
│                                                                         │
│  Step 1: SPACE keydown → Enter Pose Mode                               │
│  ────────────────────────────────────────                               │
│  Sets this.poseMode = true                                              │
│  Sends 'enter_pose_mode' action via HTTP POST /api/control/action       │
│  Updates HUD icon: running human → standing human (green)               │
│                                                                         │
│  Step 2: Poll (every 33ms / 30Hz) — Pose Mode Branch                  │
│  ──────────────────────────────────────────────────                     │
│  Requires pointer lock (returns early if not locked)                    │
│                                                                         │
│  Mouse: Accumulate deltas into poseAngles.yaw / .pitch                 │
│    poseAngles.yaw   += movementX × POSE_MOUSE_SENSITIVITY × speedMult  │
│    poseAngles.pitch += -movementY × POSE_MOUSE_SENSITIVITY × speedMult │
│    Clamp both to [-1, 1]                                                │
│                                                                         │
│  WASD: Instantaneous velocity (spring-back to 0)                       │
│    roll   = ±POSE_KEY_RATE (or 0 if no key pressed)                    │
│    height = ±POSE_KEY_RATE (or 0 if no key pressed)                    │
│                                                                         │
│  Step 3: Send Command via WebSocket                                    │
│  ──────────────────────────────────                                    │
│  { lx: roll, ly: height, rx: yaw, ry: pitch, pose_mode: true }        │
│                                                                         │
│  Step 4: SPACE keyup → Exit Pose Mode                                 │
│  ─────────────────────────────────────                                 │
│  Sets this.poseMode = false, resets poseAngles                          │
│  Sends 'exit_pose_mode' action via HTTP POST /api/control/action        │
│  Restores HUD icon: standing human → running human (teal)              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓  WebSocket (control_command event)
┌─────────────────────────────────────────────────────────────────────────┐
│ BACKEND  (app/services/control.py :: process_movement_command())        │
│                                                                         │
│  Step 5: Pose Mode Bypass                                              │
│  ────────────────────────                                              │
│  Detects pose_mode flag in data (or state.pose_mode_active)             │
│  BYPASSES entire velocity pipeline:                                     │
│    - No slew rate limiter                                               │
│    - No hardware limit re-normalization                                 │
│    - No axis inversions                                                 │
│  Clamps lx/ly/rx/ry to [-1, 1] and passes directly to robot            │
│                                                                         │
│  Step 6: WirelessController Publish                                    │
│  ──────────────────────────────                                        │
│  send_movement_command_sync(lx, ly, rx, ry)                             │
│  → publish to "rt/wirelesscontroller":                                  │
│    {"lx": roll, "ly": height, "rx": yaw, "ry": pitch, "keys": 0}      │
│  Note: ry is passed through (not zeroed) when pose_mode_active          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓  WebRTC DataChannel
┌─────────────────────────────────────────────────────────────────────────┐
│ ROBOT  (Unitree Go2 — Pose Mode 1028 active)                           │
│                                                                         │
│  WirelessController axes interpreted as POSITION (not velocity):        │
│    lx → Roll angle                                                      │
│    ly → Body height                                                     │
│    rx → Yaw angle                                                       │
│    ry → Pitch angle                                                     │
│  Robot holds the position as long as values are sent continuously.      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```



## Entry/Exit Sequences

### Entry: SPACE Keydown
1. Frontend sets `this.poseMode = true`
2. Frontend sends `POST /api/control/action` with `{"action": "enter_pose_mode"}`
3. Backend stops all movement (sends zero velocity)
4. Backend waits 200ms for robot to settle
5. Backend sends Sport API 1028 (Pose) — this is a **toggle** command
6. Backend sets `state.pose_mode_active = True`
7. Frontend updates HUD icon to standing human (green)

### Exit: SPACE Keyup
1. Frontend sets `this.poseMode = false`, resets `poseAngles`
2. Frontend sends `POST /api/control/action` with `{"action": "exit_pose_mode"}`
3. Backend sends Sport API 1006 (RecoveryStand)
4. Backend waits 1.0s for robot to stabilize
5. Backend sets `state.pose_mode_active = False`
6. Frontend restores HUD icon to running human (teal)
7. Robot returns to FreeWalk/AI mode — normal WASD movement works again

### Emergency Exit: ESC Key
1. Sends `emergency_stop` action first
2. If in Pose Mode, also sends `exit_pose_mode` action
3. Resets all Pose Mode state

## Empirical API Test Results

These findings were discovered through hardware testing and informed the implementation:

| API | ID | Result | Notes |
|-----|-----|--------|-------|
| **Pose** | 1028 | ✅ Code 0 (success) | Toggle command. Enters pose mode confirmed via app. |
| **RecoveryStand** | 1006 | ✅ Code 0 (success) | **Only** working exit command. Restores FreeWalk. |
| **Euler** | 1007 | ❌ Code 3202 (rejected) | Does NOT work in Pose mode. |
| **BodyHeight** | 1013 | ❌ Code 3203 (rejected) | Does NOT work in AI/FreeWalk mode. |
| **FreeWalk** | 1045 | ❌ Code 3203 (rejected) | Does NOT restore movement after Pose toggle. |
| **BalanceStand** | 1002 | ❌ No effect | Does not exit Pose mode. |
| **StandUp** | 1004 | ❌ No effect | Does not exit Pose mode. |
| **Move** | 1008 | ❌ No effect | Does not restore movement. |
| **SwitchGait** | 1011 | ❌ No effect | Does not restore movement. |

**Key insight:** The Euler API (1007) is rejected in Pose mode, but the WirelessController natively handles all orientation control. No additional APIs are needed beyond Pose (1028) for entry and RecoveryStand (1006) for exit.

## Constants

| Constant | Value | Location | Description |
|----------|-------|----------|-------------|
| `POSE_MOUSE_SENSITIVITY` | 0.003 | `keyboard-mouse-control.js` | Base sensitivity per raw pixel (scaled by speed slider) |
| `POSE_KEY_RATE` | 0.5 | `keyboard-mouse-control.js` | WASD velocity value per poll tick |
| `SPORT_CMD["Pose"]` | 1028 | `unitree_webrtc_connect/constants.py` | Sport API ID for Pose mode toggle |
| `SPORT_CMD["RecoveryStand"]` | 1006 | `unitree_webrtc_connect/constants.py` | Sport API ID for recovery stand (exit) |

## Pointer Lock Requirement

Both Pose Mode and Normal AI Mode require **pointer lock** to be active before any movement commands are sent. This prevents accidental robot movement when the user is interacting with UI elements outside the video feed.

- Pointer lock is acquired by clicking on the video feed
- Released by pressing ESC or clicking outside
- The `poll()` method returns early if `this.pointerLocked === false`

## Files

- `static/js/keyboard-mouse-control.js` — Pose Mode input handling, angle accumulation, HUD indicator
- `app/services/control.py` — Pose Mode bypass in `process_movement_command()`, enter/exit actions
- `app/services/state.py` — `pose_mode_active` property
- `templates/control.html` — HUD icon (shared with RAGE MODE toggle)
- `unitree_webrtc_connect/constants.py` — Sport API command IDs