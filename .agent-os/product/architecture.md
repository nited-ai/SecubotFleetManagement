# System Architecture

## Overview

Unitree WebRTC Connect is a web-based control interface for Unitree Go2 robots using WebRTC for real-time video/audio streaming and robot control.

**Current State:** Monolithic Flask application (1500+ lines in `web_interface.py`)  
**Target State:** Modular service-oriented architecture (Phase 2 refactoring)

---

## Current Architecture (Monolithic)

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Web Browser (Client)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   HTML/CSS   │  │  JavaScript  │  │   Gamepad    │      │
│  │   Interface  │  │   Controls   │  │     API      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/WebSocket/WebRTC
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Flask Application (web_interface.py)            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   Flask Routes (15+)                  │  │
│  │  /connect, /disconnect, /video_feed, /gamepad/*, ... │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              WebSocket Handlers (3)                   │  │
│  │  gamepad_command, start_microphone, stop_microphone   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                 Business Logic                        │  │
│  │  Connection, Audio, Video, Control, Settings          │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  Global State                         │  │
│  │  frame_queue, connection, audio_muted, settings, ...  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ WebRTC (aiortc)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Unitree Go2 Robot                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Camera    │  │  Microphone  │  │   Motors     │      │
│  │   (Video)    │  │   (Audio)    │  │  (Control)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### 1. **Web Interface Layer** (`templates/index.html`)
- HTML5 video player for MJPEG stream
- Gamepad API integration
- Keyboard/mouse controls (WASD + Pointer Lock API)
- Push-to-talk audio controls
- Settings UI (sensitivity, presets)

#### 2. **Flask Application Layer** (`web_interface.py`)
- **HTTP Routes:** 15+ endpoints for connection, control, settings
- **WebSocket Handlers:** 3 handlers for low-latency commands
- **Business Logic:** All services embedded in single file
- **Global State:** Thread-safe shared state management

#### 3. **WebRTC Layer** (`unitree_webrtc_connect/`)
- **Connection Management:** WebRTC peer connection setup
- **Video Streaming:** Robot → User (H.264 video track)
- **Audio Streaming:** Bidirectional (robot ↔ user)
- **Data Channels:** Control commands (AI mode, Sport mode)

#### 4. **Robot Layer** (Unitree Go2)
- **Camera:** 1080p video stream
- **Microphone:** Audio capture
- **Motors:** Movement control (vx, vy, vyaw)
- **Sensors:** LIDAR, IMU, etc.

---

## Data Flow

### Video Streaming (Robot → User)

```
Robot Camera
    │
    │ H.264 frames via WebRTC
    ▼
recv_video_stream() callback
    │
    │ Put frame in queue
    ▼
frame_queue (Queue, maxsize=30)
    │
    │ Get latest frame
    ▼
generate_frames() generator
    │
    │ JPEG encoding
    ▼
/video_feed endpoint
    │
    │ MJPEG stream
    ▼
Browser <video> element
```

**Key Details:**
- Frame queue prevents memory overflow (drops old frames)
- Thread-safe access with `frame_lock`
- JPEG quality: 85% (configurable)
- Frame rate: ~30 FPS

### Audio Streaming (Robot → User)

```
Robot Microphone
    │
    │ PCM audio frames via WebRTC
    ▼
recv_audio_stream() callback
    │
    │ Check audio_muted flag
    ▼
audio_muted == False?
    │
    │ Yes: Play audio
    ▼
asyncio.to_thread(pyaudio_stream.write, audio_bytes)
    │
    │ Non-blocking I/O
    ▼
PC Speakers
```

**Key Details:**
- **CRITICAL:** Uses `asyncio.to_thread()` to prevent blocking event loop
- Audio always connected, controlled by `audio_muted` flag
- Sample rate: 48kHz, Channels: 2 (stereo)
- Instant mute/unmute (no reconnection required)

### Audio Streaming (User → Robot)

```
PC Microphone
    │
    │ PyAudio capture (server-side)
    ▼
MicrophoneAudioTrack.recv()
    │
    │ asyncio.to_thread(mic_stream.read, ...)
    ▼
Convert mono → stereo
    │
    │ Create AVAudioFrame
    ▼
WebRTC audio track
    │
    │ Push-to-talk controlled
    ▼
Robot Speakers
```

**Key Details:**
- Server-side capture (bypasses SocketIO packet loss)
- Push-to-talk via WebSocket events
- Uses `asyncio.to_thread()` for non-blocking reads

### Control Commands (User → Robot)

```
Browser (Gamepad/Keyboard/Mouse)
    │
    │ WebSocket: gamepad_command event
    ▼
handle_websocket_gamepad_command()
    │
    │ Validate state (connected, enabled, not emergency stop)
    ▼
Apply deadzone, sensitivity, velocity limits
    │
    │ Create movement command {vx, vy, vyaw}
    ▼
asyncio.run_coroutine_threadsafe(send_command, event_loop)
    │
    │ AI mode: Move command (API ID 1008)
    ▼
WebRTC data channel
    │
    │ Low-latency transmission
    ▼
Robot Motors
```

**Key Details:**
- WebSocket for low latency (~16ms interval, ~60Hz)
- Rate limiting: 0.016s between commands (except zero velocity)
- Zero velocity commands bypass rate limit (instant stop)
- Emergency stop blocks all commands

---

## Critical Technical Concepts

### 1. **Asyncio Event Loop Management**

**Problem:** Video and audio callbacks run in the SAME asyncio event loop. Blocking operations freeze the entire loop.

**Solution:**
```python
# WRONG: Blocking I/O freezes video
pyaudio_stream.write(audio_bytes)  # Blocks event loop!

# CORRECT: Non-blocking I/O
await asyncio.to_thread(pyaudio_stream.write, audio_bytes)  # Runs in thread pool
```

**Impact:**
- Without `asyncio.to_thread()`: Video artifacts, high latency, corrupted frames
- With `asyncio.to_thread()`: Smooth video quality even with audio enabled

### 2. **Audio Muting Without Reconnection**

**Problem:** User wants instant audio toggle without reconnecting WebRTC.

**Solution:**
- Audio stream always initialized during connection
- `audio_muted` flag controls playback (not connection)
- Muted frames are discarded without playback

**Benefits:**
- Instant mute/unmute (no video interruption)
- No WebRTC reconnection overhead
- Simpler state management

### 3. **Server-Side Audio Capture**

**Problem:** SocketIO packet loss (browser sent 100+ packets, backend received 5).

**Solution:**
- Capture audio server-side using PyAudio
- Bypass SocketIO entirely for audio transmission
- Use WebRTC audio track for transmission

**Benefits:**
- No packet loss
- Lower latency
- More reliable transmission

---

## Target Architecture (Modular - Phase 2)

### Service-Oriented Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Web Browser (Client)                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/WebSocket/WebRTC
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flask Application                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   API Routes                          │  │
│  │              (routes/api.py, routes/ws.py)            │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            ▼                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  Service Layer                        │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │ Connection │  │   Audio    │  │   Video    │     │  │
│  │  │  Service   │  │  Service   │  │  Service   │     │  │
│  │  └────────────┘  └────────────┘  └────────────┘     │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │  Control   │  │  Settings  │  │   State    │     │  │
│  │  │  Service   │  │  Service   │  │  Manager   │     │  │
│  │  └────────────┘  └────────────┘  └────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            ▼                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  Data Layer                           │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │  │
│  │  │ PostgreSQL │  │   Redis    │  │   Models   │     │  │
│  │  │  Database  │  │   Cache    │  │   (ORM)    │     │  │
│  │  └────────────┘  └────────────┘  └────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ WebRTC (aiortc)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Unitree Go2 Robot                         │
└─────────────────────────────────────────────────────────────┘
```

### Proposed Directory Structure

```
unitree_webrtc_connect/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration management
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api.py               # HTTP API routes
│   │   ├── ws.py                # WebSocket handlers
│   │   └── views.py             # HTML views
│   ├── services/
│   │   ├── __init__.py
│   │   ├── connection.py        # Connection management
│   │   ├── audio.py             # Audio streaming
│   │   ├── video.py             # Video streaming
│   │   ├── control.py           # Robot control
│   │   ├── settings.py          # Settings management
│   │   └── state.py             # State management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── connection.py        # Connection model
│   │   ├── settings.py          # Settings model
│   │   └── session.py           # Session model
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py        # Input validation
│   │   ├── decorators.py        # Custom decorators
│   │   └── helpers.py           # Helper functions
│   └── templates/
│       └── index.html           # Web interface
├── tests/
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── e2e/                     # End-to-end tests
├── .agent-os/                   # Agent OS documentation
├── web_interface.py             # Entry point (legacy)
├── requirements.txt
└── README.md
```

### Service Responsibilities

#### **ConnectionService** (`services/connection.py`)
- Manage WebRTC peer connections
- Handle connection lifecycle (connect, disconnect, reconnect)
- Manage event loop and threads
- Connection state management

#### **AudioService** (`services/audio.py`)
- Audio stream reception (robot → user)
- Audio transmission (user → robot)
- Mute/unmute functionality
- Push-to-talk management
- PyAudio integration

#### **VideoService** (`services/video.py`)
- Video frame reception
- Frame queue management
- JPEG encoding
- MJPEG stream generation

#### **ControlService** (`services/control.py`)
- Movement command processing
- Gamepad/keyboard/mouse input handling
- Rate limiting
- Emergency stop management

#### **SettingsService** (`services/settings.py`)
- Gamepad settings management
- Preset configurations
- Settings persistence (database)

#### **StateManager** (`services/state.py`)
- Centralized state management
- Thread-safe state access
- State persistence
- Event broadcasting

---

## Technology Stack

### Backend
- **Python:** 3.11+
- **Web Framework:** Flask 3.0+
- **WebSocket:** Flask-SocketIO (async_mode='threading')
- **WebRTC:** aiortc (Python WebRTC implementation)
- **Audio:** PyAudio (PortAudio wrapper)
- **Video:** OpenCV (cv2), NumPy
- **Async:** asyncio, threading

### Frontend
- **HTML5:** Video player, Gamepad API
- **CSS3:** Responsive design
- **JavaScript:** Vanilla JS (no frameworks)
- **WebSocket:** Socket.IO client
- **WebRTC:** Browser WebRTC API

### Infrastructure
- **Database:** PostgreSQL (production), SQLite (development)
- **Cache:** Redis (session management)
- **Web Server:** Nginx (reverse proxy)
- **Containerization:** Docker, Docker Compose
- **Orchestration:** Kubernetes, AWS ECS

### Development Tools
- **Testing:** pytest, pytest-asyncio, pytest-mock, pytest-cov
- **Code Quality:** black, isort, flake8, mypy, pylint
- **Documentation:** Sphinx, OpenAPI/Swagger
- **CI/CD:** GitHub Actions

---

## Security Considerations

### Current Implementation
- ❌ No authentication/authorization
- ❌ No HTTPS enforcement
- ❌ No CORS configuration
- ❌ No rate limiting (except command rate limiting)
- ❌ No input validation
- ❌ No session management

### Planned Improvements (Phase 3+)
- ✅ User authentication (JWT tokens)
- ✅ Role-based access control (RBAC)
- ✅ HTTPS enforcement
- ✅ CORS configuration
- ✅ API rate limiting
- ✅ Input validation and sanitization
- ✅ Session management (Redis)
- ✅ Audit logging

---

## Performance Considerations

### Current Bottlenecks
1. **Monolithic Architecture:** All services in single file
2. **Global State:** Thread-safe but not scalable
3. **No Caching:** Settings loaded from memory
4. **No Connection Pooling:** Single connection per instance
5. **No Load Balancing:** Single instance only

### Optimization Strategies
1. **Service Extraction:** Modular services (Phase 2)
2. **State Management:** Redis for distributed state
3. **Caching:** Redis for settings and session data
4. **Connection Pooling:** Multiple robot connections
5. **Load Balancing:** Nginx + multiple instances
6. **CDN:** Static assets (CSS, JS, images)
7. **Video Optimization:** Adaptive bitrate, resolution

---

## Scalability Roadmap

### Phase 1: Single Robot, Single User (Current)
- Monolithic Flask app
- In-memory state
- Single WebRTC connection

### Phase 2: Single Robot, Multiple Users (Future)
- Modular service architecture
- Redis for shared state
- Multiple WebRTC connections (read-only viewers)

### Phase 3: Multiple Robots, Multiple Users (Future)
- Microservices architecture
- PostgreSQL for persistent data
- Load balancing and horizontal scaling
- Robot fleet management

### Phase 4: Enterprise Fleet Management (Future)
- Multi-tenancy support
- Advanced analytics and monitoring
- Role-based access control
- Audit logging and compliance

---

## Migration Strategy (Phase 1 → Phase 2)

### Step 1: Extract Services
1. Create `services/` directory
2. Extract ConnectionService from web_interface.py
3. Extract AudioService from web_interface.py
4. Extract VideoService from web_interface.py
5. Extract ControlService from web_interface.py
6. Extract SettingsService from web_interface.py

### Step 2: Refactor Routes
1. Create `routes/` directory
2. Move HTTP routes to `routes/api.py`
3. Move WebSocket handlers to `routes/ws.py`
4. Move HTML views to `routes/views.py`

### Step 3: Add Data Layer
1. Create `models/` directory
2. Add SQLAlchemy models
3. Add database migrations (Alembic)
4. Add Redis cache integration

### Step 4: Update Tests
1. Update unit tests for new services
2. Add integration tests for service interactions
3. Add E2E tests for complete workflows
4. Maintain 80%+ code coverage

### Step 5: Deploy
1. Update Docker configuration
2. Update CI/CD pipeline
3. Deploy to staging environment
4. Perform load testing
5. Deploy to production

---

## Conclusion

The current monolithic architecture serves well for single-robot, single-user scenarios. The planned modular architecture will enable:

- **Better maintainability** through service separation
- **Improved testability** with isolated components
- **Enhanced scalability** for multiple robots/users
- **Easier deployment** with containerization
- **Better performance** through caching and optimization

Phase 2 refactoring will be guided by the documentation created in Phase 1, ensuring a smooth transition to the target architecture.

