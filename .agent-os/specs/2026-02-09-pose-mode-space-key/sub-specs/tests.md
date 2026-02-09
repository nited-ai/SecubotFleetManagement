# Tests Specification

This is the tests coverage details for the spec detailed in @.agent-os/specs/2026-02-09-pose-mode-space-key/spec.md

> Created: 2026-02-09
> Version: 1.0.0

## Test Coverage

### Unit Tests

**ControlService - Pose Mode Actions**
- `test_enter_pose_mode_sends_balance_stand` - Verify BalanceStand (1002) is sent when entering pose mode
- `test_enter_pose_mode_sets_state` - Verify `state.pose_mode_active` is set to True
- `test_enter_pose_mode_stops_movement` - Verify zero velocity is sent before entering pose mode
- `test_exit_pose_mode_resets_euler` - Verify Euler angles are reset to (0, 0, 0) on exit
- `test_exit_pose_mode_switches_to_ai` - Verify Motion Switcher API is called with "ai" parameter
- `test_exit_pose_mode_sends_freewalk` - Verify FreeWalk command is sent after AI mode switch
- `test_exit_pose_mode_clears_state` - Verify `state.pose_mode_active` is set to False

**ControlService - Euler Command**
- `test_send_euler_command_valid_angles` - Verify Euler API (1007) is sent with correct parameters
- `test_send_euler_command_clamps_angles` - Verify angles are clamped to safe ranges
- `test_send_euler_command_rejected_when_not_in_pose_mode` - Verify commands are rejected when pose mode inactive

**StateService - Pose Mode Properties**
- `test_pose_mode_active_default_false` - Verify initial state is False
- `test_pose_mode_active_set_get` - Verify property getter/setter works
- `test_pose_euler_angles_default_zero` - Verify initial angles are (0, 0, 0)
- `test_reset_control_state_clears_pose_mode` - Verify pose mode is reset when control state resets

### Integration Tests

**WebSocket - Pose Euler Update**
- `test_pose_euler_update_sends_to_robot` - Verify WebSocket event triggers Euler API command
- `test_pose_euler_update_rejected_when_inactive` - Verify updates are rejected when pose mode inactive
- `test_pose_euler_update_validates_ranges` - Verify out-of-range angles are clamped/rejected

**REST API - Pose Mode Actions**
- `test_action_enter_pose_mode` - Verify POST /api/control/action with enter_pose_mode works
- `test_action_exit_pose_mode` - Verify POST /api/control/action with exit_pose_mode works
- `test_action_enter_pose_mode_requires_connection` - Verify error when robot not connected

**End-to-End Flow**
- `test_full_pose_mode_cycle` - Enter pose mode → send Euler updates → exit → verify AI mode restored
- `test_pose_mode_suppresses_movement` - Verify WASD commands are not processed during pose mode
- `test_rapid_enter_exit` - Verify rapid SPACE press/release doesn't leave robot in inconsistent state

### Mocking Requirements

- **Robot Connection:** Mock `state.connection.datachannel.pub_sub.publish_request_new` for all robot API calls
- **Motion Switcher Response:** Mock response with `{'data': {'header': {'status': {'code': 0}}, 'data': '{"name": "ai"}'}}`
- **asyncio.sleep:** Mock to avoid actual delays in tests (5s wait in exit sequence)
- **Event Loop:** Mock `state.event_loop` for sync wrapper tests

### Frontend Tests (Manual Verification)

Since the frontend uses vanilla JavaScript without a test framework:
- **SPACE hold enters Pose Mode:** Visual indicator appears, WASD stops working
- **Mouse X controls yaw:** Robot body rotates left/right with mouse movement
- **Mouse Y controls pitch:** Robot body tilts forward/back with mouse movement
- **A/D controls roll:** Robot body leans left/right with A/D keys
- **SPACE release exits Pose Mode:** Indicator disappears, WASD + mouse movement resumes
- **Emergency stop on ESC:** ESC key triggers emergency stop (former SPACE behavior)
- **Repeat cycle:** Multiple enter/exit cycles work reliably without control degradation

