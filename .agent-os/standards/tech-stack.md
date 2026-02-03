# Tech Stack: Unitree WebRTC Connect

> Version: 1.0.0
> Last Updated: 2026-02-03
> Project: Web-based control interface for Unitree Go2 robots

## Context

This file defines the technology stack for the **Unitree WebRTC Connect** project. This stack is optimized for real-time WebRTC streaming, robot control, and web-based user interfaces.

---

## Core Technologies

- **Language:** Python 3.11+
- **Web Framework:** Flask 3.0+
- **WebSocket:** Flask-SocketIO (async_mode='threading')
- **WebRTC:** aiortc (Python WebRTC implementation)
- **Async Runtime:** asyncio (Python native)
- **Robot SDK:** unitree_webrtc_connect (custom library)

---

## Backend Stack

### Web Server
- **Framework:** Flask 3.0+
- **WebSocket Server:** Flask-SocketIO with threading mode
- **WSGI Server:** Werkzeug (development), Gunicorn (production)
- **Port:** 5000 (default), configurable via `--port` argument

### WebRTC & Media Processing
- **WebRTC Library:** aiortc 1.6+
- **Audio Processing:** PyAudio (PortAudio bindings)
- **Video Processing:** OpenCV (cv2), NumPy
- **Audio Codec:** Opus (via aiortc)
- **Video Codec:** H.264 (via aiortc)

### Robot Communication
- **SDK:** unitree_webrtc_connect
- **Connection Methods:**
  - LocalSTA (WiFi network connection)
  - LocalAP (Direct robot WiFi)
  - Remote (Internet-based control)
- **Data Channel:** WebRTC data channel for commands
- **Command Protocol:** JSON-based API (RTC_TOPIC, SPORT_CMD)

---

## Frontend Stack

### UI Framework
- **HTML5:** Semantic markup
- **CSS3:** Custom styles with CSS Grid/Flexbox
- **JavaScript:** Vanilla ES6+ (no framework)
- **Template Engine:** Jinja2 (Flask templates)

### Browser APIs
- **WebRTC:** RTCPeerConnection, MediaStream
- **Gamepad API:** HTML5 Gamepad API for controller support
- **Pointer Lock API:** Mouse control for robot movement
- **WebSocket:** Socket.IO client for real-time communication

### UI Components
- **Video Display:** HTML5 `<video>` element
- **Audio Playback:** HTML5 `<audio>` element
- **Controls:** Custom HTML/CSS buttons and sliders
- **Status Indicators:** Real-time connection/audio/video status

---

## State Management

### Backend State
- **Global State:** Python global variables (to be refactored to StateService)
- **Thread Safety:** threading.Lock for shared state
- **Connection State:** Boolean flags (is_connected, audio_initialized)
- **Frame Buffers:** Queue.Queue for thread-safe frame passing

### Frontend State
- **Local Storage:** Browser localStorage for user preferences
- **Session State:** JavaScript variables for runtime state
- **Real-time Updates:** Socket.IO events for state synchronization

---

## Data Storage & Configuration

### Configuration
- **Format:** Python variables (to be migrated to .env)
- **Audio Config:** Sample rate, channels, buffer size
- **Video Config:** Frame rate, resolution, encoding quality
- **Robot Config:** IP address, connection method, credentials

### Logging
- **Library:** Python logging module
- **Format:** Structured logs with timestamps
- **Levels:** DEBUG, INFO, WARNING, ERROR, FATAL
- **Output:** Console (development), file (production)

---

## Development Tools

### Code Quality
- **Formatter:** black (line length: 100)
- **Import Sorter:** isort (profile: black)
- **Linter:** flake8 (max-line-length: 100)
- **Type Checker:** mypy (strict mode recommended)

### Testing
- **Framework:** pytest 7.4+
- **Async Testing:** pytest-asyncio
- **Mocking:** pytest-mock, unittest.mock
- **Coverage:** pytest-cov (target: 80%+)
- **Test Structure:**
  - `tests/unit/` - Unit tests for services
  - `tests/integration/` - Integration tests for routes
  - `tests/fixtures/` - Shared test fixtures

### Version Control
- **VCS:** Git
- **Hosting:** GitHub
- **Branching:** Feature branches, main/master for production
- **Commit Convention:** Conventional Commits (optional)

---

## Deployment & Infrastructure

### Development Environment
- **IDE:** VS Code with Python extension
- **Python Version:** 3.11+
- **Virtual Environment:** venv or conda
- **Package Manager:** pip

