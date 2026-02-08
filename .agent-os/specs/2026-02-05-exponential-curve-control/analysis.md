# Exponential Curve Control System - Analysis

> Created: 2026-02-05
> Status: Analysis Complete

## 1. Overview

This document analyzes the exponential curve control system from `examples/go2/controlsadjustments.py` and provides an implementation plan for integrating it into the web-based control interface.

## 2. Analysis of `controlsadjustments.py`

### 2.1 Core Formula

The `scale_input()` function implements a non-linear response curve:

```python
def scale_input(input_pct, max_val, alpha, deadzone=0.10):
    # Map the range [deadzone, 1.0] to [0.0, 1.0]
    normalized_input = (input_pct - deadzone) / (1.0 - deadzone)
    # Apply exponential curve
    output = (normalized_input ** alpha) * max_val
    return output
```

**Formula Breakdown:**
1. **Deadzone Removal:** `(input - deadzone) / (1.0 - deadzone)` → Maps [deadzone, 1.0] to [0.0, 1.0]
2. **Exponential Scaling:** `normalized_input ^ alpha` → Applies curve shape
3. **Max Velocity Scaling:** `* max_val` → Scales to actual velocity units

### 2.2 Alpha (α) Parameter Effects

| Alpha Value | Curve Shape | Use Case | Responsiveness |
|-------------|-------------|----------|----------------|
| **α < 1.0** | Concave (fast start, slow end) | High precision at low speeds | Very responsive |
| **α = 1.0** | Linear (straight line) | Proportional response | Neutral |
| **α > 1.0** | Convex (slow start, fast end) | Smooth acceleration | Less responsive |

**Example Values from Streamlit Tool:**
- **Linear (Forward/Back):** α = 1.5 (moderate exponential)
- **Strafe (Left/Right):** α = 1.2 (slight exponential)
- **Rotation (Yaw):** α = 2.5 (strong exponential for fine control)

### 2.3 Deadzone Implementation

- **Purpose:** Ignore small inputs to prevent drift/noise
- **Range:** 0% to 30% (typically 10%)
- **Effect:** Inputs below deadzone produce zero output
- **Visual:** Red dashed line on graph

### 2.4 Visualization Features

The Streamlit tool provides:
1. **Three separate graphs** (Linear, Strafe, Rotation)
2. **Real-time curve updates** as sliders change
3. **Filled area under curve** (visual feedback)
4. **Deadzone indicator** (red dashed line)
5. **Reference table** showing output at 10%, 25%, 50%, 75%, 100% input

## 3. Comparison: Sqrt Dampening vs Exponential Curve

### 3.1 Current Implementation (Sqrt Dampening)

```javascript
const rotationMultiplier = Math.sqrt(speedMultiplier);
const rotationSpeed = Math.min(BASE_ROTATION, BASE_ROTATION * rotationMultiplier);
```

**Characteristics:**
- Fixed curve shape (always square root)
- No user adjustment
- Clamped at hardware limit
- Only applies to rotation

### 3.2 Proposed Implementation (Exponential Curve)

```javascript
const normalizedInput = (input - deadzone) / (1.0 - deadzone);
const output = Math.pow(normalizedInput, alpha) * maxVelocity;
```

**Characteristics:**
- Adjustable curve shape (alpha parameter)
- User-configurable via UI
- Applies to all three axes (linear, strafe, rotation)
- More flexible and powerful

### 3.3 Recommendation

**Replace sqrt dampening with exponential curve system for consistency:**
- ✅ Unified approach across all axes
- ✅ User can fine-tune each axis independently
- ✅ More intuitive (higher alpha = smoother, lower alpha = more responsive)
- ✅ Matches industry-standard gamepad/joystick response curves

## 4. Implementation Architecture

### 4.1 Data Flow

```
User Input (0-100%) 
  → Apply Deadzone 
  → Normalize to [0, 1] 
  → Apply Exponential Curve (^alpha) 
  → Scale to Max Velocity 
  → Clamp to Hardware Limit 
  → Send to Robot
```

### 4.2 Settings Storage (localStorage)

```javascript
{
  keyboard_mouse: {
    // Existing settings
    kb_max_linear_velocity: 1.5,
    kb_max_strafe_velocity: 1.2,
    kb_max_rotation_velocity: 3.0,
    
    // New curve settings
    linear_alpha: 1.5,
    linear_deadzone: 0.10,
    strafe_alpha: 1.2,
    strafe_deadzone: 0.10,
    rotation_alpha: 2.5,
    rotation_deadzone: 0.10
  }
}
```

### 4.3 Integration Points

