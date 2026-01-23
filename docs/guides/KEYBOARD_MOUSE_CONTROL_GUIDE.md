# Keyboard & Mouse Control Guide

## 🎮 **Overview**

The Unitree Go2 robot now supports keyboard and mouse control alongside gamepad control, providing flexible input options for robot operation.

---

## ⌨️ **Keyboard Controls**

### **Movement Keys (WASD)**
- **W**: Move forward (positive vx)
- **S**: Move backward (negative vx)
- **A**: Strafe left (positive vy)
- **D**: Strafe right (negative vy)

### **Action Keys**
- **Space**: Emergency stop
- **E**: Stand up
- **Q**: Crouch
- **R**: Toggle Lidar on/off

### **Special Keys**
- **ESC**: Release mouse control (exit pointer lock)

---

## 🖱️ **Mouse Controls**

### **Mouse Movement**
- **Horizontal (X-axis)**: Control yaw rotation (turn left/right)
- **Vertical (Y-axis)**: Control pitch (head up/down) - *Future feature*

### **Mouse Capture**
- **Click anywhere**: Capture mouse for control (pointer lock)
- **ESC key**: Release mouse control

---

## 🚀 **How to Use**

### **Step 1: Enable Keyboard/Mouse Control**
1. Connect to the robot
2. Toggle "Keyboard & Mouse Control" ON
3. Click anywhere on the page to capture the mouse

### **Step 2: Control the Robot**
- Use **WASD** keys to move the robot
- Move the **mouse** to rotate the robot
- Press **Space** for emergency stop
- Press **ESC** to release mouse control

### **Step 3: Disable Control**
- Toggle "Keyboard & Mouse Control" OFF
- Or press **ESC** to release mouse, then toggle OFF

---

## ⚙️ **Settings**

Keyboard and mouse control uses the same settings as gamepad control:

### **Sensitivity Settings**
- **Linear Sensitivity**: Affects W/S forward/backward speed
- **Strafe Sensitivity**: Affects A/D left/right speed
- **Rotation Sensitivity**: Affects mouse yaw rotation speed
- **Speed Multiplier**: Global speed multiplier for all movements

### **Velocity Limits**
- **Max Linear Velocity**: Maximum forward/backward speed (m/s)
- **Max Strafe Velocity**: Maximum left/right speed (m/s)
- **Max Rotation Velocity**: Maximum yaw rotation speed (rad/s)

### **Mouse Sensitivity**
- **Yaw Sensitivity**: 0.002 (adjustable in code)
- **Pitch Sensitivity**: 0.001 (adjustable in code)

---

## 🎯 **Features**

### **✅ Implemented**
- ✅ WASD keyboard movement control
- ✅ Mouse yaw rotation control
- ✅ Simultaneous key press support (e.g., W+D for diagonal movement)
- ✅ Pointer lock for mouse capture
- ✅ Emergency stop (Space key)
- ✅ Stand up (E key) and Crouch (Q key)
- ✅ Lidar toggle (R key)
- ✅ WebSocket support for low latency (~150ms)
- ✅ HTTP fallback if WebSocket unavailable
- ✅ Real-time velocity and latency display
- ✅ Same velocity limits and sensitivity as gamepad
- ✅ ESC key to release mouse control

### **🔄 Control Mode Switching**
- Can switch between gamepad and keyboard/mouse control
- Only one control mode active at a time
- Disable one before enabling the other

---

## 📊 **Display Information**

The keyboard/mouse control panel shows:
- **Forward**: Current forward/backward velocity
- **Strafe**: Current left/right velocity
- **Yaw**: Current rotation velocity
- **Pitch**: Current pitch value (for future use)

The velocity status panel shows:
- **Velocity**: Current velocity magnitude in m/s
- **Connection**: Current latency and connection method (WebSocket/HTTP)
- **Avg Latency**: Rolling average latency over last 10 commands

---

## 🔒 **Safety Features**

### **Emergency Stop**
- Press **Space** key for immediate emergency stop
- Same as gamepad X button
- Stops all movement immediately

### **Connection Validation**
- Must be connected to robot before enabling control
- Automatic disable if connection lost
- Clear error messages if connection fails

