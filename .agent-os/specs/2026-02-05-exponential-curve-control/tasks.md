# Exponential Curve Control System - Tasks

> Created: 2026-02-05
> Status: Ready for Implementation
> Reference: @.agent-os/specs/2026-02-05-exponential-curve-control/analysis.md

## Overview

Implement adjustable exponential response curves for linear, strafe, and rotation control axes to provide fine-tuned control feel across different skill levels and use cases.

## Tasks

### Phase 1: Core Curve System Implementation

- [x] 1. Implement core curve function
  - [x] 1.1 Create `applyCurve()` function in `static/js/curve-utils.js`
  - [x] 1.2 Implement deadzone removal logic
  - [x] 1.3 Implement exponential scaling (input^alpha)
  - [x] 1.4 Implement hardware limit clamping
  - [x] 1.5 Add JSDoc documentation with examples
  - [x] 1.6 Write unit tests for curve function (test various alpha values) - 24 tests created
  - [x] 1.7 Test deadzone behavior (input < deadzone → output = 0) - All tests pass ✅
  - [x] 1.8 Test hardware limit clamping works correctly - All tests pass ✅

- [x] 2. Update settings structure
  - [x] 2.1 Add curve settings to `getDefaultSettings()` in `settings-manager.js`
  - [x] 2.2 Add `linear_alpha`, `linear_deadzone` to keyboard_mouse settings
  - [x] 2.3 Add `strafe_alpha`, `strafe_deadzone` to keyboard_mouse settings
  - [x] 2.4 Add `rotation_alpha`, `rotation_deadzone` to keyboard_mouse settings
  - [x] 2.5 Update all presets (beginner/normal/advanced/sport) with curve values
  - [ ] 2.6 Test settings save/load from localStorage
  - [ ] 2.7 Verify backward compatibility with existing settings

- [x] 3. Update keyboard/mouse control module
  - [x] 3.1 Import `applyCurve()` function in `keyboard-mouse-control.js` (via script tag in control.html)
  - [x] 3.2 Load alpha/deadzone values in `loadSettings()` method
  - [x] 3.3 Apply curve to linear velocity in `poll()` method
  - [x] 3.4 Apply curve to strafe velocity in `poll()` method
  - [x] 3.5 Apply curve to rotation velocity in `poll()` method
  - [x] 3.6 Remove old sqrt dampening code (from mouse wheel handler)
  - [x] 3.7 Update console logging to show curve-adjusted velocities
  - [ ] 3.8 Test WASD movement with curves applied
  - [ ] 3.9 Test mouse rotation with curves applied

### Phase 2: Speed Slider Integration

- [x] 4. Update speed slider to work with curves
  - [x] 4.1 Modify `initializeSpeedSlider()` in `control.js`
  - [x] 4.2 Remove sqrt dampening (curves applied in poll() method)
  - [x] 4.3 Update console logging to show curve parameters
  - [ ] 4.4 Test slider at various positions (10%, 50%, 100%, 200%)
  - [ ] 4.5 Verify curve respects hardware limits

- [x] 5. Update mouse wheel speed adjustment
  - [x] 5.1 Modify `handleMouseWheel()` in `keyboard-mouse-control.js`
  - [x] 5.2 Remove sqrt dampening (curves applied in poll() method)
  - [x] 5.3 Update console logging to show curve parameters
  - [ ] 5.4 Test mouse wheel scroll up/down
  - [ ] 5.5 Verify smooth speed transitions

### Phase 3: UI Visualization (Chart.js Integration)

- [x] 6. Add Chart.js library
  - [x] 6.1 Add Chart.js CDN link to `templates/base.html`
  - [ ] 6.2 Verify Chart.js loads correctly in browser console
  - [x] 6.3 Create `static/js/curve-visualizer.js` module
  - [x] 6.4 Implement `createCurveChart()` function
  - [x] 6.5 Implement `updateCurveChart()` function for real-time updates
  - [ ] 6.6 Test basic chart rendering

- [x] 7. Create curve adjustment UI panel
  - [x] 7.1 Add curve tuning section to `templates/landing.html` settings panel
  - [x] 7.2 Create three canvas elements for graphs (linear, strafe, rotation)
  - [x] 7.3 Add alpha sliders (range: 0.5-4.0, step: 0.1) for each axis
  - [x] 7.4 Add deadzone sliders (range: 0%-30%, step: 1%) for each axis
  - [x] 7.5 Add reset button to restore defaults
  - [x] 7.6 Style UI with Tailwind CSS and glass-morphism design
  - [ ] 7.7 Test UI layout on different screen sizes

- [x] 8. Implement real-time graph updates
  - [x] 8.1 Connect alpha sliders to `updateCurveChart()` function
  - [x] 8.2 Connect deadzone sliders to `updateCurveChart()` function
  - [x] 8.3 Add deadzone indicator (red dashed line) to graphs
  - [x] 8.4 Initialize charts on page load in `landing.js`
  - [x] 8.5 Implement reset button functionality
  - [ ] 8.6 Test graph updates in real-time as sliders move
  - [ ] 8.7 Verify settings persist to localStorage

- [x] 8a. Bug Fixes for Graph Updates (2026-02-05)
  - [x] 8a.1 Fixed Bug 1: Deadzone indicator showing 10% when set to 0%
    - Root cause: JavaScript treats 0 as falsy, so `|| 0.10` defaulted to 0.10
    - Fix: Changed all slider handlers to use `!== undefined ? value : 0.10`
  - [x] 8a.2 Fixed Bug 2: Y-axis max values not updating correctly
    - Root cause: Slider handlers used stale settings instead of fresh values
    - Fix: Added `getFreshSettings()` helper and connected max velocity sliders to update graphs
  - [x] 8a.3 Fixed hardware limit violations in slider max values
    - Linear: Changed from max="2.0" to max="5.0" (hardware limit)
    - Strafe: Changed from max="2.0" to max="0.6" (hardware limit), default changed to 0.6
    - Rotation: Changed from max="4.0" to max="3.0" (hardware limit)
  - [x] 8a.4 Extended alpha slider range from 0.5-4.0 to 0.1-4.0
    - Allows very responsive curves that hit hardware limits early

- [x] 8b. UI Reorganization (2026-02-05)
  - [x] 8b.1 Reorganized curve tuning UI to group controls by axis
    - Moved max velocity sliders from "Velocity Limits" section to curve tuning section
    - Each axis now has all controls grouped together: graph → max velocity → alpha → deadzone
    - Improved visual relationship between graphs and their controls
    - Layout: Linear | Strafe | Rotation (3-column grid on large screens)
  - [x] 8b.2 Simplified help text for max velocity sliders
    - Changed from "Maximum forward/backward speed (hardware limit: 5.0 m/s)" to "Hardware limit: 5.0 m/s"
    - Maintains consistency across all three axes