### Production Deployment
- **Server:** Linux (Ubuntu 22.04 LTS recommended)
- **Process Manager:** systemd or supervisor
- **Reverse Proxy:** nginx (optional, for HTTPS)
- **SSL/TLS:** Let's Encrypt (for remote access)

### CI/CD Pipeline
- **Platform:** GitHub Actions
- **Triggers:** Push to main, pull requests
- **Pipeline Steps:**
  1. Run linters (black, isort, flake8)
  2. Run type checker (mypy)
  3. Run unit tests (pytest)
  4. Run integration tests
  5. Generate coverage report
  6. Build Docker image (optional)

### Monitoring & Logging
- **Application Logs:** Python logging to file
- **Error Tracking:** Sentry (optional)
- **Metrics:** Prometheus + Grafana (optional)
- **Health Checks:** `/health` endpoint

---

## Package Management

### Python Dependencies (requirements.txt)

**Core Dependencies:**
```
Flask==3.0.0
Flask-SocketIO==5.3.5
aiortc==1.6.0
opencv-python==4.8.1.78
numpy==1.26.2
pyaudio==0.2.14
```

**Development Dependencies:**
```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-mock==3.12.0
pytest-cov==4.1.0
black==23.12.1
isort==5.13.2
flake8==7.0.0
mypy==1.8.0
```

**Optional Dependencies:**
```
python-dotenv==1.0.0
pydantic==2.5.3
structlog==24.1.0
```

### Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development only
```

---

## File Structure

Current monolithic structure (to be refactored):

```
unitree_webrtc_connect/
├── web_interface.py              # Main Flask app (1500+ lines - TO REFACTOR)
├── templates/
│   └── index.html                # Frontend UI (2500+ lines)
├── unitree_webrtc_connect/       # Robot SDK
│   ├── __init__.py
│   ├── webrtc_driver.py          # WebRTC connection driver
│   ├── webrtc_audio.py           # Audio channel management
│   ├── webrtc_video.py           # Video channel management
│   ├── webrtc_datachannel.py     # Data channel for commands
│   ├── constants.py              # RTC_TOPIC, SPORT_CMD constants
│   └── ...
├── tests/
│   ├── test_audio_stream.py
│   ├── test_connection.py
│   └── test_microphone_to_robot.py
├── requirements.txt
└── README.md
```

Target refactored structure:

```
unitree_webrtc_connect/
├── app/
│   ├── __init__.py               # Flask app factory
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── connection.py         # /connect, /disconnect
│   │   ├── control.py            # /gamepad/*, /keyboard/*
│   │   ├── audio.py              # /audio/*
│   │   └── video.py              # /video_feed
│   ├── services/
│   │   ├── __init__.py
│   │   ├── webrtc_service.py     # WebRTC connection management
│   │   ├── audio_service.py      # Audio streaming
│   │   ├── video_service.py      # Video streaming
│   │   ├── control_service.py    # Robot control
│   │   └── state_service.py      # Global state
│   ├── models/
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration models
│   │   ├── commands.py           # Robot command models
│   │   └── state.py              # Application state
│   └── utils/
│       ├── __init__.py
│       ├── async_helpers.py      # asyncio utilities
│       └── logging_config.py     # Logging setup
├── templates/
│   └── index.html                # Frontend UI
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_audio_service.py
│   │   ├── test_video_service.py
│   │   ├── test_control_service.py
│   │   └── test_webrtc_service.py
│   ├── integration/
│   │   ├── test_routes.py
│   │   └── test_end_to_end.py
│   └── fixtures/
│       ├── __init__.py
│       └── mock_data.py
├── unitree_webrtc_connect/       # Robot SDK (unchanged)
├── web_interface.py              # Main entry point (simplified)
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── pyproject.toml                # Tool configuration
└── .env.example                  # Environment variables template
```

---

## Future Enhancements

### Planned Features (from examples/go2/)
- **Audio Features:**
  - MP3 player (play files to robot)
  - Internet radio streaming
  - Audio recording from robot
- **Data Channel Features:**
  - Low-level state monitoring (IMU, motors, battery)
  - LIDAR visualization
  - VUI (Voice User Interface)
- **Advanced Control:**
  - Gesture commands (Hello, BackFlip, etc.)
  - Handstand mode
  - Advanced movement patterns

### Technology Additions
- **Database:** SQLite for session history (optional)
- **API Documentation:** Flask-RESTX or apispec
- **Monitoring:** prometheus-flask-exporter
- **Configuration:** python-dotenv for environment variables
- **Validation:** Pydantic for request/response validation

---