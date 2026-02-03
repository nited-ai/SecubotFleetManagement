# Code Style Guide: Unitree WebRTC Connect

> Version: 1.0.0
> Last Updated: 2026-02-03
> Stack: Python 3.11+, Flask, WebRTC, asyncio

## Context

This document outlines the global code style rules for the **Unitree WebRTC Connect** project. These guidelines ensure consistency and readability across the Python/Flask codebase for robot control and WebRTC streaming.

---

## General Formatting

### Indentation & Line Length

* Use **4 spaces** for indentation (never tabs), following PEP 8.
* The maximum line length should be **100 characters** (PEP 8 recommendation).
* Use **black** formatter with default settings for automatic formatting.
* Maintain consistent indentation throughout files.

### Naming Conventions

* **Functions and Variables**: Use **snake_case** (e.g., `process_audio_frame`, `is_connected`).
* **Classes**: Use **PascalCase** (e.g., `AudioService`, `WebRTCConnection`).
* **Constants**: Use **UPPER_SNAKE_CASE** (e.g., `DEFAULT_SAMPLE_RATE`, `MAX_FRAME_QUEUE_SIZE`).
* **Private Methods/Variables**: Prefix with single underscore (e.g., `_internal_method`, `_buffer`).
* **Files**: Use **snake_case** matching the primary class/module (e.g., `audio_service.py`).
* **Packages/Modules**: Use lowercase with underscores (e.g., `app.services.audio_service`).

### String Formatting

* Prefer **f-strings** for variable interpolation: `message = f"Processing frame: {frame_id}"`
* Use **triple-quoted strings** for multi-line text or docstrings:
  ```python
  error_message = """
  Connection failed. Please check:
  - Robot is powered on
  - IP address is correct
  - Network connection is stable
  """
  ```
* Use raw strings for regex patterns: `pattern = r"^\d{3}\.\d{3}\.\d{3}\.\d{3}$"`

---

## Python & Flask Formatting

### Class/Function Structure

