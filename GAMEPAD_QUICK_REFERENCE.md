# 🎮 Gamepad Quick Reference Card

## Quick Start
1. Connect robot → 2. Enable gamepad toggle → 3. Start controlling!

## Control Layout (Xbox-Style Controller)

```
        [LB]                                    [RB]
         │                                       │
    ┌────┴────┐                             ┌───┴────┐
    │         │                             │        │
   [LT]      [RT]                          [Y]      [B]
    │         │                          ┌──┴──┐  ┌──┴──┐
    │    ┌────┴────┐                     │     │  │     │
    │    │  Right  │                    [X]   [A]
    │    │  Stick  │                     └─────┘  └─────┘
    │    │  (RX/RY)│
    │    └─────────┘
    │
┌───┴────┐
│  Left  │
│  Stick │
│ (LX/LY)│
└────────┘
```

## Movement Controls

### Left Stick (Movement)
- **Push Forward**: Move forward
- **Pull Back**: Move backward  
- **Push Left**: Strafe left
- **Push Right**: Strafe right
- **Diagonal**: Combined movement

### Right Stick (Rotation & Pitch)
- **Push Left**: Turn left (yaw)
- **Push Right**: Turn right (yaw)
- **Push Forward**: Pitch head down
- **Pull Back**: Pitch head up

## Action Buttons

| Button | Action | Description |
|--------|--------|-------------|
| **X** | 🛑 **EMERGENCY STOP** | Immediately halt all movement |
| **Y** | Stand Up | Robot stands up |
| **A** | Sit Down | Robot sits down |
| **B** | Lidar Toggle | Switch lidar on/off |

## Bumpers & Triggers

| Control | Action | Description |
|---------|--------|-------------|
| **LB** | Walk/Pose Mode | Toggle between modes |
| **RB** | Body Height | Cycle: Low → Mid → High |
| **LT** | Camera Left | (Planned feature) |
| **RT** | Camera Right | (Planned feature) |

## Safety Features

### Dead Zone
- **10%** of stick range ignored
- Prevents controller drift

### Speed Limits
- **Linear**: Max 0.5 m/s
- **Angular**: Max 1.0 rad/s
- **Pitch**: ±0.3 radians

### Emergency Stop
- Press **X** button
- Sends damp command
- Disables gamepad
- Click "Clear Emergency Stop" to resume

## Status Indicators

| Indicator | Meaning |
|-----------|---------|
| 🟢 Gamepad Active | Ready to control |
| ⚫ Gamepad Disabled | Control off |
| ⚠️ Gamepad Disconnected | Controller lost |
| 🛑 EMERGENCY STOP | Safety stop active |

## Live Values Display

Monitor real-time joystick positions:
- **LX**: Left stick X-axis (-1.0 to 1.0)
- **LY**: Left stick Y-axis (-1.0 to 1.0)
- **RX**: Right stick X-axis (-1.0 to 1.0)
- **RY**: Right stick Y-axis (-1.0 to 1.0)

## Tips

✅ **DO:**
- Start with small movements
- Keep video feed visible
- Use emergency stop if needed
- Check battery level
- Practice in open area

❌ **DON'T:**
- Make sudden large movements
- Ignore emergency situations
- Use with low battery
- Control without video feed
- Operate near obstacles initially

## Troubleshooting

**Gamepad not detected?**
→ Connect controller, press any button, refresh page

**Robot not moving?**
→ Check connection status, verify gamepad enabled

**Emergency stop active?**
→ Click "Clear Emergency Stop" button

**Jerky movement?**
→ Check network connection, reduce speed

## Command Rate
- **20 Hz** (50ms interval)
- Smooth, responsive control
- Prevents command flooding

---

**For detailed information, see:** `GAMEPAD_CONTROL_GUIDE.md`

