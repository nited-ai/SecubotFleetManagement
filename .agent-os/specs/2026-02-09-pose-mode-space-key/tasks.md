# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2026-02-09-pose-mode-space-key/spec.md

> Created: 2026-02-09
> Updated: 2026-02-09 (Simplified based on empirical hardware testing)
> Status: Implementation Complete

## Summary of Changes from Original Plan

The original plan used **BalanceStand (1002) + Euler API (1007)** for pose control
and **Motion Switcher + FreeWalk** for exit. Empirical testing revealed:

- **Euler API (1007)** is rejected in Pose mode (code 3202)
- **BodyHeight API (1013)** is rejected in AI mode (code 3203)
- **FreeWalk (1045)** is rejected after Pose toggle (code 3203)
- **WirelessController** axes are automatically remapped in Pose mode (1028):
  lx→roll, ly→height, rx→yaw, ry→pitch
- **RecoveryStand (1006)** is the ONLY command that exits Pose mode and restores movement

This means: **No Euler API, no new WebSocket events, no Motion Switcher needed.**
The existing `control_command` event and WirelessController handle everything.

## Tasks

- [x] 1. Backend: State Management for Pose Mode
  - [x] 1.1 Add `pose_mode_active` property to StateService (default: False)
  - [-] 1.2 ~~Add `pose_euler_angles` property~~ (Not needed - WirelessController handles it)
  - [x] 1.3 Update `reset_control_state()` to clear `_pose_mode_active`

- [x] 2. Backend: Pose Mode Enter/Exit Actions in ControlService
  - [x] 2.1 Implement `enter_pose_mode` action: stop movement → wait 200ms → Pose (1028)
  - [x] 2.2 Implement `exit_pose_mode` action: RecoveryStand (1006) → wait 1s
  - [x] 2.3 Add guard checks to prevent duplicate enter/exit calls

- [x] 3. Backend: Pass ry Through in Pose Mode
  - [x] 3.1 Modify `send_movement_command()`: send actual ry when pose_mode_active, else 0.0
  - [-] 3.2 ~~Euler angle command method~~ (Not needed - WirelessController handles it)
  - [-] 3.3 ~~WebSocket handler for Euler updates~~ (Not needed)

- [x] 4. Frontend: SPACE Key Hold Detection & Pose Mode State
  - [x] 4.1 Add `this.poseMode` flag to KeyboardMouseControl constructor
  - [x] 4.2 SPACE keydown → enter_pose_mode (with e.repeat guard)
  - [x] 4.3 SPACE keyup → exit_pose_mode
  - [x] 4.4 Relocate emergency_stop from SPACE to ESC key
  - [x] 4.5 ESC also exits Pose Mode if active
  - [-] 4.6 ~~Input remapping / Euler sending~~ (Not needed - WirelessController axes auto-remap)

- [x] 5. Frontend: Visual Feedback (HUD Indicator)
  - [x] 5.1 Add "🎯 POSE MODE" overlay element to control.html
  - [x] 5.2 Add `updatePoseModeIndicator()` method to show/hide overlay
  - [x] 5.3 Styled with teal border, backdrop blur, control hints

- [x] 6. Cleanup
  - [x] 6.1 Remove temporary test endpoint (POST /api/test/sport_command)
  - [x] 6.2 Update technical-spec.md with empirical findings
  - [x] 6.3 Update api-spec.md with simplified approach

- [ ] 7. End-to-End Testing & Verification
  - [ ] 7.1 Test full cycle: SPACE hold → pose controls → SPACE release → FreeWalk restored
  - [ ] 7.2 Verify pitch control (mouse Y / ry) works in Pose mode
  - [ ] 7.3 Test rapid SPACE press/release doesn't break mode switching
  - [ ] 7.4 Test ESC emergency stop works in both normal and Pose Mode
  - [ ] 7.5 Test multiple enter/exit cycles don't degrade controls
