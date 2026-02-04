# Tests Specification

This is the tests coverage details for the spec detailed in @.agent-os/specs/2026-02-03-frontend-ui-overhaul/spec.md

> Created: 2026-02-03
> Version: 1.0.0

## Overview

This document outlines the testing strategy for the frontend UI overhaul. Testing will focus on JavaScript functionality, user workflows, and integration with existing backend services.

## Test Categories

### Unit Tests (JavaScript)

**Testing Framework:** Jest or Mocha (to be determined based on project setup)

**Alternative:** Manual testing with browser console for initial phase

#### robot-manager.js

**Test Suite: Robot CRUD Operations**

- **Test:** `loadRobots()` returns empty array when LocalStorage is empty
- **Test:** `loadRobots()` returns parsed robot array from LocalStorage
- **Test:** `saveRobot()` adds new robot to LocalStorage
- **Test:** `saveRobot()` updates existing robot by ID
- **Test:** `deleteRobot()` removes robot from LocalStorage
- **Test:** `getRobot()` returns correct robot by ID
- **Test:** `getRobot()` returns null for non-existent ID
- **Test:** `updateLastConnected()` updates timestamp for robot

**Test Suite: Data Validation**

- **Test:** Robot object has required fields (id, connectionMethod, ip)
- **Test:** UUID generation creates unique IDs
- **Test:** Connection method validation (LocalSTA, LocalAP, Remote)
- **Test:** IP address format validation (basic regex)

#### settings-manager.js

**Test Suite: Settings Persistence**

