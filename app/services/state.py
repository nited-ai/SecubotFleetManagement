"""
StateService - Centralized state management for Unitree WebRTC Connect.

This service replaces all global variables from web_interface.py with a thread-safe,
centralized state manager. All state access goes through this service to ensure
consistency and thread safety.

CRITICAL THREAD SAFETY RULES:
==============================

1. ALL PROPERTIES USE INTERNAL LOCKING
   - Every property getter/setter acquires its respective lock internally
   - Example: state.latest_frame uses self._frame_lock internally

2. NEVER USE EXPLICIT LOCKS WITH PROPERTIES
   - ❌ WRONG: with state._frame_lock: state.latest_frame = img
   - ✅ RIGHT: state.latest_frame = img

3. WHY DOUBLE-LOCKING IS DEADLY
   - Using 'with state._lock:' before accessing a property creates a DEADLOCK
   - The outer 'with' acquires the lock, then the property tries to acquire it again
   - This freezes the entire application (video/audio streaming stops)

4. WHEN TO USE LOCKS DIRECTLY
   - Only when accessing multiple private attributes atomically
   - Only when you need to read/write the private _attribute directly
   - Example: with self._frame_lock: self._latest_frame = value

5. EXTERNAL CODE SHOULD ONLY USE PROPERTIES
   - Never access private attributes (e.g., state._latest_frame) from outside
   - Never use locks (e.g., state._frame_lock) from outside
   - Always use properties (e.g., state.latest_frame)

See .agent-os/standards/best-practices.md for detailed examples.
"""

import threading
from queue import Queue
from typing import Optional, Dict, Any
import asyncio


