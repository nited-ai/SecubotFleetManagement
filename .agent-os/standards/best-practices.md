# Development Best Practices - Unitree WebRTC Connect

> Version: 1.0.0
> Last updated: 2026-02-03
> Scope: Unitree Go2 Robot WebRTC Control Interface
> Stack: Python 3.11+, Flask, WebRTC, asyncio, PyAudio

## Context

This file defines development best practices for the Unitree WebRTC Connect project - a web-based control interface for Unitree Go2 robots using WebRTC for real-time video/audio streaming and robot control.

**Current State:** Monolithic `web_interface.py` (1500+ lines) that needs refactoring into modular, testable components.

**Goal:** Transform into a production-ready, maintainable codebase with comprehensive test coverage.

## Core Principles

### Keep It Simple
- Implement code in the fewest lines possible
- Avoid over-engineering solutions
- Choose straightforward approaches over clever ones
- Prefer composition over inheritance
- Use Python's type hints to catch errors early
- Follow PEP 8 style guidelines

### Optimize for Readability
- Prioritize code clarity over micro-optimizations
- Write self-documenting code with clear variable names
- Add docstrings for "why" not "what"
- Use descriptive function and class names
- Keep functions small and focused (< 50 lines)
- Use type hints for all function signatures

### DRY (Don't Repeat Yourself)
- Extract repeated business logic to service classes
- Extract repeated route logic to blueprint modules
- Create utility functions for common operations
- Use dataclasses or Pydantic models for shared data structures
- Avoid duplicating WebRTC connection logic

## Modular Architecture & Service Separation

### Service Isolation
- Each service should be **completely self-contained**
- Services must function independently with clear interfaces
- Avoid tight coupling between services
- Use dependency injection for service dependencies
- Services should not directly access Flask routes or global state

### Modular Structure
- **Small, focused modules** (< 200 lines each)
- **Single responsibility principle** - one module, one purpose
- **Clear separation of concerns** - routes, services, models, utilities
- **Independent testing** - each module testable in isolation

### Microservice Principles
- Each feature module should be **independently testable**
- **Parallel team development** - multiple developers can work simultaneously
- **Easy to locate and fix bugs** - clear module boundaries
- **Simple to add new features** - plug-and-play architecture

### Target Module Structure for Unitree WebRTC Connect
```
unitree_webrtc_connect/
├── app/
│   ├── __init__.py                   # Flask app factory
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── connection.py             # /connect, /disconnect endpoints
│   │   ├── control.py                # /gamepad/*, /keyboard/* endpoints
│   │   ├── audio.py                  # /audio/* endpoints
│   │   └── video.py                  # /video_feed endpoint
│   ├── services/
│   │   ├── __init__.py
│   │   ├── webrtc_service.py         # WebRTC connection management
│   │   ├── audio_service.py          # Audio streaming (PyAudio, tracks)
│   │   ├── video_service.py          # Video streaming (frame queue)
│   │   ├── control_service.py        # Robot control commands
│   │   └── state_service.py          # Global state management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── config.py                 # Configuration dataclasses
│   │   ├── commands.py               # Robot command models
│   │   └── state.py                  # Application state models
│   └── utils/
│       ├── __init__.py
│       ├── async_helpers.py          # asyncio utilities
│       └── logging_config.py         # Logging setup
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
├── templates/
│   └── index.html                    # Frontend UI
├── web_interface.py                  # Main entry point (simplified)
├── requirements.txt
└── pytest.ini
```

## Dependencies

### Choose Libraries Wisely
When adding third-party dependencies:
- Select the most popular and actively maintained option
- Check the library's GitHub repository for:
  - Recent commits (within last 6 months)
  - Active issue resolution
  - Number of stars/downloads
  - Clear documentation
  - Python type hints support
- Prefer lightweight libraries over heavy frameworks
- Avoid dependencies that bundle large amounts of unused code
- Pin versions in requirements.txt for reproducibility

### Current Production Stack
- **Web Framework**: Flask 3.0+ with Flask-SocketIO
- **WebRTC**: aiortc (Python WebRTC implementation)
- **Audio Processing**: PyAudio (PortAudio bindings)
- **Video Processing**: OpenCV (cv2), NumPy
- **Async Runtime**: asyncio (Python 3.11+ native)
- **Robot SDK**: unitree_webrtc_connect (custom library)
- **Testing**: pytest, pytest-asyncio, pytest-mock, pytest-cov
- **Type Checking**: mypy (optional but recommended)
- **Code Quality**: black (formatter), flake8 (linter), isort (import sorter)

