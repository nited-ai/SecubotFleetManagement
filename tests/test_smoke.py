"""
Smoke tests to verify testing infrastructure is working correctly.

These tests verify that pytest, fixtures, and async testing are configured properly.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock


@pytest.mark.unit
def test_pytest_working():
    """Verify pytest is working."""
    assert True


@pytest.mark.unit
def test_fixtures_working(mock_webrtc_connection):
    """Verify fixtures are loaded correctly."""
    assert mock_webrtc_connection is not None
    assert hasattr(mock_webrtc_connection, 'connect')


@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_testing_working():
    """Verify async testing is working."""
    async def async_function():
        await asyncio.sleep(0.001)
        return True
    
    result = await async_function()
    assert result is True


@pytest.mark.unit
def test_mocking_working():
    """Verify mocking is working."""
    mock_obj = Mock()
    mock_obj.method.return_value = "mocked"
    
    result = mock_obj.method()
    
    assert result == "mocked"
    mock_obj.method.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_mocking_working():
    """Verify async mocking is working."""
    mock_obj = AsyncMock()
    mock_obj.async_method.return_value = "async_mocked"
    
    result = await mock_obj.async_method()
    
    assert result == "async_mocked"
    mock_obj.async_method.assert_called_once()


@pytest.mark.unit
def test_gamepad_settings_fixture(default_gamepad_settings):
    """Verify gamepad settings fixture is working."""
    assert default_gamepad_settings is not None
    assert 'deadzone_left_stick' in default_gamepad_settings
    assert default_gamepad_settings['deadzone_left_stick'] == 0.15


@pytest.mark.unit
def test_frame_queue_fixture(frame_queue):
    """Verify frame queue fixture is working."""
    assert frame_queue is not None
    assert frame_queue.maxsize == 30
    assert frame_queue.empty()

