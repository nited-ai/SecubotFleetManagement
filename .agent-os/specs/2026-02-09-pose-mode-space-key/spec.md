# Spec Requirements Document

> Spec: Pose Mode (SPACE Key Hold)
> Created: 2026-02-09
> Status: Planning

## Overview

Implement a Pose Mode feature that allows users to control the robot's body orientation (yaw, pitch, roll) by holding the SPACE key, using mouse movement for yaw/pitch and A/D keys for roll. This enables precise body posture adjustments while the robot remains stationary, with reliable return to AI Mode when SPACE is released.

## User Stories

### Story 1: Pose Mode Activation

As a **robot operator**, I want to hold SPACE to enter Pose Mode so that I can adjust the robot's body orientation (yaw, pitch, roll) for camera positioning or visual inspection, and have the robot resume normal AI movement when I release SPACE.

**Workflow:**
1. User is in normal AI mode, controlling robot with WASD + mouse
2. User holds SPACE key → robot stops moving, enters Pose Mode
3. Mouse X controls yaw (left/right body rotation)
4. Mouse Y controls pitch (body tilt forward/back)
5. A/D keys control roll (body lean left/right)
6. User releases SPACE → robot exits Pose Mode, returns to AI Mode
7. WASD + mouse movement controls resume working normally

### Story 2: Reliable AI Mode Return

As a **robot operator**, I want the robot to reliably return to AI Mode after exiting Pose Mode, so that WASD movement and yaw control continue working without needing to restart the connection.

**Workflow:**
1. User releases SPACE key to exit Pose Mode
2. System sends BalanceStand command to reset pose
3. System uses Motion Switcher API to switch back to AI mode
4. System waits for mode switch to stabilize (5-10 seconds)
5. System sends FreeWalk command to re-enter Agile Mode
6. WASD + mouse controls resume normal operation

## Spec Scope

1. **SPACE Key Hold Detection** - Detect SPACE keydown/keyup events to enter/exit Pose Mode with hold-to-activate behavior
2. **Euler Angle Control** - Send Euler API (1007) commands with roll, pitch, yaw parameters from mouse + A/D input
3. **Mode Switching** - Reliable enter (BalanceStand → Euler) and exit (BalanceStand → Motion Switcher → AI → FreeWalk) sequences
4. **Input Remapping** - In Pose Mode: repurpose mouse X/Y for yaw/pitch, A/D for roll; suppress WASD movement
5. **Emergency Stop Relocation** - Move emergency_stop from SPACE to a different key binding (SPACE is now Pose Mode)

## Out of Scope

- Gamepad pose mode control (keyboard/mouse only for this phase)
- Pose Mode sensitivity settings UI (use reasonable defaults, defer settings to future phase)
- Saving/recalling specific poses
- Pose mode for Pose API (1028) - investigate but use BalanceStand + Euler approach
- Smooth transition animations between modes (use immediate switching)

## Expected Deliverable

1. **Holding SPACE enters Pose Mode** - Robot stops moving, mouse controls yaw/pitch, A/D controls roll via Euler API (1007)
2. **Releasing SPACE exits Pose Mode** - Robot reliably returns to AI Mode with working WASD + mouse movement controls
3. **Visual feedback** - HUD indicator shows when Pose Mode is active (e.g., "POSE MODE" text overlay)

## Spec Documentation

- Tasks: @.agent-os/specs/2026-02-09-pose-mode-space-key/tasks.md
- Technical Specification: @.agent-os/specs/2026-02-09-pose-mode-space-key/sub-specs/technical-spec.md
- API Specification: @.agent-os/specs/2026-02-09-pose-mode-space-key/sub-specs/api-spec.md
- Tests Specification: @.agent-os/specs/2026-02-09-pose-mode-space-key/sub-specs/tests.md

