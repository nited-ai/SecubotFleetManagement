# AI Motion Mode Implementation Status

## Current Status

The web interface has been updated to initialize the robot into **AI motion mode** instead of normal mode when gamepad control is enabled.

## Changes Made

### 1. Motion Mode Initialization (web_interface.py lines 276-287)

When you enable gamepad control, the system now:
1. Checks the current motion mode
2. Switches to **AI mode** if not already in AI mode
3. Waits 5 seconds for the mode switch to complete
4. Sends StandUp command
5. Sends ContinuousGait command

```python
# Switch to AI mode if not already
if current_mode != "ai":
    logging.info(f"Switching from {current_mode} to AI mode...")
    await connection.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["MOTION_SWITCHER"],
        {
            "api_id": 1002,
            "parameter": {"name": "ai"}
        }
    )
    await asyncio.sleep(5)  # Wait for mode switch (AI mode takes longer)
    logging.info("Switched to AI mode")
```

## Known Issues

### Wireless Controller in AI Mode

**Problem:** The robot may not respond to wireless controller commands (`rt/wirelesscontroller`) in AI mode.

**Evidence:**
- The example code in `examples/go2/data_channel/sportmode/sportmode.py` shows:
  - Normal mode uses wireless controller and Move commands
  - AI mode uses special commands like `StandOut` (handstand mode)
  - No wireless controller usage is shown in AI mode

**Possible Reasons:**
1. AI mode may not support wireless controller commands
2. AI mode may require different commands or topics for movement
3. AI mode may need additional initialization or configuration

## What We're Currently Sending

### Movement Commands (when holding LB and moving joystick):
```python
connection.datachannel.pub_sub.publish_without_callback(
    RTC_TOPIC["WIRELESS_CONTROLLER"],  # "rt/wirelesscontroller"
    {
        "lx": 0.0,    # Left stick X (strafe left/right)
        "ly": 0.0,    # Left stick Y (forward/back)
        "rx": 0.0,    # Right stick X (yaw rotation)
        "ry": 0.0,    # Right stick Y (pitch)
        "keys": 0
    }
)
```

## Next Steps to Investigate

### Option 1: Check if AI Mode Supports Wireless Controller
- Test if wireless controller works in AI mode
- Check console logs for any error messages
- Verify the robot is actually in AI mode

### Option 2: Use Different Commands in AI Mode
- Research AI mode specific movement commands
- Check if there are AI-specific topics or API IDs
- Look for documentation on AI motion service

### Option 3: Use Sport Commands Instead
- Try using `SPORT_CMD["Move"]` with parameters instead of wireless controller
- This is what the normal mode example uses for movement

## Testing Instructions

1. **Start the web interface:**
   ```bash
   python web_interface.py
   ```

2. **Connect to robot** (192.168.178.155)

3. **Enable gamepad control**
   - Watch console logs for mode switching messages
   - Should see: "Switching from X to AI mode..."
   - Should see: "Switched to AI mode"

4. **Try to move:**
   - Hold LB button
   - Move left joystick
   - Check if robot moves

5. **Check console logs:**
   - Look for any error messages
   - Verify commands are being sent
   - Check for responses from robot

## Alternative Approach: Normal Mode

If AI mode doesn't support wireless controller, we could:
1. Switch back to normal mode for movement
2. Use AI mode only for special AI features
3. Add a toggle to switch between modes

**To switch back to normal mode**, change line 277 in `web_interface.py`:
```python
if current_mode != "normal":  # Change "ai" to "normal"
```

## Questions for User

1. **Why do you need AI mode?** 
   - What specific AI features do you want to use?
   - Do you need AI mode for movement, or for other features?

2. **Does the physical remote work in AI mode?**
   - If yes, then wireless controller should work
   - If no, then AI mode may not support wireless control

3. **What happens when you try to move?**
   - Does the robot respond at all?
   - Any error messages in console?
   - Does the robot stay in pose mode?