### **Pointer Lock**
- Mouse control only active when pointer is locked
- Press ESC to release mouse control
- Visual indicator when mouse is captured

---

## 🧪 **Testing Checklist**

### **Basic Movement**
- [ ] W key moves robot forward
- [ ] S key moves robot backward
- [ ] A key strafes robot left
- [ ] D key strafes robot right
- [ ] W+D moves robot diagonally (forward-right)
- [ ] W+A moves robot diagonally (forward-left)

### **Mouse Control**
- [ ] Click captures mouse (pointer lock)
- [ ] Mouse left/right rotates robot
- [ ] ESC releases mouse control
- [ ] Mouse control info appears when captured

### **Action Keys**
- [ ] Space triggers emergency stop
- [ ] E makes robot stand up
- [ ] Q makes robot crouch
- [ ] R toggles lidar on/off

### **Display Updates**
- [ ] Forward value updates when pressing W/S
- [ ] Strafe value updates when pressing A/D
- [ ] Yaw value updates when moving mouse
- [ ] Velocity status shows current speed
- [ ] Latency display shows real-time latency

### **Connection Methods**
- [ ] WebSocket connection shows ~150ms latency
- [ ] HTTP fallback works if WebSocket disconnected
- [ ] Connection method badge shows current method

---

## 🐛 **Troubleshooting**

### **Mouse not working**
- **Solution**: Click anywhere on the page to capture mouse
- Check that pointer lock is active (info message appears)

### **Keys not responding**
- **Solution**: Make sure keyboard/mouse control is enabled (toggle ON)
- Check that robot is connected
- Verify browser has focus on the page

### **High latency**
- **Solution**: Check WebSocket connection status
- Verify network connection to robot
- Check if HTTP fallback is being used (slower)

### **Robot not moving**
- **Solution**: Check velocity status panel
- Verify settings (sensitivity, max velocity)
- Check emergency stop is not active
- Ensure robot is in AI mode

---

## 📝 **Technical Details**

### **Polling Rate**
- 30Hz (33ms interval) - same as gamepad control
- Balanced for responsiveness without network overload

### **Input Processing**
1. Read keyboard state (keys pressed)
2. Read mouse movement (accumulated since last poll)
3. Calculate velocities with sensitivity and limits
4. Convert to normalized gamepad-style input
5. Send via WebSocket or HTTP
6. Update display with current values

### **Latency**
- **WebSocket**: ~150ms (low latency)
- **HTTP**: ~300ms (fallback)
- Real-time latency monitoring
- Color-coded indicators

---

## 🎮 **Comparison: Gamepad vs Keyboard/Mouse**

| Feature | Gamepad | Keyboard/Mouse |
|---------|---------|----------------|
| **Movement** | Analog sticks | WASD keys (digital) |
| **Rotation** | Right stick | Mouse (analog) |
| **Precision** | Analog (0-100%) | Digital (0% or 100%) |
| **Emergency Stop** | X button | Space key |
| **Stand/Crouch** | Y/A buttons | E/Q keys |
| **Lidar** | B button | R key |
| **Latency** | ~150ms (WebSocket) | ~150ms (WebSocket) |
| **Ease of Use** | Requires gamepad | Built-in keyboard/mouse |

---

## 🚀 **Future Enhancements**

Potential improvements for keyboard/mouse control:
- [ ] Mouse pitch control for camera/head movement
- [ ] Configurable key bindings
- [ ] Adjustable mouse sensitivity in UI
- [ ] Smooth acceleration/deceleration
- [ ] Shift key for speed boost
- [ ] Ctrl key for precision mode (slower)
- [ ] Number keys for preset speeds
- [ ] Mouse wheel for body height adjustment

---

## ✅ **Summary**

Keyboard and mouse control provides an accessible alternative to gamepad control:
- **Easy to use**: No special hardware required
- **Low latency**: WebSocket support for ~150ms response time
- **Full featured**: All essential controls available
- **Safe**: Emergency stop and connection validation
- **Flexible**: Works alongside gamepad control

Perfect for users who don't have a gamepad or prefer keyboard/mouse input!