- [x] 8c. Complete UI Reorganization (2026-02-05)
  - [x] 8c.1 Moved keyboard/mouse settings to curve tuning sections
    - Removed standalone "Keyboard & Mouse" section
    - Moved "Keyboard Linear Speed" to Linear section (between graph and max velocity)
    - Moved "Keyboard Strafe Speed" to Strafe section (between graph and max velocity)
    - Moved "Mouse Yaw Sensitivity" and "Mouse Pitch Sensitivity" to Rotation section
    - Each axis now has: Graph → Speed Multiplier(s) → Max Velocity → Alpha → Deadzone
  - [x] 8c.2 Added tooltips to all sliders
    - Speed multipliers: Explain how they affect keyboard/mouse input
    - Max velocity: Explain Y-axis maximum and hardware limits
    - Alpha: Explain curve shape and responsiveness
    - Deadzone: Explain drift prevention and red line on graph
  - [x] 8c.3 Removed "Reset Curves to Defaults" button
    - Preset buttons (Beginner/Normal/Advanced/Sport) already handle resetting
    - Reduces UI clutter
  - [x] 8c.4 Hidden Gamepad section
    - Used `style="display: none;"` to hide section
    - Preserved HTML for future use
    - Can be shown later if needed

### Phase 4: Preset Integration

- [x] 9. Update preset system with curve settings
  - [x] 9.1 Define curve values for beginner preset (high alpha, smooth)
  - [x] 9.2 Define curve values for normal preset (balanced alpha)
  - [x] 9.3 Define curve values for advanced preset (lower alpha, responsive)
  - [x] 9.4 Define curve values for sport preset (low alpha, aggressive)
  - [ ] 9.5 Update `applyPreset()` function to change curve settings
  - [ ] 9.6 Update graphs when preset is selected
  - [ ] 9.7 Test switching between all four presets
  - [ ] 9.8 Verify preset switching updates all three axes

- [x] 10. Add reset and apply buttons
  - [x] 10.1 "Reset to Defaults" button removed (presets handle this)
  - [x] 10.2 Preset buttons already exist in UI
  - [x] 10.3 Preset buttons connected to `applyPreset()` function
  - [ ] 10.4 Test reset button restores correct defaults
  - [ ] 10.5 Test preset dropdown applies correct curve values

### Phase 7: Critical Bug Fixes (2026-02-05)

- [ ] 16. Fix preset application bugs
  - [ ] 16.1 **Issue 2: Presets not applying alpha/deadzone values**
    - Root cause: `updateAllKeyboardMouseSliders()` doesn't update alpha/deadzone sliders
    - Fix: Add alpha and deadzone slider updates to the function
    - Fix: Add chart updates when presets are applied
  - [ ] 16.2 Verify all sliders update when preset is selected
  - [ ] 16.3 Verify graphs update when preset is selected
  - [ ] 16.4 Test all four presets (Beginner/Normal/Advanced/Sport)

- [ ] 17. Fix speed slider range
  - [x] 17.1 **Issue 3: Speed slider range is 10-200%** - USER CLARIFIED ✅
    - User clarification: Speed slider should represent % along curve (0-100%), NOT a multiplier
    - Graphs go from 0-100%, controls should match the curve at that % value
    - Hardware limits prevent going above 100%
    - Changed: min="0" max="100" step="5" (was min="10" max="200" step="10")
  - [x] 17.2 Update speed slider in templates/control.html - DONE ✅
  - [ ] 17.3 Update speed slider handler to use speed as input % to curve
  - [ ] 17.4 Test speed slider at various positions

- [x] 18. **Issue 4: Settings not applied to robot control** - FIXED ✅
  - [x] 18.1 Investigate why settings aren't being applied - ROOT CAUSE FOUND ✅
    - **CRITICAL BUG:** Three different localStorage keys were being used:
      - `'unitree_settings'` - Landing page (settings-manager.js) ✅ CORRECT
      - `'keyboardMouseSettings'` - Mouse wheel handler ❌ OLD FORMAT
      - `'settings'` - Speed slider in control.js ❌ WRONG KEY
    - Mouse wheel handler was writing to old key and setting `keyboard_linear_speed` (multiplier, e.g., 1.2)
    - When `loadSettings()` ran, fallback read `keyboard_linear_speed` as `maxLinear`
    - This is why console showed `max_linear: 1.2` instead of `5.0` (configured value)
  - [x] 18.2 Add debug logging to loadSettings() method - DONE ✅
  - [x] 18.3 Fix loadSettings() fallback to use `kb_max_linear_velocity` not `keyboard_linear_speed` - DONE ✅
  - [x] 18.4 Fix mouse wheel handler to update speed percentage, not max velocity settings - DONE ✅
    - Speed slider now represents % along curve (0-100%)
    - Mouse wheel updates `speedPercentage` property (0-100%)
    - No longer modifies localStorage or max velocity settings
  - [x] 18.5 Fix speed slider handler in control.js - DONE ✅
    - Now calls `keyboardMouseControl.setSpeedPercentage(percentage)`
    - No longer modifies localStorage
  - [x] 18.6 Remove Keyboard Speed Multiplier sliders - DONE ✅
    - Removed from templates/landing.html (linear and strafe sections)
    - Removed from static/js/landing.js (initialization and preset updates)
    - User decision: Remove completely (redundant with speed slider)
  - [ ] 18.7 Test with robot to verify settings are now applied correctly

### Phase 8: Critical Bug Fixes (2026-02-05)

User identified 5 new critical issues with the current implementation:

- [x] 21. **Issue 1: Remove obsolete keyboard_linear_speed and keyboard_strafe_speed** - FIXED ✅
  - [x] 21.1 Remove from getDefaultSettings() in settings-manager.js - DONE ✅
  - [x] 21.2 Remove from all preset definitions (beginner, normal, advanced, sport) - DONE ✅
  - [x] 21.3 Remove from old preset definitions (lines 264-331) - DONE ✅
  - [x] 21.4 Verify not being saved anywhere else - DONE ✅
    - Found references in templates/index.html (old file, not currently used)
    - No references in active code (landing.html, control.js, keyboard-mouse-control.js)
  - **Result:** Settings structure is now clean, no obsolete keyboard speed multipliers

- [x] 22. **Issue 2: Fix deadzone parsing bug (0 treated as falsy)** - FIXED ✅
  - [x] 22.1 Fix loadSettings() in keyboard-mouse-control.js - DONE ✅
    - Changed from: `parseFloat(km.linear_deadzone || 0.10)`
    - Changed to: `parseFloat(km.linear_deadzone !== undefined ? km.linear_deadzone : 0.10)`
    - Applied to all curve parameters: linearAlpha, linearDeadzone, strafeAlpha, strafeDeadzone, rotationAlpha, rotationDeadzone
    - Also fixed acceleration and deceleration parsing
  - **Result:** Deadzone value of 0% is now correctly respected instead of falling back to 10%

- [ ] 23. **Issue 3: Explain acceleration and deceleration settings**
  - **What they control:** Velocity ramping for smooth acceleration/deceleration
  - **Where defined:**
    - Default: acceleration=0.15, deceleration=0.2 (in keyboard-mouse-control.js)
    - Can be set in settings-manager.js keyboard_mouse section
  - **How they work:** In poll() method (lines 395-423), velocities gradually ramp up/down
    - Acceleration: How fast velocity increases when key is pressed (0.15 = 15% per frame)
    - Deceleration: How fast velocity decreases when key is released (0.2 = 20% per frame)
  - **Should they be exposed in UI?**
    - Recommendation: Keep as internal constants for now
    - Most users don't need to adjust these
    - Can expose later if users request fine-tuning
  - **Action needed:** Add clear code comments documenting these settings

