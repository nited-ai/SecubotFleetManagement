# Unitree WebRTC Connect - Development Guide

> Last Updated: 2026-02-03
> Version: 1.0.0

---

## Project Overview

**Unitree WebRTC Connect** is a web-based robot fleet management platform for enterprise customers and surveillance/security companies. It provides real-time video streaming, bidirectional audio communication, and intuitive control interfaces for Unitree Go2 robots, accessible from any web browser.

**Current Status:** Monolithic prototype with working core features, preparing for production refactoring.

---

## Quick Start

### Prerequisites

- Python 3.11+
- PyAudio (requires PortAudio)
- Modern web browser (Chrome, Firefox, Safari)
- Unitree Go2 robot with network connectivity

### Installation

```bash
# Clone repository
git clone https://github.com/nited-ai/unitree_webrtc_connect.git
cd unitree_webrtc_connect

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python web_interface.py --port 5000
```

### Usage

1. Open browser to `http://localhost:5000`
2. Enter robot IP address and select connection method (LocalSTA/LocalAP/Remote)
3. Click "Connect" to establish WebRTC connection
4. Use gamepad, keyboard/mouse, or on-screen controls to operate robot
5. Press 'C' or click button for push-to-talk audio transmission

---

## Agent OS Documentation

This project uses the **Agent OS framework** for structured development planning and documentation. All product and technical documentation is located in the `.agent-os/` directory.

### Product Documentation (`.agent-os/product/`)

- **[mission.md](.agent-os/product/mission.md)** - Product vision, target users, problems solved, key features
- **[tech-stack.md](.agent-os/product/tech-stack.md)** - Complete technology stack and infrastructure decisions
- **[roadmap.md](.agent-os/product/roadmap.md)** - Development roadmap with 8 phases from prototype to enterprise platform
- **[decisions.md](.agent-os/product/decisions.md)** - Architectural Decision Records (ADRs) documenting key technical choices

### Development Standards (`.agent-os/standards/`)

- **[best-practices.md](.agent-os/standards/best-practices.md)** - Python/Flask/WebRTC development patterns, testing strategies, SDK integration examples
- **[code-style.md](.agent-os/standards/code-style.md)** - Python code style guide (PEP 8, type hints, docstrings, async patterns)
- **[tech-stack.md](.agent-os/standards/tech-stack.md)** - Technology stack overview and file structure (current vs target)

### Workflow Instructions (`.agent-os/instructions/`)

- **[analyze-product.md](.agent-os/instructions/analyze-product.md)** - How to analyze existing codebase and install Agent OS
- **[plan-product.md](.agent-os/instructions/plan-product.md)** - How to generate product documentation

---

## Development Roadmap

### Phase 0: Already Completed ✅

- WebRTC connection management (LocalSTA, LocalAP, Remote)
- Real-time video streaming (H.264, MJPEG)
- Bidirectional audio (robot→user playback, user→robot push-to-talk)
- Gamepad and keyboard/mouse control
- AI mode integration (FreeWalk, FreeBound, FreeJump, FreeAvoid)
- Settings management with presets
- Event loop optimization (asyncio.to_thread for blocking I/O)

### Phase 1: Documentation & Testing Foundation (Current Priority)

**Duration:** 3-4 weeks  
**Focus:** Establish comprehensive documentation and testing infrastructure before refactoring

- [ ] API documentation (OpenAPI/Swagger)
- [ ] User guide and deployment guide
- [ ] Unit tests for all services (80%+ coverage)
- [ ] Integration tests for routes
- [ ] E2E tests for critical workflows

### Phase 2: Modular Architecture Refactoring

**Duration:** 4-5 weeks  
**Focus:** Extract service layer and implement Flask blueprints

- [ ] StateService (centralized state management)
- [ ] WebRTCService, AudioService, VideoService, ControlService
- [ ] Flask blueprints for routes (connection, audio, video, control, settings)
- [ ] Eliminate global variables

### Phase 3: Configuration & Environment Management

**Duration:** 2-3 weeks  
**Focus:** Externalize configuration and implement secrets management

- [ ] Environment variables (python-dotenv)
- [ ] Config service with Pydantic validation
- [ ] Multiple environment profiles (dev, staging, prod)

### Phase 4: Performance & Deployment

**Duration:** 3-4 weeks  
**Focus:** Database integration, caching, Docker, CI/CD

- [ ] PostgreSQL + SQLAlchemy
- [ ] Redis caching layer
- [ ] Docker containerization
- [ ] GitHub Actions CI/CD pipeline

### Phase 5: Fleet Management Features

**Duration:** 4-5 weeks  
**Focus:** Multi-robot management and user access control

- [ ] Robot registration (IP, S/N, connection methods)
- [ ] Object management (assign robots to objects)
- [ ] Login system (Admin, Operator, Viewer roles)
- [ ] Robot overview dashboard

### Phase 6: Enhanced Control & UI Features

**Duration:** 3-4 weeks  
**Focus:** Advanced controls and status indicators