class StateService:
    """
    Centralized state management service.

    Manages all application state including:
    - Connection state (WebRTC connection, event loop, threads)
    - Video state (frame queue, latest frame)
    - Audio state (streaming, mute, push-to-talk)
    - Control state (gamepad, keyboard/mouse, emergency stop)
    - Settings (gamepad sensitivity, velocity limits, presets)
    - AI mode state (speed level, free functions)

    THREAD SAFETY:
    --------------
    All properties are thread-safe and use internal locking.
    External code should NEVER use explicit locks when accessing properties.

    ❌ ANTI-PATTERN (causes deadlock):
        with state._frame_lock:
            state.latest_frame = img  # Property already uses _frame_lock!

    ✅ CORRECT USAGE:
        state.latest_frame = img  # Property handles locking internally
    """
    
    def __init__(self):
        """Initialize state service with default values."""
        # Thread locks for thread-safe access
        self._frame_lock = threading.Lock()
        self._gamepad_lock = threading.Lock()
        self._keyboard_mouse_lock = threading.Lock()
        self._audio_lock = threading.Lock()
        
        # Connection state
        self._connection = None
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._is_connected = False
        
        # Video state
        self._frame_queue = Queue(maxsize=30)
        self._latest_frame = None
        
        # Audio state
        self._audio_streaming_enabled = False
        self._audio_initialized = False
        self._push_to_talk_active = False
        self._microphone_audio_track = None
        self._pyaudio_instance = None
        self._audio_muted = True  # Muted by default
        self._pyaudio_stream = None
        self._audio_output_queue = Queue(maxsize=100)
        
        # Gamepad control state
        self._gamepad_enabled = False
        self._last_command_time = 0
        self._command_interval = 0.016  # ~60Hz
        self._emergency_stop_active = False
        self._current_body_height = 1  # 0=low, 1=middle, 2=high
        self._lidar_state = False
        
        # Keyboard & Mouse control state
        self._keyboard_mouse_enabled = False

        # Pose Mode state
        self._pose_mode_active = False

        # AI Mode Free functions state
        self._speed_level = 0  # -1=slow, 0=normal, 1=fast
        self._free_bound_active = False
        self._free_jump_active = False
        self._free_avoid_active = False

        # Robot status data (for HUD display)
        self._battery_level = None  # Battery SOC percentage (0-100)
        self._current_mode = None  # Current motion mode (ai, normal, sport)
        self._last_status_update = 0  # Timestamp of last status update
        self._ping_ms = None  # Network round-trip time in milliseconds
        self._max_temperature = None  # Maximum temperature from all sensors (°C)

        # Gamepad settings
        self._gamepad_settings = {
            'deadzone_left_stick': 0.15,
            'deadzone_right_stick': 0.15,
            'sensitivity_linear': 1.0,
            'sensitivity_strafe': 1.0,
            'sensitivity_rotation': 1.0,
            'max_linear_velocity': 0.6,
            'max_strafe_velocity': 0.4,
            'max_rotation_velocity': 0.8,
            'speed_multiplier': 1.0
        }
        
        # Last sent velocities for zero-velocity detection
        self._last_sent_velocities = {'vx': 0.0, 'vy': 0.0, 'vyaw': 0.0}
        self._zero_velocity_sent = False
    
    # ========== Connection State ==========
    
    @property
    def connection(self):
        """Get WebRTC connection."""
        return self._connection
    
    @connection.setter
    def connection(self, value):
        """Set WebRTC connection."""
        self._connection = value
    
    @property
    def event_loop(self) -> Optional[asyncio.AbstractEventLoop]:
        """Get asyncio event loop."""
        return self._event_loop
    
    @event_loop.setter
    def event_loop(self, value: Optional[asyncio.AbstractEventLoop]):
        """Set asyncio event loop."""
        self._event_loop = value
    
    @property
    def loop_thread(self) -> Optional[threading.Thread]:
        """Get event loop thread."""
        return self._loop_thread
    
    @loop_thread.setter
    def loop_thread(self, value: Optional[threading.Thread]):
        """Set event loop thread."""
        self._loop_thread = value
    
    @property
    def is_connected(self) -> bool:
        """Get connection status."""
        return self._is_connected
    
    @is_connected.setter
    def is_connected(self, value: bool):
        """Set connection status."""
        self._is_connected = value
    
    # ========== Video State ==========
    
    @property
    def frame_queue(self) -> Queue:
        """Get video frame queue."""
        return self._frame_queue
    
    @property
    def latest_frame(self):
        """Get latest video frame (thread-safe)."""
        with self._frame_lock:
            return self._latest_frame
    
    @latest_frame.setter
    def latest_frame(self, value):
        """Set latest video frame (thread-safe)."""
        with self._frame_lock:
            self._latest_frame = value

    # ========== Audio State ==========

    @property
    def audio_streaming_enabled(self) -> bool:
        """Get audio streaming enabled state."""
        with self._audio_lock:
            return self._audio_streaming_enabled

    @audio_streaming_enabled.setter
    def audio_streaming_enabled(self, value: bool):
        """Set audio streaming enabled state."""
        with self._audio_lock:
            self._audio_streaming_enabled = value

    @property
    def audio_initialized(self) -> bool:
        """Get audio initialized state."""
        with self._audio_lock:
            return self._audio_initialized

    @audio_initialized.setter
    def audio_initialized(self, value: bool):
        """Set audio initialized state."""
        with self._audio_lock:
            self._audio_initialized = value

    @property
    def push_to_talk_active(self) -> bool:
        """Get push-to-talk active state."""
        with self._audio_lock:
            return self._push_to_talk_active

    @push_to_talk_active.setter
    def push_to_talk_active(self, value: bool):
        """Set push-to-talk active state."""
        with self._audio_lock:
            self._push_to_talk_active = value

    @property
    def microphone_audio_track(self):
        """Get microphone audio track."""
        with self._audio_lock:
            return self._microphone_audio_track

    @microphone_audio_track.setter
    def microphone_audio_track(self, value):
        """Set microphone audio track."""
        with self._audio_lock:
            self._microphone_audio_track = value

    @property
    def pyaudio_instance(self):
        """Get PyAudio instance."""
        with self._audio_lock:
            return self._pyaudio_instance

    @pyaudio_instance.setter
    def pyaudio_instance(self, value):
        """Set PyAudio instance."""
        with self._audio_lock:
            self._pyaudio_instance = value

    @property
    def audio_muted(self) -> bool:
        """Get audio muted state."""
        with self._audio_lock:
            return self._audio_muted

    @audio_muted.setter
    def audio_muted(self, value: bool):
        """Set audio muted state."""
        with self._audio_lock:
            self._audio_muted = value

    @property
    def pyaudio_stream(self):
        """Get PyAudio stream."""
        with self._audio_lock:
            return self._pyaudio_stream

    @pyaudio_stream.setter
    def pyaudio_stream(self, value):
        """Set PyAudio stream."""
        with self._audio_lock:
            self._pyaudio_stream = value

    @property
    def audio_output_queue(self) -> Queue:
        """Get audio output queue."""
        return self._audio_output_queue

    # ========== Gamepad Control State ==========

    @property
    def gamepad_enabled(self) -> bool:
        """Get gamepad enabled state (thread-safe)."""
        with self._gamepad_lock:
            return self._gamepad_enabled

    @gamepad_enabled.setter
    def gamepad_enabled(self, value: bool):
        """Set gamepad enabled state (thread-safe)."""
        with self._gamepad_lock:
            self._gamepad_enabled = value

    @property
    def last_command_time(self) -> float:
        """Get last command time."""
        return self._last_command_time

    @last_command_time.setter
    def last_command_time(self, value: float):
        """Set last command time."""
        self._last_command_time = value

    @property
    def command_interval(self) -> float:
        """Get command interval."""
        return self._command_interval

    @property
    def emergency_stop_active(self) -> bool:
        """Get emergency stop state."""
        return self._emergency_stop_active

    @emergency_stop_active.setter
    def emergency_stop_active(self, value: bool):
        """Set emergency stop state."""
        self._emergency_stop_active = value

    @property
    def pose_mode_active(self) -> bool:
        """Get pose mode active state."""
        return self._pose_mode_active

    @pose_mode_active.setter
    def pose_mode_active(self, value: bool):
        """Set pose mode active state."""
        self._pose_mode_active = value

    @property
    def current_body_height(self) -> int:
        """Get current body height (0=low, 1=middle, 2=high)."""
        return self._current_body_height

    @current_body_height.setter
    def current_body_height(self, value: int):
        """Set current body height."""
        self._current_body_height = value

    @property
    def lidar_state(self) -> bool:
        """Get LIDAR state."""
        return self._lidar_state

    @lidar_state.setter
    def lidar_state(self, value: bool):
        """Set LIDAR state."""
        self._lidar_state = value

    # ========== Keyboard & Mouse Control State ==========

    @property
    def keyboard_mouse_enabled(self) -> bool:
        """Get keyboard/mouse enabled state (thread-safe)."""
        with self._keyboard_mouse_lock:
            return self._keyboard_mouse_enabled

    @keyboard_mouse_enabled.setter
    def keyboard_mouse_enabled(self, value: bool):
        """Set keyboard/mouse enabled state (thread-safe)."""
        with self._keyboard_mouse_lock:
            self._keyboard_mouse_enabled = value

    # ========== AI Mode State ==========

    @property
    def speed_level(self) -> int:
        """Get speed level (-1=slow, 0=normal, 1=fast)."""
        return self._speed_level

    @speed_level.setter
    def speed_level(self, value: int):
        """Set speed level."""
        self._speed_level = value

    @property
    def free_bound_active(self) -> bool:
        """Get FreeBound active state."""
        return self._free_bound_active

    @free_bound_active.setter
    def free_bound_active(self, value: bool):
        """Set FreeBound active state."""
        self._free_bound_active = value

    @property
    def free_jump_active(self) -> bool:
        """Get FreeJump active state."""
        return self._free_jump_active

    @free_jump_active.setter
    def free_jump_active(self, value: bool):
        """Set FreeJump active state."""
        self._free_jump_active = value

    @property
    def free_avoid_active(self) -> bool:
        """Get FreeAvoid active state."""
        return self._free_avoid_active

    @free_avoid_active.setter
    def free_avoid_active(self, value: bool):
        """Set FreeAvoid active state."""
        self._free_avoid_active = value

    # ========== Robot Status Data ==========

    @property
    def battery_level(self) -> Optional[int]:
        """Get battery level (SOC percentage 0-100)."""
        return self._battery_level

    @battery_level.setter
    def battery_level(self, value: Optional[int]):
        """Set battery level."""
        self._battery_level = value

    @property
    def current_mode(self) -> Optional[str]:
        """Get current motion mode (ai, normal, sport)."""
        return self._current_mode

    @current_mode.setter
    def current_mode(self, value: Optional[str]):
        """Set current motion mode."""
        self._current_mode = value

    @property
    def last_status_update(self) -> float:
        """Get timestamp of last status update."""
        return self._last_status_update

    @last_status_update.setter
    def last_status_update(self, value: float):
        """Set timestamp of last status update."""
        self._last_status_update = value

    @property
    def ping_ms(self) -> Optional[int]:
        """Get network ping in milliseconds."""
        return self._ping_ms

    @ping_ms.setter
    def ping_ms(self, value: Optional[int]):
        """Set network ping in milliseconds."""
        self._ping_ms = value

    @property
    def max_temperature(self) -> Optional[float]:
        """Get maximum temperature from all sensors (°C)."""
        return self._max_temperature

    @max_temperature.setter
    def max_temperature(self, value: Optional[float]):
        """Set maximum temperature."""
        self._max_temperature = value

    # ========== Gamepad Settings ==========

    @property
    def gamepad_settings(self) -> Dict[str, float]:
        """Get gamepad settings (returns a copy for thread safety)."""
        return self._gamepad_settings.copy()

    def update_gamepad_settings(self, settings: Dict[str, Any]):
        """Update gamepad settings (thread-safe)."""
        for key, value in settings.items():
            if key in self._gamepad_settings:
                self._gamepad_settings[key] = value

    def get_gamepad_setting(self, key: str) -> Optional[float]:
        """Get a specific gamepad setting."""
        return self._gamepad_settings.get(key)

    def set_gamepad_setting(self, key: str, value: float):
        """Set a specific gamepad setting."""
        if key in self._gamepad_settings:
            self._gamepad_settings[key] = value

    # ========== Velocity Tracking ==========

    @property
    def last_sent_velocities(self) -> Dict[str, float]:
        """Get last sent velocities."""
        return self._last_sent_velocities.copy()

    def update_last_sent_velocities(self, vx: float, vy: float, vyaw: float):
        """Update last sent velocities."""
        self._last_sent_velocities = {'vx': vx, 'vy': vy, 'vyaw': vyaw}

    @property
    def zero_velocity_sent(self) -> bool:
        """Get zero velocity sent flag."""
        return self._zero_velocity_sent

    @zero_velocity_sent.setter
    def zero_velocity_sent(self, value: bool):
        """Set zero velocity sent flag."""
        self._zero_velocity_sent = value

    # ========== Utility Methods ==========

    def reset_connection_state(self):
        """Reset all connection-related state."""
        self._connection = None
        self._event_loop = None
        self._loop_thread = None
        self._is_connected = False

    def reset_audio_state(self):
        """Reset all audio-related state."""
        with self._audio_lock:
            self._audio_streaming_enabled = False
            self._audio_initialized = False
            self._push_to_talk_active = False
            self._microphone_audio_track = None
            self._pyaudio_instance = None
            self._audio_muted = True
            self._pyaudio_stream = None
            # Clear audio queue
            while not self._audio_output_queue.empty():
                try:
                    self._audio_output_queue.get_nowait()
                except:
                    break

    def reset_control_state(self):
        """Reset all control-related state."""
        with self._gamepad_lock:
            self._gamepad_enabled = False
        with self._keyboard_mouse_lock:
            self._keyboard_mouse_enabled = False
        self._emergency_stop_active = False
        self._pose_mode_active = False
        self._last_command_time = 0
        self._zero_velocity_sent = False

    def reset_all_state(self):
        """Reset all state to initial values."""
        self.reset_connection_state()
        self.reset_audio_state()
        self.reset_control_state()

        # Reset video state
        with self._frame_lock:
            self._latest_frame = None
        # Clear frame queue
        while not self._frame_queue.empty():
            try:
                self._frame_queue.get_nowait()
            except:
                break

        # Reset AI mode state
        self._speed_level = 0
        self._free_bound_active = False
        self._free_jump_active = False
        self._free_avoid_active = False
        self._current_body_height = 1
        self._lidar_state = False

        # Reset robot status data
        self._battery_level = None
        self._current_mode = None
        self._last_status_update = 0
        self._ping_ms = None
        self._max_temperature = None

