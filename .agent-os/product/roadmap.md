# Product Roadmap

> Last Updated: 2026-02-03
> Version: 1.0.0
> Status: Active Development

---

## Overview

This roadmap outlines the development plan for transforming Unitree WebRTC Connect from a monolithic prototype into an enterprise-grade robot fleet management platform. The roadmap is organized into phases, with Phase 0 documenting completed work and subsequent phases outlining the refactoring and feature development strategy.

**Priority Ranking (from user requirements):**
1. Documentation - API docs, user guides, deployment guides
2. Testing - Comprehensive unit/integration tests
3. Modular Architecture - Service layer extraction
4. Configuration - Environment variables, settings management
5. Performance - Optimization, caching, connection pooling
6. Deployment - Docker, CI/CD, production readiness
7. Advanced Features - Integration from examples/go2/

---

## Phase 0: Already Completed ✅

**Goal:** Document the current working implementation
**Status:** Complete
**Duration:** Completed over previous development cycles

### Must-Have Features (Completed)

- [x] **WebRTC Connection Management** - Connect to robots via LocalSTA, LocalAP, Remote methods `COMPLETE`
- [x] **Real-Time Video Streaming** - H.264 video with frame buffering, MJPEG HTTP streaming `COMPLETE`
- [x] **Bidirectional Audio Streaming** - Robot→User playback with instant mute/unmute `COMPLETE`
- [x] **Push-to-Talk Audio Transmission** - User→Robot audio via server-side PyAudio capture `COMPLETE`
- [x] **Gamepad Control** - HTML5 Gamepad API with configurable sensitivity `COMPLETE`
- [x] **Keyboard/Mouse Control** - WASD movement, pointer lock rotation, mouse wheel speed `COMPLETE`
- [x] **WebSocket Commands** - Low-latency movement control via persistent WebSocket `COMPLETE`
- [x] **AI Mode Integration** - FreeWalk (Agile Mode) with obstacle avoidance `COMPLETE`
- [x] **Robot Actions** - Emergency stop, stand up, sit, crouch, speed levels `COMPLETE`
- [x] **Advanced Modes** - FreeBound, FreeJump, FreeAvoid toggle controls `COMPLETE`
- [x] **Settings Management** - Configurable dead zones, sensitivity, velocity limits `COMPLETE`
- [x] **Preset Configurations** - Beginner, normal, advanced, sport presets `COMPLETE`
- [x] **LIDAR Control** - Toggle LIDAR on/off with traffic saving management `COMPLETE`
- [x] **Event Loop Optimization** - asyncio.to_thread() for blocking I/O operations `COMPLETE`

### Technical Achievements

- [x] **Fixed Video Degradation** - Resolved blocking I/O issue causing video artifacts `COMPLETE`
- [x] **Instant Audio Muting** - Dynamic mute/unmute without reconnection `COMPLETE`
- [x] **Fire-and-Forget Commands** - Minimal latency movement control `COMPLETE`
- [x] **Thread-Safe Frame Buffering** - Queue-based video frame management `COMPLETE`

### Current Architecture

- **File Structure:** Monolithic (web_interface.py: 1512 lines, index.html: 2574 lines)
- **Global State:** 40+ global variables for connection, video, audio, control
- **Routes:** 15+ Flask HTTP endpoints
- **WebSocket Handlers:** 3 Socket.IO event handlers
- **Testing:** Minimal (test files cleared, only 1 line each)

---

## Phase 1: Documentation & Testing Foundation (Current Priority)

**Goal:** Establish comprehensive documentation and testing infrastructure before refactoring
**Success Criteria:** 
- Complete API documentation
- 80%+ code coverage
- All critical paths tested
- Deployment guide complete

**Duration:** 3-4 weeks

### Must-Have Features

- [ ] **API Documentation** - OpenAPI/Swagger spec for all endpoints `L`
- [ ] **Deployment Guide** - Step-by-step production deployment instructions `M`
- [ ] **Architecture Documentation** - Current system architecture diagrams `S`
- [ ] **Unit Tests - Connection** - Test WebRTC connection management `M`
- [ ] **Unit Tests - Audio** - Test audio streaming and push-to-talk `M`
- [ ] **Unit Tests - Video** - Test video frame processing `M`
- [ ] **Unit Tests - Control** - Test gamepad/keyboard command processing `M`
- [ ] **Integration Tests - Routes** - Test all Flask endpoints `L`
- [ ] **Integration Tests - WebSocket** - Test Socket.IO handlers `M`
- [ ] **E2E Tests - Critical Workflows** - Test connect→control→disconnect flow `L`

