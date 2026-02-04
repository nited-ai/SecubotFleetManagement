# Architectural Decision Records (ADRs)

> Last Updated: 2026-02-03
> Version: 1.0.0
> Status: Active

---

## Overview

This document captures key architectural and technical decisions made during the development of Unitree WebRTC Connect. Each decision record follows the format: Context, Decision, Rationale, Consequences, and Status.

---

## DEC-001: Initial Product Planning - Commercial Fleet Management

**Date:** 2026-02-03  
**Status:** ✅ Accepted  
**Deciders:** Product Owner

### Context

The project started as a prototype for controlling a single Unitree Go2 robot via web interface. We needed to define the product vision and target market.

### Decision

Position Unitree WebRTC Connect as a **commercial robot fleet management platform** targeting enterprise customers and surveillance/security companies, rather than a hobbyist single-robot control tool.

### Rationale

- **Market Opportunity:** Security companies need scalable solutions for managing multiple robots across facilities
- **Differentiation:** Existing solutions (Unitree mobile app) are designed for single-robot hobbyist use
- **Value Proposition:** Web-based platform enables multi-user access, role-based permissions, and centralized fleet management
- **Revenue Potential:** Enterprise customers willing to pay for fleet management capabilities

### Consequences

**Positive:**
- Clear product vision and target market
- Roadmap focused on enterprise features (robot registration, object management, multi-user login)
- Justifies investment in production-grade architecture (testing, deployment, monitoring)

**Negative:**
- Increased complexity compared to single-robot prototype
- Requires database layer, authentication, and authorization
- Longer development timeline to reach MVP

### Related Decisions

- DEC-005: TDD Testing Philosophy (enterprise quality requirements)
- DEC-006: Cloud Deployment Target (enterprise scalability requirements)

---

## DEC-002: Flask vs FastAPI for Web Framework

**Date:** 2026-02-03  
**Status:** 🔍 Under Investigation  
**Deciders:** Technical Team

### Context

The current implementation uses Flask 3.0+ with Flask-SocketIO for WebSocket support. We need to evaluate whether Flask is the right choice for production or if FastAPI would be better.

### Options Considered

**Option A: Continue with Flask**
- ✅ Already implemented and working
- ✅ Mature ecosystem with extensive documentation
- ✅ Flask-SocketIO provides WebSocket support
- ✅ Jinja2 templating for server-side rendering
- ❌ Synchronous by default (requires careful async handling)
- ❌ Less modern than FastAPI

**Option B: Migrate to FastAPI**
- ✅ Native async/await support (better for WebRTC)
- ✅ Automatic OpenAPI documentation generation
- ✅ Built-in data validation with Pydantic
- ✅ Better performance for async workloads
- ❌ Requires full rewrite of existing code
- ❌ WebSocket support less mature than Flask-SocketIO
- ❌ No built-in templating (need separate frontend)

### Decision

**TO BE DECIDED** - Requires further investigation

### Investigation Tasks

- [ ] Benchmark Flask vs FastAPI for WebRTC workloads
- [ ] Evaluate FastAPI WebSocket stability for production
- [ ] Estimate migration effort (routes, templates, SocketIO handlers)
- [ ] Compare ecosystem maturity (extensions, community support)
- [ ] Assess impact on current roadmap timeline

### Recommendation Criteria

- **Performance:** Must handle 50+ concurrent WebRTC connections
- **Development Velocity:** Must not delay Phase 1-3 timeline significantly
- **Maintainability:** Must support long-term enterprise development
- **Documentation:** Must enable automatic API documentation generation

---

## DEC-003: aiortc vs Native WebRTC Implementation

**Date:** 2026-02-03  
**Status:** 🔍 Under Investigation  
**Deciders:** Technical Team

### Context

The current implementation uses aiortc (Python WebRTC library) for WebRTC peer connections. We need to evaluate whether this is the best approach for production.

### Options Considered

**Option A: Continue with aiortc**
- ✅ Pure Python implementation (no native dependencies)
- ✅ Already working with Unitree SDK
- ✅ Good integration with asyncio
- ✅ Active maintenance and community support
- ❌ Performance overhead compared to native WebRTC
- ❌ Limited codec support compared to native implementations