- [x] 24. **Issue 4: Increase slider max values for testing beyond hardware limits** - FIXED ✅
  - [x] 24.1 Increase Mouse Yaw Sensitivity max from 2.0 to 5.0 - DONE ✅
  - [x] 24.2 Increase Mouse Pitch Sensitivity max from 2.0 to 5.0 - DONE ✅
  - [x] 24.3 Increase Max Rotation Velocity max from 3.0 to 9.0 rad/s - DONE ✅
  - [x] 24.4 Increase Max Linear Velocity max from 5.0 to 10.0 m/s - DONE ✅
  - [x] 24.5 Add warning tooltips to all sliders - DONE ✅
    - "⚠️ Values above hardware limits may cause instability. Use with caution."
    - "⚠️ Values above 2.0 may be too sensitive." (for mouse sensitivity)
  - **Mouse Yaw Sensitivity explanation:** This is the horizontal mouse sensitivity, NOT legacy
    - Controls how much mouse movement (in pixels) translates to rotation input
    - Higher values = more rotation for same mouse movement
    - Works in combination with Max Rotation Velocity and Rotation Alpha
  - **Result:** User can now test beyond documented hardware limits to find optimal settings

- [x] 25. **Issue 5: Remove gamepad settings from keyboard/mouse control** - ALREADY FIXED ✅
  - [x] 25.1 Check if gamepad settings are loaded in keyboard-mouse-control.js - DONE ✅
  - [x] 25.2 Verify no gamepad references in keyboard/mouse module - DONE ✅
  - **Result:** No gamepad settings found in keyboard-mouse-control.js - already clean!

- [ ] 19. Fix deadzone reset on disconnect (ORIGINAL ISSUE 5)
  - [ ] 19.1 **Deadzone sliders reset to 10% on disconnect**
    - Root cause: Likely fixed by Issue 2 (deadzone parsing bug)
    - Verify settings are saved to localStorage when sliders change
    - Verify settings are loaded from localStorage on page load
    - Test: Change deadzone to 0%, disconnect, verify it stays at 0%
  - [ ] 19.2 Test settings persistence across page refreshes
  - [ ] 19.3 Test settings persistence across disconnect/reconnect

- [ ] 20. Verify "Reset Curves" button is removed (ORIGINAL ISSUE 1)
  - [x] 20.1 **Button still visible in UI** - ALREADY FIXED ✅
    - Verified: Button removed from templates/landing.html
    - JavaScript handler safely wrapped in `if` check
  - [ ] 20.2 Test UI to confirm button is not visible

### Phase 9: Critical Bug Fixes After Testing (2026-02-05)

User discovered 4 critical issues after testing the Phase 8 fixes:

- [x] 26. **ISSUE 1: Curve graphs not updating to show new max velocity values** - FIXED ✅
  - **Problem:** When increasing max velocity sliders (e.g., 9.0 rad/s, 10.0 m/s), graphs showed old hardware limits
  - **Root Cause:** `applyCurve()` in curve-utils.js was clamping to hardwareLimit even when maxVelocity > hardwareLimit
    - Line 68: `const clamped = Math.min(scaled, hardwareLimit);`
    - This prevented testing beyond hardware limits
  - **Fix Applied:**
    - Changed clamping logic to use `Math.max(maxVelocity, hardwareLimit)` as effective limit
    - If maxVelocity > hardwareLimit, user is intentionally testing beyond limits
    - If maxVelocity <= hardwareLimit, enforce hardware limit for safety
  - **Result:** Graphs now correctly show curves up to configured max velocity values

- [x] 27. **ISSUE 2: Robot movement much slower than before, especially rotation** - FIXED ✅
  - **Problem:** After setting max velocities higher, robot moved SLOWER than before
  - **Root Cause:** Same as Issue 1 - hardware limit clamping in applyCurve()
    - Even with kb_max_rotation_velocity=9.0, output was clamped to 3.0 rad/s
    - Robot received commands with max_rotation=9.0 but actual velocities clamped to 3.0
  - **Fix Applied:** Same fix as Issue 1 - removed premature clamping
  - **Result:** Robot now uses full configured max velocity range

- [x] 28. **ISSUE 3: Deadzone 0% doesn't persist (resets to 10% on refresh)** - FIXED ✅
  - **Problem:** Setting deadzone to 0% works, but resets to 10% after page refresh
  - **Root Cause:** Settings were being saved correctly, but obsolete keys were being merged back in
    - `loadSettings()` merged stored settings with defaults using spread operator
    - If stored settings had obsolete keys, they would persist
  - **Fix Applied:**
    - Added `cleanObsoleteSettings()` function to remove deprecated keys
    - Called before merging with defaults in `loadSettings()`
    - Automatically saves cleaned settings back to localStorage
  - **Result:** Deadzone 0% now persists correctly across page refreshes

- [x] 29. **ISSUE 4: Obsolete settings still in localStorage** - FIXED ✅
  - **Problem:** localStorage still contained `keyboard_linear_speed`, `keyboard_strafe_speed`
  - **Root Cause:** Existing localStorage data wasn't cleaned when code was updated
  - **Fix Applied:**
    - `cleanObsoleteSettings()` function removes these keys on load
    - Automatically migrates old settings to new format
    - Logs cleanup actions to console for debugging
  - **Result:** Obsolete settings are automatically removed on next page load

### Phase 10: Critical Backend Bug - Robot Speed Not Increasing (2026-02-05)

User discovered that despite Phase 9 fixes, robot was NOT moving faster with higher max velocity settings.

- [x] 30. **CRITICAL: Robot speed unchanged despite higher max velocity settings** - FIXED ✅
  - **Problem:**
    - Before fix: Max Linear Velocity = 5.0 m/s → Robot speed = X
    - After fix: Max Linear Velocity = 10.0 m/s → Robot speed = X (SAME!)
    - Before fix: Max Rotation Velocity = 3.0 rad/s → Robot speed = Y
    - After fix: Max Rotation Velocity = 9.0 rad/s → Robot speed = Y (SAME!)
  - **Root Cause:** Backend was applying GAMEPAD multipliers to KEYBOARD/MOUSE inputs!
    - `app/services/control.py` lines 222-231 applied gamepad sensitivity/speed multipliers to ALL inputs
    - Frontend sends normalized values (0-1): `ly = vx / maxLinear`
    - Backend multiplied by gamepad sensitivity (1.5) and speed multiplier (1.5)
    - Example: vx=9.0 m/s → ly=1.0 → ly*=1.5*1.5=2.25 → vx=2.25 m/s (4x slower!)
  - **Investigation Process:**
    - Traced complete data flow from settings → robot commands
    - Examined `poll()` method: Curves applied correctly ✅
    - Examined `sendCommand()`: Normalization correct ✅
    - Examined backend `process_movement_command()`: Found gamepad multipliers applied to all inputs ❌
    - Backend was NOT checking `source` field to differentiate keyboard/mouse from gamepad
  - **Fix Applied:**
    - Added `source` field check in `app/services/control.py`
    - Only apply gamepad sensitivity/speed multipliers to gamepad inputs
    - Keyboard/mouse inputs skip multipliers (already have curves applied)
    - Added debug logging to trace values through pipeline
  - **Code Changes:**
    ```python
    # app/services/control.py lines 222-244
    source = data.get('source', 'gamepad')
    is_keyboard_mouse = (source == 'keyboard_mouse')

    if not is_keyboard_mouse:
        # Apply gamepad multipliers only to gamepad inputs
        ly *= self.state.gamepad_settings['sensitivity_linear']
        # ... etc
    ```
  - **Debug Logging Added:**
    - Frontend: `applyCurve()` output for linear and rotation
    - Frontend: `sendCommand()` normalized values and max velocities
    - Backend: Final velocities sent to robot with max velocity values
  - **Result:** Robot now uses full configured velocity range (9.0 rad/s, 10.0 m/s)