1. **`static/js/keyboard-mouse-control.js`**
   - `poll()` method: Apply curve to WASD input
   - `handleMouseWheel()`: Apply curve to speed adjustment
   - `loadSettings()`: Load alpha/deadzone values

2. **`static/js/control.js`**
   - `initializeSpeedSlider()`: Apply curve to slider input
   - New function: `initializeCurveAdjustment()` for UI

3. **`static/js/settings-manager.js`**
   - Add alpha/deadzone to default settings
   - Add to all presets (beginner/normal/advanced/sport)

4. **`templates/landing.html`** or **`templates/control.html`**
   - Add curve adjustment UI panel
   - Add Chart.js for visualization

## 5. UI Design Proposal

### 5.1 Location Options

**Option A: Landing Page Settings Panel** (Recommended)
- ✅ Centralized configuration
- ✅ Adjust before connecting to robot
- ✅ Consistent with existing settings UI
- ❌ Not accessible during active control

**Option B: Control Page Quick Settings**
- ✅ Adjust during active control
- ✅ Immediate feedback
- ❌ More complex UI overlay
- ❌ Potential distraction during operation

**Option C: New "Advanced Tuning" Section**
- ✅ Separates basic vs advanced settings
- ✅ Cleaner UI organization
- ❌ Extra navigation step
- ❌ May hide important settings

**Recommendation:** Option A (Landing Page) with Option B (Quick Settings) for read-only display

### 5.2 UI Components

```
┌─────────────────────────────────────────────────────────┐
│ ⚙️ Response Curve Tuning                                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ [Linear Graph] [Strafe Graph] [Rotation Graph]         │
│                                                          │
│ Linear (Forward/Back):                                  │
│   Alpha: [====●====] 1.5  (0.5 - 4.0)                  │
│   Deadzone: [==●======] 10%  (0% - 30%)                │
│   Max Velocity: [1.5 m/s]                              │
│                                                          │
│ Strafe (Left/Right):                                    │
│   Alpha: [===●=====] 1.2  (0.5 - 4.0)                  │
│   Deadzone: [==●======] 10%  (0% - 30%)                │
│   Max Velocity: [0.6 m/s]                              │
│                                                          │
│ Rotation (Yaw):                                         │
│   Alpha: [=======●=] 2.5  (0.5 - 4.0)                  │
│   Deadzone: [==●======] 10%  (0% - 30%)                │
│   Max Velocity: [3.0 rad/s]                            │
│                                                          │
│ [Reset to Defaults] [Apply Preset ▼]                   │
└─────────────────────────────────────────────────────────┘
```

### 5.3 Charting Library Selection

**Option A: Chart.js** (Recommended)
- ✅ Lightweight (60KB minified)
- ✅ Simple API
- ✅ Good documentation
- ✅ Responsive and interactive
- ❌ Less feature-rich than Plotly

**Option B: Plotly.js**
- ✅ Very feature-rich
- ✅ Beautiful default styling
- ✅ Interactive zoom/pan
- ❌ Large bundle size (3MB+)
- ❌ Overkill for simple line charts

**Option C: D3.js**
- ✅ Maximum flexibility
- ✅ Industry standard
- ❌ Steep learning curve
- ❌ Requires custom implementation

**Recommendation:** Chart.js for simplicity and performance

## 6. Preset Configuration

### 6.1 Recommended Alpha Values by Preset

| Preset | Linear α | Strafe α | Rotation α | Deadzone | Rationale |
|--------|----------|----------|------------|----------|-----------|
| **Beginner** | 1.8 | 1.5 | 3.0 | 15% | Smooth, forgiving, high deadzone |
| **Normal** | 1.5 | 1.2 | 2.5 | 10% | Balanced, default values |
| **Advanced** | 1.2 | 1.0 | 2.0 | 5% | More responsive, lower deadzone |
| **Sport** | 1.0 | 0.8 | 1.5 | 5% | Linear/aggressive, minimal deadzone |

**Design Philosophy:**
- **Higher alpha** = Smoother acceleration, more forgiving for beginners
- **Lower alpha** = More responsive, better for experienced users
- **Rotation always has highest alpha** = Fine control for precise turning

### 6.2 Per-Preset vs Global Settings

**Recommendation: Per-Preset Settings**

**Rationale:**
- ✅ Each preset can have optimized curve for skill level
- ✅ Switching presets changes entire control feel
- ✅ Beginner preset can have very smooth curves
- ✅ Sport preset can have aggressive curves
- ❌ More complex to implement
- ❌ More settings to manage

**Alternative: Global Settings**
- ✅ Simpler implementation
- ✅ User has full control
- ❌ Preset switching only changes max velocities
- ❌ Less cohesive preset experience