### Should-Have Features

- [ ] **Code Coverage Report** - Automated coverage reporting in CI `S`
- [ ] **Performance Benchmarks** - Baseline latency and throughput metrics `M`
- [ ] **Security Audit** - Initial security review and recommendations `M`

### Dependencies

- pytest, pytest-asyncio, pytest-mock, pytest-cov installed
- CI/CD pipeline configured for test execution
- Documentation tooling (Sphinx or MkDocs)

---

## Phase 2: Modular Architecture Refactoring

**Goal:** Extract service layer and implement Flask blueprints
**Success Criteria:**
- All business logic in service classes
- Routes are thin wrappers
- No global state variables
- All tests passing after refactoring

**Duration:** 4-5 weeks

### Must-Have Features

- [ ] **StateService** - Centralized state management with thread-safe access `L`
- [ ] **WebRTCService** - Connection management and lifecycle `L`
- [ ] **AudioService** - Audio streaming (reception and transmission) `L`
- [ ] **VideoService** - Video frame processing and streaming `M`
- [ ] **ControlService** - Robot command processing and validation `M`
- [ ] **Connection Blueprint** - /connect, /disconnect routes `M`
- [ ] **Audio Blueprint** - /audio/* routes `S`
- [ ] **Video Blueprint** - /video_feed route `S`
- [ ] **Control Blueprint** - /gamepad/*, /keyboard_mouse/* routes `M`
- [ ] **Settings Blueprint** - /gamepad/settings routes `S`

### Should-Have Features

- [ ] **Service Factory Pattern** - Dependency injection for services `M`
- [ ] **Configuration Models** - Pydantic models for all config `M`
- [ ] **Error Handling Middleware** - Centralized error handling `S`

### Dependencies

- Phase 1 complete (tests ensure refactoring doesn't break functionality)
- Service class patterns documented in best-practices.md

---

## Phase 3: Configuration & Environment Management

**Goal:** Externalize configuration and implement proper secrets management
**Success Criteria:**
- All config in .env files
- No hardcoded values
- Secrets properly managed
- Multiple environments supported (dev, staging, prod)

**Duration:** 2-3 weeks

### Must-Have Features

- [ ] **Environment Variables** - python-dotenv integration `S`
- [ ] **Config Service** - Centralized configuration management `M`
- [ ] **Secrets Management** - Separate .env.secrets for sensitive data `M`
- [ ] **Environment Profiles** - Dev, staging, production configs `M`
- [ ] **Config Validation** - Pydantic models for type-safe config `M`

### Should-Have Features

- [ ] **Config Documentation** - Document all environment variables `S`
- [ ] **Config Templates** - .env.example files for each environment `S`

### Dependencies

- Phase 2 complete (services ready to consume config)

---

## Phase 4: Performance & Deployment

**Goal:** Optimize performance, add database layer, and prepare for production deployment
**Success Criteria:**
- Database integration complete
- Caching layer operational
- Docker containerization working
- CI/CD pipeline deployed
- Performance benchmarks met

**Duration:** 3-4 weeks

### Must-Have Features

- [ ] **Database Integration** - PostgreSQL + SQLAlchemy for robot registry `L`
- [ ] **Database Migrations** - Alembic for schema versioning `M`
- [ ] **Caching Layer** - Redis for session management and caching `M`
- [ ] **Connection Pooling** - Database connection pooling `S`
- [ ] **Performance Optimization** - Profile and optimize hot paths `M`
- [ ] **Docker Containerization** - Multi-stage Dockerfile `L`
- [ ] **Docker Compose** - Local development environment `M`
- [ ] **CI/CD Pipeline** - GitHub Actions for automated testing and deployment `L`
- [ ] **Health Check Endpoints** - /health and /ready for monitoring `S`
- [ ] **Structured Logging** - structlog for production logging `M`

### Should-Have Features

- [ ] **Load Testing** - Artillery or Locust for load testing `M`
- [ ] **Performance Monitoring** - Prometheus metrics collection `M`
- [ ] **Error Tracking** - Sentry integration for exception monitoring `S`

### Dependencies

- Phase 3 complete (config ready for database credentials)
- Cloud infrastructure provisioned (AWS/Azure/GCP)

---

## Phase 5: Fleet Management Features

**Goal:** Implement multi-robot management and user access control
**Success Criteria:**
- Robot registration working
- Object management operational
- Login system with 3 roles functional
- Robot overview dashboard complete

**Duration:** 4-5 weeks

### Must-Have Features (from user requirements)

- [ ] **Robot Registration** - Add robots with IP, S/N, connection methods `L` (Priority 1, Difficulty 1)
- [ ] **Robot CRUD Operations** - Edit and delete robot entries `M`
- [ ] **Object Management** - Create objects (buildings, zones, patrol routes) `M` (Priority 3, Difficulty 1)
- [ ] **Robot-to-Object Assignment** - Assign robots to objects `M`
- [ ] **Login System** - JWT-based authentication `L` (Priority 3, Difficulty 3)
- [ ] **Organization/Admin Role** - Full access to fleet management `M`
- [ ] **Operator Role** - Robot control and monitoring access `M`
- [ ] **Viewer Role** - Read-only access to robot feeds `S`
- [ ] **Robot Overview Dashboard** - Fleet status, assignments, battery, connection `L` (Priority 4, Difficulty 3)
- [ ] **User Management** - Admin can create/edit/delete users `M`

### Should-Have Features

- [ ] **Audit Logging** - Track all user actions for security `M`
- [ ] **Session Management** - Redis-based session storage `S`
- [ ] **Password Reset** - Email-based password recovery `S`

### Dependencies

- Phase 4 complete (database and authentication infrastructure ready)

---

## Phase 6: Enhanced Control & UI Features

**Goal:** Implement advanced control features and UI enhancements
**Success Criteria:**
- All keyboard controls working
- Camera control operational
- Status indicators complete
- Screenshot/recording functional

**Duration:** 3-4 weeks

### Must-Have Features (from user requirements)

- [ ] **Keyboard Control - WASD** - Forward/back, strafe left/right `COMPLETE` ✅
- [ ] **Keyboard Control - Ctrl** - Crouch `S` (Priority 4, Difficulty 3)
- [ ] **Keyboard Control - Shift** - Slow walk `S` (Priority 3, Difficulty 2)
- [ ] **Keyboard Control - Space** - Pose/look around `M` (Priority 1, Difficulty 2)
- [ ] **Keyboard Control - C** - Push to talk `COMPLETE` ✅
- [ ] **Keyboard Control - R** - Rage mode (fast mode) `S` (Priority 4, Difficulty 2)
- [ ] **Keyboard Control - Q** - Crouch down (stand down) `COMPLETE` ✅
- [ ] **Keyboard Control - E** - Recovery stand (stand up) `COMPLETE` ✅
- [ ] **Camera Control - Mouse X/Y** - Yaw and pitch control `M` (Priority 1, Difficulty 1)
- [ ] **Volume Control - Arrow Keys** - Volume up/down `S` (Priority 3, Difficulty 3)
- [ ] **Light Control** - Adjustable intensity 1-100% `M` (Priority 1, Difficulty 2)
- [ ] **Fullscreen Video** - Immersive video interface `M` (Priority 1, Difficulty 1)
- [ ] **Battery Status Indicator** - Real-time battery level `M` (Priority 1, Difficulty 1)
- [ ] **Connection/Ping Indicator** - Latency and connection quality `M` (Priority 1, Difficulty 2)
- [ ] **Temperature Monitoring** - Display robot temperatures `S` (Priority 5, Difficulty 2)
- [ ] **Avoidance Status Display** - Show obstacle avoidance state `S` (Priority 2, Difficulty 2)
- [ ] **Current Mode Indicator** - Display active mode (Rage, AI, Endurance, etc.) `S` (Priority 2, Difficulty 2)
- [ ] **Screenshot Capture** - Save current frame to download folder `M` (Priority 3, Difficulty 2)
- [ ] **Video Recording** - Save video stream for review `M` (Priority 3, Difficulty 5)

### Should-Have Features

- [ ] **Keyboard Customization** - Configurable key bindings `S` (Priority 2, Difficulty 4)
- [ ] **Sensitivity Settings UI** - Visual sensitivity adjustment `S`
- [ ] **Preset Switching UI** - Quick preset selection `S`

### Dependencies

- Phase 2 complete (service layer ready for new features)
- Phase 5 complete (robot data available for status indicators)

---

## Phase 7: Advanced Features

**Goal:** Integrate advanced SDK features for autonomous operations
**Success Criteria:**
- LIDAR visualization working
- DimOS navigation operational
- Autonomous notifications functional
- Predefined audio library complete

**Duration:** 5-6 weeks

### Must-Have Features (from user requirements)

- [ ] **LIDAR Point Cloud Visualization** - Real-time 3D point cloud display `L` (Priority 4, Difficulty 5)
- [ ] **DimOS Click Navigation** - Click-to-navigate interface `L` (Priority 2, Difficulty 5)
- [ ] **Costmap Creation** - Generate navigation costmaps `L`
- [ ] **Autonomous Bot Notifications** - Alerts from autonomous robots `L` (Priority 1, Difficulty 5)
- [ ] **Predefined Audio Library** - Sirens, instructions, movement sounds `M` (Priority 3, Difficulty 5)
- [ ] **Audio Playback Control** - Trigger predefined audio from UI `M`

### Should-Have Features (from examples/go2/)

- [ ] **LowState Monitoring** - Real-time robot state data (from examples/go2/data_channel/lowstate) `M`
- [ ] **Sport Mode Commands** - Advanced movement commands (from examples/go2/data_channel/sportmode) `M`
- [ ] **VUI Integration** - Voice user interface (from examples/go2/vui) `S`
- [ ] **Multi-Camera Support** - Switch between robot cameras `S`

### Dependencies

- Phase 2 complete (service layer ready for SDK integration)
- Phase 6 complete (UI ready for advanced visualizations)
- SDK examples reviewed and patterns documented

---

## Phase 8: Future Enhancements

**Goal:** Long-term improvements and scalability features
**Status:** Planned for future consideration

### Potential Features

- [ ] **Multi-Robot Control** - Control multiple robots simultaneously
- [ ] **Fleet Analytics** - Usage statistics, patrol coverage, incident reports
- [ ] **Mobile App** - Native iOS/Android apps for field operators
- [ ] **Patrol Route Planning** - Define and schedule autonomous patrol routes
- [ ] **Incident Recording** - Automatic recording on security events
- [ ] **Integration APIs** - REST API for third-party integrations
- [ ] **WebRTC Mesh Networking** - Peer-to-peer robot communication
- [ ] **AI-Powered Features** - Object detection, person tracking, anomaly detection

---

## Success Metrics

### Technical Metrics

- **Code Coverage:** 80%+ across all modules
- **API Response Time:** <100ms for control commands
- **Video Latency:** <200ms end-to-end
- **Audio Latency:** <150ms end-to-end
- **Uptime:** 99.9% availability
- **Error Rate:** <0.1% of requests

### Business Metrics

- **User Onboarding Time:** <15 minutes for new operators
- **Robot Fleet Size:** Support 100+ robots per deployment
- **Concurrent Users:** Support 50+ simultaneous operators
- **Deployment Time:** <30 minutes from code to production

---

## Risk Management

### Technical Risks

- **WebRTC Compatibility:** Browser compatibility issues → Mitigation: Test on Chrome, Firefox, Safari
- **Network Latency:** High latency in remote connections → Mitigation: Adaptive quality, local caching
- **Database Scalability:** PostgreSQL performance at scale → Mitigation: Connection pooling, read replicas
- **Blocking I/O:** Event loop blocking → Mitigation: asyncio.to_thread() pattern (already implemented)

### Business Risks

- **Feature Creep:** Scope expansion delaying core features → Mitigation: Strict phase prioritization
- **Testing Overhead:** Comprehensive testing slowing development → Mitigation: TDD approach, automated CI/CD
- **Deployment Complexity:** Cloud infrastructure complexity → Mitigation: Docker, infrastructure-as-code

---

## Version History

- **v1.0.0** (2026-02-03): Initial roadmap created with 8 phases
- **Phase 0**: Documented completed features (14 items)
- **Phase 1-3**: Foundation (documentation, testing, architecture, config)
- **Phase 4**: Performance & deployment
- **Phase 5**: Fleet management features
- **Phase 6**: Enhanced control & UI
- **Phase 7**: Advanced features (LIDAR, DimOS, autonomous)
- **Phase 8**: Future enhancements