### Recommended Additional Libraries
- **Validation**: Pydantic (data validation with type hints)
- **Configuration**: python-dotenv (environment variables)
- **Logging**: structlog (structured logging)
- **API Documentation**: Flask-RESTX or apispec (OpenAPI/Swagger)
- **Monitoring**: prometheus-flask-exporter (metrics)

## Code Organization

### File Structure
- Keep files focused on a single responsibility
- Group related functionality together
- Use consistent naming conventions (snake_case for Python)
- Use `__init__.py` to expose public APIs
- Separate concerns: routes, services, models, utilities

### Service Class Best Practices

#### Service Size
- **Maximum 200 lines** per service file
- Extract complex logic to utility functions
- Split large services into smaller specialized services
- Use composition patterns for flexibility

#### Service Dependencies
- Use dependency injection (pass dependencies to `__init__`)
- Avoid global state within services
- Use type hints for all method signatures
- Make services stateless when possible (state in StateService)

#### Example Service Structure
```python
# app/services/audio_service.py
"""Audio streaming service for bidirectional robot audio."""
import asyncio
import logging
from typing import Optional
import pyaudio
import numpy as np
from av import AudioFrame as AVAudioFrame

from ..models.config import AudioConfig
from .state_service import StateService


class AudioService:
    """Manages bidirectional audio streaming with the robot."""

    def __init__(self, config: AudioConfig, state_service: StateService):
        """Initialize audio service with configuration.

        Args:
            config: Audio configuration (sample rate, channels, etc.)
            state_service: Shared state management service
        """
        self.config = config
        self.state = state_service
        self.pyaudio_instance: Optional[pyaudio.PyAudio] = None
        self.pyaudio_stream: Optional[pyaudio.Stream] = None
        self._logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """Initialize PyAudio streams for audio playback."""
        self.pyaudio_instance = pyaudio.PyAudio()
        self.pyaudio_stream = self.pyaudio_instance.open(
            format=self.config.format,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            output=True,
            frames_per_buffer=self.config.frames_per_buffer
        )
        self.state.audio_initialized = True
        self._logger.info("Audio service initialized")

    async def play_audio_frame(self, frame: AVAudioFrame) -> None:
        """Play audio frame through speakers (non-blocking).

        Args:
            frame: Audio frame from robot
        """
        if self.state.audio_muted or not self.pyaudio_stream:
            return

        audio_data = np.frombuffer(frame.to_ndarray(), dtype=np.int16)
        audio_bytes = audio_data.tobytes()

        # Offload blocking I/O to thread pool
        await asyncio.to_thread(self.pyaudio_stream.write, audio_bytes)

    async def cleanup(self) -> None:
        """Clean up audio resources."""
        if self.pyaudio_stream:
            self.pyaudio_stream.stop_stream()
            self.pyaudio_stream.close()
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
        self.state.audio_initialized = False
        self._logger.info("Audio service cleaned up")
```

### Route Blueprint Pattern
- Organize routes into Flask blueprints by feature
- Keep route handlers thin (delegate to services)
- Use consistent error handling across routes
- Return proper HTTP status codes

```python
# app/routes/audio.py
"""Audio control routes."""
from flask import Blueprint, request, jsonify
from ..services.audio_service import AudioService
from ..services.state_service import StateService

audio_bp = Blueprint('audio', __name__, url_prefix='/audio')


def create_audio_routes(audio_service: AudioService, state_service: StateService):
    """Create audio routes with injected dependencies."""

    @audio_bp.route('/toggle', methods=['POST'])
    def toggle_audio():
        """Mute or unmute audio playback dynamically."""
        try:
            data = request.json
            enable = data.get('enable', False)

            state_service.audio_muted = not enable

            return jsonify({
                'status': 'success',
                'enabled': enable,
                'muted': state_service.audio_muted,
                'message': f"Audio {'unmuted' if enable else 'muted'}"
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    return audio_bp
```

## Testing

### Testing Strategy
- **Unit Tests**: Test individual services and utilities in isolation
- **Integration Tests**: Test route handlers with mocked services
- **E2E Tests**: Test critical user journeys (connection, control, audio/video)
- Use pytest for all tests
- Use pytest-asyncio for async function tests
- Use pytest-mock for mocking dependencies
- Aim for 80%+ code coverage