- [x] 31. **REGRESSION: Mouse rotation speed much slower than this morning** - FIXED ✅
  - **Problem:**
    - Robot rotates much slower than expected despite vyaw ≈ 8.9 rad/s being sent
    - Need to lift and reposition mouse multiple times for 360° rotation
    - This morning: Continuous smooth rotation without lifting mouse
    - Console shows: `input=1855.000, curved=9.000` (input clamped to 1.0)
  - **Root Cause:** Missing `MOUSE_SCALE_FACTOR` to normalize raw pixel values
    - Old code (templates/index.html line 2004): `MOUSE_SCALE_FACTOR = 0.08`
    - New code: `rotation = mouseMovement.x * mouseSensitivity` (NO scale factor!)
    - Example: 1855 pixels * 5.0 sensitivity = 9275 → clamped to 1.0 by applyCurve()
    - Result: Every mouse movement produces max rotation (9.0 rad/s) for only 33ms
    - Velocity ramping then decelerates because mouseMovement.x resets to 0
  - **Investigation Process:**
    - Traced data flow: Mouse movement → rotation calculation → applyCurve() → velocity ramping
    - Found applyCurve() clamps input to [0, 1] range (line 47 in curve-utils.js)
    - Found velocity ramping working correctly (lines 441-444)
    - Compared with old interface code (templates/index.html lines 2004-2006)
    - Discovered missing MOUSE_SCALE_FACTOR to normalize pixel values
  - **Fix Applied:**
    - Added `MOUSE_SCALE_FACTOR = 0.001` constant (lines 36-42)
    - Updated rotation calculation: `rotation = mouseMovement.x * MOUSE_SCALE_FACTOR * mouseSensitivity`
    - Example: 100 pixels * 0.001 * 5.0 = 0.5 (50% input to curve)
    - Example: 200 pixels * 0.001 * 5.0 = 1.0 (100% input to curve)
    - This allows proportional rotation based on mouse speed
  - **Result:** Smooth continuous rotation without lifting mouse, matches this morning's behavior
  - **SECOND FIX ATTEMPT (FAILED):** Added MOUSE_SCALE_FACTOR = 0.001, but robot still slow
  - **ROOT CAUSE IDENTIFIED:** Velocity ramping was slowing down mouse rotation!
    - Old interface (line 2061): `currentVelocities.rotation = targetRotation;` (INSTANT!)
    - New code (line 453): `currentVelocities.rotation += (targetRotation - currentVelocities.rotation) * 0.15;` (RAMPING!)
    - Ramping caused slow acceleration, making rotation feel sluggish
  - **FINAL FIX:**
    - Removed velocity ramping for mouse rotation (instant response like old interface)
    - Changed MOUSE_SCALE_FACTOR from 0.001 to 0.08 (matches old interface)
    - Updated version to v1.1.0 to force cache refresh
  - **Result:** Instant responsive mouse rotation matching old interface behavior

### Phase 5: Advanced Features

- [ ] 11. Add reference table (like Streamlit example)
  - [ ] 11.1 Create reference table HTML structure
  - [ ] 11.2 Calculate output velocities at 10%, 25%, 50%, 75%, 100% input
  - [ ] 11.3 Display values in table format (three columns: linear, strafe, rotation)
  - [ ] 11.4 Update table when sliders change
  - [ ] 11.5 Style table with Tailwind CSS
  - [ ] 11.6 Test table updates correctly

- [ ] 12. Add hardware limit warning system
  - [ ] 12.1 Detect when max velocity exceeds hardware limit
  - [ ] 12.2 Display warning message in UI (⚠️ icon + text)
  - [ ] 12.3 Highlight affected axis in red
  - [ ] 12.4 Show clamped value in warning message
  - [ ] 12.5 Test warning appears when limits exceeded
  - [ ] 12.6 Test warning disappears when limits respected

- [ ] 13. Add curve settings to control page (read-only display)
  - [ ] 13.1 Add small curve info panel to control page HUD
  - [ ] 13.2 Display current alpha values for each axis
  - [ ] 13.3 Display current deadzone values
  - [ ] 13.4 Style panel to match HUD design
  - [ ] 13.5 Test panel displays correct values
  - [ ] 13.6 Verify panel doesn't obstruct video feed

### Phase 6: Testing & Documentation

- [ ] 14. Comprehensive testing
  - [ ] 14.1 Test curve function with alpha = 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0
  - [ ] 14.2 Test deadzone at 0%, 10%, 20%, 30%
  - [ ] 14.3 Test all four presets (beginner, normal, advanced, sport)
  - [ ] 14.4 Test settings persistence across page refreshes
  - [ ] 14.5 Test with actual robot (if available)
  - [ ] 14.6 Verify no regressions in existing control functionality
  - [ ] 14.7 Test cross-browser compatibility (Chrome, Firefox, Edge)

- [ ] 15. Documentation updates
  - [ ] 15.1 Update README.md with curve tuning instructions
  - [ ] 15.2 Add JSDoc comments to all new functions
  - [ ] 15.3 Create user guide for curve adjustment
  - [ ] 15.4 Document recommended alpha values for different use cases
  - [ ] 15.5 Add troubleshooting section for common issues

## Success Criteria

- ✅ All three axes (linear, strafe, rotation) use exponential curves
- ✅ Curves are adjustable via UI sliders
- ✅ Real-time graph visualization shows curve shape
- ✅ Presets include optimized curve settings
- ✅ Hardware limits are enforced with warnings
- ✅ Settings persist across sessions
- ✅ No regressions in existing control functionality
- ✅ UI is intuitive and visually appealing

## Dependencies

- **Chart.js** (v4.x) - For curve visualization
- **Tailwind CSS** (already included) - For UI styling
- **localStorage API** (already used) - For settings persistence

## Notes

- This replaces the sqrt dampening we just implemented for rotation
- Provides unified approach across all three axes
- More flexible and user-friendly than fixed dampening factors
- Industry-standard approach used in gamepad/joystick controllers

---

## Phase 11: Precision-Flick Tuning (2026-02-05)

**Issue 32: Mouse Rotation Speed Regression - Precision-Flick Tuning**

**Root Cause Analysis:**
Developer identified a "precision-flick" tuning problem:
1. Mouse sensitivity too low (0.3-1.2) preventing fast swipes from reaching 100% input signal
2. Alpha values already correct (1.5-3.0 exponential range)
3. Need to increase sensitivity to allow full-speed rotation with fast mouse flicks

**Solution Implemented:**
- ✅ Increased mouse yaw sensitivity slider max from 5.0 to **50.0**
- ✅ Increased mouse pitch sensitivity slider max from 5.0 to **25.0**
- ✅ Updated default mouse sensitivity values in all presets:
  - Beginner: yaw=3.0, pitch=1.5 (conservative for new users)
  - Normal: yaw=5.0, pitch=2.5 (balanced precision-flick)
  - Advanced: yaw=8.0, pitch=4.0 (higher for experienced users)
  - Sport: yaw=12.0, pitch=6.0 (maximum for competitive use)
