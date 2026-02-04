# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2026-02-03-frontend-ui-overhaul/spec.md

> Created: 2026-02-03
> Version: 1.0.0

## Technical Requirements

### Frontend Architecture

**Technology Stack:**
- **Vanilla JavaScript (ES6+)** - No frameworks, maintain current approach
- **Tailwind CSS 3.x** - Utility-first CSS framework via CDN
- **HTML5** - Semantic markup with template inheritance
- **Socket.IO Client** - Maintain existing WebSocket functionality
- **WebRTC API** - Maintain existing video/audio streaming

**File Structure:**
```
templates/
├── base.html                    # Base template with Tailwind CSS
├── landing.html                 # Landing page (robot management)
├── control.html                 # Fullscreen control interface
└── components/
    ├── robot-card.html          # Robot card component (optional)
    └── status-hud.html          # Status HUD component (optional)

static/
├── css/
│   └── custom.css               # Custom styles beyond Tailwind
├── js/
│   ├── landing.js               # Landing page logic
│   ├── control.js               # Control interface logic
│   ├── robot-manager.js         # Robot CRUD operations
│   ├── settings-manager.js      # Settings persistence
│   └── websocket-client.js      # WebSocket/control logic (extracted)
└── images/
    └── robot-placeholder.png    # Default robot image
```

### Component Specifications

#### 1. Landing Page (`templates/landing.html`)

**Layout:**
- Header: Logo, title, version
- Main content area:
  - Robot dashboard (grid layout, 3 columns)
  - "Add Robot" button (prominent, top-right)
  - Settings panel (collapsible, bottom or sidebar)
- Footer: Links, copyright

**Robot Card Component:**
- Display: IP address, serial number, connection method badge
- Actions: "Connect" button (primary), "Edit" icon, "Delete" icon
- Visual: Card with hover effect, connection method color-coded badge
- State: Show "last connected" timestamp (future enhancement)

**Add/Edit Robot Modal:**
- Fields:
  - Connection Method (dropdown: LocalSTA, LocalAP, Remote)
  - IP Address (text input, shown for LocalSTA/LocalAP)
  - Serial Number (text input, shown for LocalSTA/Remote)
  - Username (email input, shown for Remote only)
  - Password (password input, shown for Remote only)
- Validation: Required fields based on connection method
- Actions: "Save" button, "Cancel" button

**Settings Panel:**
- Sections:
  - Keyboard/Mouse Settings (sensitivity sliders)
  - Gamepad Settings (sensitivity sliders, presets)
  - Velocity Limits (max linear, strafe, rotation)
- Collapsible: Click header to expand/collapse
- Persistence: Auto-save to LocalStorage on change

#### 2. Control Interface (`templates/control.html`)

**Layout:**
- Fullscreen video element (100vw x 100vh)
- Status HUD overlay (top-left corner, semi-transparent)
- Quick settings button (floating, bottom-right)
- Exit button (floating, top-right)

**Status HUD Overlay:**
- Position: Fixed, top-left, 20px padding
- Background: Semi-transparent dark (rgba(0,0,0,0.7))
- Border: Subtle border with rounded corners
- Content:
  - Battery level (icon + percentage + progress bar)
  - Connection ping (icon + ms value + color indicator)
  - Current mode (text badge: "AI Mode", "Sport Mode", etc.)
  - Light level slider (0-100%, real-time control)
- Styling: Clean, minimal, high contrast for readability

**Light Level Slider:**
- Range: 1-100 (integer values)
- Visual: Horizontal slider with sun icon
- Behavior: Real-time update on slide (debounced API call)
- Feedback: Show current value next to slider

**Quick Settings Button:**
- Position: Fixed, bottom-right, 20px padding
- Icon: Gear/settings icon
- Behavior: Opens modal with sensitivity settings
- Modal: Same settings as landing page, but in overlay

**Exit Button:**
- Position: Fixed, top-right, 20px padding
- Icon: X or "Exit" text
- Behavior: Disconnect from robot, redirect to landing page
- Confirmation: Optional "Are you sure?" dialog

### Data Management

#### LocalStorage Schema

**Robot List:**
```javascript
// Key: 'unitree_robots'
{
  "robots": [
    {
      "id": "uuid-v4",
      "name": "Robot 1",  // Optional, defaults to "Robot {index}"
      "connectionMethod": "LocalSTA",
      "ip": "192.168.8.181",
      "serialNumber": "B42D2000XXXXXXXX",
      "username": "",  // Only for Remote
      "password": "",  // Only for Remote (consider encryption)
      "lastConnected": "2026-02-03T10:30:00Z",  // ISO timestamp
      "createdAt": "2026-02-01T08:00:00Z"
    }
  ]
}
```

