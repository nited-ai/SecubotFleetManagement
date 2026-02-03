# Technical Stack

> Last Updated: 2026-02-03
> Version: 1.0.0
> Project: Unitree WebRTC Connect - Commercial Robot Fleet Management Platform

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
- **Current:** Python global variables (to be refactored to StateService)
- **Target:** Centralized StateService class with thread-safe access
- **Thread Safety:** threading.Lock for shared state
- **Connection State:** Boolean flags (is_connected, audio_initialized)
- **Frame Buffers:** Queue.Queue for thread-safe frame passing

### Frontend State
- **Local Storage:** Browser localStorage for user preferences
- **Session State:** JavaScript variables for runtime state
- **Real-time Updates:** Socket.IO events for state synchronization

---

## Data Storage & Configuration

### Configuration (Current)
- **Format:** Python variables (to be migrated to .env)
- **Audio Config:** Sample rate, channels, buffer size
- **Video Config:** Frame rate, resolution, encoding quality
- **Robot Config:** IP address, connection method, credentials

### Configuration (Target)
- **Environment Variables:** python-dotenv for .env file support
- **Config Models:** Pydantic for validation and type safety
- **Secrets Management:** Separate .env.secrets for sensitive data

### Database (Planned)
- **Primary:** PostgreSQL for production (robot registry, user accounts, object assignments)
- **Development:** SQLite for local development
- **ORM:** SQLAlchemy for database abstraction
- **Migrations:** Alembic for schema versioning

### Logging
- **Library:** Python logging module
- **Format:** Structured logs with timestamps
- **Levels:** DEBUG, INFO, WARNING, ERROR, FATAL
- **Output:** Console (development), file + cloud (production)
- **Target:** structlog for structured logging in production

---

## Development Tools

### Code Quality
- **Formatter:** black (line length: 100)
- **Import Sorter:** isort (profile: black)
- **Linter:** flake8 (max-line-length: 100)
- **Type Checker:** mypy (strict mode recommended)

### Testing (TDD Approach)
- **Framework:** pytest 7.4+
- **Async Testing:** pytest-asyncio
- **Mocking:** pytest-mock, unittest.mock
- **Coverage:** pytest-cov (target: 80%+)
- **Test Structure:**
  - `tests/unit/` - Unit tests for services
  - `tests/integration/` - Integration tests for routes
  - `tests/e2e/` - End-to-end tests for critical workflows
  - `tests/fixtures/` - Shared test fixtures

### Version Control
- **VCS:** Git
- **Hosting:** GitHub
- **Branching:** Feature branches, main/master for production
- **Commit Convention:** Conventional Commits

---

## Deployment & Infrastructure

### Development Environment
- **IDE:** VS Code with Python extension
- **Python Version:** 3.11+
- **Virtual Environment:** venv or conda
- **Package Manager:** pip

### Production Deployment (Cloud Target)
- **Platform:** AWS / Azure / GCP (to be decided)
- **Container:** Docker with multi-stage builds
- **Orchestration:** Kubernetes or AWS ECS
- **Load Balancer:** nginx or cloud-native LB
- **SSL/TLS:** Let's Encrypt or cloud-managed certificates
- **CDN:** CloudFront / Azure CDN for static assets

### CI/CD Pipeline
- **Platform:** GitHub Actions
- **Triggers:** Push to main, pull requests
- **Pipeline Steps:**
  1. Run linters (black, isort, flake8)
  2. Run type checker (mypy)
  3. Run unit tests (pytest)
  4. Run integration tests
  5. Generate coverage report (fail if <80%)
  6. Build Docker image
  7. Push to container registry
  8. Deploy to staging (auto)
  9. Deploy to production (manual approval)

### Monitoring & Observability
- **Application Logs:** structlog to CloudWatch / Azure Monitor
- **Error Tracking:** Sentry for exception monitoring
- **Metrics:** Prometheus + Grafana
- **APM:** New Relic or Datadog (optional)
- **Health Checks:** `/health` and `/ready` endpoints
- **Uptime Monitoring:** UptimeRobot or cloud-native monitoring

---

## Security

### Authentication & Authorization (Planned)
- **Authentication:** JWT tokens with refresh mechanism
- **Password Hashing:** bcrypt or Argon2
- **Session Management:** Redis for session storage
- **Role-Based Access:** Admin, Operator, Viewer roles
- **API Security:** Rate limiting, CORS configuration

### Network Security
- **HTTPS:** Mandatory for production
- **WebSocket Security:** WSS (WebSocket Secure)
- **CORS:** Configured for specific origins
- **Rate Limiting:** Flask-Limiter for API endpoints

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

**Development Dependencies (requirements-dev.txt):**
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

**Planned Dependencies:**
```
python-dotenv==1.0.0
pydantic==2.5.3
structlog==24.1.0
SQLAlchemy==2.0.23
alembic==1.13.1
psycopg2-binary==2.9.9
redis==5.0.1
PyJWT==2.8.0
bcrypt==4.1.2
Flask-Limiter==3.5.0
```

---

## Code Repository

- **URL:** https://github.com/nited-ai/unitree_webrtc_connect
- **Branch Strategy:** 
  - `main` - Production-ready code
  - `develop` - Integration branch
  - `feature/*` - Feature branches
  - `hotfix/*` - Emergency fixes
- **Protected Branches:** main, develop (require PR + review)


