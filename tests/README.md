# Testing Guide for Unitree WebRTC Connect

> Last Updated: 2026-02-03
> Testing Framework: pytest 7.4+
> Target Coverage: 80%+

---

## Test Directory Structure

```
tests/
├── conftest.py          # Shared fixtures for all tests
├── unit/                # Unit tests for individual components
│   ├── test_connection.py
│   ├── test_audio.py
│   ├── test_video.py
│   └── test_control.py
├── integration/         # Integration tests for routes and services
│   ├── test_routes.py
│   └── test_websocket.py
├── e2e/                 # End-to-end tests for complete workflows
│   └── test_workflows.py
└── fixtures/            # Test data and mock objects
    └── sample_data.py
```

---

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# E2E tests only
pytest -m e2e

# Tests for specific component
pytest -m audio
pytest -m video
pytest -m control
pytest -m connection
```

### Run Tests with Coverage

```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

### Run Tests in Parallel

```bash
# Use all CPU cores
pytest -n auto

# Use specific number of workers
pytest -n 4
```

### Run Tests with Verbose Output

```bash
pytest -v
pytest -vv  # Extra verbose
```

---

## Writing Tests

### Test Naming Conventions

- **Test files:** `test_*.py`
- **Test classes:** `Test*`
- **Test functions:** `test_*`

### Test Markers

Use markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_connection_initialization():
    """Test WebRTC connection initialization."""
    pass

@pytest.mark.integration
@pytest.mark.webrtc
def test_connect_route():
    """Test /connect route with mocked WebRTC."""
    pass

@pytest.mark.e2e
@pytest.mark.slow
async def test_full_connection_workflow():
    """Test complete connection workflow."""
    pass
```

### Using Fixtures

```python
def test_audio_streaming(mock_pyaudio, mock_audio_track):
    """Test audio streaming with mocked PyAudio."""
    # Fixtures are automatically injected
    assert mock_pyaudio is not None
    assert mock_audio_track.kind == "audio"
```

### Async Tests

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await some_async_function()
    assert result is True
```

### Mocking

```python
from unittest.mock import Mock, AsyncMock, patch

def test_with_mock():
    """Test with mocked dependency."""
    mock_service = Mock()
    mock_service.method.return_value = "mocked"
    
    result = function_under_test(mock_service)
    
    assert result == "mocked"
    mock_service.method.assert_called_once()
```

---

## Test Coverage Goals

### Overall Coverage Target: 80%+

### Component-Specific Targets:

- **Connection Management:** 100% (critical path)
- **Audio Streaming:** 100% (critical path)
- **Video Streaming:** 100% (critical path)
- **Control Commands:** 100% (critical path)
- **Flask Routes:** 90%+
- **WebSocket Handlers:** 90%+
- **Settings Management:** 80%+
- **Utility Functions:** 70%+

---

## Continuous Integration

Tests run automatically on:
- Every commit to feature branches
- Pull requests to `main` or `develop`
- Scheduled nightly builds

### CI Pipeline Steps:

1. Install dependencies
2. Run linters (black, isort, flake8)
3. Run type checker (mypy)
4. Run unit tests
5. Run integration tests
6. Generate coverage report
7. Fail if coverage < 80%

---

## Troubleshooting

### Common Issues

**Issue:** Tests fail with `RuntimeError: Event loop is closed`

**Solution:** Use the `event_loop` fixture:
```python
@pytest.mark.asyncio
async def test_async_function(event_loop):
    # Test code here
    pass
```

**Issue:** PyAudio tests fail on CI

**Solution:** Mock PyAudio in CI environment:
```python
@pytest.mark.skipif(os.getenv('CI') == 'true', reason="PyAudio not available in CI")
def test_audio_playback():
    pass
```

**Issue:** WebRTC tests require actual robot connection

**Solution:** Use mocked WebRTC connection:
```python
def test_connection(mock_webrtc_connection):
    # Use mock instead of real connection
    pass
```

---

## Best Practices

1. **Test Isolation:** Each test should be independent and not rely on other tests
2. **Fast Tests:** Unit tests should run in milliseconds, not seconds
3. **Clear Assertions:** Use descriptive assertion messages
4. **Arrange-Act-Assert:** Structure tests with clear setup, execution, and verification
5. **Mock External Dependencies:** Don't make real network calls or file I/O in unit tests
6. **Test Edge Cases:** Test boundary conditions, error cases, and invalid inputs
7. **Async Testing:** Use `pytest-asyncio` for async functions
8. **Cleanup:** Use fixtures with `yield` for setup/teardown

---

## Resources

- **pytest Documentation:** https://docs.pytest.org/
- **pytest-asyncio:** https://pytest-asyncio.readthedocs.io/
- **Coverage.py:** https://coverage.readthedocs.io/
- **Best Practices:** `.agent-os/standards/best-practices.md`


