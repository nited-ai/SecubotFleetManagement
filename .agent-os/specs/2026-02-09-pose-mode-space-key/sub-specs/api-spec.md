# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2026-02-09-pose-mode-space-key/spec.md

> Created: 2026-02-09
> Version: 2.0.0 (Updated based on empirical hardware testing)

## REST Endpoints

### POST /api/control/action

**Existing endpoint** - Two new actions added:

#### Action: `enter_pose_mode`

**Purpose:** Enter Pose Mode - stops movement, sends Pose API (1028)
**Request Body:**
```json
{ "action": "enter_pose_mode" }
```
**Backend Sequence:**
1. Send zero velocity via WirelessController (stop movement)
2. Wait 200ms
3. Send Pose (1028) via SPORT_MOD topic
4. Set `state.pose_mode_active = True`

**Response:**
```json
{ "status": "success", "action": "enter_pose_mode" }
```

#### Action: `exit_pose_mode`

**Purpose:** Exit Pose Mode - sends RecoveryStand (1006), restores FreeWalk
**Request Body:**
```json
{ "action": "exit_pose_mode" }
```
**Backend Sequence:**
1. Send RecoveryStand (1006) via SPORT_MOD topic
2. Wait 1 second (robot stabilization)
3. Set `state.pose_mode_active = False`

**Response:**
```json
{ "status": "success", "action": "exit_pose_mode" }
```

## WebSocket Events

No new WebSocket events needed. The existing `control_command` event handles all movement
in both Normal and Pose modes via WirelessController. The only change is that `ry` (pitch)
is passed through to the robot when `pose_mode_active` is True.

### Existing Event: `control_command` (Client → Server) — Modified Behavior

When `state.pose_mode_active == True`, the backend sends the actual `ry` value to
WirelessController instead of hardcoding it to 0.0.

**WirelessController axis remapping in Pose mode:**
- `lx`: roll (was strafe)
- `ly`: body height (was forward/back)
- `rx`: yaw with spring-back (was yaw velocity)
- `ry`: pitch (was always 0.0)

## Robot API Commands Used

### Pose API (1028) - SPORT_MOD Topic ✅ Entry Command

**Topic:** `rt/api/sport/request`
**Payload:**
```json
{ "api_id": 1028 }
```
**Note:** Toggle command. Enters Pose mode where WirelessController axes are remapped.

### RecoveryStand API (1006) - SPORT_MOD Topic ✅ Exit Command

**Topic:** `rt/api/sport/request`
**Payload:**
```json
{ "api_id": 1006 }
```
**Note:** Only command that reliably exits Pose mode and restores FreeWalk movement.

## Rejected APIs (Empirical Testing)

| API | ID | Status | Reason |
|-----|------|--------|--------|
| Euler | 1007 | ❌ Rejected (3202) | Does not work in Pose mode |
| BodyHeight | 1013 | ❌ Rejected (3203) | Does not work in AI/FreeWalk mode |
| FreeWalk | 1045 | ❌ Rejected (3203) | Fails after Pose toggle |
| BalanceStand | 1002 | ❌ No effect | Does not restore movement after Pose |
| StandUp | 1004 | ❌ No effect | Does not restore movement after Pose |
| Motion Switcher | 1002 | ❌ No effect | Full re-init sequence fails |