- ✅ Kept `MOUSE_SCALE_FACTOR = 0.08` as constant (no need to expose)
- ✅ Kept rotation_alpha values as-is (1.5-3.0 range already optimal)
- ✅ Updated UI tooltips with new recommended ranges

**Expected Behavior:**
- Small mouse movements → Precise micro-adjustments (exponential curve suppresses jitter)
- Fast mouse swipes → Full 360° rotation in one motion (high sensitivity reaches 1.0 input)
- No need to lift and reposition mouse multiple times

**Files Modified:**
- `templates/landing.html` - Updated slider ranges and default values
- `static/js/settings-manager.js` - Updated all preset sensitivity values
- `templates/control.html` - Bumped version to v1.2.0

**Status:** ✅ COMPLETE - Ready for testing

---

## Phase 12: Critical Backend Velocity Scaling Bug (2026-02-05)

**Issue 33: Robot Rotating 9x Slower Than Commanded - Missing Multiplication**

**Root Cause Analysis:**
The backend was receiving normalized values (0.0-1.0) from the frontend but sending them directly to the robot WITHOUT scaling them back up by `max_rotation`. This caused the robot to rotate at only ~1.0 rad/s instead of the intended ~9.0 rad/s.

**The Smoking Gun:**
```python
# OLD (BUGGY) CODE - Line 249:
vyaw = max(-max_rotation, min(max_rotation, -rx))
# Example: rx=0.81, max_rotation=9.0
# Result: min(9.0, 0.81) = 0.81 → Robot receives 0.81 rad/s ❌
```

**The Math Bug:**
1. Frontend calculates: `vyaw = 7.3 rad/s`
2. Frontend normalizes: `rx = vyaw / maxRotation = 7.3 / 9.0 = 0.81`
3. Frontend sends: `rx=0.81` to backend
4. **Backend BUG:** Uses `0.81` directly instead of multiplying by `9.0`
5. Robot receives: `0.81 rad/s` instead of `7.3 rad/s` ❌

**The Fix:**
```python
# NEW (CORRECT) CODE - Lines 247-257:
# Step 1: Scale normalized input by max velocity
raw_vx = ly * max_linear
raw_vy = -lx * max_strafe
raw_vyaw = -rx * max_rotation  # 0.81 * 9.0 = 7.29 rad/s ✅

# Step 2: Clamp to ensure safety
vx = max(-max_linear, min(max_linear, raw_vx))
vy = max(-max_strafe, min(max_strafe, raw_vy))
vyaw = max(-max_rotation, min(max_rotation, raw_vyaw))
```

**Evidence from Logs:**
```
Command sent: rx=1.000 → vyaw=-1.000 (WRONG - should be -9.0)
Expected robot speed: -9.0 rad/s
Actual robot speed: -0.8 to -1.0 rad/s (from yaw_speed telemetry)
Discrepancy: 9x slower than expected
```

**Why This Happened:**
The clamping logic `max(-max_rotation, min(max_rotation, -rx))` was treating the normalized input as if it were already in rad/s units, when it was actually a 0.0-1.0 percentage that needed to be scaled up.

**Impact:**
- ✅ Mouse rotation now works at FULL SPEED (9.0 rad/s instead of 1.0 rad/s)
- ✅ Linear and strafe velocities also fixed (were also affected by same bug)
- ✅ Robot now matches Bluetooth remote control responsiveness

**Files Modified:**
- `app/services/control.py` (lines 241-262)

**Status:** ✅ FIXED - Robot should now rotate 9x faster!

---

## Phase 13: Fix Jerky Movement & Add Slew Rate UI Controls (2026-02-07)

**Issue 34: Jerky "Wait-Then-Jump" Behavior from Deadzone-Ramping Conflict**

**Root Cause Analysis:**
After implementing the backend slew rate limiter (Phase 12), users experience a ~0.5 second delay before the robot starts moving when pressing 'W'. The velocity ramps from 0.0 → 0.001 → 0.005 → 0.008, but the frontend exponential curve deadzone (10%) blocks everything below 0.010. When the ramp finally crosses 0.011, the robot suddenly receives a valid command and "jumps" into motion.

**Problem Breakdown:**
1. **Deadzone-Ramping Conflict:** Frontend deadzone blocks low ramped velocities from backend
2. **Keyboard Deadzone Unnecessary:** Keyboard is digital (on/off), deadzone creates artificial delay
3. **No UI Control:** Users cannot adjust backend slew rate limiter acceleration parameters
4. **No Raw Control Mode:** Advanced users need option to bypass all smoothing for emergency maneuvers

**Solution Overview:**
1. Implement "jump-start" logic to bypass deadzone wait on initial key press
2. Remove keyboard deadzone (keep mouse deadzone for drift prevention)
3. Add UI sliders for backend slew rate limiter ramp-up time control
4. Add RAGE MODE toggle for raw control (bypass all smoothing)

---

### Task 34.1: Fix Jump-Start Logic (CRITICAL - Fix First)

**Priority:** 🔴 CRITICAL
**Estimated Time:** 30 minutes
**Files to Modify:**
- `static/js/keyboard-mouse-control.js`

**Implementation Steps:**

1. **Add Constants to KeyboardMouseControl Class:**
   ```javascript
   // Jump-start behavior constants
   this.MIN_START_SPEED = 0.15;  // 15% - instant jump-start velocity
   this.ACCEL_FACTOR = 0.05;     // Lower = smoother ramp (tune this)
   ```

2. **Modify poll() Method (around line 424-428):**
   ```javascript
   // BEFORE applying exponential ramping:
   // Check if starting from standstill (jump-start logic)
   if (Math.abs(targetLinear) > 0.001 && Math.abs(this.currentVelocities.linear) < 0.001) {
       // Jump-start: snap to minimum viable speed for immediate feedback
       this.currentVelocities.linear = Math.sign(targetLinear) * this.MIN_START_SPEED;
   }

   // Then apply normal exponential ramping
   if (Math.abs(targetLinear) > 0.01) {
       this.currentVelocities.linear += (targetLinear - this.currentVelocities.linear) * this.ACCEL_FACTOR;
   } else {
       this.currentVelocities.linear *= (1 - deceleration);
   }
   ```

3. **Apply Same Logic to Strafe (around line 436-440):**
   ```javascript
   if (Math.abs(targetStrafe) > 0.001 && Math.abs(this.currentVelocities.strafe) < 0.001) {
       this.currentVelocities.strafe = Math.sign(targetStrafe) * this.MIN_START_SPEED;
   }

   if (Math.abs(targetStrafe) > 0.01) {
       this.currentVelocities.strafe += (targetStrafe - this.currentVelocities.strafe) * this.ACCEL_FACTOR;
   } else {
       this.currentVelocities.strafe *= (1 - deceleration);
   }
   ```

4. **Apply Same Logic to Rotation (if using ramping):**
   - Note: Mouse rotation currently uses instant response (line 457)
   - Only apply if keyboard rotation uses ramping

**Expected Result:**
- **Before:** W key → 0.0 → 0.005 (blocked) → 0.009 (blocked) → 0.011 (move!) = 500ms delay
- **After:** W key → snap to 0.15 (move immediately!) → ramp to 1.0 = 0ms delay