**Option B: Native WebRTC (libwebrtc bindings)**
- ✅ Better performance (native C++ implementation)
- ✅ Full codec support
- ✅ Industry-standard implementation
- ❌ Complex build process and dependencies
- ❌ Harder to debug and maintain
- ❌ May not integrate well with Unitree SDK

**Option C: Hybrid Approach (aiortc + native codecs)**
- ✅ Balance of Python convenience and native performance
- ✅ Use native codecs where performance critical
- ❌ Increased complexity
- ❌ More dependencies to manage

### Decision

**TO BE DECIDED** - Requires performance benchmarking

### Investigation Tasks

- [ ] Benchmark aiortc latency and throughput
- [ ] Test aiortc stability with 10+ concurrent connections
- [ ] Evaluate native WebRTC Python bindings (pywebrtc, etc.)
- [ ] Measure CPU/memory usage under load
- [ ] Assess Unitree SDK compatibility with alternatives

### Recommendation Criteria

- **Latency:** Must achieve <200ms video latency
- **Stability:** Must handle 24/7 operation without memory leaks
- **Scalability:** Must support 50+ concurrent connections per server
- **Maintainability:** Must be debuggable and maintainable by Python developers

---

## DEC-004: Server-Side PyAudio vs Browser Audio Capture

**Date:** 2025-12-XX (Implemented during audio feature development)  
**Status:** ✅ Accepted  
**Deciders:** Technical Team

### Context

For user-to-robot audio transmission (push-to-talk), we initially attempted browser-based audio capture with SocketIO transmission. This resulted in severe packet loss (browser sent 100+ packets, backend received only 5).

### Decision

Use **server-side PyAudio capture** instead of browser-based audio capture, bypassing SocketIO entirely for audio data transmission.

### Rationale

**Root Cause of Browser Approach Failure:**
- SocketIO with `async_mode='threading'` cannot handle high-frequency audio packets (48kHz sample rate)
- Browser MediaRecorder API generates many small packets
- Network latency and SocketIO overhead caused packet loss and audio degradation

**Server-Side Approach Benefits:**
- PyAudio captures PC microphone directly on server
- Audio data stays in Python process (no network transmission for capture)
- Custom `MicrophoneAudioTrack` class integrates with aiortc WebRTC
- Frames sent to robot via WebRTC data channel (reliable, low-latency)

### Implementation

```python
class MicrophoneAudioTrack(MediaStreamTrack):
    """Capture audio from PC microphone and transmit to robot via WebRTC"""
    
    async def recv(self):
        # Read from PyAudio stream using asyncio.to_thread()
        mic_data = await asyncio.to_thread(
            self.mic_stream.read,
            self.samples_per_frame,
            exception_on_overflow=False
        )
        # Convert to WebRTC audio frame and return
        ...
```

### Consequences

**Positive:**
- ✅ Eliminated packet loss issue completely
- ✅ High-quality audio transmission (48kHz, 2 channels)
- ✅ Push-to-talk works reliably
- ✅ No browser compatibility issues

**Negative:**
- ❌ Requires PyAudio installation on server (platform-specific)
- ❌ Server must have microphone access (not suitable for headless cloud deployment)
- ❌ Cannot support multiple users transmitting audio simultaneously

### Future Considerations

For multi-user scenarios, may need to revisit browser-based audio with:
- WebRTC data channel instead of SocketIO
- Opus codec for efficient transmission
- Proper buffering and jitter handling

---

## DEC-005: Blocking I/O and Event Loop Management

**Date:** 2025-12-XX (Implemented during video degradation fix)
**Status:** ✅ Accepted
**Deciders:** Technical Team

### Context

When audio streaming was enabled, video quality degraded significantly with artifacts, high latency, and corrupted frames. Investigation revealed that PyAudio's blocking I/O operations were freezing the asyncio event loop.

### Decision

Use **`asyncio.to_thread()`** to offload all blocking PyAudio operations (`read()` and `write()`) to a thread pool, preventing them from blocking the event loop.