**Settings:**
```javascript
// Key: 'unitree_settings'
{
  "keyboard_mouse": {
    "mouse_yaw_sensitivity": 0.5,
    "mouse_pitch_sensitivity": 0.25,
    "keyboard_linear_speed": 0.2,
    "keyboard_strafe_speed": 0.2,
    "kb_max_linear_velocity": 1.5,
    "kb_max_strafe_velocity": 1.2,
    "kb_max_rotation_velocity": 3.0
  },
  "gamepad": {
    "deadzone_left_stick": 0.15,
    "deadzone_right_stick": 0.15,
    "sensitivity_linear": 1.0,
    "sensitivity_strafe": 1.0,
    "sensitivity_rotation": 1.0,
    "speed_multiplier": 1.0,
    "max_linear_velocity": 0.6,
    "max_strafe_velocity": 0.4,
    "max_rotation_velocity": 0.8
  },
  "audio": {
    "enabled": false
  }
}
```

**Current Connection State:**
```javascript
// Key: 'unitree_current_connection'
{
  "robotId": "uuid-v4",
  "connectedAt": "2026-02-03T10:30:00Z",
  "isConnected": true
}
```

### State Management

**Connection Flow:**
1. User clicks "Connect" on robot card
2. Landing page stores robot ID in `unitree_current_connection`
3. Landing page initiates connection via `/connect` API
4. On successful connection, redirect to `/control`
5. Control page reads `unitree_current_connection` to identify robot
6. Control page establishes WebSocket connection
7. Control page starts video/audio streaming

**Disconnection Flow:**
1. User clicks "Exit" button on control page
2. Control page calls `/disconnect` API
3. Control page clears `unitree_current_connection`
4. Control page redirects to `/` (landing page)
5. Landing page updates "last connected" timestamp for robot

### Tailwind CSS Integration

**Installation Method:**
- Use Tailwind CDN for simplicity (no build step)
- Include in `base.html` template

**CDN Link:**
```html
<script src="https://cdn.tailwindcss.com"></script>
```

**Custom Configuration:**
```html
<script>
  tailwind.config = {
    theme: {
      extend: {
        colors: {
          'unitree-primary': '#00E8DA',
          'unitree-secondary': '#00B8AD',
          'unitree-dark': '#1e1e1e',
          'unitree-success': '#10b981',
          'unitree-warning': '#f59e0b',
          'unitree-danger': '#ef4444',
        }
      }
    }
  }
</script>
```