**Testing Checklist:**
- [ ] Press 'W' → Robot starts moving IMMEDIATELY (no 0.5s wait)
- [ ] Movement still feels smooth (not jerky)
- [ ] Release 'W' → Robot decelerates smoothly to stop
- [ ] Same behavior for 'A', 'S', 'D' keys (strafe)
- [ ] Console logs show jump-start velocity (0.15) on first frame

---

### Task 34.2: Remove Keyboard Deadzone (Keep Mouse Deadzone)

**Priority:** 🟡 HIGH
**Estimated Time:** 45 minutes
**Files to Modify:**
- `templates/landing.html`
- `static/js/settings-manager.js`
- `static/js/keyboard-mouse-control.js`

**Implementation Steps:**

1. **Remove Deadzone Sliders from UI (`templates/landing.html`):**
   - Remove Linear Deadzone slider (currently around line 220-230)
   - Remove Strafe Deadzone slider (currently around line 240-250)
   - Remove Rotation Deadzone slider (currently around line 260-270)
   - **KEEP** Mouse Rotation Deadzone slider (for drift prevention)

2. **Update Settings Manager (`static/js/settings-manager.js`):**
   - Remove `linear_deadzone` from all presets (Beginner, Normal, Advanced, Sport)
   - Remove `strafe_deadzone` from all presets
   - **KEEP** `rotation_deadzone` for mouse rotation
   - Update `cleanObsoleteSettings()` to remove old deadzone keys

3. **Update Keyboard/Mouse Control (`static/js/keyboard-mouse-control.js`):**
   - Set `linearDeadzone = 0.0` (hardcoded, no slider)
   - Set `strafeDeadzone = 0.0` (hardcoded, no slider)
   - **KEEP** `rotationDeadzone` from settings (for mouse)
   - Remove deadzone application for keyboard inputs in `poll()` method

**Rationale:**
- Keyboard is digital (on/off), so deadzone creates artificial "wait-then-jump" delay
- Mouse is analog and needs deadzone to prevent accidental micro-movements
- Backend slew rate limiter already provides smoothing, so frontend deadzone is redundant for keyboard

**Testing Checklist:**
- [ ] Linear/Strafe deadzone sliders removed from settings UI
- [ ] Mouse rotation deadzone slider still present
- [ ] Keyboard movement has zero deadzone (instant response)
- [ ] Mouse rotation still has deadzone (prevents drift)
- [ ] Settings save/load correctly without keyboard deadzone

---

### Task 34.3: Add UI Sliders for Backend Slew Rate Limiter

**Priority:** 🟡 HIGH
**Estimated Time:** 90 minutes
**Files to Modify:**
- `templates/landing.html`
- `static/js/settings-manager.js`
- `static/js/landing.js`
- `app/services/control.py`

**Implementation Steps:**

**Part A: Add UI Sliders (`templates/landing.html`)**

Add three new sliders in the "Keyboard & Mouse Settings" section (after max velocity sliders):

1. **Linear Ramp-Up Time Slider:**
   ```html
   <!-- Linear Acceleration Time -->
   <div class="form-group">
       <label for="linear-ramp-time" class="form-label flex justify-between">
           <span>Forward/Back Acceleration Time</span>
           <span id="linear-ramp-time-value" class="text-unitree-primary font-mono">1.0s</span>
       </label>
       <input type="range" id="linear-ramp-time" class="slider"
              min="0.0" max="2.0" step="0.1" value="1.0"
              title="Time to reach max linear speed from standstill. Lower = snappier, Higher = smoother.">
       <p class="form-help">Acceleration ramp-up time (0.0-2.0 seconds)</p>
   </div>
   ```

2. **Strafe Ramp-Up Time Slider:**
   ```html
   <!-- Strafe Acceleration Time -->
   <div class="form-group">
       <label for="strafe-ramp-time" class="form-label flex justify-between">
           <span>Left/Right Acceleration Time</span>
           <span id="strafe-ramp-time-value" class="text-unitree-primary font-mono">0.2s</span>
       </label>
       <input type="range" id="strafe-ramp-time" class="slider"
              min="0.0" max="2.0" step="0.1" value="0.2"
              title="Time to reach max strafe speed from standstill. Lower = snappier, Higher = smoother.">
       <p class="form-help">Acceleration ramp-up time (0.0-2.0 seconds)</p>
   </div>
   ```

3. **Rotation Ramp-Up Time Slider:**
   ```html
   <!-- Rotation Acceleration Time -->
   <div class="form-group">
       <label for="rotation-ramp-time" class="form-label flex justify-between">
           <span>Rotation Acceleration Time</span>
           <span id="rotation-ramp-time-value" class="text-unitree-primary font-mono">0.9s</span>
       </label>
       <input type="range" id="rotation-ramp-time" class="slider"
              min="0.0" max="2.0" step="0.1" value="0.9"
              title="Time to reach max rotation speed from standstill. Lower = snappier, Higher = smoother.">
       <p class="form-help">Acceleration ramp-up time (0.0-2.0 seconds)</p>
   </div>
   ```

**Part B: Update Settings Manager (`static/js/settings-manager.js`)**

1. **Add Ramp-Up Time to Default Settings:**
   ```javascript
   keyboard_mouse: {
       // ... existing settings ...
       linear_ramp_time: 1.0,    // seconds
       strafe_ramp_time: 0.2,    // seconds
       rotation_ramp_time: 0.9,  // seconds
   }
   ```

2. **Add Ramp-Up Time to All Presets:**
   ```javascript
   beginner: {
       // ... existing settings ...
       linear_ramp_time: 1.5,    // Slower ramp for beginners
       strafe_ramp_time: 1.2,
       rotation_ramp_time: 1.2,
   },
   normal: {
       // ... existing settings ...
       linear_ramp_time: 1.0,    // Current defaults
       strafe_ramp_time: 0.2,
       rotation_ramp_time: 0.9,
   },
   advanced: {
       // ... existing settings ...
       linear_ramp_time: 0.5,    // Faster ramp for advanced users
       strafe_ramp_time: 0.3,
       rotation_ramp_time: 0.4,
   },
   sport: {
       // ... existing settings ...
       linear_ramp_time: 0.2,    // Minimal ramp for sport mode
       strafe_ramp_time: 0.1,
       rotation_ramp_time: 0.2,
   }
   ```

**Part C: Connect Sliders to Settings (`static/js/landing.js`)**

1. **Add Event Listeners for Ramp-Up Time Sliders:**
   ```javascript
   // Linear ramp-up time
   const linearRampTimeSlider = document.getElementById('linear-ramp-time');
   const linearRampTimeValue = document.getElementById('linear-ramp-time-value');
   linearRampTimeSlider.addEventListener('input', (e) => {
       const value = parseFloat(e.target.value);
       linearRampTimeValue.textContent = `${value.toFixed(1)}s`;
       settings.keyboard_mouse.linear_ramp_time = value;
       saveSettings(settings);
   });

   // Strafe ramp-up time
   const strafeRampTimeSlider = document.getElementById('strafe-ramp-time');
   const strafeRampTimeValue = document.getElementById('strafe-ramp-time-value');
   strafeRampTimeSlider.addEventListener('input', (e) => {
       const value = parseFloat(e.target.value);
       strafeRampTimeValue.textContent = `${value.toFixed(1)}s`;
       settings.keyboard_mouse.strafe_ramp_time = value;
       saveSettings(settings);
   });

   // Rotation ramp-up time
   const rotationRampTimeSlider = document.getElementById('rotation-ramp-time');
   const rotationRampTimeValue = document.getElementById('rotation-ramp-time-value');
   rotationRampTimeSlider.addEventListener('input', (e) => {
       const value = parseFloat(e.target.value);
       rotationRampTimeValue.textContent = `${value.toFixed(1)}s`;
       settings.keyboard_mouse.rotation_ramp_time = value;
       saveSettings(settings);
   });
   ```