### Rationale

**Root Cause:**
- Video and audio callbacks run in the SAME asyncio event loop
- PyAudio's `stream.write()` and `stream.read()` are synchronous blocking operations
- When audio callback blocked on PyAudio I/O, video frames piled up in the queue
- Frame accumulation caused latency spikes and visual artifacts

**Solution:**
```python
async def recv_audio_stream(frame):
    """Receive audio from robot and play through speakers"""
    # Run blocking PyAudio write in separate thread
    await asyncio.to_thread(pyaudio_stream.write, audio_bytes)

async def recv(self):
    """Capture microphone audio for transmission"""
    # Run blocking PyAudio read in separate thread
    mic_data = await asyncio.to_thread(
        self.mic_stream.read,
        self.samples_per_frame,
        exception_on_overflow=False
    )
```

### Consequences

**Positive:**
- ✅ Eliminated video degradation completely
- ✅ Smooth video quality even with audio enabled
- ✅ Established pattern for handling blocking I/O in async code
- ✅ Documented in best-practices.md for future development

**Negative:**
- ❌ Slight overhead from thread pool management
- ❌ Requires careful management of thread-safe operations

### Lessons Learned

**Critical Rule:** Never perform blocking I/O operations directly in asyncio event loop callbacks. Always use:
- `asyncio.to_thread()` for blocking operations
- `asyncio.create_task()` for async operations
- Thread pools for CPU-intensive work

This pattern is now documented in `.agent-os/standards/best-practices.md` and must be followed for all future async code.

---

## DEC-006: Flask-SocketIO Threading Mode

**Date:** 2026-02-03
**Status:** 🔍 Under Investigation
**Deciders:** Technical Team

### Context

The current implementation uses Flask-SocketIO with `async_mode='threading'`. We need to evaluate whether this is optimal for production or if other modes (eventlet, gevent) would be better.

### Options Considered

**Option A: Continue with threading mode**
- ✅ Already implemented and working
- ✅ Compatible with standard Python threading
- ✅ No additional dependencies
- ❌ Limited scalability compared to eventlet/gevent
- ❌ Higher memory overhead per connection

**Option B: Switch to eventlet mode**
- ✅ Better scalability for many concurrent connections
- ✅ Lower memory overhead
- ✅ Recommended by Flask-SocketIO documentation
- ❌ Requires eventlet dependency
- ❌ May conflict with asyncio event loop
- ❌ Requires code changes for compatibility

**Option C: Switch to gevent mode**
- ✅ Similar benefits to eventlet
- ✅ Mature and stable
- ❌ Requires gevent dependency
- ❌ May conflict with asyncio event loop
- ❌ Requires code changes for compatibility

### Decision

**TO BE DECIDED** - Requires load testing and compatibility verification

### Investigation Tasks

- [ ] Load test threading mode with 50+ concurrent connections
- [ ] Test eventlet compatibility with aiortc and asyncio
- [ ] Test gevent compatibility with aiortc and asyncio
- [ ] Measure memory usage per connection for each mode
- [ ] Evaluate migration effort and risks

### Recommendation Criteria

- **Scalability:** Must support 50+ concurrent WebSocket connections
- **Compatibility:** Must work with aiortc and asyncio event loop
- **Stability:** Must handle 24/7 operation without issues
- **Migration Risk:** Must not break existing functionality

---

## DEC-007: TDD Testing Philosophy

**Date:** 2026-02-03
**Status:** ✅ Accepted
**Deciders:** Product Owner, Technical Team

### Context

The project currently has minimal testing (test files cleared, only 1 line each). We need to establish a testing philosophy for production development.

### Decision

Adopt **Test-Driven Development (TDD)** approach for all new features and refactoring work.

### Rationale

**Why TDD:**
- **Enterprise Quality:** Commercial fleet management requires high reliability
- **Refactoring Safety:** Comprehensive tests ensure refactoring doesn't break functionality
- **Documentation:** Tests serve as executable documentation of expected behavior
- **Regression Prevention:** Automated tests catch regressions early
- **Design Improvement:** Writing tests first leads to better API design

