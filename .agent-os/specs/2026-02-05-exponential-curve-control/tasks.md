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

- [ ] 9. Update preset system with curve settings
  - [ ] 9.1 Define curve values for beginner preset (high alpha, smooth)
  - [ ] 9.2 Define curve values for normal preset (balanced alpha)
  - [ ] 9.3 Define curve values for advanced preset (lower alpha, responsive)
  - [ ] 9.4 Define curve values for sport preset (low alpha, aggressive)
  - [ ] 9.5 Update `applyPreset()` function to change curve settings
  - [ ] 9.6 Update graphs when preset is selected
  - [ ] 9.7 Test switching between all four presets
  - [ ] 9.8 Verify preset switching updates all three axes

- [ ] 10. Add reset and apply buttons
  - [ ] 10.1 Add "Reset to Defaults" button to curve tuning panel
  - [ ] 10.2 Implement reset functionality (restore default alpha/deadzone)
  - [ ] 10.3 Add "Apply Preset" dropdown to curve tuning panel
  - [ ] 10.4 Connect dropdown to `applyPreset()` function
  - [ ] 10.5 Test reset button restores correct defaults
  - [ ] 10.6 Test preset dropdown applies correct curve values

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