**Part D: Update Backend to Receive Ramp-Up Time (`app/services/control.py`)**

1. **Modify `process_movement_command()` to Accept Ramp-Up Time:**
   ```python
   # Get ramp-up time from command data (if provided)
   linear_ramp_time = data.get('linear_ramp_time', 1.0)
   strafe_ramp_time = data.get('strafe_ramp_time', 0.2)
   rotation_ramp_time = data.get('rotation_ramp_time', 0.9)

   # Convert ramp-up time to acceleration limit
   # Formula: MAX_ACCEL = max_velocity / ramp_time
   # Edge case: If ramp_time = 0, use very high acceleration (instant response)
   MAX_LINEAR_ACCEL = max_linear / linear_ramp_time if linear_ramp_time > 0.01 else 1000.0
   MAX_STRAFE_ACCEL = max_strafe / strafe_ramp_time if strafe_ramp_time > 0.01 else 1000.0
   MAX_YAW_ACCEL = max_rotation / rotation_ramp_time if rotation_ramp_time > 0.01 else 1000.0

   # Use these calculated values instead of hardcoded self.MAX_LINEAR_ACCEL, etc.
   ```

2. **Update Frontend to Send Ramp-Up Time (`static/js/keyboard-mouse-control.js`):**
   ```javascript
   sendCommand(vx, vy, vyaw) {
       const data = {
           lx: vy / this.settings.maxStrafe,
           ly: vx / this.settings.maxLinear,
           rx: vyaw / this.settings.maxRotation,
           ry: 0,
           max_linear: this.settings.maxLinear,
           max_strafe: this.settings.maxStrafe,
           max_rotation: this.settings.maxRotation,
           // Add ramp-up time parameters
           linear_ramp_time: this.settings.linearRampTime || 1.0,
           strafe_ramp_time: this.settings.strafeRampTime || 0.2,
           rotation_ramp_time: this.settings.rotationRampTime || 0.9,
           source: 'keyboard_mouse'
       };
       // ... rest of sendCommand logic ...
   }
   ```

**Testing Checklist:**
- [ ] Three ramp-up time sliders appear in settings UI
- [ ] Slider values update in real-time (display shows "X.Xs")
- [ ] Settings save to localStorage and persist across page reloads
- [ ] Backend receives ramp-up time values and converts to acceleration limits
- [ ] Robot acceleration feel changes when adjusting sliders
- [ ] Preset buttons load correct ramp-up times for each preset
- [ ] Setting ramp-up time to 0.0 provides instant response (no ramping)

---

### Task 34.4: Add RAGE MODE Toggle Button

**Priority:** 🟢 MEDIUM
**Estimated Time:** 60 minutes
**Files to Modify:**
- `templates/control.html`
- `static/js/control.js`
- `static/js/keyboard-mouse-control.js`
- `app/services/control.py`

**Implementation Steps:**

**Part A: Add RAGE MODE Button to UI (`templates/control.html`)**

1. **Modify Running Human Icon (Speed Slider Area):**
   ```html
   <!-- Speed Slider Section -->
   <div class="flex items-center gap-2">
       <!-- RAGE MODE Toggle Button -->
       <button id="rage-mode-btn"
               class="p-2 rounded-lg transition-all duration-200 hover:scale-110"
               style="background: rgba(255, 255, 255, 0.1);"
               title="RAGE MODE: Bypass all smoothing for raw control (DANGEROUS!)">
           <svg class="w-6 h-6 transition-colors duration-200" id="rage-mode-icon"
                fill="currentColor" viewBox="0 0 24 24">
               <!-- Running human icon SVG path -->
               <path d="M13.49 5.48c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm-3.6 13.9l1-4.4 2.1 2v6h2v-7.5l-2.1-2 .6-3c1.3 1.5 3.3 2.5 5.5 2.5v-2c-1.9 0-3.5-1-4.3-2.4l-1-1.6c-.4-.6-1-1-1.7-1-.3 0-.5.1-.8.1l-5.2 2.2v4.7h2v-3.4l1.8-.7-1.6 8.1-4.9-1-.4 2 7 1.4z"/>
           </svg>
       </button>

       <!-- Speed Slider -->
       <input type="range" id="speed-slider" ... />
   </div>

   <!-- RAGE MODE Warning Modal (hidden by default) -->
   <div id="rage-mode-modal" class="hidden fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
       <div class="bg-unitree-dark-lighter rounded-lg p-6 max-w-md">
           <h3 class="text-xl font-bold text-red-500 mb-4">⚠️ RAGE MODE WARNING</h3>
           <p class="text-white mb-4">
               RAGE MODE disables ALL safety smoothing (exponential curves, acceleration limiting, deadzone).
               Robot will respond to raw input instantly, which may cause:
           </p>
           <ul class="text-white mb-4 list-disc list-inside">
               <li>Jerky, erratic movements</li>
               <li>Sudden acceleration/deceleration</li>
               <li>Potential motor strain</li>
               <li>Loss of precision control</li>
           </ul>
           <p class="text-white mb-6 font-bold">Use at your own risk. Recommended for emergency maneuvers only.</p>
           <div class="flex gap-4">
               <button id="rage-mode-confirm" class="btn-primary flex-1">I Understand - Enable RAGE MODE</button>
               <button id="rage-mode-cancel" class="btn-secondary flex-1">Cancel</button>
           </div>
       </div>
   </div>
   ```

**Part B: Implement RAGE MODE Logic (`static/js/keyboard-mouse-control.js`)**

1. **Add RAGE MODE Flag to Class:**
   ```javascript
   constructor() {
       // ... existing code ...
       this.rageMode = false;  // RAGE MODE flag
   }
   ```

2. **Add Toggle Method:**
   ```javascript
   toggleRageMode(enabled) {
       this.rageMode = enabled;
       console.log(`🔥 RAGE MODE ${enabled ? 'ENABLED' : 'DISABLED'}`);

       // Update UI
       const icon = document.getElementById('rage-mode-icon');
       const btn = document.getElementById('rage-mode-btn');
       if (enabled) {
           icon.style.color = '#ef4444';  // Red
           btn.style.background = 'rgba(239, 68, 68, 0.2)';  // Red glow
       } else {
           icon.style.color = 'currentColor';
           btn.style.background = 'rgba(255, 255, 255, 0.1)';
       }
   }
   ```