**TDD Workflow:**
1. Write failing test for new feature
2. Implement minimum code to make test pass
3. Refactor code while keeping tests green
4. Repeat for next feature

### Implementation

**Testing Stack:**
- **Framework:** pytest 7.4+
- **Async Testing:** pytest-asyncio
- **Mocking:** pytest-mock, unittest.mock
- **Coverage:** pytest-cov (target: 80%+)

**Test Structure:**
```
tests/
├── unit/           # Unit tests for services
├── integration/    # Integration tests for routes
├── e2e/            # End-to-end tests for workflows
└── fixtures/       # Shared test fixtures
```

**Coverage Requirements:**
- **Minimum:** 80% code coverage for all modules
- **Critical Paths:** 100% coverage for connection, audio, video, control
- **CI/CD:** Fail build if coverage drops below 80%

### Consequences

**Positive:**
- ✅ High confidence in refactoring (Phase 2)
- ✅ Fewer production bugs
- ✅ Better code design
- ✅ Living documentation

**Negative:**
- ❌ Slower initial development (write tests first)
- ❌ Learning curve for team members unfamiliar with TDD
- ❌ Requires discipline to maintain test coverage

### Success Metrics

- 80%+ code coverage across all modules
- All critical workflows have E2E tests
- CI/CD pipeline runs all tests on every commit
- Zero regressions in production

---

## DEC-008: Cloud Deployment Target

**Date:** 2026-02-03
**Status:** ✅ Accepted
**Deciders:** Product Owner

### Context

The application needs to be deployed for enterprise customers. We need to decide on the deployment target and infrastructure strategy.

### Decision

Target **cloud deployment** (AWS/Azure/GCP) with containerization (Docker) and orchestration (Kubernetes or AWS ECS).

### Rationale

**Why Cloud:**
- **Scalability:** Enterprise customers may need to scale from 10 to 100+ robots
- **Reliability:** Cloud providers offer 99.9%+ uptime SLAs
- **Global Reach:** Deploy close to customer facilities for low latency
- **Managed Services:** Database, caching, monitoring provided by cloud
- **Cost Efficiency:** Pay-per-use model scales with customer growth

**Why Containerization:**
- **Consistency:** Same environment from dev to production
- **Portability:** Can switch cloud providers if needed
- **Scalability:** Easy horizontal scaling with container orchestration
- **CI/CD:** Automated deployment pipeline

### Implementation Plan

**Phase 4 (Performance & Deployment):**
- Docker multi-stage builds for optimized images
- Docker Compose for local development
- Kubernetes or AWS ECS for production orchestration
- GitHub Actions for CI/CD pipeline

**Infrastructure Components:**
- **Compute:** Container instances (ECS/EKS, Azure Container Instances, GKE)
- **Database:** Managed PostgreSQL (RDS, Azure Database, Cloud SQL)
- **Caching:** Managed Redis (ElastiCache, Azure Cache, Memorystore)
- **Load Balancer:** Cloud-native LB (ALB, Azure Load Balancer, Cloud Load Balancing)
- **SSL/TLS:** Let's Encrypt or cloud-managed certificates
- **Monitoring:** CloudWatch, Azure Monitor, or Cloud Monitoring

### Consequences

**Positive:**
- ✅ Enterprise-grade reliability and scalability
- ✅ Managed infrastructure reduces operational overhead
- ✅ Global deployment capabilities
- ✅ Built-in monitoring and logging

**Negative:**
- ❌ Cloud costs (compute, storage, bandwidth)
- ❌ Vendor lock-in risk (mitigated by containerization)
- ❌ Requires cloud expertise for operations

### Cloud Provider Selection

**TO BE DECIDED** - Requires evaluation of:
- Customer preferences and existing infrastructure
- Pricing for expected workload
- Regional availability (data residency requirements)
- Managed service offerings (PostgreSQL, Redis, monitoring)

---

## DEC-009: API-First Documentation Approach

**Date:** 2026-02-03
**Status:** ✅ Accepted
**Deciders:** Product Owner

### Context

The project needs comprehensive documentation for enterprise customers. We need to decide on documentation style and priorities.

