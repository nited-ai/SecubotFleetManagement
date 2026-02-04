# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2026-02-03-frontend-ui-overhaul/spec.md

> Created: 2026-02-03
> Version: 1.0.0

## Overview

This document specifies the Flask routes and API endpoints required for the frontend UI overhaul. Most existing API endpoints will remain unchanged, with only routing modifications needed to support the new multi-page architecture.

## Flask Routes (Views)

### GET `/`

**Purpose:** Serve the landing page with robot management dashboard

**Template:** `templates/landing.html`

**Response:** HTML page

**Changes Required:**
- Modify existing `/` route in `app/routes/views.py`
- Change from rendering `index.html` to `landing.html`

**Implementation:**
```python
@views_bp.route('/')
def landing():
    """Render the landing page with robot management dashboard."""
    return render_template('landing.html')
```

### GET `/control`

**Purpose:** Serve the fullscreen control interface

**Template:** `templates/control.html`

**Response:** HTML page

**Requirements:**
- User must have an active connection (check session or connection state)
- If no active connection, redirect to `/` with error message

**Implementation:**
```python
@views_bp.route('/control')
def control():
    """Render the fullscreen control interface."""
    # Optional: Check if robot is connected
    # if not state_service.is_connected():
    #     flash('Please connect to a robot first', 'warning')
    #     return redirect(url_for('views.landing'))
    
    return render_template('control.html')
```

### GET `/test` (Temporary)

**Purpose:** Serve the old interface during migration (fallback)

**Template:** `templates/index.html`

**Response:** HTML page

**Lifecycle:** Remove after Phase 4 completion

**Implementation:**
```python
@views_bp.route('/test')
def test_interface():
    """Temporary route for old interface during migration."""
    return render_template('index.html')
```

### GET `/video_feed`

**Purpose:** Stream MJPEG video feed

**Response:** Multipart JPEG stream

**Changes Required:** None (keep existing implementation)

**Current Implementation:** Already exists in `app/routes/views.py`

## API Endpoints (Existing)

### POST `/connect`

**Purpose:** Initiate connection to robot

**Request Body:**
```json
{
  "connection_method": "LocalSTA",
  "ip": "192.168.8.181",
  "serial_number": "B42D2000XXXXXXXX",
  "username": "",
  "password": ""
}
```

**Response:**
```json
{
  "success": true,
  "message": "Connected successfully"
}
```

**Changes Required:** None (keep existing implementation)

### POST `/disconnect`

**Purpose:** Disconnect from robot

**Request Body:** None

**Response:**
```json
{
  "success": true,
  "message": "Disconnected successfully"
}
```

**Changes Required:** None (keep existing implementation)

### POST `/control/command`

**Purpose:** Send movement command to robot (HTTP fallback)

**Request Body:**
```json
{
  "vx": 0.5,
  "vy": 0.0,
  "vyaw": 0.0
}
```

**Response:**
```json
{
  "success": true
}
```

**Changes Required:** None (keep existing implementation)

**Note:** WebSocket is preferred for low-latency control

## API Endpoints (New)

### GET `/api/robot/status`

**Purpose:** Get current robot status for HUD display

**Response:**
```json
{
  "battery": 85,
  "ping": 45,
  "mode": "AI Mode",
  "light_level": 75,
  "temperature": 42,
  "connected": true
}
```

**Implementation Required:** Yes (new endpoint)

**Priority:** High (required for status HUD)

**Location:** `app/routes/api.py`

**Implementation:**
```python
@api_bp.route('/api/robot/status', methods=['GET'])
def get_robot_status():
    """Get current robot status."""
    if not state_service.is_connected():
        return jsonify({'error': 'Not connected'}), 400
    
    status = {
        'battery': state_service.get_battery_level(),
        'ping': state_service.get_ping(),
        'mode': state_service.get_mode(),
        'light_level': state_service.get_light_level(),
        'temperature': state_service.get_temperature(),
        'connected': True
    }
    return jsonify(status)
```

### POST `/api/robot/light`

**Purpose:** Set robot light level

**Request Body:**
```json
{
  "level": 75
}
```

**Response:**
```json
{
  "success": true,
  "level": 75
}
```

**Implementation Required:** Yes (new endpoint)

**Priority:** High (required for light slider)

**Location:** `app/routes/api.py`

## WebSocket Events (Existing)

### Event: `control_command`

**Purpose:** Send real-time movement commands

**Payload:**
```json
{
  "vx": 0.5,
  "vy": 0.0,
  "vyaw": 0.0
}
```

**Changes Required:** None (keep existing implementation)

### Event: `start_microphone`

**Purpose:** Start audio streaming

**Changes Required:** None (keep existing implementation)

### Event: `stop_microphone`

**Purpose:** Stop audio streaming

**Changes Required:** None (keep existing implementation)

## Error Handling

### Standard Error Response Format

```json
{
  "success": false,
  "error": "Error message description"
}
```

### HTTP Status Codes

- `200 OK` - Successful request
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Route not found
- `500 Internal Server Error` - Server error

## CORS Configuration

**Changes Required:** None

**Current Configuration:** Already configured in `web_interface.py`

## Session Management

**Current Approach:** Server-side state management via `StateService`

**Changes Required:** None for this phase

**Future Enhancement (Phase 5):** Implement proper session management with Flask-Login

