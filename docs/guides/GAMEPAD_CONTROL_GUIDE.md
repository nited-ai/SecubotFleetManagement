# 🎮 Gamepad Control Guide for Unitree Go2

## Overview
This guide explains how to use gamepad control with your Unitree Go2 robot through the web interface. The system supports standard Xbox-style controllers using the HTML5 Gamepad API.

## Prerequisites
- ✅ Unitree Go2 robot connected via WebRTC
- ✅ Xbox-style gamepad controller (Xbox One, Xbox Series, or compatible)
- ✅ Gamepad connected to your PC (USB or Bluetooth)
- ✅ Web interface running (`python web_interface.py`)

## Quick Start

### 1. Connect Your Robot
1. Open the web interface at `http://localhost:5000`
2. Select connection method (e.g., "Local STA")
3. Enter robot IP address (e.g., `192.168.178.155`)
4. Click "Connect to Robot"
5. Wait for connection to establish

### 2. Enable Gamepad Control
1. Connect your gamepad to your PC
2. Press any button on the gamepad to activate it
3. In the web interface, find the "🎮 Gamepad Control" section
4. Toggle the switch to enable gamepad control
5. Status should change to "🟢 Gamepad Active"

### 3. Control Your Robot
Use the gamepad controls as mapped below to control your robot!

## Control Mapping

### Analog Sticks (Movement)
| Control | Function | Range | Description |
|---------|----------|-------|-------------|
| **Left Stick X** | Lateral Movement | -1.0 to 1.0 | Strafe left/right |
| **Left Stick Y** | Linear Movement | -1.0 to 1.0 | Move forward/backward |
| **Right Stick X** | Yaw Rotation | -1.0 to 1.0 | Turn left/right |
| **Right Stick Y** | Pitch Control | -0.3 to 0.3 | Head up/down |

### Triggers (Camera Control)
| Control | Function | Description |
|---------|----------|-------------|
| **Left Trigger (LT)** | Camera Look Left | Analog 0.0-1.0 (planned) |
| **Right Trigger (RT)** | Camera Look Right | Analog 0.0-1.0 (planned) |

### Bumpers (Mode Control)
| Control | Function | Description |
|---------|----------|-------------|
| **Left Bumper (LB)** | Toggle Walk/Pose Mode | Switch between movement modes |
| **Right Bumper (RB)** | Cycle Body Height | Low → Middle → High → Low |

### Face Buttons (Actions)
| Control | Function | Description |
|---------|----------|-------------|
| **X Button** | 🛑 Emergency Stop | Immediately halt all movement (Damp) |
| **Y Button** | Stand Up | Command robot to stand up |
| **A Button** | Sit Down | Command robot to sit down |
| **B Button** | Lidar Switch | Toggle lidar on/off |

## Safety Features

### 1. Dead Zone
- **Default**: 0.1 (10% of stick range)
- **Purpose**: Prevents controller drift from causing unwanted movement
- **Effect**: Small stick movements near center are ignored

### 2. Speed Limits
- **Linear Speed**: Maximum 0.5 m/s (forward/backward/strafe)
- **Angular Speed**: Maximum 1.0 rad/s (rotation)
- **Pitch Range**: Limited to ±0.3 radians

### 3. Emergency Stop
- **Trigger**: Press X button
- **Action**: Sends `SPORT_CMD["Damp"]` to immediately halt all motors
- **Effect**: Disables gamepad control until manually cleared
- **Recovery**: Click "Clear Emergency Stop" button in web interface

### 4. Connection Validation
- Commands only sent when robot is connected
- Gamepad control automatically disabled if connection lost
- Visual feedback for all connection states

### 5. Rate Limiting
- **Command Rate**: 20Hz (50ms interval)
- **Purpose**: Prevents command flooding
- **Effect**: Smooth, controlled movement

## Real-Time Feedback

### Status Indicators
- **🟢 Gamepad Active**: Gamepad enabled and working
- **⚫ Gamepad Disabled**: Gamepad control off
- **⚠️ Gamepad Disconnected**: Controller disconnected
- **🛑 EMERGENCY STOP ACTIVE**: Emergency stop engaged

### Live Values Display
The interface shows real-time joystick values:
- **LX**: Left stick X-axis value
- **LY**: Left stick Y-axis value
- **RX**: Right stick X-axis value
- **RY**: Right stick Y-axis value

## Troubleshooting

### Gamepad Not Detected
**Problem**: "No gamepad detected" message when enabling
**Solutions**:
1. Ensure gamepad is properly connected (USB or Bluetooth)
2. Press any button on the gamepad to wake it up
3. Check Windows Game Controllers settings (joy.cpl)
4. Try a different USB port or re-pair Bluetooth
5. Refresh the web page and try again

### Gamepad Disconnects During Use
**Problem**: "⚠️ Gamepad Disconnected" appears during operation
**Solutions**:
1. Check USB cable connection
2. Replace batteries (wireless controllers)
3. Move closer to PC (Bluetooth controllers)
4. Disable USB power saving in Windows settings

### Robot Not Responding to Commands
**Problem**: Gamepad active but robot doesn't move
**Solutions**:
1. Verify robot is connected (check status indicator)
2. Ensure emergency stop is not active
3. Check that robot is in sport mode
4. Verify joystick values are changing (check live display)
5. Check browser console (F12) for errors

### Movement is Jerky or Unresponsive
**Problem**: Robot movement is not smooth
**Solutions**:
1. Check network connection quality
2. Reduce dead zone if sticks feel unresponsive
3. Increase dead zone if robot drifts when sticks are centered
4. Ensure no other applications are using the gamepad

### Emergency Stop Won't Clear
**Problem**: Cannot re-enable gamepad after emergency stop
**Solutions**:
1. Click "Clear Emergency Stop" button
2. Wait a few seconds for robot to recover
3. Disconnect and reconnect to robot if needed
4. Check robot's physical state

## Technical Details

### Command Topics
- **Movement**: `rt/wirelesscontroller` (continuous, no callback)
- **Sport Commands**: `rt/api/sport/request` (request/response)
- **Lidar**: `rt/utlidar/switch` (request/response)

### Sport Command IDs
- Damp (Emergency Stop): 1001
- StopMove: 1003
- StandUp: 1004
- Sit: 1009
- BodyHeight: 1013
- Pose: 1028

### Browser Compatibility
- ✅ Chrome/Edge (Recommended)
- ✅ Firefox
- ⚠️ Safari (Limited gamepad support)

## Tips for Best Experience

1. **Start Slow**: Begin with small stick movements to get a feel for the controls
2. **Use Emergency Stop**: Don't hesitate to use X button if something goes wrong
3. **Monitor Video**: Keep an eye on the video feed while controlling
4. **Check Battery**: Ensure gamepad has sufficient battery
5. **Stable Connection**: Use wired connection for most reliable control
6. **Practice**: Test in a safe, open area first

## Future Enhancements

The following features are planned for future updates:
- [ ] Camera control via triggers (LT/RT)
- [ ] Configurable dead zones in UI
- [ ] Adjustable speed limits
- [ ] Custom button mapping
- [ ] Gamepad vibration feedback
- [ ] Multiple gamepad profiles
- [ ] Recording and playback of movement sequences

## Support

If you encounter issues not covered in this guide:
1. Check the browser console (F12) for error messages
2. Review `TROUBLESHOOTING.md` for general issues
3. Check the server logs for backend errors
4. Ensure you're using a compatible gamepad

---

**Last Updated**: 2026-01-22
**Version**: 1.0
**Compatible with**: Unitree Go2 robots