### Decision

Adopt **API-first documentation approach** with OpenAPI/Swagger specification as the primary documentation artifact.

### Rationale

**Why API-First:**
- **Integration Focus:** Enterprise customers may want to integrate with existing systems
- **Automation:** OpenAPI spec enables automatic client generation
- **Testing:** API spec can be used for contract testing
- **Clarity:** Forces clear definition of API contracts before implementation

**Documentation Priorities (from user requirements):**
1. **API Documentation** - OpenAPI/Swagger spec for all endpoints
2. **User Guide** - Operator manual for robot control
3. **Deployment Guide** - Step-by-step production deployment

### Implementation

**Phase 1 (Documentation & Testing Foundation):**
- Generate OpenAPI 3.0 specification for all Flask routes
- Use Swagger UI for interactive API documentation
- Document request/response schemas with examples
- Include authentication and authorization details

**Tools:**
- **OpenAPI Generation:** flask-swagger-ui or manual YAML
- **API Testing:** Use OpenAPI spec for contract testing
- **Documentation Hosting:** Swagger UI served at `/api/docs`

### Consequences

**Positive:**
- ✅ Clear API contracts for integrations
- ✅ Automatic client generation possible
- ✅ Better developer experience for API consumers
- ✅ API spec serves as single source of truth

**Negative:**
- ❌ Requires maintaining OpenAPI spec alongside code
- ❌ Learning curve for OpenAPI specification format

### Success Metrics

- Complete OpenAPI spec for all endpoints
- Interactive Swagger UI accessible at `/api/docs`
- All request/response schemas documented with examples
- User guide and deployment guide complete

---

## DEC-010: Vanilla JavaScript + Tailwind CSS for Frontend

**Date:** 2026-02-03
**Status:** ✅ Accepted
**Deciders:** Product Owner, Technical Team
**Related Spec:** @.agent-os/specs/2026-02-03-frontend-ui-overhaul/

### Context

The frontend UI overhaul requires choosing between modern JavaScript frameworks (React/Vue with Shadcn UI) or enhanced vanilla JavaScript with a CSS framework (Tailwind CSS). The current implementation uses vanilla JavaScript successfully, but the UI needs modernization.

### Decision

Use **Enhanced Vanilla JavaScript + Tailwind CSS** instead of modern frameworks (React/Vue).

### Rationale

**Why Vanilla JS + Tailwind:**
- **Simpler Flask Integration:** No build step required, just serve static files
- **Maintains Current Patterns:** Current codebase uses vanilla JS successfully for WebRTC/WebSocket
- **Easier Incremental Migration:** Can migrate piece by piece without framework overhead
- **No Framework Lock-in:** Flexibility to adopt framework later if needed
- **Faster Initial Development:** No framework learning curve or build tooling setup
- **Better for Phase 5:** Server-side rendering with Flask templates aligns with planned login/auth

**Tailwind CSS Benefits:**
- Utility-first approach enables rapid UI development
- CDN delivery (no build step)
- Comprehensive design system out of the box
- Excellent documentation and community support

### Consequences

**Positive:**
- ✅ Faster development without build complexity
- ✅ Simpler deployment (no webpack/vite configuration)
- ✅ Easier to understand for developers unfamiliar with React/Vue
- ✅ Smaller bundle size (no framework overhead)
- ✅ Direct DOM manipulation maintains control over WebRTC/WebSocket integration

**Negative:**
- ❌ More manual DOM manipulation code
- ❌ Less structured state management (no Redux/Vuex)
- ❌ More boilerplate for complex UI interactions
- ❌ Harder to scale to very complex UIs (mitigated by modular JS organization)

### Alternatives Considered

**React + Shadcn UI:**
- ✅ Component-based architecture, rich UI library, better state management
- ❌ Requires build tooling, more complex Flask integration, steeper learning curve

**Vue + Shadcn:**
- ✅ Similar benefits to React, gentler learning curve
- ❌ Still requires build step, adds framework dependency

### Related Decisions

