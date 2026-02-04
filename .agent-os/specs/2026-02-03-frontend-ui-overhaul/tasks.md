# Spec Tasks

These are the tasks to be completed for the spec detailed in @.agent-os/specs/2026-02-03-frontend-ui-overhaul/spec.md

> Created: 2026-02-03
> Status: Ready for Implementation

## Tasks

### Phase 1: Foundation Setup

- [x] 1. Set up Tailwind CSS and base templates
  - [x] 1.1 Create `templates/base.html` with Tailwind CDN
  - [x] 1.2 Add Tailwind configuration with custom colors (updated to teal/cyan #00E8DA)
  - [x] 1.3 Create `static/css/custom.css` for additional styles
  - [x] 1.4 Create `static/js/` directory structure
  - [x] 1.5 Test Tailwind CSS loads correctly in browser
  - [x] 1.6 Verify custom color palette works

- [x] 2. Create empty page templates
  - [x] 2.1 Create `templates/landing.html` extending base.html
  - [x] 2.2 Create `templates/control.html` extending base.html
  - [x] 2.3 Add basic page structure (header, main, footer)
  - [x] 2.4 Test pages render without errors

- [x] 3. Update Flask routes
  - [x] 3.1 Modify `/` route to render `landing.html`
  - [x] 3.2 Create `/control` route to render `control.html`
  - [x] 3.3 Create `/test` route for old `index.html` (temporary)
  - [x] 3.4 Test all routes are accessible
  - [x] 3.5 Verify old interface still works at `/test`

### Phase 2: Landing Page Development

- [x] 4. Create robot management JavaScript module
  - [x] 4.1 Create `static/js/robot-manager.js`
  - [x] 4.2 Implement `loadRobots()` function
  - [x] 4.3 Implement `saveRobot()` function
  - [x] 4.4 Implement `deleteRobot()` function
  - [x] 4.5 Implement `getRobot()` function
  - [x] 4.6 Implement `updateLastConnected()` function
  - [x] 4.7 Test LocalStorage operations in browser console

- [x] 5. Build robot dashboard UI
  - [x] 5.1 Create robot card HTML structure
  - [x] 5.2 Style robot cards with Tailwind CSS
  - [x] 5.3 Implement grid layout for robot cards
  - [x] 5.4 Add "Add Robot" button (already existed from Task 1)
  - [x] 5.5 Render robot cards from LocalStorage
  - [x] 5.6 Test robot cards display correctly

- [x] 6. Implement add/edit robot modal
  - [x] 6.1 Create modal HTML structure
  - [x] 6.2 Style modal with Tailwind CSS
  - [x] 6.3 Implement form fields (connection method, IP, serial, etc.)
  - [x] 6.4 Add conditional field visibility based on connection method
  - [x] 6.5 Implement form validation
  - [x] 6.6 Connect "Save" button to `saveRobot()`
  - [x] 6.7 Test add robot workflow
  - [x] 6.8 Test edit robot workflow
  - [x] 6.9 **UI Improvements (2026-02-03)**
    - [x] 6.9.1 Update form validation: Serial Number is now optional
    - [x] 6.9.2 Implement conditional validation: Either IP OR Serial Number required
    - [x] 6.9.3 Apply glass-morphism design to modal (transparency, blur, rounded corners)
    - [x] 6.9.4 Improve modal spacing and padding (2rem)
    - [x] 6.9.5 Add smooth transitions and hover effects
    - [x] 6.9.6 Enhance input field styling with better focus states
    - [x] 6.9.7 Apply glass-morphism to robot cards (16px border-radius, subtle shadows)
    - [x] 6.9.8 Improve card hover effects (elevation, border glow)
    - [x] 6.9.9 Add favicon to `static/images/favicon.ico`
    - [x] 6.9.10 Update `base.html` to reference favicon correctly

- [x] 7. Implement delete robot functionality (COMPLETED IN TASK 5)
  - [x] 7.1 Add delete button to robot cards
  - [x] 7.2 Implement confirmation dialog
  - [x] 7.3 Connect delete button to `deleteRobot()`
  - [x] 7.4 Test delete robot workflow

- [x] 8. Build settings panel
  - [x] 8.1 Create `static/js/settings-manager.js`
  - [x] 8.2 Implement `loadSettings()` function
  - [x] 8.3 Implement `saveSettings()` function
  - [x] 8.4 Implement `getDefaultSettings()` function
  - [x] 8.5 Create settings panel HTML structure
  - [x] 8.6 Add keyboard/mouse sensitivity sliders
  - [x] 8.7 Add gamepad sensitivity sliders
  - [x] 8.8 Add velocity limit inputs
  - [x] 8.9 Implement collapsible panel behavior
  - [x] 8.10 Connect sliders to `saveSettings()`
  - [x] 8.11 Test settings persistence
  - [x] 8.12 Add gamepad preset selector (beginner, normal, advanced, sport)
  - [x] 8.13 Add reset to defaults button
  - [x] 8.14 Add slider styles with glass-morphism design

- [x] 9. Implement connect functionality (COMPLETED IN TASK 5)
  - [x] 9.1 Add "Connect" button to robot cards
  - [x] 9.2 Implement connection logic (stores robot ID in sessionStorage)
  - [x] 9.3 Update lastConnected timestamp
  - [x] 9.4 Redirect to `/control` on successful connection
  - [x] 9.5 Test connection workflow

### Phase 3: Control Interface Development

- [x] 10. Create fullscreen video layout (COMPLETED IN TASK 2)
  - [x] 10.1 Add video element to `control.html`
  - [x] 10.2 Style video for fullscreen (100vw x 100vh)
  - [x] 10.3 Connect video to `/video_feed` endpoint
  - [x] 10.4 Test video streaming works (requires connection implementation)

- [x] 11. Build status HUD overlay (COMPLETED IN TASK 2)
  - [x] 11.1 Create HUD HTML structure
  - [x] 11.2 Style HUD with semi-transparent background
  - [x] 11.3 Add battery level display (icon + percentage + progress bar)
  - [x] 11.4 Add ping display (icon + ms value)
  - [x] 11.5 Add mode badge display
  - [x] 11.6 Position HUD in top-left corner
  - [x] 11.7 Test HUD displays correctly

- [x] 12. Implement status data fetching
  - [x] 12.1 Create `/api/robot/status` endpoint in Flask
  - [x] 12.2 Implement status polling in JavaScript (every 1-2 seconds)
  - [x] 12.3 Update HUD with fetched data
  - [x] 12.4 Handle API errors gracefully
  - [ ] 12.5 Test status updates in real-time

- [x] 13. Implement light level slider
  - [x] 13.1 Add slider to HUD
  - [x] 13.2 Style slider with Tailwind CSS
  - [x] 13.3 Create `/api/robot/light` endpoint in Flask
  - [x] 13.4 Implement slider change handler
  - [x] 13.5 Debounce API calls (avoid sending on every pixel)
  - [x] 13.6 Show current value next to slider
  - [x] 13.7 Test light level control
  - [x] 13.8 Update slider to use 0-10 discrete levels (UX improvement)
  - [x] 13.9 Add keyboard controls (Left/Right arrow keys)
  - [x] 13.10 Add visual feedback on brightness change

- [x] 14. Extract and integrate control logic
  - [x] 14.1 Create `static/js/websocket-client.js`
  - [x] 14.2 Extract WebSocket initialization from `index.html`
  - [x] 14.3 Extract keyboard control logic
  - [x] 14.4 Extract mouse control logic (Pointer Lock)
  - [x] 14.5 Extract gamepad control logic
  - [x] 14.6 Implement `sendControlCommand()` function
  - [x] 14.7 Implement latency measurement (reuses old system pattern)
  - [x] 14.8 Add color-coded latency display
  - [x] 14.9 Auto-enable keyboard/mouse control on page load
  - [x] 14.10 Test keyboard controls work
  - [x] 14.11 Test mouse controls work
  - [ ] 14.12 Test gamepad controls work (deferred - will complete later)
  - [x] 14.13 Extract mouse wheel speed control from old interface (2026-02-04)
  - [x] 14.14 Add speed indicator overlay with auto-hide (2026-02-04)
  - [ ] 14.15 Refine mouse wheel speed control (deferred - will complete during preset adjustments)
    - [ ] 14.15.1 Review speed adjustment increments (currently 0.2x steps)
    - [ ] 14.15.2 Consider separate speed multipliers for linear vs strafe
    - [ ] 14.15.3 Integrate with preset system (beginner/normal/advanced/sport)
    - [ ] 14.15.4 Add visual feedback improvements (e.g., show current preset name)
    - [ ] 14.15.5 Test speed control with different presets

- [ ] 15. Add quick settings modal
  - [ ] 15.1 Create quick settings button (floating, bottom-right)
  - [ ] 15.2 Create settings modal overlay
  - [ ] 15.3 Reuse settings panel from landing page
  - [ ] 15.4 Implement modal open/close behavior
  - [ ] 15.5 Test quick settings during active control

- [x] 16. Implement exit functionality (COMPLETED 2026-02-04)
  - [x] 16.1 Add exit button (floating, top-right) - Moved to HUD (already exists)
  - [x] 16.2 Implement disconnect logic (call `/disconnect` API)
  - [x] 16.3 Clear connection state from LocalStorage
  - [x] 16.4 Update last connected timestamp
  - [x] 16.5 Redirect to landing page
  - [x] 16.6 Test exit workflow
  - [x] 16.7 Fix disconnect cleanup order (heartbeat, topics, WebRTC)
  - [x] 16.8 Suppress expected errors during disconnect (video/audio)
  - [x] 16.9 Reduce console logging verbosity (WebSocket, Werkzeug)

### Phase 4: Integration & Testing

- [ ] 17. Test complete navigation flow
  - [ ] 17.1 Test landing → control → landing flow
  - [ ] 17.2 Test connection state persistence
  - [ ] 17.3 Test settings persistence across pages
  - [ ] 17.4 Test multiple connect/disconnect cycles

- [ ] 18. Cross-browser testing
  - [ ] 18.1 Test in Chrome 90+
  - [ ] 18.2 Test in Firefox 88+
  - [ ] 18.3 Test in Edge 90+
  - [ ] 18.4 Fix any browser-specific issues

- [ ] 19. Performance testing
  - [ ] 19.1 Measure page load times
  - [ ] 19.2 Measure video streaming latency
  - [ ] 19.3 Measure control command latency
  - [ ] 19.4 Optimize if needed

- [ ] 20. Final cleanup and deployment
  - [ ] 20.1 Remove `/test` route
  - [ ] 20.2 Delete old `templates/index.html`
  - [ ] 20.3 Update documentation
  - [ ] 20.4 Commit changes to `ui-overhaul` branch
  - [ ] 20.5 Create pull request
  - [ ] 20.6 Merge to main after review