**Design System:**
- Primary color: Teal/Cyan gradient (#00E8DA → #00B8AD)
- Background: Dark theme (#1e1e1e, #2d2d2d)
- Text: White (#ffffff) and gray (#9ca3af)
- Accent colors: Green (success), Yellow (warning), Red (danger)
- Border radius: Rounded (0.5rem)
- Shadows: Subtle elevation

### JavaScript Module Organization

**robot-manager.js:**
- `loadRobots()` - Load robots from LocalStorage
- `saveRobot(robot)` - Add or update robot
- `deleteRobot(robotId)` - Remove robot
- `getRobot(robotId)` - Get single robot by ID
- `updateLastConnected(robotId)` - Update timestamp

**settings-manager.js:**
- `loadSettings()` - Load settings from LocalStorage
- `saveSettings(settings)` - Save settings to LocalStorage
- `getDefaultSettings()` - Return default settings object
- `applySettings()` - Send settings to backend via API

**websocket-client.js:**
- Extract existing WebSocket logic from index.html
- `initializeWebSocket()` - Connect to Socket.IO
- `sendControlCommand(data)` - Send movement command
- `handleCommandResponse(data)` - Process response
- Event handlers for connect/disconnect/reconnect

## Approach Options

### Option A: Big Bang Replacement (Not Selected)

**Description:** Replace entire `index.html` with new landing and control pages in one go.

**Pros:**
- Clean slate, no legacy code
- Faster initial development
- Consistent architecture from start

**Cons:**
- High risk of breaking existing functionality
- Difficult to test incrementally
- No fallback if issues arise
- Longer time before users see improvements

### Option B: Incremental Migration (Selected)

**Description:** Create new pages alongside existing interface, migrate functionality piece by piece.

**Pros:**
- Low risk, existing interface remains functional
- Can test each component independently
- Easy rollback if issues occur
- Users see improvements incrementally
- Maintains backward compatibility during transition

**Cons:**
- Temporary code duplication
- Slightly longer total development time
- Need to maintain both interfaces briefly

**Rationale:** Option B is selected because it minimizes risk, allows for thorough testing, and ensures the existing interface remains functional throughout the migration. This approach aligns with the project's need for reliability in a production environment.

## Migration Strategy

### Phase 1: Foundation Setup (Week 1)

**Goal:** Set up Tailwind CSS and create base templates without breaking existing functionality.

**Tasks:**
1. Add Tailwind CSS CDN to project
2. Create `templates/base.html` with Tailwind configuration
3. Create empty `templates/landing.html` and `templates/control.html`
4. Create `static/js/` and `static/css/` directories
5. Keep existing `index.html` at `/test` route for fallback

**Deliverable:** Base templates ready, existing interface still accessible.

### Phase 2: Landing Page Development (Week 1-2)

**Goal:** Build robot management dashboard with LocalStorage persistence.

**Tasks:**
1. Create robot card UI components
2. Implement add/edit/delete robot functionality
3. Build settings panel with all existing settings
4. Implement LocalStorage persistence
5. Add "Connect" button that calls existing `/connect` API
6. Test robot CRUD operations thoroughly

**Deliverable:** Functional landing page at `/`, existing interface at `/test`.

### Phase 3: Control Interface Development (Week 2-3)

**Goal:** Create fullscreen control interface with status HUD.

**Tasks:**
1. Create fullscreen video layout
2. Build status HUD overlay with battery, ping, mode display
3. Implement light level slider with API integration
4. Add quick settings modal
5. Add exit button with disconnect logic
6. Extract and integrate existing control logic (keyboard/mouse/gamepad)
7. Test all control methods (keyboard, mouse, gamepad)

**Deliverable:** Functional control interface at `/control`, all controls working.

### Phase 4: Integration & Testing (Week 3-4)

**Goal:** Connect landing and control pages, ensure smooth navigation flow.

**Tasks:**
1. Implement connection state management
2. Test landing → control → landing navigation flow
3. Verify settings persistence across pages
4. Test WebSocket/WebRTC functionality
5. Cross-browser testing (Chrome, Firefox, Edge)
6. Performance testing (video latency, control responsiveness)
7. Remove `/test` route and old `index.html`

**Deliverable:** Complete UI overhaul, old interface removed.

## External Dependencies

### Tailwind CSS

- **Version:** 3.x (latest via CDN)
- **Purpose:** Utility-first CSS framework for rapid UI development
- **Justification:**
  - No build step required (CDN)
  - Comprehensive utility classes reduce custom CSS
  - Excellent documentation and community support
  - Maintains performance with minimal overhead
  - Easy to customize with configuration

**Installation:**
```html
<!-- Add to base.html -->
<script src="https://cdn.tailwindcss.com"></script>
```

### UUID Generation (Optional)

- **Library:** `uuid` (browser-compatible version) or native `crypto.randomUUID()`
- **Purpose:** Generate unique IDs for robots
- **Justification:** Ensures unique robot identifiers in LocalStorage

**Implementation:**
```javascript
// Use native browser API (no external dependency)
const robotId = crypto.randomUUID();
```

## Performance Considerations

### Video Streaming
- Maintain existing MJPEG streaming approach
- No changes to video frame processing
- Fullscreen video may improve perceived performance

### Control Latency
- Maintain existing WebSocket implementation
- No changes to control command processing
- Extract control logic to separate JS file for better organization

### LocalStorage
- Minimal performance impact (small data size)
- Synchronous operations acceptable for this use case
- Consider IndexedDB for future scalability (Phase 5+)

### Page Load Time
- Tailwind CDN adds ~50KB (gzipped)
- Minimal impact on load time
- Consider self-hosting Tailwind in production for better caching

## Security Considerations

### Password Storage
- **Current:** Passwords stored in LocalStorage (plain text)
- **Risk:** XSS attacks could expose credentials
- **Mitigation (Future):**
  - Move to server-side session storage (Phase 5)
  - Implement proper authentication with JWT tokens
  - Never store passwords client-side in production

### XSS Protection
- Sanitize all user inputs (robot names, IP addresses)
- Use textContent instead of innerHTML where possible
- Validate connection method selection

### CORS
- Maintain existing CORS configuration
- No changes required for this phase

## Browser Compatibility

**Target Browsers:**
- Chrome 90+ (primary)
- Firefox 88+ (secondary)
- Edge 90+ (secondary)

**Required Features:**
- ES6+ JavaScript (arrow functions, template literals, modules)
- CSS Grid and Flexbox
- WebRTC API
- WebSocket API
- LocalStorage API
- Pointer Lock API (for mouse control)

**Testing Strategy:**
- Primary testing on Chrome (most common browser)
- Secondary testing on Firefox and Edge
- No support for IE11 or older browsers