- **Test:** `loadSettings()` returns default settings when LocalStorage is empty
- **Test:** `loadSettings()` returns saved settings from LocalStorage
- **Test:** `saveSettings()` persists settings to LocalStorage
- **Test:** `getDefaultSettings()` returns complete default settings object
- **Test:** Settings merge correctly (partial updates don't lose other settings)

**Test Suite: Settings Validation**

- **Test:** Sensitivity values are within valid range (0-2)
- **Test:** Velocity limits are positive numbers
- **Test:** Deadzone values are between 0 and 1

#### websocket-client.js

**Test Suite: WebSocket Connection**

- **Test:** `initializeWebSocket()` creates Socket.IO connection
- **Test:** Connection event handler fires on successful connection
- **Test:** Disconnect event handler fires on connection loss
- **Test:** Reconnect logic attempts reconnection

**Test Suite: Command Sending**

- **Test:** `sendControlCommand()` emits correct event with data
- **Test:** Command data structure is valid (vx, vy, vyaw)
- **Test:** Commands are throttled/debounced appropriately

**Mocking Requirements:**
- Mock Socket.IO client library
- Mock WebSocket connection events
- Mock server responses

### Integration Tests

#### Landing Page Workflow

**Test Suite: Robot Management Flow**

- **Test:** Add robot button opens modal
- **Test:** Add robot form validates required fields
- **Test:** Save robot adds card to dashboard
- **Test:** Edit robot button opens modal with pre-filled data
- **Test:** Update robot saves changes to LocalStorage
- **Test:** Delete robot removes card from dashboard
- **Test:** Delete robot shows confirmation dialog

**Test Suite: Connection Flow**

- **Test:** Connect button calls `/connect` API with correct data
- **Test:** Successful connection redirects to `/control`
- **Test:** Failed connection shows error message
- **Test:** Connection state is saved to LocalStorage

**Test Suite: Settings Panel**

- **Test:** Settings panel expands/collapses on click
- **Test:** Sensitivity sliders update values in real-time
- **Test:** Settings are saved to LocalStorage on change
- **Test:** Settings persist across page reloads

#### Control Interface Workflow

**Test Suite: Page Load**

- **Test:** Control page loads video feed
- **Test:** Status HUD displays initial values
- **Test:** WebSocket connection is established
- **Test:** Settings are loaded and applied

**Test Suite: Status HUD**

- **Test:** Battery level updates from API
- **Test:** Ping value updates in real-time
- **Test:** Mode badge displays current mode
- **Test:** Light level slider shows current value

**Test Suite: Light Control**

- **Test:** Light slider sends API request on change
- **Test:** Light level updates are debounced (not sent on every pixel)
- **Test:** Light level value displays next to slider
- **Test:** API errors are handled gracefully

**Test Suite: Controls**

- **Test:** Keyboard controls send movement commands
- **Test:** Mouse controls (Pointer Lock) send yaw/pitch commands
- **Test:** Gamepad controls send movement commands
- **Test:** Emergency stop button works
- **Test:** Robot action buttons work (sit, stand, etc.)

**Test Suite: Exit Flow**

- **Test:** Exit button calls `/disconnect` API
- **Test:** Successful disconnect redirects to landing page
- **Test:** Connection state is cleared from LocalStorage
- **Test:** Last connected timestamp is updated

### End-to-End Tests

**Test Suite: Complete User Workflows**

**Scenario 1: First-time User**
1. User opens landing page (no saved robots)
2. User clicks "Add Robot"
3. User fills in robot details
4. User saves robot
5. Robot card appears in dashboard
6. User clicks "Connect"
7. User is redirected to control interface
8. User controls robot
9. User clicks "Exit"
10. User returns to landing page

**Scenario 2: Returning User**
1. User opens landing page (saved robots exist)
2. User sees robot cards
3. User clicks "Connect" on existing robot
4. User is redirected to control interface
5. User sees status HUD with real-time data
6. User adjusts light level slider
7. User clicks "Exit"
8. User returns to landing page

**Scenario 3: Settings Management**
1. User opens landing page
2. User opens settings panel
3. User adjusts sensitivity sliders
4. User connects to robot
5. User verifies settings are applied
6. User opens quick settings during control
7. User fine-tunes sensitivity
8. User exits and returns to landing
9. User verifies settings persisted

### Browser Compatibility Tests

**Test Suite: Cross-Browser Testing**

- **Test:** Landing page renders correctly in Chrome 90+
- **Test:** Landing page renders correctly in Firefox 88+
- **Test:** Landing page renders correctly in Edge 90+
- **Test:** Control interface works in Chrome 90+
- **Test:** Control interface works in Firefox 88+
- **Test:** Control interface works in Edge 90+
- **Test:** WebRTC video streaming works in all browsers
- **Test:** WebSocket connection works in all browsers
- **Test:** Pointer Lock API works in all browsers

### Performance Tests

**Test Suite: Page Load Performance**

- **Test:** Landing page loads in < 2 seconds
- **Test:** Control page loads in < 2 seconds
- **Test:** Video feed starts streaming in < 3 seconds
- **Test:** LocalStorage operations complete in < 100ms

**Test Suite: Control Latency**

- **Test:** Keyboard commands have < 50ms latency
- **Test:** Mouse commands have < 50ms latency
- **Test:** Gamepad commands have < 50ms latency
- **Test:** WebSocket round-trip time < 100ms

## Mocking Requirements

### LocalStorage Mock

```javascript
// Mock LocalStorage for testing
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
global.localStorage = localStorageMock;
```

### Socket.IO Mock

```javascript
// Mock Socket.IO client
const socketMock = {
  on: jest.fn(),
  emit: jest.fn(),
  disconnect: jest.fn()
};
```

### API Response Mocks

```javascript
// Mock fetch API
global.fetch = jest.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve({ success: true })
  })
);
```

## Testing Tools

**Recommended Tools:**
- **Jest** - JavaScript testing framework (if automated tests are implemented)
- **Playwright** - E2E testing (future enhancement)
- **Browser DevTools** - Manual testing and debugging

**Current Approach:**
- Manual testing in browser during development
- Console logging for debugging
- Visual inspection of UI components

**Future Enhancement (Phase 2+):**
- Automated unit tests with Jest
- E2E tests with Playwright
- CI/CD integration for automated testing

## Test Execution Strategy

### Phase 1: Foundation Setup
- Manual testing of base templates
- Verify Tailwind CSS loads correctly
- Test routing to new pages

### Phase 2: Landing Page Development
- Manual testing of robot CRUD operations
- Test LocalStorage persistence
- Verify settings panel functionality

### Phase 3: Control Interface Development
- Manual testing of all control methods
- Test status HUD updates
- Verify light level slider
- Test WebSocket/WebRTC functionality

### Phase 4: Integration & Testing
- Complete end-to-end workflow testing
- Cross-browser compatibility testing
- Performance testing
- Regression testing of existing functionality

## Acceptance Criteria

**All tests must pass before:**
- Merging to main branch
- Deploying to production
- Removing old interface (`/test` route)

**Critical Tests (Must Pass):**
- All control methods work (keyboard, mouse, gamepad)
- Video streaming works without lag
- WebSocket connection is stable
- Settings persist across sessions
- Robot CRUD operations work correctly

