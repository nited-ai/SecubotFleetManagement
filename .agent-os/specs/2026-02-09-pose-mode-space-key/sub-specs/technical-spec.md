# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2026-02-09-pose-mode-space-key/spec.md

> Created: 2026-02-09
> Version: 2.0.0 (Updated based on empirical hardware testing)

## API Investigation: Pose Mode Approaches

### Option A: Pose API (1028) ✅ SELECTED (Empirically Verified)

The `SPORT_CMD["Pose"]` (API ID 1028) is a standalone command that toggles pose mode.

- **Pros:** Single API call, WirelessController automatically remaps axes in Pose mode
- **Cons:** Spring-back behavior on yaw (rx axis returns to center when input stops)
- **Status:** ✅ Tested on hardware — enters Pose mode, WirelessController controls work
- **Exit:** RecoveryStand (1006) is the ONLY command that reliably exits Pose mode

**Empirical Test Results (2026-02-09):**
- Pose (1028): Response code 0 (success) — confirmed enters Pose mode via official app
- WirelessController in Pose mode: A/D (lx) = roll, W/S (ly) = height, Mouse X (rx) = yaw, ry = pitch
- RecoveryStand (1006): ✅ Only exit command that restores FreeWalk movement

### Option B: BalanceStand (1002) + Euler (1007) ❌ REJECTED

- **Reason:** Euler API (1007) returns response code 3202 (rejected) when in Pose mode
- **Also rejected:** BodyHeight (1013) returns code 3203 in AI/FreeWalk mode
- **Also rejected:** FreeWalk (1045) returns code 3203 after toggling Pose off

### Exit Command Testing Results

| Command | API ID | Result | Movement Restored? |
|---------|--------|--------|-------------------|
| RecoveryStand | 1006 | ✅ Success | ✅ Yes |
| BalanceStand | 1002 | ❌ Failed | No |
| StandUp | 1004 | ❌ Failed | No |
| Move | 1008 | ❌ Failed | No |
| SwitchGait | 1011 | ❌ Failed | No |
| Full re-init (BalanceStand + Motion Switcher + FreeWalk) | Multiple | ❌ Failed | No |

## Technical Requirements

### State Management

1. **New state property:** `pose_mode_active` (boolean) in StateService - tracks whether Pose Mode is active
2. **Frontend state:** `this.poseMode` flag in KeyboardMouseControl class
3. No Euler angle accumulation needed — WirelessController handles it natively

### Frontend Changes (keyboard-mouse-control.js)

1. **SPACE key handling:** Change from triggering `emergency_stop` to hold-to-activate Pose Mode
   - `keydown` (SPACE): Set `this.poseMode = true`, send `enter_pose_mode` action
   - `keyup` (SPACE): Set `this.poseMode = false`, send `exit_pose_mode` action
   - Guard against `keydown` repeat events (held keys fire repeated keydown events)

2. **Poll loop:** No modification needed in Pose Mode — same WirelessController commands work
   - The robot automatically remaps axes when in Pose mode (1028)
   - lx (A/D) → roll, ly (W/S) → height, rx (mouse X) → yaw, ry (mouse Y) → pitch

3. **Emergency stop relocation:** Move from SPACE to ESC key

### Backend Changes (control.py)

1. **New action: `enter_pose_mode`**
   - Stop all movement (send zero velocity via WirelessController)
   - Wait 200ms for movement to stop
   - Send Pose (1028) to enter Pose mode
   - Set `state.pose_mode_active = True`

2. **New action: `exit_pose_mode`**
   - Send RecoveryStand (1006) — only command that works
   - Wait 1s for robot to stabilize
   - Set `state.pose_mode_active = False`

3. **Modified: `send_movement_command()`**
   - When `state.pose_mode_active` is True: send actual `ry` value (pitch)
   - When `state.pose_mode_active` is False: send `ry = 0.0` (existing behavior)

### No Backend Changes Needed (ws.py)

No new WebSocket events needed — existing `control_command` handles all movement.

## State Transition Diagram

```
  [AI Mode (Normal)]
        |
        | SPACE keydown
        v
  [Entering Pose Mode]
   - Stop movement (zero velocity)
   - Wait 200ms
   - Pose API (1028)
   - state.pose_mode_active = True
        |
        v
  [Pose Mode Active]
   - Mouse X (rx) → yaw (spring-back)
   - Mouse Y (ry) → pitch (now sent to robot)
   - A/D (lx) → roll
   - W/S (ly) → body height
   - Same WirelessController topic
        |
        | SPACE keyup
        v
  [Exiting Pose Mode]
   - RecoveryStand (1006)
   - Wait 1s
   - state.pose_mode_active = False
        |
        v
  [AI Mode (Restored)]
   - WASD + mouse working normally
```

## WirelessController Axis Mapping

| Axis | Normal Mode (AI/FreeWalk) | Pose Mode (1028) |
|------|--------------------------|-------------------|
| lx   | Strafe (left/right)      | Roll              |
| ly   | Forward/back             | Body height       |
| rx   | Yaw rotation velocity    | Yaw (spring-back) |
| ry   | ~~unused (hardcoded 0)~~ | Pitch             |

## External Dependencies

No new external dependencies. All functionality uses existing:
- **unitree_webrtc_connect SDK** — Pose API (1028), RecoveryStand (1006)
- **Frontend JavaScript** — Existing KeyboardMouseControl class modifications only

## Critical Design Decisions

### 1. WirelessController Instead of Euler API

Empirical testing showed that the WirelessController axes are automatically remapped in Pose mode.
No separate Euler API calls are needed. This is simpler, lower latency, and doesn't require
a new WebSocket event. The existing `control_command` flow works unchanged.

### 2. RecoveryStand as Only Exit Command

Extensive testing of 6+ exit approaches showed RecoveryStand (1006) is the ONLY command that
reliably restores FreeWalk movement after Pose mode. No Motion Switcher or FreeWalk commands needed.

### 3. Emergency Stop Relocation

SPACE → Pose Mode (hold), ESC → Emergency Stop. ESC also exits pointer lock,
making it a natural "stop everything" button.
