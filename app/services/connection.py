"""
ConnectionService - WebRTC connection lifecycle management.

This service manages:
- Event loop creation and management
- WebRTC peer connection lifecycle (connect, disconnect, reconnect)
- Connection method handling (LocalAP, LocalSTA, Remote)
- Video and audio track setup
- PyAudio initialization for audio streaming
- Connection state management

THREAD SAFETY:
- All async operations run in a dedicated event loop thread
- Use asyncio.run_coroutine_threadsafe() to schedule coroutines from sync context
- PyAudio operations use asyncio.to_thread() to prevent blocking the event loop

DEPENDENCIES:
- StateService: For storing connection state
- Video/Audio callbacks: recv_camera_stream, recv_audio_stream
- MicrophoneAudioTrack: For user→robot audio transmission
"""

import asyncio
import logging
import threading
from typing import Optional, Callable, Dict, Any
import pyaudio

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod
from unitree_webrtc_connect.constants import RTC_TOPIC, SPORT_CMD, OBSTACLES_AVOID_API


class ConnectionService:
    """
    Manages WebRTC connection lifecycle and event loop.
    
    This service encapsulates all connection-related logic including:
    - Event loop management (creation, threading, cleanup)
    - Connection creation based on method (LocalAP, LocalSTA, Remote)
    - Video/audio track setup and callbacks
    - PyAudio initialization for bidirectional audio
    - Robot initialization (AI mode, FreeWalk)
    """
    
    def __init__(self, state_service, debug_level=1, socketio=None):
        """
        Initialize ConnectionService.

        Args:
            state_service: StateService instance for state management
            debug_level: Logging verbosity (0=Silent, 1=Basic, 2=Verbose, 3=Deep Debug)
            socketio: Flask-SocketIO instance for emitting progress updates (optional)
        """
        self.state = state_service
        self.logger = logging.getLogger(__name__)
        self.debug_level = debug_level
        self.socketio = socketio
        self._status_polling_task = None  # Background task for status polling

    def emit_progress(self, stage: str, message: str = None):
        """
        Emit connection progress update via Socket.IO.

        Args:
            stage: Progress stage ('establishing', 'video', 'audio', 'robot', 'complete')
            message: Optional custom message
        """
        if self.socketio:
            try:
                self.socketio.emit('connection_progress', {
                    'stage': stage,
                    'message': message
                })
                self.logger.debug(f"Progress update emitted: {stage}")
            except Exception as e:
                self.logger.error(f"Error emitting progress: {e}")
    
    def _run_event_loop(self, loop: asyncio.AbstractEventLoop):
        """
        Run asyncio event loop in a separate thread.
        
        Args:
            loop: Event loop to run
        """
        asyncio.set_event_loop(loop)
        loop.run_forever()
    
    def ensure_event_loop(self):
        """
        Ensure event loop exists and is running.
        Creates new event loop if needed.
        """
        if self.state.event_loop is None or not self.state.event_loop.is_running():
            self.state.event_loop = asyncio.new_event_loop()
            self.state.loop_thread = threading.Thread(
                target=self._run_event_loop,
                args=(self.state.event_loop,),
                daemon=True
            )
            self.state.loop_thread.start()
            self.logger.info("Event loop created and started")
    
    def create_connection(
        self,
        method: str,
        ip: Optional[str] = None,
        serial_number: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> UnitreeWebRTCConnection:
        """
        Create WebRTC connection based on method.
        
        Args:
            method: Connection method ('LocalAP', 'LocalSTA', 'Remote')
            ip: IP address (for LocalSTA)
            serial_number: Serial number (for LocalSTA or Remote)
            username: Username (for Remote)
            password: Password (for Remote)
            
        Returns:
            UnitreeWebRTCConnection instance
            
        Raises:
            ValueError: If required parameters are missing
        """
        if method == 'LocalAP':
            return UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalAP)
        
        elif method == 'LocalSTA':
            if ip:
                return UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip=ip)
            elif serial_number:
                return UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, serialNumber=serial_number)
            else:
                raise ValueError('IP or Serial Number required for LocalSTA')
        
        elif method == 'Remote':
            if not all([serial_number, username, password]):
                raise ValueError('Serial Number, Username, and Password required for Remote')
            return UnitreeWebRTCConnection(
                WebRTCConnectionMethod.Remote,
                serialNumber=serial_number,
                username=username,
                password=password
            )
        
        else:
            raise ValueError(f'Invalid connection method: {method}')
    
    async def setup_connection(
        self,
        conn: UnitreeWebRTCConnection,
        video_callback: Callable,
        audio_callback: Callable,
        microphone_track_class: type,
        audio_config: Dict[str, Any]
    ):
        """
        Setup WebRTC connection with video and audio tracks.

        This async function:
        1. Connects to robot via WebRTC
        2. Enables video streaming with callback
        3. Initializes PyAudio for audio reception (using asyncio.to_thread)
        4. Adds microphone track for audio transmission
        5. Enables audio reception with callback

        Args:
            conn: UnitreeWebRTCConnection instance
            video_callback: Callback for video frames (recv_camera_stream)
            audio_callback: Callback for audio frames (recv_audio_stream)
            microphone_track_class: MicrophoneAudioTrack class
            audio_config: Audio configuration dict with keys:
                - format: PyAudio format (e.g., pyaudio.paInt16)
                - channels: Number of channels (e.g., 2 for stereo)
                - rate: Sample rate (e.g., 48000)
                - frames_per_buffer: Buffer size (e.g., 8192)
        """
        try:
            # Stage 1: Establishing connection
            self.emit_progress('establishing')
            await conn.connect()

            # Stage 2: Setup video
            self.emit_progress('video')
            conn.video.switchVideoChannel(True)
            conn.video.add_track_callback(video_callback)
            self.logger.info("📹 Video streaming enabled")

            # Stage 3: Setup audio
            self.emit_progress('audio')
            # Initialize PyAudio for audio reception
            # Use asyncio.to_thread() to prevent blocking the event loop
            self.state.pyaudio_instance = await asyncio.to_thread(pyaudio.PyAudio)
            self.state.pyaudio_stream = await asyncio.to_thread(
                self.state.pyaudio_instance.open,
                format=audio_config['format'],
                channels=audio_config['channels'],
                rate=audio_config['rate'],
                output=True,
                frames_per_buffer=audio_config['frames_per_buffer']
            )

            # Setup audio - add microphone track immediately after connection
            # Use addTrack() like the examples do (stream_radio.py, play_mp3.py)
            # Use asyncio.to_thread() to prevent blocking during PyAudio initialization
            self.state.microphone_audio_track = await asyncio.to_thread(microphone_track_class)
            conn.pc.addTrack(self.state.microphone_audio_track)
            self.logger.info("🎤 Microphone track added to peer connection")

            # Enable audio reception (robot → user)
            conn.audio.switchAudioChannel(True)
            conn.audio.add_track_callback(audio_callback)
            self.logger.info("🎤 Audio reception enabled")

            self.state.audio_initialized = True
            # Audio is muted by default (state.audio_muted = True)
            self.logger.info("Successfully connected to robot (video + audio stream initialized, audio muted by default)")

            # Update state
            self.state.connection = conn
            self.state.is_connected = True

            # Query obstacle avoidance state early to sync frontend UI ASAP
            # This prevents visual flicker from loading state → actual state
            asyncio.create_task(self.query_obstacle_avoidance_state())

            # Subscribe to LOW_STATE for battery data
            self.subscribe_to_robot_status()

            # Start periodic status polling for mode and ping
            self.start_status_polling()

        except Exception as e:
            self.logger.error(f"Error connecting to robot: {e}")
            # Emit error event
            if self.socketio:
                self.socketio.emit('connection_error', {'message': str(e)})
            raise

    def subscribe_to_robot_status(self):
        """
        Subscribe to robot status topics for real-time telemetry.

        Subscribes to:
        - LOW_STATE: Battery data (BMS SOC percentage)
        - LF_SPORT_MOD_STATE: Motion mode and gait type
        """
        try:
            from unitree_webrtc_connect.constants import RTC_TOPIC
            import time

            def lowstate_callback(message):
                """Process LOW_STATE data for battery level and temperature."""
                try:
                    data = message['data']
                    bms_state = data.get('bms_state', {})
                    battery_soc = bms_state.get('soc', None)

                    if battery_soc is not None:
                        self.state.battery_level = battery_soc
                        self.state.last_status_update = time.time()
                        self.logger.debug(f"Battery level updated: {battery_soc}%")

                    # Extract all temperature values and store the maximum
                    temps = []

                    def _append_temp(value):
                        """Safely append a numeric temperature value, handling lists and non-numeric types."""
                        if value is None:
                            return
                        if isinstance(value, list):
                            for v in value:
                                _append_temp(v)
                            return
                        if isinstance(value, (int, float)):
                            temps.append(float(value))

                    # Motor temperatures (12 motors)
                    motor_state = data.get('motor_state', [])
                    for motor in motor_state:
                        if isinstance(motor, dict):
                            _append_temp(motor.get('temperature', None))

                    # BMS temperatures
                    _append_temp(bms_state.get('bq_ntc', None))
                    _append_temp(bms_state.get('mcu_ntc', None))

                    # Additional NTC sensor
                    _append_temp(data.get('temperature_ntc1', None))

                    # Store maximum temperature
                    if temps:
                        max_temp = max(temps)
                        self.state.max_temperature = max_temp
                        # Only log temperature details at DEBUG_LEVEL >= 2 (Verbose)
                        if self.debug_level >= 2:
                            self.logger.debug(f"🌡️ Max temperature: {max_temp}°C (from {len(temps)} sensors, all: {[round(t, 1) for t in temps]})")
                    else:
                        self.logger.warning("🌡️ No temperature data found in LOW_STATE message")
                except Exception as e:
                    self.logger.error(f"Error processing LOW_STATE data: {e}")

            # Track previous state for change detection
            self._prev_sport_state = {'mode': None, 'gait_type': None, 'body_height': None, 'progress': None}

            def sportmode_callback(message):
                """Process LF_SPORT_MOD_STATE data for mode, gait type, and actual velocities."""
                try:
                    data = message['data']

                    # Extract key state fields
                    mode = data.get('mode', None)
                    gait_type = data.get('gait_type', 0)
                    body_height = data.get('body_height', 0)
                    progress = data.get('progress', 0)

                    # Map gait type to user-friendly names
                    gait_names = {
                        0: 'idle',
                        1: 'trot',
                        2: 'climb_stairs',
                        3: 'trot_obstacle'
                    }

                    gait_name = gait_names.get(gait_type, f'gait_{gait_type}')

                    # Log ANY state change prominently (for monitoring mode switches)
                    prev = self._prev_sport_state
                    changed = False
                    if mode != prev['mode']:
                        self.logger.info(f"🔄 [STATE CHANGE] mode: {prev['mode']} → {mode}")
                        prev['mode'] = mode
                        changed = True
                    if gait_type != prev['gait_type']:
                        self.logger.info(f"🔄 [STATE CHANGE] gait_type: {prev['gait_type']} → {gait_type} ({gait_name})")
                        prev['gait_type'] = gait_type
                        changed = True
                    if prev['body_height'] is not None and abs(body_height - (prev['body_height'] or 0)) > 0.01:
                        self.logger.info(f"🔄 [STATE CHANGE] body_height: {prev['body_height']:.3f} → {body_height:.3f}")
                        changed = True
                    prev['body_height'] = body_height
                    if progress != prev['progress']:
                        self.logger.info(f"🔄 [STATE CHANGE] progress: {prev['progress']} → {progress}")
                        prev['progress'] = progress
                        changed = True

                    if changed:
                        self.logger.info(f"📊 [FULL STATE] mode={mode}, gait_type={gait_type} ({gait_name}), body_height={body_height:.3f}, progress={progress}")

                    # Update stored gait mode
                    if gait_name != self.state.current_mode:
                        self.state.current_mode = gait_name

                    # Log actual robot velocities when moving (Level 2: Verbose)
                    if self.debug_level >= 2:
                        velocity = data.get('velocity', [0, 0, 0])
                        yaw_speed = data.get('yaw_speed', 0)
                        if abs(yaw_speed) > 0.01 or abs(velocity[0]) > 0.01 or abs(velocity[1]) > 0.01:
                            self.logger.info(f"🤖 [ROBOT ACTUAL] velocity=[{velocity[0]:.3f}, {velocity[1]:.3f}, {velocity[2]:.3f}] m/s, yaw_speed={yaw_speed:.3f} rad/s")

                except Exception as e:
                    self.logger.error(f"Error processing LF_SPORT_MOD_STATE data: {e}")

            # Subscribe to LOW_STATE topic
            self.state.connection.datachannel.pub_sub.subscribe(
                RTC_TOPIC['LOW_STATE'],
                lowstate_callback
            )
            self.logger.info("✓ Subscribed to LOW_STATE for battery telemetry")

            # Subscribe to LF_SPORT_MOD_STATE topic
            self.state.connection.datachannel.pub_sub.subscribe(
                RTC_TOPIC['LF_SPORT_MOD_STATE'],
                sportmode_callback
            )
            self.logger.info("✓ Subscribed to LF_SPORT_MOD_STATE for mode/gait telemetry")

        except Exception as e:
            self.logger.error(f"Error subscribing to robot status: {e}")

    def start_status_polling(self):
        """
        Start periodic polling for ping measurement.

        Polls every 3 seconds to measure network round-trip time.
        Note: Mode/gait is now obtained via LF_SPORT_MOD_STATE subscription.
        """
        if self.state.event_loop and self.state.is_connected:
            # Schedule the polling task in the event loop
            self._status_polling_task = asyncio.run_coroutine_threadsafe(
                self._poll_robot_status(),
                self.state.event_loop
            )
            self.logger.info("✓ Started periodic ping measurement")

    async def _poll_robot_status(self):
        """
        Periodic task to measure network ping.

        Runs continuously while connected, polling every 3 seconds.
        Uses a lightweight query to measure round-trip time.
        """
        import time

        while self.state.is_connected:
            try:
                # Measure ping by timing a lightweight MOTION_SWITCHER query
                start_time = time.time()

                response = await self.state.connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["MOTION_SWITCHER"],
                    {"api_id": 1001}
                )

                # Calculate round-trip time
                end_time = time.time()
                ping_ms = int((end_time - start_time) * 1000)
                self.state.ping_ms = ping_ms

                self.logger.debug(f"Ping: {ping_ms}ms")

            except Exception as e:
                self.logger.error(f"Error measuring ping: {e}")

            # Wait 3 seconds before next poll
            await asyncio.sleep(3)

    def stop_status_polling(self):
        """
        Stop the periodic status polling task.

        Note: The actual async task will exit on its own when it checks
        self.state.is_connected and finds it False. This method just
        cancels the Future wrapper to prevent any pending results.
        """
        if self._status_polling_task:
            try:
                self._status_polling_task.cancel()
            except Exception as e:
                self.logger.error(f"Error cancelling status polling task: {e}")
            finally:
                self._status_polling_task = None
                self.logger.info("✓ Status polling task cancelled")

    async def initialize_robot(self):
        """
        Initialize robot into AI mode and Agile Mode (FreeWalk).

        This function:
        1. Checks current motion mode
        2. Switches to AI mode if needed (AI mode uses Move command for speed control)
        3. Sends FreeWalk command to enter Agile Mode (AI mode with obstacle avoidance)

        Requires:
        - Active connection (state.connection must be set)
        - Event loop running
        """
        try:
            # Stage 4: Initialize robot
            self.emit_progress('robot')
            self.logger.info(">>> initialize_robot() function started <<<")

            # First, check and set motion mode
            self.logger.info("Checking motion mode...")
            response = await self.state.connection.datachannel.pub_sub.publish_request_new(
                RTC_TOPIC["MOTION_SWITCHER"],
                {"api_id": 1001}
            )

            if response and 'data' in response:
                import json
                if 'data' in response['data']:
                    data = json.loads(response['data']['data'])
                    current_mode = data.get('name', 'unknown')
                    self.logger.info(f"Current motion mode: {current_mode}")

                    # Store current mode in state
                    self.state.current_mode = current_mode

                    # Switch to AI mode if not already
                    # AI mode uses Move command for speed control, not wireless controller
                    if current_mode != "ai":
                        self.logger.info(f"Switching from {current_mode} to AI mode...")
                        await self.state.connection.datachannel.pub_sub.publish_request_new(
                            RTC_TOPIC["MOTION_SWITCHER"],
                            {
                                "api_id": 1002,
                                "parameter": {"name": "ai"}
                            }
                        )
                        await asyncio.sleep(5)  # Wait for mode switch (AI mode takes longer)
                        self.logger.info("Switched to AI mode")
                        # Update mode in state
                        self.state.current_mode = "ai"

            # Send FreeWalk command to enter Agile Mode (AI mode with obstacle avoidance)
            self.logger.info("Sending FreeWalk command to enter Agile Mode...")
            await self.state.connection.datachannel.pub_sub.publish_request_new(
                RTC_TOPIC["SPORT_MOD"],
                {"api_id": SPORT_CMD["FreeWalk"]}
            )
            await asyncio.sleep(1)
            self.logger.info("Robot initialized successfully (AI mode + FreeWalk)")

            # Query current obstacle avoidance state from robot
            await self.query_obstacle_avoidance_state()

            # Go2 boots with LiDAR ON (AI mode + obstacle avoidance enabled by default)
            # Sync initial LiDAR state to backend and frontend
            self.state.lidar_state = True
            if self.socketio:
                self.socketio.emit('lidar_state_update', {'enabled': True})
                self.logger.info("📡 Sent initial LiDAR state to frontend: ON (Go2 default)")

            # Emit completion event
            self.emit_progress('complete')
            if self.socketio:
                self.socketio.emit('connection_complete', {'status': 'success'})

        except Exception as e:
            self.logger.error(f"Error initializing robot: {e}")
            # Emit error event
            if self.socketio:
                self.socketio.emit('connection_error', {'message': str(e)})
            raise

    async def query_obstacle_avoidance_state(self):
        """
        Query current obstacle avoidance state from robot.

        Uses OBSTACLES_AVOID_API["SWITCH_GET"] (API ID 1002) to retrieve
        the current enable/disable state and syncs it with backend and frontend.

        This ensures consistency between:
        - Robot's actual obstacle avoidance state
        - Backend state (StateService.obstacle_avoid_active)
        - Frontend UI (toggle button appearance)
        """
        try:
            self.logger.info("Querying obstacle avoidance state from robot...")

            response = await self.state.connection.datachannel.pub_sub.publish_request_new(
                RTC_TOPIC["OBSTACLES_AVOID"],
                {"api_id": OBSTACLES_AVOID_API["SWITCH_GET"]}
            )

            if response and 'data' in response:
                import json

                # Check response status
                header = response.get('data', {}).get('header', {})
                status = header.get('status', {})
                status_code = status.get('code', -1)

                if status_code == 0:
                    # Success - parse the data
                    if 'data' in response['data']:
                        data = json.loads(response['data']['data'])
                        enable_state = data.get('enable', False)

                        # Store in state
                        self.state.obstacle_avoid_active = enable_state

                        self.logger.info(f"✅ Obstacle avoidance state: {'ENABLED' if enable_state else 'DISABLED'}")

                        # Emit to frontend to sync UI
                        if self.socketio:
                            self.socketio.emit('obstacle_avoid_state_update', {
                                'enabled': enable_state
                            })
                            self.logger.info(f"📡 Sent obstacle avoidance state to frontend: {enable_state}")
                    else:
                        self.logger.warning("No data field in obstacle avoidance state response")
                        self.state.obstacle_avoid_active = False
                else:
                    self.logger.warning(f"Failed to query obstacle avoidance state (status code: {status_code})")
                    self.state.obstacle_avoid_active = False
            else:
                self.logger.warning("No response received when querying obstacle avoidance state")
                self.state.obstacle_avoid_active = False

        except Exception as e:
            self.logger.error(f"Error querying obstacle avoidance state: {e}")
            # Default to disabled on error
            self.state.obstacle_avoid_active = False

    async def disconnect_connection(self):
        """
        Disconnect from robot and clean up resources.

        This async function performs cleanup in the correct order:
        1. Update connection state to stop all background tasks
        2. Disable all control modes
        3. Stop heartbeat mechanism
        4. Unsubscribe from robot status topics
        5. Close WebRTC peer connection
        """
        if not self.state.connection:
            self.logger.warning("No active connection to disconnect")
            return

        try:
            # STEP 1: Update state FIRST to stop all polling loops
            self.logger.info("=" * 60)
            self.logger.info("DISCONNECTING FROM ROBOT")
            self.logger.info("=" * 60)

            self.state.is_connected = False
            self.logger.info("✓ Connection state set to disconnected")

            # STEP 2: Disable all control modes
            self.state.keyboard_mouse_enabled = False
            self.state.gamepad_enabled = False
            self.state.emergency_stop_active = False
            self.logger.info("✓ All control modes disabled")

            # STEP 3: Wait for polling loop to exit (it checks is_connected)
            await asyncio.sleep(0.5)
            self.logger.info("✓ Background tasks stopped")

            # STEP 4: Stop heartbeat mechanism
            try:
                if hasattr(self.state.connection.datachannel, 'heartbeat'):
                    self.state.connection.datachannel.heartbeat.stop_heartbeat()
                    self.logger.info("✓ Heartbeat stopped")
            except Exception as e:
                self.logger.error(f"Error stopping heartbeat: {e}")

            # STEP 5: Unsubscribe from all topics
            try:
                from unitree_webrtc_connect.constants import RTC_TOPIC

                # Unsubscribe from LOW_STATE topic
                self.state.connection.datachannel.pub_sub.unsubscribe(RTC_TOPIC['LOW_STATE'])
                self.logger.info("✓ Unsubscribed from LOW_STATE")

                # Unsubscribe from LF_SPORT_MOD_STATE topic
                self.state.connection.datachannel.pub_sub.unsubscribe(RTC_TOPIC['LF_SPORT_MOD_STATE'])
                self.logger.info("✓ Unsubscribed from LF_SPORT_MOD_STATE")

                # Give a brief moment for unsubscribe messages to be sent
                await asyncio.sleep(0.2)

            except Exception as e:
                self.logger.error(f"Error unsubscribing from topics: {e}")

            # STEP 6: Close WebRTC peer connection
            try:
                await self.state.connection.disconnect()
                self.logger.info("✓ WebRTC peer connection closed")
            except Exception as e:
                self.logger.error(f"Error closing WebRTC connection: {e}")

            self.logger.info("=" * 60)
            self.logger.info("DISCONNECT COMPLETE")
            self.logger.info("=" * 60)

        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}", exc_info=True)
            # Ensure state is set to disconnected even if errors occur
            self.state.is_connected = False

    def cleanup_audio_resources(self):
        """
        Clean up PyAudio resources.

        This function:
        1. Stops and closes PyAudio stream
        2. Terminates PyAudio instance
        3. Resets audio state variables
        """
        # Clean up audio resources (properties handle locking internally)
        if self.state.pyaudio_stream:
            try:
                self.state.pyaudio_stream.stop_stream()
                self.state.pyaudio_stream.close()
            except Exception as e:
                self.logger.error(f"Error closing PyAudio stream: {e}")
            self.state.pyaudio_stream = None

        if self.state.pyaudio_instance:
            try:
                self.state.pyaudio_instance.terminate()
            except Exception as e:
                self.logger.error(f"Error terminating PyAudio: {e}")
            self.state.pyaudio_instance = None

        self.state.microphone_audio_track = None
        self.state.audio_initialized = False
        self.state.audio_muted = True  # Reset to muted on disconnect
        self.logger.info("Audio resources cleaned up")

    def cleanup_connection(self):
        """
        Clean up connection resources.

        This function:
        1. Stops status polling (if still running)
        2. Cleans up audio resources
        3. Resets connection object
        4. Resets all state variables
        """
        # Stop status polling (if still running)
        self.stop_status_polling()

        # Clean up audio resources
        self.cleanup_audio_resources()

        # Reset connection object
        self.state.connection = None

        # Reset all state variables
        self.state.battery_level = 0
        self.state.ping_ms = 0
        self.state.current_mode = 'unknown'
        self.state.lidar_state = False
        self.state.free_bound_active = False

        self.logger.info("✓ All connection resources cleaned up")

    def connect_sync(
        self,
        method: str,
        video_callback: Callable,
        audio_callback: Callable,
        microphone_track_class: type,
        audio_config: Dict[str, Any],
        ip: Optional[str] = None,
        serial_number: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Synchronous wrapper for connection setup.

        This function:
        1. Ensures event loop is running
        2. Creates connection based on method
        3. Schedules async setup_connection() in event loop
        4. Waits for completion with timeout

        Args:
            method: Connection method ('LocalAP', 'LocalSTA', 'Remote')
            video_callback: Callback for video frames
            audio_callback: Callback for audio frames
            microphone_track_class: MicrophoneAudioTrack class
            audio_config: Audio configuration dict
            ip: IP address (for LocalSTA)
            serial_number: Serial number (for LocalSTA or Remote)
            username: Username (for Remote)
            password: Password (for Remote)
            timeout: Connection timeout in seconds (default: 30)

        Raises:
            asyncio.TimeoutError: If connection times out
            ValueError: If invalid parameters
            Exception: If connection fails
        """
        # Ensure event loop is running
        self.ensure_event_loop()

        # Create connection
        conn = self.create_connection(method, ip, serial_number, username, password)

        # Schedule connection in event loop
        future = asyncio.run_coroutine_threadsafe(
            self.setup_connection(conn, video_callback, audio_callback, microphone_track_class, audio_config),
            self.state.event_loop
        )
        future.result(timeout=timeout)  # Wait for completion
        self.logger.info("Connection established successfully")

    def disconnect_sync(self, timeout: int = 10):
        """
        Synchronous wrapper for disconnection.

        This function:
        1. Schedules async disconnect_connection() in event loop
        2. Waits for completion with timeout
        3. Cleans up connection resources

        Args:
            timeout: Disconnection timeout in seconds (default: 10)
        """
        if self.state.connection:
            if self.state.event_loop and self.state.event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self.disconnect_connection(),
                    self.state.event_loop
                )
                future.result(timeout=timeout)

        # Clean up resources
        self.cleanup_connection()
        self.logger.info("Disconnected successfully")

    def initialize_robot_sync(self):
        """
        Synchronous wrapper for robot initialization.

        Schedules async initialize_robot() in event loop (fire-and-forget).
        Does not wait for completion.
        """
        if self.state.event_loop and self.state.event_loop.is_running():
            self.logger.info("Starting robot initialization...")
            asyncio.run_coroutine_threadsafe(self.initialize_robot(), self.state.event_loop)
        else:
            self.logger.error(
                f"Event loop not running! state.event_loop={self.state.event_loop}, "
                f"is_running={self.state.event_loop.is_running() if self.state.event_loop else 'N/A'}"
            )