### Test Organization
- Organize tests by type: `tests/unit/`, `tests/integration/`
- Create fixtures in `tests/fixtures/` for reusable test data
- Mock external dependencies (WebRTC, PyAudio, robot connection)
- Test both happy path and error conditions
- Use descriptive test names that explain what is being tested

### Example Test Structure
```python
# tests/unit/test_audio_service.py
"""Unit tests for AudioService."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import numpy as np
from av import AudioFrame as AVAudioFrame

from app.services.audio_service import AudioService
from app.services.state_service import StateService
from app.models.config import AudioConfig


@pytest.fixture
def audio_config():
    """Create test audio configuration."""
    return AudioConfig(
        sample_rate=48000,
        channels=2,
        format=8,  # paInt16
        frames_per_buffer=8192
    )


@pytest.fixture
def state_service():
    """Create test state service."""
    return StateService()


@pytest.fixture
def audio_service(audio_config, state_service):
    """Create test audio service."""
    return AudioService(audio_config, state_service)


@pytest.mark.asyncio
async def test_initialize_audio_service(audio_service, state_service):
    """Test audio service initialization."""
    with patch('pyaudio.PyAudio') as mock_pyaudio:
        await audio_service.initialize()

        assert state_service.audio_initialized is True
        mock_pyaudio.assert_called_once()


@pytest.mark.asyncio
async def test_play_audio_frame_when_muted(audio_service, state_service):
    """Test that audio frames are discarded when muted."""
    state_service.audio_muted = True
    mock_frame = Mock(spec=AVAudioFrame)

    # Should not raise exception, just return early
    await audio_service.play_audio_frame(mock_frame)

    # Frame should not be processed
    mock_frame.to_ndarray.assert_not_called()


@pytest.mark.asyncio
async def test_play_audio_frame_when_unmuted(audio_service, state_service):
    """Test that audio frames are played when unmuted."""
    state_service.audio_muted = False

    # Mock PyAudio stream
    mock_stream = Mock()
    audio_service.pyaudio_stream = mock_stream

    # Create mock frame
    mock_frame = Mock(spec=AVAudioFrame)
    mock_frame.to_ndarray.return_value = np.zeros(1920, dtype=np.int16)

    with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
        await audio_service.play_audio_frame(mock_frame)

        # Verify frame was processed
        mock_frame.to_ndarray.assert_called_once()
        mock_to_thread.assert_called_once()


@pytest.mark.asyncio
async def test_cleanup_audio_service(audio_service, state_service):
    """Test audio service cleanup."""
    # Setup mocks
    audio_service.pyaudio_stream = Mock()
    audio_service.pyaudio_instance = Mock()
    state_service.audio_initialized = True

    await audio_service.cleanup()

    # Verify cleanup
    audio_service.pyaudio_stream.stop_stream.assert_called_once()
    audio_service.pyaudio_stream.close.assert_called_once()
    audio_service.pyaudio_instance.terminate.assert_called_once()
    assert state_service.audio_initialized is False
```

### Integration Test Example
```python
# tests/integration/test_audio_routes.py
"""Integration tests for audio routes."""
import pytest
from flask import Flask
from app.routes.audio import create_audio_routes
from app.services.audio_service import AudioService
from app.services.state_service import StateService
from app.models.config import AudioConfig


@pytest.fixture
def app():
    """Create test Flask app."""
    app = Flask(__name__)
    app.config['TESTING'] = True

    # Create services
    config = AudioConfig(sample_rate=48000, channels=2, format=8, frames_per_buffer=8192)
    state_service = StateService()
    audio_service = AudioService(config, state_service)

    # Register routes
    audio_bp = create_audio_routes(audio_service, state_service)
    app.register_blueprint(audio_bp)

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_toggle_audio_enable(client):
    """Test enabling audio via API."""
    response = client.post('/audio/toggle', json={'enable': True})

    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['enabled'] is True
    assert data['muted'] is False


def test_toggle_audio_disable(client):
    """Test disabling audio via API."""
    response = client.post('/audio/toggle', json={'enable': False})

    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['enabled'] is False
    assert data['muted'] is True
```

## Performance

### Async Performance (Critical for WebRTC)
- **NEVER block the asyncio event loop** - use `asyncio.to_thread()` for blocking I/O
- Use `asyncio.create_task()` for concurrent operations
- Avoid synchronous I/O in async functions (PyAudio, file I/O, network calls)
- Profile async code with `asyncio` debug mode
- Monitor event loop lag with custom metrics