- DEC-011: Multi-page architecture (complements vanilla JS approach)
- DEC-001: Commercial fleet management (enterprise quality without framework complexity)

---

## DEC-011: Multi-Page Architecture with Enhanced Templates

**Date:** 2026-02-03
**Status:** ✅ Accepted
**Deciders:** Product Owner, Technical Team
**Related Spec:** @.agent-os/specs/2026-02-03-frontend-ui-overhaul/

### Context

The UI overhaul requires choosing between a Single Page Application (SPA) architecture with client-side routing or a multi-page architecture with server-side routing and enhanced templates.

### Decision

Use **Multi-Page Architecture** with separate landing (`/`) and control (`/control`) pages, leveraging Flask's server-side routing and Jinja2 templates.

### Rationale

**Why Multi-Page:**
- **Easier Incremental Migration:** Can create new pages alongside existing monolithic UI
- **Maintains Flask Strengths:** Leverages server-side rendering and template inheritance
- **Simpler Deployment:** No client-side routing complexity
- **Better for Phase 5:** Server-side session management aligns with planned login/auth
- **Lower Migration Risk:** Existing interface remains functional during transition
- **Can Evolve Later:** Can migrate to SPA in future if requirements change

**Architecture:**
- Landing page (`/`) - Robot management dashboard with settings
- Control page (`/control`) - Fullscreen video with status HUD
- Shared base template (`base.html`) with Tailwind CSS
- Server-side routing via Flask blueprints

### Consequences

**Positive:**
- ✅ Low-risk incremental migration strategy
- ✅ Simpler architecture (no client-side router)
- ✅ Better SEO (server-rendered pages)
- ✅ Easier integration with Flask session management
- ✅ Maintains existing WebSocket/WebRTC patterns

**Negative:**
- ❌ Full page reload when navigating between landing and control
- ❌ Less "app-like" feel compared to SPA
- ❌ Duplicate code if shared components needed across pages (mitigated by template inheritance)

### Alternatives Considered

**Single Page Application (SPA):**
- ✅ No page reloads, better UX, more "app-like" feel
- ❌ Requires client-side routing, API-first backend, more complex state management
- ❌ Higher migration risk (bigger architectural change)

**Hybrid Approach (SPA with server-side initial render):**
- ✅ Best of both worlds
- ❌ Most complex to implement, requires framework like Next.js or Nuxt.js

### Related Decisions

- DEC-010: Vanilla JS + Tailwind (complements multi-page approach)
- DEC-001: Commercial fleet management (prioritizes reliability over "app-like" UX)

---

## Decision Template

Use this template for future architectural decisions:

```markdown
## DEC-XXX: Decision Title

**Date:** YYYY-MM-DD
**Status:** 🔍 Under Investigation | ✅ Accepted | ❌ Rejected | ⚠️ Deprecated
**Deciders:** Names/Roles

### Context

What is the issue we're facing? What factors are driving this decision?

### Decision

What is the change we're proposing or have agreed to?

### Rationale

Why did we choose this option? What are the key factors?

### Consequences

**Positive:**
- ✅ Benefit 1
- ✅ Benefit 2

**Negative:**
- ❌ Drawback 1
- ❌ Drawback 2

### Alternatives Considered

What other options did we evaluate and why were they rejected?

### Related Decisions

- DEC-XXX: Related decision
```

---

## Version History

- **v1.0.0** (2026-02-03): Initial ADR document created
- **DEC-001**: Commercial fleet management positioning
- **DEC-002**: Flask vs FastAPI (under investigation)
- **DEC-003**: aiortc vs native WebRTC (under investigation)
- **DEC-004**: Server-side PyAudio for audio capture (accepted)
- **DEC-005**: Blocking I/O and event loop management (accepted)
- **DEC-006**: Flask-SocketIO threading mode (under investigation)
- **DEC-007**: TDD testing philosophy (accepted)
- **DEC-008**: Cloud deployment target (accepted)
- **DEC-009**: API-first documentation approach (accepted)
- **DEC-010**: Vanilla JavaScript + Tailwind CSS for frontend (accepted)
- **DEC-011**: Multi-page architecture with enhanced templates (accepted)


