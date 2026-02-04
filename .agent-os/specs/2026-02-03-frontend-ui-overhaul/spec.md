# Spec Requirements Document

> Spec: Frontend UI Overhaul
> Created: 2026-02-03
> Status: Planning

## Overview

Transform the current monolithic single-page interface into a modern, organized multi-page web application with a dedicated landing page for robot management and a fullscreen control interface with real-time status overlay. This overhaul will improve user experience by separating robot management from active control, while maintaining all existing functionality and preparing the foundation for future fleet management features.

## User Stories

### Story 1: Robot Management Dashboard

As a **security operator**, I want to save multiple robot configurations (IP, serial number, connection method) on a landing page, so that I can quickly connect to different robots without re-entering connection details each time.

**Workflow:**
1. User opens the web interface and sees a landing page with saved robots
2. User can add a new robot by clicking "Add Robot" button
3. User fills in robot details (IP address, serial number, connection method)
4. Robot is saved to LocalStorage and displayed as a card in the dashboard
5. User clicks "Connect" on any robot card to initiate connection
6. Upon successful connection, user is redirected to fullscreen control interface

### Story 2: Fullscreen Control with Status Overlay

As a **security operator**, I want to control the robot in a fullscreen video interface with real-time status information overlaid on the video, so that I can focus on navigation while monitoring critical robot metrics without switching views.

**Workflow:**
1. After connecting to a robot, user sees fullscreen video feed
2. Status HUD overlay displays battery level, connection ping, current mode, and light level
3. User can adjust light level using a slider in the HUD
4. User controls robot using existing keyboard/mouse or gamepad controls by clicking on the videostream
5. User can access quick settings (sensitivity) via floating button
6. User clicks "Exit" button to disconnect and return to landing page

### Story 3: Settings Management

As a **security operator**, I want to access and adjust control sensitivity settings from the landing page before connecting, so that I can configure my preferred control settings without needing to connect to a robot first.

**Workflow:**
1. User opens settings panel on landing page
2. User selects preferred control method and adjusts keyboard/mouse sensitivity, gamepad sensitivity, and velocity limits
3. Settings are saved to LocalStorage
4. When user connects to a robot, saved settings are automatically applied
5. During active control, user can access quick settings to fine-tune sensitivity without disconnecting

## Spec Scope

1. **Landing Page with Robot Management** - Create new `/` route with robot dashboard, add/edit/delete robot functionality, and LocalStorage persistence
2. **Fullscreen Control Interface** - Create new `/control` route with fullscreen video, status HUD overlay (battery, ping, mode, light slider), and exit button
3. **Settings Panel** - Move all control settings to landing page settings panel, implement quick settings access during active control
4. **Tailwind CSS Integration** - Add Tailwind CSS for modern styling, create reusable component classes, implement clean dark theme design
5. **Multi-Page Routing** - Implement Flask routes for landing (`/`) and control (`/control`), handle connection state transitions, maintain WebSocket/WebRTC functionality

## Out of Scope

- Responsive design for mobile/tablet (desktop-only for now)
- Light/dark theme toggle (dark theme only, light theme deferred to future phase)
- Gamepad control enhancements (keep existing functionality)
- Key binding customization UI (deferred to Phase 6+)
- Video quality controls
- Audio visualizer
- Real-time performance metrics dashboard
- Database integration (LocalStorage only, database migration in Phase 5)
- User authentication/login (Phase 5)
- LIDAR point cloud visualization (Phase 7)

## Expected Deliverable

1. **Landing page accessible at `/`** with robot management dashboard, add/edit/delete robot cards, settings panel, and quick connect functionality
2. **Fullscreen control interface at `/control`** with video feed, status HUD overlay showing battery/ping/mode/light level, light level slider, and exit button
3. **All existing controls working** - keyboard/mouse, gamepad, audio, emergency stop, and robot actions function identically to current implementation
4. **Settings persistence** - Control sensitivity settings saved to LocalStorage and applied automatically on connection
5. **Smooth navigation flow** - Connect from landing page → fullscreen control → disconnect returns to landing page

## Spec Documentation

- Tasks: @.agent-os/specs/2026-02-03-frontend-ui-overhaul/tasks.md
- Technical Specification: @.agent-os/specs/2026-02-03-frontend-ui-overhaul/sub-specs/technical-spec.md
- API Specification: @.agent-os/specs/2026-02-03-frontend-ui-overhaul/sub-specs/api-spec.md
- Tests Specification: @.agent-os/specs/2026-02-03-frontend-ui-overhaul/sub-specs/tests.md