* Follow **[PEP 8](https://peps.python.org/pep-0008/)** as the primary style guide.
* Use **dataclasses** for data-holding classes (e.g., configuration models).
* Use **type hints** for all function signatures and class attributes.
* Use **async/await** for all I/O operations (WebRTC, network, file I/O).
* **Import Order** (enforced by `isort`):
  1. Standard library imports (`import asyncio`, `import logging`)
  2. Third-party imports (`import flask`, `import pyaudio`, `import cv2`)
  3. Local application imports (`from app.services import AudioService`)
  4. Separate groups with a blank line

### Example Service Class Structure

This example demonstrates proper formatting, type hints, dependency injection, and async patterns for a typical service in our application.

```python
"""Audio streaming service for bidirectional robot audio."""
import asyncio
import logging
from typing import Optional

import numpy as np
import pyaudio
from av import AudioFrame as AVAudioFrame

from app.models.config import AudioConfig
from app.services.state_service import StateService


class AudioService:
    """Manages bidirectional audio streaming with the robot.

    This service handles:
    - Audio playback from robot to speakers
    - Audio transmission from microphone to robot
    - Dynamic muting without reconnection
    """

    def __init__(self, config: AudioConfig, state_service: StateService) -> None:
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
            frames_per_buffer=self.config.frames_per_buffer,
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

### Example Flask Route Structure

```python
"""Audio control routes."""
from flask import Blueprint, request, jsonify
import logging

from app.services.audio_service import AudioService
from app.services.state_service import StateService

logger = logging.getLogger(__name__)
audio_bp = Blueprint("audio", __name__, url_prefix="/audio")


def create_audio_routes(
    audio_service: AudioService, state_service: StateService
) -> Blueprint:
    """Create audio routes with injected dependencies.

    Args:
        audio_service: Audio streaming service
        state_service: Application state service

    Returns:
        Configured Flask blueprint
    """

    @audio_bp.route("/toggle", methods=["POST"])
    def toggle_audio():
        """Mute or unmute audio playback dynamically."""
        try:
            data = request.json
            enable = data.get("enable", False)

            state_service.audio_muted = not enable

            return jsonify({
                "status": "success",
                "enabled": enable,
                "muted": state_service.audio_muted,
                "message": f"Audio {'unmuted' if enable else 'muted'}",
            })
        except Exception as e:
            logger.error(f"Error toggling audio: {e}", exc_info=True)
            return jsonify({"status": "error", "message": str(e)}), 500

    return audio_bp
```

---

## Code Comments & Documentation

### When to Comment

* Add **docstrings** for all public functions, classes, and modules.
* Add inline comments to explain non-obvious business logic, especially:
  - WebRTC event loop management
  - Async I/O patterns (`asyncio.to_thread()` usage)
  - Robot command protocols
  - Audio/video frame processing
* Explain the "why" behind implementation choices, not the "what".
* Document any workarounds for SDK limitations or bugs.

### Docstring Format

Use **Google-style docstrings** for consistency.

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
    # Validate velocity range
    if not -1.0 <= velocity <= 1.0:
        raise ValueError(f"Velocity {velocity} out of range [-1.0, 1.0]")

    # Implementation...
    return {"status": "success", "message": "Command sent", "command_id": 1008}
```

### Critical Code Comments

For critical sections (event loop management, blocking I/O), use clear warning comments:

```python
async def recv_audio_stream(frame: AVAudioFrame) -> None:
    """Receive audio frames from robot and play through speakers.

    CRITICAL: Uses asyncio.to_thread() to prevent blocking the event loop.
    Video and audio callbacks run in the SAME event loop - blocking here
    would freeze video streaming and cause frame drops.
    """
    if audio_muted:
        return  # Discard frame when muted

    audio_data = np.frombuffer(frame.to_ndarray(), dtype=np.int16)

    # ⚠️ CRITICAL: PyAudio write() is blocking - must use to_thread()
    await asyncio.to_thread(pyaudio_stream.write, audio_data.tobytes())
```

---

## File Organization

### Import Order (Enforced by isort)

1. Standard library imports (alphabetically sorted)
2. Third-party imports (alphabetically sorted)
3. Local application imports (alphabetically sorted)
4. Separate each group with a blank line

### Example Import Block

```python
"""Audio streaming service for bidirectional robot audio."""
import asyncio
import logging
import threading
from typing import Optional

import cv2
import numpy as np
import pyaudio
from av import AudioFrame as AVAudioFrame
from flask import Blueprint, jsonify, request

from app.models.config import AudioConfig
from app.services.state_service import StateService
from unitree_webrtc_connect.constants import RTC_TOPIC, SPORT_CMD
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
```

### Module Structure

* Use one primary class per file, with filename matching the class name:
  - `audio_service.py` contains `class AudioService`
  - `webrtc_service.py` contains `class WebRTCService`
* Related utility functions can be in the same file if tightly coupled
* Use `__init__.py` to expose public APIs:
  ```python
  # app/services/__init__.py
  from .audio_service import AudioService
  from .video_service import VideoService
  from .webrtc_service import WebRTCService

  __all__ = ["AudioService", "VideoService", "WebRTCService"]
  ```

### File Header

Every module should start with a docstring:

```python
"""Audio streaming service for bidirectional robot audio.

This module provides the AudioService class which manages:
- Audio playback from robot to speakers
- Audio transmission from microphone to robot
- Dynamic muting without reconnection

Example:
    >>> config = AudioConfig(sample_rate=48000, channels=2)
    >>> state = StateService()
    >>> audio_service = AudioService(config, state)
    >>> await audio_service.initialize()
"""
```

---

## Type Hints

### Required Type Hints

* **All function signatures** must have type hints for parameters and return values
* **Class attributes** should have type hints
* **Use `Optional[T]`** for nullable values
* **Use `Union[T1, T2]`** for multiple possible types (or `T1 | T2` in Python 3.10+)
* **Use `typing.Protocol`** for structural typing (duck typing with type safety)

### Example Type Hints

```python
from typing import Optional, Union, Protocol
import asyncio

class AudioCallback(Protocol):
    """Protocol for audio frame callbacks."""
    async def __call__(self, frame: AVAudioFrame) -> None:
        ...

class AudioService:
    """Audio streaming service."""

    def __init__(
        self,
        config: AudioConfig,
        state_service: StateService,
        callback: Optional[AudioCallback] = None,
    ) -> None:
        self.config: AudioConfig = config
        self.state: StateService = state_service
        self._callback: Optional[AudioCallback] = callback
        self._stream: Optional[pyaudio.Stream] = None

    async def process_frame(
        self, frame: AVAudioFrame
    ) -> Union[bytes, None]:
        """Process audio frame and return bytes or None if muted."""
        if self.state.audio_muted:
            return None

        audio_data: np.ndarray = np.frombuffer(
            frame.to_ndarray(), dtype=np.int16
        )
        return audio_data.tobytes()
```

---

## Async/Await Patterns

### Async Function Guidelines

* **Use `async def`** for all I/O operations (network, file, database)
* **Use `await`** for all async calls (never use `.result()` or blocking waits)
* **Use `asyncio.to_thread()`** for blocking operations (PyAudio, OpenCV)
* **Use `asyncio.create_task()`** for concurrent operations
* **Use `async with`** for async context managers

### Example Async Patterns

```python
import asyncio
from typing import List

class WebRTCService:
    """WebRTC connection service."""

    async def connect(self, ip: str, timeout: int = 30) -> bool:
        """Connect to robot with timeout."""
        try:
            # Use asyncio.wait_for for timeout
            await asyncio.wait_for(
                self._establish_connection(ip),
                timeout=timeout
            )
            return True
        except asyncio.TimeoutError:
            logger.error("Connection timeout")
            return False

    async def process_frames_concurrently(
        self, frames: List[AVAudioFrame]
    ) -> None:
        """Process multiple frames concurrently."""
        # Create tasks for concurrent processing
        tasks = [
            asyncio.create_task(self.process_frame(frame))
            for frame in frames
        ]

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

    async def cleanup(self) -> None:
        """Clean up resources with async context manager."""
        async with self._connection_lock:
            if self._stream:
                # Offload blocking cleanup to thread pool
                await asyncio.to_thread(self._stream.close)
```

---

## Error Handling

### Exception Handling Guidelines

* **Catch specific exceptions**, not bare `except:`
* **Use try-except-finally** for resource cleanup
* **Log exceptions** with context using `exc_info=True`
* **Raise custom exceptions** for domain-specific errors
* **Use context managers** for automatic cleanup

### Example Error Handling

```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AudioStreamError(Exception):
    """Custom exception for audio streaming errors."""
    pass

class AudioService:
    """Audio streaming service with proper error handling."""

    async def initialize(self) -> None:
        """Initialize audio with comprehensive error handling."""
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            self.pyaudio_stream = self.pyaudio_instance.open(
                format=self.config.format,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                output=True,
            )
            self.state.audio_initialized = True
            logger.info("Audio service initialized successfully")

        except OSError as e:
            logger.error(
                f"Failed to open audio device: {e}",
                exc_info=True
            )
            raise AudioStreamError(
                "No audio output device available"
            ) from e

        except Exception as e:
            logger.error(
                f"Unexpected error initializing audio: {e}",
                exc_info=True
            )
            raise

    async def play_audio_frame(
        self, frame: AVAudioFrame
    ) -> Optional[int]:
        """Play audio frame with error handling.

        Returns:
            Number of bytes written, or None if muted/error
        """
        if self.state.audio_muted or not self.pyaudio_stream:
            return None

        try:
            audio_data = np.frombuffer(frame.to_ndarray(), dtype=np.int16)
            audio_bytes = audio_data.tobytes()

            # Offload blocking I/O
            await asyncio.to_thread(
                self.pyaudio_stream.write, audio_bytes
            )
            return len(audio_bytes)

        except IOError as e:
            logger.warning(f"Audio buffer overflow: {e}")
            return None  # Skip frame on overflow

        except Exception as e:
            logger.error(
                f"Error playing audio frame: {e}",
                exc_info=True
            )
            raise AudioStreamError("Failed to play audio") from e

    async def cleanup(self) -> None:
        """Clean up resources with guaranteed execution."""
        try:
            if self.pyaudio_stream:
                await asyncio.to_thread(self.pyaudio_stream.stop_stream)
                await asyncio.to_thread(self.pyaudio_stream.close)
        except Exception as e:
            logger.error(f"Error stopping stream: {e}", exc_info=True)
        finally:
            # Always terminate PyAudio instance
            if self.pyaudio_instance:
                try:
                    await asyncio.to_thread(
                        self.pyaudio_instance.terminate
                    )
                except Exception as e:
                    logger.error(
                        f"Error terminating PyAudio: {e}",
                        exc_info=True
                    )

            self.state.audio_initialized = False
            logger.info("Audio service cleaned up")
```

---

## Code Quality Tools

### Formatter: black

* **Run before every commit**: `black .`
* **Configuration** (pyproject.toml):
  ```toml
  [tool.black]
  line-length = 100
  target-version = ['py311']
  include = '\.pyi?$'
  ```

### Import Sorter: isort

* **Run before every commit**: `isort .`
* **Configuration** (pyproject.toml):
  ```toml
  [tool.isort]
  profile = "black"
  line_length = 100
  ```

### Linter: flake8

* **Run before every commit**: `flake8 .`
* **Configuration** (.flake8):
  ```ini
  [flake8]
  max-line-length = 100
  extend-ignore = E203, W503
  exclude = .git,__pycache__,venv
  ```

### Type Checker: mypy

* **Run before every commit**: `mypy .`
* **Configuration** (pyproject.toml):
  ```toml
  [tool.mypy]
  python_version = "3.11"
  warn_return_any = true
  warn_unused_configs = true
  disallow_untyped_defs = true
  ```

### Pre-commit Hook

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

Install: `pre-commit install`

---

## Project-Specific Style Guidelines

### WebRTC Event Loop Management

**CRITICAL**: Never block the asyncio event loop!

```python
# ❌ BAD: Blocks event loop
async def recv_audio_stream(frame):
    stream.write(audio_data.tobytes())  # BLOCKS!

# ✅ GOOD: Non-blocking
async def recv_audio_stream(frame):
    await asyncio.to_thread(stream.write, audio_data.tobytes())
```

### Robot Command Formatting

Always use constants from SDK:

```python
# ❌ BAD: Magic numbers and strings
await conn.datachannel.pub_sub.publish_request_new(
    "rt/api/sport/request",
    {"api_id": 1008, "parameter": {"vx": 0.5}}
)

# ✅ GOOD: Use constants
from unitree_webrtc_connect.constants import RTC_TOPIC, SPORT_CMD

await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["SPORT_MOD"],
    {
        "api_id": SPORT_CMD["Move"],
        "parameter": {"vx": 0.5, "vy": 0.0, "vyaw": 0.0}
    }
)
```

### Flask Route Formatting

Keep routes thin, delegate to services:

```python
# ❌ BAD: Business logic in route
@app.route('/connect', methods=['POST'])
def connect():
    global connection, is_connected
    data = request.json
    ip = data.get('ip')

    # ... 50 lines of connection logic ...

    return jsonify({'status': 'success'})

# ✅ GOOD: Delegate to service
@app.route('/connect', methods=['POST'])
def connect():
    """Connect to robot endpoint."""
    try:
        data = request.json
        ip = data.get('ip')

        if not ip:
            return jsonify({'status': 'error', 'message': 'IP required'}), 400

        # Delegate to service
        result = webrtc_service.connect(ip)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Connection error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500
```

### Logging Format

Use structured logging with context:

```python
import logging

logger = logging.getLogger(__name__)

# ❌ BAD: Unstructured logging
logger.info("Connected")

# ✅ GOOD: Structured with context
logger.info(
    "WebRTC connection established",
    extra={
        "ip": robot_ip,
        "connection_method": "LocalSTA",
        "duration_ms": connection_time,
    }
)
```

---