## 7. Hardware Limit Enforcement

### 7.1 Current Limits (from robot specifications)

```javascript
const HARDWARE_LIMITS = {
  linear: 5.0,    // m/s
  strafe: 0.6,    // m/s
  rotation: 3.0   // rad/s
};
```

### 7.2 Clamping Strategy

```javascript
function applyCurve(input, alpha, deadzone, maxVelocity, hardwareLimit) {
  // Apply deadzone
  if (input < deadzone) return 0;

  // Normalize to [0, 1]
  const normalized = (input - deadzone) / (1.0 - deadzone);

  // Apply exponential curve
  const curved = Math.pow(normalized, alpha);

  // Scale to max velocity
  const scaled = curved * maxVelocity;

  // Clamp to hardware limit
  return Math.min(scaled, hardwareLimit);
}
```

### 7.3 Warning System

If `maxVelocity > hardwareLimit`, show warning in UI:
```
⚠️ Warning: Max velocity (1.2 m/s) exceeds hardware limit (0.6 m/s)
Output will be clamped to 0.6 m/s
```

## 8. Testing Strategy

### 8.1 Unit Tests

1. **Curve Function Tests:**
   - Test deadzone behavior (input < deadzone → output = 0)
   - Test alpha = 1.0 produces linear response
   - Test alpha > 1.0 produces convex curve
   - Test alpha < 1.0 produces concave curve
   - Test hardware limit clamping

2. **Settings Persistence Tests:**
   - Test alpha values save/load correctly
   - Test deadzone values save/load correctly
   - Test preset switching updates curve settings

### 8.2 Integration Tests

1. **Keyboard/Mouse Control:**
   - Test WASD input applies curve correctly
   - Test mouse rotation applies curve correctly
   - Test speed slider applies curve correctly

2. **UI Tests:**
   - Test sliders update graph in real-time
   - Test preset selector updates all curve settings
   - Test reset button restores defaults

### 8.3 Manual Testing Checklist

- [ ] Adjust alpha slider → Graph updates immediately
- [ ] Adjust deadzone slider → Graph shows deadzone line
- [ ] Move WASD keys → Robot responds with curved velocity
- [ ] Rotate mouse → Robot turns with curved velocity
- [ ] Switch presets → All curves update to preset values
- [ ] Refresh page → Settings persist from localStorage
- [ ] Test at 10%, 25%, 50%, 75%, 100% input → Verify output matches curve

## 9. Implementation Phases

### Phase 1: Core Curve System (Backend)
- Implement `applyCurve()` function in JavaScript
- Add alpha/deadzone to settings structure
- Update `loadSettings()` to load curve parameters
- Add hardware limit clamping

### Phase 2: Integration with Control System
- Apply curve in `keyboard-mouse-control.js` poll method
- Apply curve in speed slider handler
- Apply curve in mouse wheel handler
- Test with existing control interface

### Phase 3: UI Visualization
- Add Chart.js library
- Create curve graph component
- Implement real-time graph updates
- Add sliders for alpha/deadzone adjustment

### Phase 4: Preset Integration
- Add curve settings to all presets
- Update preset selector to change curves
- Add reset to defaults button
- Test preset switching

### Phase 5: Polish & Testing
- Add warning system for hardware limit violations
- Add reference table (like Streamlit example)
- Comprehensive testing
- Documentation updates

## 10. Answers to User Questions

### Q1: Should we replace sqrt dampening with exponential curve?

**Answer: YES**

**Rationale:**
- ✅ Exponential curve is more flexible (adjustable alpha)
- ✅ Provides consistency across all three axes
- ✅ Industry-standard approach (used in gamepad controllers)
- ✅ User can achieve sqrt-like behavior with α ≈ 0.5
- ✅ Better user experience with visual feedback

### Q2: Where should curve adjustment panel be placed?

**Answer: Landing Page Settings Panel (Primary) + Control Page Quick Settings (Secondary)**

**Rationale:**
- **Landing Page:** Full curve adjustment UI with graphs and sliders
- **Control Page:** Read-only display showing current curve settings
- **Quick Settings Modal:** Optional simplified adjustment during active control

### Q3: Per-preset or global curve settings?

**Answer: Per-Preset Settings**

**Rationale:**
- Each preset represents a different skill level/control style
- Beginner preset should have smooth curves (high alpha)
- Sport preset should have aggressive curves (low alpha)
- More cohesive user experience when switching presets
- Advanced users can still create custom preset with their preferred curves

## 11. Next Steps

See `tasks.md` for detailed implementation tasks.