### Video Streaming Optimization
- Use frame queues with bounded size (prevent memory leaks)
- Implement frame dropping when queue is full (maintain real-time)
- Use thread-safe locks for shared frame buffers
- Compress frames before transmission (JPEG encoding)
- Limit frame rate to 30 FPS (balance quality vs bandwidth)

### Audio Streaming Optimization
- Use `asyncio.to_thread()` for PyAudio read/write operations
- Keep audio buffer sizes optimal (960 samples for 20ms at 48kHz)
- Discard frames when muted (don't process unnecessarily)
- Use proper timestamp management for WebRTC audio frames
- Monitor audio buffer overflow/underflow

### Memory Management
- Clean up resources in finally blocks or context managers
- Avoid circular references (use weak references if needed)
- Monitor memory usage with `tracemalloc` in development
- Implement proper cleanup on disconnect
- Use generators for large data processing

## Error Handling

### Exception Handling Strategy
- Use try-except blocks for all external I/O operations
- Catch specific exceptions, not bare `except:`
- Log exceptions with context (use structured logging)
- Return proper HTTP status codes from routes
- Clean up resources in finally blocks

### Async Error Handling
- Always handle exceptions in async functions
- Use `asyncio.CancelledError` for task cancellation
- Provide user-friendly error messages in API responses
- Implement retry mechanisms for transient failures (WebRTC connection)
- Use proper error states in frontend

### WebRTC-Specific Error Handling
- Handle connection timeouts gracefully
- Detect and recover from peer connection failures
- Handle audio/video track errors without crashing
- Implement reconnection logic with exponential backoff
- Log WebRTC errors for debugging

```python
# app/services/webrtc_service.py
"""WebRTC connection service with proper error handling."""
import asyncio
import logging
from typing import Optional
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection

logger = logging.getLogger(__name__)


class WebRTCService:
    """Manages WebRTC connection to robot."""

    async def connect(
        self,
        ip: str,
        timeout: int = 30,
        max_retries: int = 3
    ) -> bool:
        """Connect to robot with retry logic.

        Args:
            ip: Robot IP address
            timeout: Connection timeout in seconds
            max_retries: Maximum number of retry attempts

        Returns:
            True if connected successfully, False otherwise

        Raises:
            ConnectionError: If connection fails after all retries
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Connection attempt {attempt + 1}/{max_retries}")

                # Attempt connection with timeout
                await asyncio.wait_for(
                    self._establish_connection(ip),
                    timeout=timeout
                )

                logger.info("Successfully connected to robot")
                return True

            except asyncio.TimeoutError:
                logger.warning(f"Connection timeout (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

            except ConnectionRefusedError:
                logger.error("Robot refused connection - may be connected to another client")
                raise

            except Exception as e:
                logger.error(f"Unexpected error during connection: {e}", exc_info=True)
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        raise ConnectionError(f"Failed to connect after {max_retries} attempts")

    async def _establish_connection(self, ip: str) -> None:
        """Internal method to establish WebRTC connection."""
        # Connection logic here
        pass
```

### Route Error Handling Pattern
```python
# app/routes/connection.py
"""Connection routes with consistent error handling."""
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)
connection_bp = Blueprint('connection', __name__)


@connection_bp.route('/connect', methods=['POST'])
def connect():
    """Connect to robot with proper error handling."""
    try:
        data = request.json
        ip = data.get('ip')

        if not ip:
            return jsonify({
                'status': 'error',
                'message': 'IP address is required'
            }), 400

        # Delegate to service
        # ... connection logic ...

        return jsonify({
            'status': 'success',
            'message': 'Connected to robot'
        })

    except ConnectionRefusedError:
        logger.error("Robot refused connection")
        return jsonify({
            'status': 'error',
            'message': 'Robot is already connected to another client'
        }), 409

    except asyncio.TimeoutError:
        logger.error("Connection timeout")
        return jsonify({
            'status': 'error',
            'message': 'Connection timeout - check if robot is powered on'
        }), 504

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500
```

## Documentation

### Code Documentation
- Use docstrings for all public functions, classes, and modules
- Follow Google-style or NumPy-style docstring format
- Document parameters, return values, and exceptions
- Include usage examples for complex functions
- Document any side effects or state changes

### API Documentation
- Document all route endpoints with docstrings
- Include request/response examples
- Document error responses and status codes
- Use OpenAPI/Swagger for API documentation (optional)
- Keep README.md updated with setup instructions

### Example Docstring Format
```python
def process_robot_command(command: str, velocity: float) -> dict:
    """Process and validate robot movement command.

    This function validates the command type and velocity range before
    sending to the robot. Invalid commands are rejected with an error.

    Args:
        command: Movement command ('forward', 'backward', 'left', 'right')
        velocity: Movement velocity in m/s, range [-1.0, 1.0]

    Returns:
        dict: Command result with keys:
            - status (str): 'success' or 'error'
            - message (str): Result message
            - command_id (int): Unique command identifier (if successful)

    Raises:
        ValueError: If command is invalid or velocity out of range
        ConnectionError: If robot is not connected

    Example:
        >>> result = process_robot_command('forward', 0.5)
        >>> print(result)
        {'status': 'success', 'message': 'Command sent', 'command_id': 1008}
    """
    # Implementation here
    pass
```

## Refactoring Guidelines

### Breaking Down the Monolith
When refactoring `web_interface.py` (1500+ lines):

1. **Identify Logical Boundaries**
   - Group related functions (connection, audio, video, control)
   - Extract global state into StateService
   - Separate route handlers from business logic

2. **Extract Services First**
   - Create service classes for each domain (audio, video, control, webrtc)
   - Move business logic from routes to services
   - Inject dependencies (don't use global state in services)

3. **Create Route Blueprints**
   - Split routes into separate blueprint files
   - Keep route handlers thin (just validation + service calls)
   - Use consistent error handling patterns

4. **Write Tests During Refactoring**
   - Write tests for existing functionality BEFORE refactoring
   - Ensure tests pass after each refactoring step
   - Use tests to verify no functionality is broken

5. **Refactor Incrementally**
   - Don't refactor everything at once
   - Refactor one service/route at a time
   - Commit after each successful refactoring step
   - Keep the application working at all times

### Refactoring Checklist
- [ ] Extract StateService (global state management)
- [ ] Extract WebRTCService (connection management)
- [ ] Extract AudioService (audio streaming)
- [ ] Extract VideoService (video streaming)
- [ ] Extract ControlService (robot commands)
- [ ] Create route blueprints (connection, audio, video, control)
- [ ] Write unit tests for each service
- [ ] Write integration tests for routes
- [ ] Update documentation
- [ ] Remove old monolithic code

---

## Project-Specific Best Practices

### WebRTC Event Loop Management
- **CRITICAL**: Never block the asyncio event loop
- Use `asyncio.to_thread()` for all blocking I/O (PyAudio, file I/O)
- Run WebRTC connection in dedicated event loop thread
- Use `asyncio.run_coroutine_threadsafe()` to schedule tasks from Flask routes

### Audio Streaming Best Practices
- Always initialize audio stream on connection (even if muted)
- Use `audio_muted` flag for instant mute/unmute (no reconnection)
- Discard frames when muted (don't process unnecessarily)
- Use proper timestamp management for WebRTC audio frames
- Clean up PyAudio resources on disconnect

### Video Streaming Best Practices
- Use bounded frame queue (prevent memory leaks)
- Drop frames when queue is full (maintain real-time)
- Use thread-safe locks for frame buffer access
- Encode frames as JPEG before transmission
- Limit frame rate to 30 FPS

### Robot Control Best Practices
- Validate all movement commands before sending
- Implement emergency stop functionality
- Use proper command IDs (API ID 1008 for Move command)
- Handle control mode switching (AI mode, Sport mode)
- Implement control timeout (stop if no commands received)

### State Management
- Use StateService for all global state
- Make state changes atomic (use locks)
- Avoid direct global variable access
- Provide clear state getters/setters
- Log state changes for debugging

---

## Thread Safety Anti-Patterns

### ❌ CRITICAL: Double-Locking Deadlock

**This is the #1 most dangerous bug pattern in this codebase.**

The StateService uses properties with **internal locking** for thread-safety. External code must NEVER use explicit locks when accessing these properties, as this creates a deadlock that freezes the entire application.

#### The Problem

StateService properties acquire locks internally:

```python
# Inside StateService class
@property
def latest_frame(self):
    """Get latest frame."""
    with self._frame_lock:  # ✅ Lock acquired here
        return self._latest_frame

@latest_frame.setter
def latest_frame(self, value):
    """Set latest frame."""
    with self._frame_lock:  # ✅ Lock acquired here
        self._latest_frame = value
```

When external code wraps property access with the same lock, it tries to acquire the lock **twice**, causing a deadlock:

```python
# ❌ WRONG - CAUSES DEADLOCK!
with state._frame_lock:  # First lock acquisition
    state.latest_frame = img.copy()  # Property tries to acquire SAME lock = DEADLOCK!
```

#### Real-World Impact

This bug caused **complete system failure** during Phase 2 refactoring:
- ✗ Video streaming frozen (no frames displayed)
- ✗ Audio playback broken (no sound from robot)
- ✗ Browser loading indicator spinning forever
- ✗ All WebRTC callbacks deadlocked

The application appeared to connect successfully but all media streaming was completely broken.

#### Anti-Pattern Examples

**❌ WRONG - Video Callback:**
```python
async def recv_camera_stream(track: MediaStreamTrack):
    while True:
        frame = await track.recv()
        img = frame.to_ndarray(format="bgr24")

        # ❌ DEADLOCK! Property already uses _frame_lock
        with state._frame_lock:
            state.latest_frame = img.copy()
```

**❌ WRONG - Audio Toggle:**
```python
@app.route('/audio/toggle', methods=['POST'])
def toggle_audio_streaming():
    data = request.json
    enable = data.get('enable', False)

    # ❌ DEADLOCK! Properties already use _audio_lock
    with state._audio_lock:
        state.audio_streaming_enabled = enable
        state.audio_muted = not enable
```

**❌ WRONG - Cleanup:**
```python
def disconnect():
    # ❌ DEADLOCK! Properties already use _frame_lock
    with state._frame_lock:
        state.latest_frame = None
```

#### ✅ Correct Patterns

**✅ RIGHT - Video Callback:**
```python
async def recv_camera_stream(track: MediaStreamTrack):
    while True:
        frame = await track.recv()
        img = frame.to_ndarray(format="bgr24")

        # ✅ Property handles locking internally
        state.latest_frame = img.copy()
```

**✅ RIGHT - Audio Toggle:**
```python
@app.route('/audio/toggle', methods=['POST'])
def toggle_audio_streaming():
    data = request.json
    enable = data.get('enable', False)

    # ✅ Properties handle locking internally
    state.audio_streaming_enabled = enable
    state.audio_muted = not enable
```

**✅ RIGHT - Cleanup:**
```python
def disconnect():
    # ✅ Property handles locking internally
    state.latest_frame = None
```

#### When to Use Locks Directly

**Only use locks directly in these specific cases:**

1. **Inside StateService class methods** (accessing private attributes):
   ```python
   # Inside StateService class
   def reset_audio_state(self):
       with self._audio_lock:
           self._audio_muted = True  # ✅ Direct attribute access
           self._audio_streaming_enabled = False
   ```

2. **Atomic multi-attribute operations** (inside StateService only):
   ```python
   # Inside StateService class
   def update_frame_atomically(self, frame, timestamp):
       with self._frame_lock:
           self._latest_frame = frame  # ✅ Direct attributes
           self._frame_timestamp = timestamp
   ```

**NEVER use locks from external code:**
```python
# ❌ NEVER DO THIS from web_interface.py or any external code
with state._frame_lock:
    # Any code here
```

#### Detection and Prevention

**Automated Detection:**
```bash
# Run before committing
grep -n "with state\._.*lock:" web_interface.py app/**/*.py

# If this returns ANY results, review them - likely bugs!
```

**Code Review Checklist:**
- [ ] No `with state._frame_lock:` in external code
- [ ] No `with state._audio_lock:` in external code
- [ ] No `with state._gamepad_lock:` in external code
- [ ] No `with state._keyboard_mouse_lock:` in external code
- [ ] All state access uses properties directly

**Pre-commit Hook:**
```bash
# .git/hooks/pre-commit
#!/bin/bash
if grep -q "with state\._.*lock:" web_interface.py app/**/*.py; then
    echo "❌ ERROR: Double-locking pattern detected!"
    echo "External code should NEVER use 'with state._lock:'"
    echo "Properties handle locking internally."
    exit 1
fi
```

#### Summary

**Golden Rules:**
1. **External code**: ALWAYS use properties directly (e.g., `state.latest_frame = value`)
2. **StateService methods**: Can use locks with private attributes (e.g., `self._latest_frame`)
3. **Never mix**: Don't use `with state._lock:` and then access properties
4. **When in doubt**: Just use the property - it's thread-safe!

See `.agent-os/standards/code-review-checklist.md` for automated detection scripts.

---

## SDK Example Patterns (examples/go2/)

The `examples/go2/` folder contains reference implementations that demonstrate best practices for integrating Unitree SDK features. Follow these patterns when adding new functionality.

### Connection Pattern (All Examples)

**Standard connection setup:**
```python
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

# Choose connection method based on deployment
conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.8.181")
# conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, serialNumber="B42D2000XXXXXXXX")
# conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.Remote, serialNumber="...", username="...", password="...")
# conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalAP)

await conn.connect()
```

**Best Practices:**
- Always provide multiple connection method examples (commented out)
- Use LocalSTA with IP for development (fastest, most reliable)
- Use Remote for internet-based control
- Use LocalAP for direct robot WiFi connection
- Handle connection errors with try-except blocks

### Audio Streaming Pattern (examples/go2/audio/)

**Reference:** `examples/go2/audio/live_audio/live_recv_audio.py`

**Key Pattern - Audio Reception:**
```python
import pyaudio
import numpy as np

# Initialize PyAudio OUTSIDE async context
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=2, rate=48000,
                output=True, frames_per_buffer=8192)

async def recv_audio_stream(frame):
    """Handle audio frames - BLOCKING I/O WARNING!"""
    audio_data = np.frombuffer(frame.to_ndarray(), dtype=np.int16)
    stream.write(audio_data.tobytes())  # ⚠️ BLOCKS EVENT LOOP

# Setup audio channel
conn.audio.switchAudioChannel(True)
conn.audio.add_track_callback(recv_audio_stream)

# Cleanup in finally block
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
```

**⚠️ CRITICAL ISSUE IN EXAMPLE:**
The example uses blocking `stream.write()` which will freeze the event loop. **Our production code fixes this:**

```python
async def recv_audio_stream(frame):
    """Fixed version - non-blocking."""
    audio_data = np.frombuffer(frame.to_ndarray(), dtype=np.int16)
    # Use asyncio.to_thread() to prevent blocking
    await asyncio.to_thread(stream.write, audio_data.tobytes())
```

**Best Practices:**
- Use `asyncio.to_thread()` for PyAudio operations (not in example, but required!)
- Initialize PyAudio before async context
- Use 48kHz sample rate, 2 channels (stereo)
- Use 8192 frames per buffer for stability
- Always clean up PyAudio resources in finally block

### Video Streaming Pattern (examples/go2/video/)

**Reference:** `examples/go2/video/camera_stream/display_video_channel.py`

**Key Pattern - Separate Event Loop Thread:**
```python
import asyncio
import threading
from queue import Queue

frame_queue = Queue()

async def recv_camera_stream(track):
    """Receive video frames and queue them."""
    while True:
        frame = await track.recv()
        img = frame.to_ndarray(format="bgr24")
        frame_queue.put(img)

def run_asyncio_loop(loop):
    """Run WebRTC in dedicated thread."""
    asyncio.set_event_loop(loop)
    async def setup():
        await conn.connect()
        conn.video.switchVideoChannel(True)
        conn.video.add_track_callback(recv_camera_stream)

    loop.run_until_complete(setup())
    loop.run_forever()

# Create separate event loop for WebRTC
loop = asyncio.new_event_loop()
asyncio_thread = threading.Thread(target=run_asyncio_loop, args=(loop,))
asyncio_thread.start()

# Main thread processes frames
while True:
    if not frame_queue.empty():
        img = frame_queue.get()
        cv2.imshow('Video', img)
```

**Best Practices:**
- Run WebRTC in dedicated event loop thread (prevents blocking main thread)
- Use Queue for thread-safe frame passing
- Convert frames to numpy arrays with `to_ndarray(format="bgr24")`
- Process frames in main thread (OpenCV display, encoding, etc.)
- Clean up event loop on exit: `loop.call_soon_threadsafe(loop.stop)`

### Robot Control Pattern (examples/go2/data_channel/sportmode/)

**Reference:** `examples/go2/data_channel/sportmode/sportmode.py`

**Key Pattern - Motion Mode Switching:**
```python
from unitree_webrtc_connect.constants import RTC_TOPIC, SPORT_CMD

# Check current motion mode
response = await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["MOTION_SWITCHER"],
    {"api_id": 1001}
)

current_mode = json.loads(response['data']['data'])['name']

# Switch to AI mode
await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["MOTION_SWITCHER"],
    {"api_id": 1002, "parameter": {"name": "ai"}}
)
await asyncio.sleep(10)  # Wait for mode switch

# Send movement command
await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["SPORT_MOD"],
    {"api_id": SPORT_CMD["Move"], "parameter": {"x": 0.5, "y": 0, "z": 0}}
)
```

**Best Practices:**
- Always check current mode before switching (avoid unnecessary switches)
- Use constants from `RTC_TOPIC` and `SPORT_CMD` (never hardcode)
- Wait after mode switches (5-10 seconds for robot to stabilize)
- Use `publish_request_new()` for commands that need responses
- Validate response status codes before proceeding
- Use proper parameter structure: `{"api_id": ..., "parameter": {...}}`

### Data Channel Subscription Pattern (examples/go2/data_channel/)

**Reference:** `examples/go2/data_channel/lowstate/lowstate.py`

**Key Pattern - Subscribe to Robot State:**
```python
from unitree_webrtc_connect.constants import RTC_TOPIC

def lowstate_callback(message):
    """Process robot state data."""
    data = message['data']
    imu_state = data['imu_state']['rpy']
    motor_state = data['motor_state']
    bms_state = data['bms_state']
    # Process data...

# Subscribe to low-level state
conn.datachannel.pub_sub.subscribe(RTC_TOPIC['LOW_STATE'], lowstate_callback)

# Keep running to receive updates
await asyncio.sleep(3600)
```

**Best Practices:**
- Use callback functions for data subscriptions (not async)
- Extract data from `message['data']` structure
- Use `RTC_TOPIC` constants for topic names
- Keep callbacks fast (don't block processing)
- Subscribe after connection is established

### LIDAR Integration Pattern (examples/go2/data_channel/lidar/)

**Reference:** `examples/go2/data_channel/lidar/lidar_stream.py`

**Key Pattern - LIDAR Streaming:**
```python
# Disable traffic saving for high-bandwidth data
await conn.datachannel.disableTrafficSaving(True)

# Set decoder type
conn.datachannel.set_decoder(decoder_type='libvoxel')

# Turn LIDAR on
conn.datachannel.pub_sub.publish_without_callback("rt/utlidar/switch", "ON")

# Subscribe to LIDAR data
def lidar_callback(message):
    print(message["data"])

conn.datachannel.pub_sub.subscribe("rt/utlidar/voxel_map_compressed", lidar_callback)
```

**Best Practices:**
- Disable traffic saving for high-bandwidth sensors (LIDAR, high-res video)
- Choose appropriate decoder ('libvoxel' or 'native')
- Turn sensors on/off with publish_without_callback
- Use compressed data streams when available
- Process LIDAR data in callback (don't block)

### Error Handling Pattern (All Examples)

**Standard error handling:**
```python
import sys
import logging

logging.basicConfig(level=logging.FATAL)

async def main():
    try:
        # Main logic here
        await conn.connect()
        # ...
    except ValueError as e:
        logging.error(f"An error occurred: {e}")
    finally:
        # Cleanup resources
        pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        sys.exit(0)
```

**Best Practices:**
- Use `logging.FATAL` for production (reduce noise)
- Catch `ValueError` for SDK-specific errors
- Always handle `KeyboardInterrupt` for graceful shutdown
- Use finally blocks for resource cleanup
- Exit with `sys.exit(0)` on interrupt

### Integration Roadmap

**Future features to integrate from examples:**

1. **Audio Features** (`examples/go2/audio/`)
   - [ ] MP3 player (play audio files to robot)
   - [ ] Internet radio streaming
   - [ ] Save audio from robot to file

2. **Data Channel Features** (`examples/go2/data_channel/`)
   - [ ] Low-level state monitoring (IMU, motors, battery)
   - [ ] LIDAR visualization
   - [ ] Multiple state subscriptions
   - [ ] VUI (Voice User Interface) integration

3. **Advanced Control** (`examples/go2/data_channel/sportmode/`)
   - [ ] Gesture commands (Hello, BackFlip, etc.)
   - [ ] Handstand mode
   - [ ] Advanced movement patterns

**When integrating new features:**
- Follow the example patterns closely
- Fix blocking I/O issues (use `asyncio.to_thread()`)
- Add proper error handling and logging
- Write unit tests for new services
- Update documentation with usage examples

---