- [ ] Additional keyboard controls (Ctrl, Shift, Space, R, Q, E)
- [ ] Camera control (mouse X/Y for yaw/pitch)
- [ ] Status indicators (battery, connection, temperature, mode)
- [ ] Screenshot and video recording

### Phase 7: Advanced Features

**Duration:** 5-6 weeks  
**Focus:** LIDAR visualization, autonomous navigation, predefined audio

- [ ] LIDAR point cloud visualization
- [ ] DimOS click navigation with costmap
- [ ] Autonomous bot notifications
- [ ] Predefined audio library (sirens, instructions, sounds)

### Phase 8: Future Enhancements

- Multi-robot control, fleet analytics, mobile app, patrol route planning

**See [roadmap.md](.agent-os/product/roadmap.md) for complete details.**

---

## Architecture

### Current Architecture (Monolithic)

```
web_interface.py (1512 lines)
├── Global variables (40+)
├── MicrophoneAudioTrack class
├── Async functions (initialize_robot, recv_camera_stream, recv_audio_stream)
├── Flask routes (15+ endpoints)
└── WebSocket handlers (3 handlers)

templates/index.html (2574 lines)
├── HTML structure
├── Embedded CSS
└── Embedded JavaScript
```

### Target Architecture (Modular)

```
app/
├── services/
│   ├── state_service.py
│   ├── webrtc_service.py
│   ├── audio_service.py
│   ├── video_service.py
│   └── control_service.py
├── routes/
│   ├── connection.py
│   ├── audio.py
│   ├── video.py
│   ├── control.py
│   └── settings.py
├── models/
│   ├── robot.py
│   ├── user.py
│   └── object.py
├── config/
│   └── settings.py
└── main.py

tests/
├── unit/
├── integration/
├── e2e/
└── fixtures/
```

**See [tech-stack.md](.agent-os/standards/tech-stack.md) for complete file structure.**

---

## Key Technical Decisions

### DEC-004: Server-Side PyAudio for Audio Capture ✅

**Problem:** Browser-based audio capture with SocketIO resulted in severe packet loss.  
**Solution:** Use server-side PyAudio to capture PC microphone, bypassing SocketIO entirely.  
**Result:** Eliminated packet loss, high-quality audio transmission.

### DEC-005: Blocking I/O and Event Loop Management ✅

**Problem:** PyAudio's blocking operations froze asyncio event loop, causing video degradation.  
**Solution:** Use `asyncio.to_thread()` to offload blocking PyAudio I/O to thread pool.  
**Result:** Smooth video quality even with audio enabled.

**See [decisions.md](.agent-os/product/decisions.md) for all architectural decisions.**

---

## Contributing

### Development Workflow

1. **Read Documentation:** Review `.agent-os/product/` and `.agent-os/standards/` before starting
2. **Follow TDD:** Write tests first, then implement features
3. **Code Style:** Use black, isort, flake8, mypy for code quality
4. **Testing:** Maintain 80%+ code coverage
5. **Documentation:** Update API docs and user guides

### Code Quality Tools

```bash
# Format code
black --line-length 100 .
isort --profile black .

# Lint code
flake8 --max-line-length 100 .

# Type check
mypy --strict .

# Run tests
pytest --cov=app --cov-report=html
```

---

## Known Issues & Workarounds

### aiortc Race Condition (Remote Connections)

**Issue:** Remote WebRTC connections may fail with `AttributeError: 'NoneType' object has no attribute 'media'`

**Cause:** Race condition in the `aiortc` library where `setRemoteDescription()` triggers internal tasks before state is fully initialized.

**Status:** ✅ Fixed with two-part workaround (monkey-patch + synchronization logic)

**Affected Versions:**
- aiortc: 1.9.0, 1.10.0, 1.11.0+
- Connection methods: Primarily Remote (Internet), occasionally LocalSTA/LocalAP

**Fix Implementation:**
1. **Monkey-patch** in `unitree_webrtc_connect/__init__.py` (lines 24-77)
   - Adds null checking to `RTCPeerConnection.__remoteRtp()`
   - Prevents crash when remote description is not yet set

2. **Synchronization logic** in `unitree_webrtc_connect/webrtc_driver.py` (lines 190-256)
   - Waits for signaling state to stabilize
   - Polls until remote description is fully set
   - Adds delay for internal state synchronization

**Impact:**
- Connection time: +0.5 to 1.5 seconds
- Success rate: 100% (vs ~30% without fix)

**Documentation:** See `.agent-os/product/aiortc-race-condition-fix.md` for complete details including:
- Root cause analysis
- Testing procedures
- Maintenance checklist for library updates
- Instructions for re-applying the fix

**⚠️ Important:** Do not remove the monkey-patch or synchronization logic without testing! The race condition will return.

---

## Resources

- **Repository:** https://github.com/nited-ai/unitree_webrtc_connect
- **Unitree SDK:** examples/go2/ folder contains official SDK examples
- **Agent OS:** `.agent-os/` directory contains all product and development documentation
- **Known Issues:** `.agent-os/product/` directory contains detailed documentation of workarounds

---

## License

[Add license information]