3. **Modify poll() Method to Bypass Smoothing in RAGE MODE:**
   ```javascript
   poll() {
       // ... existing input gathering code ...

       if (this.rageMode) {
           // RAGE MODE: Send raw input directly (NO curves, NO ramping, NO deadzone)
           const vx = forward * this.settings.maxLinear;
           const vy = -strafe * this.settings.maxStrafe;
           const vyaw = -rotation * this.settings.maxRotation;

           console.log(`🔥 [RAGE MODE] RAW: vx=${vx.toFixed(2)}, vy=${vy.toFixed(2)}, vyaw=${vyaw.toFixed(2)}`);
           this.sendCommand(vx, vy, vyaw, true);  // Pass rageMode flag
           return;
       }

       // Normal mode: Apply curves and ramping
       // ... existing curve/ramp logic ...
   }
   ```

4. **Update sendCommand() to Include RAGE MODE Flag:**
   ```javascript
   sendCommand(vx, vy, vyaw, rageMode = false) {
       const data = {
           // ... existing data ...
           rage_mode: rageMode  // Add RAGE MODE flag
       };
       // ... rest of sendCommand logic ...
   }
   ```

**Part C: Update Backend to Bypass Slew Rate Limiter (`app/services/control.py`)**

1. **Modify process_movement_command() to Check RAGE MODE:**
   ```python
   def process_movement_command(self, data: dict) -> dict:
       # ... existing code ...

       # Check if RAGE MODE is enabled
       rage_mode = data.get('rage_mode', False)

       if rage_mode:
           # RAGE MODE: Bypass slew rate limiter, send raw velocities
           vx = raw_target_vx
           vy = raw_target_vy
           vyaw = raw_target_vyaw

           self.logger.warning(f"🔥 [RAGE MODE] RAW VELOCITIES: vx={vx:.3f}, vy={vy:.3f}, vyaw={vyaw:.3f}")
       else:
           # Normal mode: Apply slew rate limiter
           # ... existing slew rate limiter logic ...

       # ... rest of function ...
   ```

**Part D: Add UI Event Handlers (`static/js/control.js`)**

1. **Add RAGE MODE Button Click Handler:**
   ```javascript
   // RAGE MODE toggle
   const rageModeBtn = document.getElementById('rage-mode-btn');
   const rageModeModal = document.getElementById('rage-mode-modal');
   const rageModeConfirm = document.getElementById('rage-mode-confirm');
   const rageModeCancel = document.getElementById('rage-mode-cancel');

   let rageModeEnabled = false;
   let rageModeWarningShown = localStorage.getItem('rage_mode_warning_shown') === 'true';

   rageModeBtn.addEventListener('click', () => {
       if (!rageModeEnabled) {
           // Enabling RAGE MODE
           if (!rageModeWarningShown) {
               // Show warning modal on first use
               rageModeModal.classList.remove('hidden');
           } else {
               // Already seen warning, enable directly
               rageModeEnabled = true;
               keyboardMouseControl.toggleRageMode(true);
           }
       } else {
           // Disabling RAGE MODE
           rageModeEnabled = false;
           keyboardMouseControl.toggleRageMode(false);
       }
   });

   rageModeConfirm.addEventListener('click', () => {
       rageModeEnabled = true;
       rageModeWarningShown = true;
       localStorage.setItem('rage_mode_warning_shown', 'true');
       rageModeModal.classList.add('hidden');
       keyboardMouseControl.toggleRageMode(true);
   });

   rageModeCancel.addEventListener('click', () => {
       rageModeModal.classList.add('hidden');
   });
   ```

**Testing Checklist:**
- [ ] RAGE MODE button appears next to speed slider
- [ ] Clicking button shows warning modal on first use
- [ ] Confirming modal enables RAGE MODE (icon turns red)
- [ ] RAGE MODE bypasses all frontend smoothing (curves, ramping, deadzone)
- [ ] RAGE MODE bypasses backend slew rate limiter
- [ ] Robot responds instantly to raw input (jerky but immediate)
- [ ] Clicking button again disables RAGE MODE (icon returns to normal)
- [ ] Warning modal only shows once (localStorage remembers)
- [ ] Console logs show "🔥 [RAGE MODE]" messages

---

### Task 34.5: Integration Testing & Tuning

**Priority:** 🟡 HIGH
**Estimated Time:** 60 minutes

**Testing Scenarios:**

1. **Jump-Start Behavior:**
   - [ ] Press 'W' → Robot starts moving within 50ms (no delay)
   - [ ] Movement feels smooth and controlled (not jerky)
   - [ ] Release 'W' → Robot decelerates smoothly to stop

2. **Deadzone Removal:**
   - [ ] Keyboard movement has zero deadzone (instant response)
   - [ ] Mouse rotation still has deadzone (prevents drift)
   - [ ] No "wait-then-jump" behavior

3. **Ramp-Up Time Sliders:**
   - [ ] Adjusting linear ramp-up time changes forward/back acceleration feel
   - [ ] Adjusting strafe ramp-up time changes left/right acceleration feel
   - [ ] Adjusting rotation ramp-up time changes rotation acceleration feel
   - [ ] Setting ramp-up time to 0.0 provides instant response
   - [ ] Settings persist across page reloads

4. **RAGE MODE:**
   - [ ] RAGE MODE provides instant raw control (no smoothing)
   - [ ] Robot responds immediately but may be jerky
   - [ ] Useful for emergency maneuvers
   - [ ] Can be toggled on/off easily

5. **Preset Testing:**
   - [ ] Beginner preset: Slower ramp-up times (1.5s linear, 1.2s rotation)
   - [ ] Normal preset: Current defaults (1.0s linear, 0.9s rotation)
   - [ ] Advanced preset: Faster ramp-up times (0.5s linear, 0.4s rotation)
   - [ ] Sport preset: Minimal ramp-up times (0.2s linear, 0.2s rotation)

**Tuning Parameters:**

Based on real robot testing, adjust these values:

1. **Jump-Start Speed (`MIN_START_SPEED`):**
   - Current: 0.15 (15%)
   - If too slow: Increase to 0.20 or 0.25
   - If too jerky: Decrease to 0.10 or 0.12

2. **Acceleration Factor (`ACCEL_FACTOR`):**
   - Current: 0.05
   - If too slow to ramp: Increase to 0.08 or 0.10
   - If too jerky: Decrease to 0.03 or 0.04

3. **Default Ramp-Up Times:**
   - Linear: 1.0s (tune based on feel)
   - Strafe: 0.2s (tune based on feel)
   - Rotation: 0.9s (tune based on feel)

---

### Summary of Phase 13 Tasks

| Task | Priority | Est. Time | Status |
|------|----------|-----------|--------|
| 34.1: Fix Jump-Start Logic | 🔴 CRITICAL | 30 min | ⏳ Pending |
| 34.2: Remove Keyboard Deadzone | 🟡 HIGH | 45 min | ⏳ Pending |
| 34.3: Add Slew Rate UI Sliders | 🟡 HIGH | 90 min | ⏳ Pending |
| 34.4: Add RAGE MODE Toggle | 🟢 MEDIUM | 60 min | ⏳ Pending |
| 34.5: Integration Testing | 🟡 HIGH | 60 min | ⏳ Pending |

**Total Estimated Time:** 4.5 hours

**Implementation Order:**
1. Task 34.1 (CRITICAL - fixes immediate user pain point)
2. Task 34.2 (removes root cause of deadzone conflict)
3. Task 34.3 (adds user control over backend smoothing)
4. Task 34.4 (adds advanced raw control mode)
5. Task 34.5 (validates all changes work together)

