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
from unitree_webrtc_connect.constants import RTC_TOPIC, SPORT_CMD


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
    
    def __init__(self, state_service):
        """
        Initialize ConnectionService.

        Args:
            state_service: StateService instance for state management
        """
        self.state = state_service
        self.logger = logging.getLogger(__name__)
        self._status_polling_task = None  # Background task for status polling
    
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
            # Connect to robot
            await conn.connect()
            
            # Setup video (always enabled)
            conn.video.switchVideoChannel(True)
            conn.video.add_track_callback(video_callback)
            self.logger.info("📹 Video streaming enabled")

            # Setup audio (ALWAYS initialize, but muted by default)
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

            # Subscribe to LOW_STATE for battery data
            self.subscribe_to_robot_status()

            # Start periodic status polling for mode and ping
            self.start_status_polling()

        except Exception as e:
            self.logger.error(f"Error connecting to robot: {e}")
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
                """Process LOW_STATE data for battery level."""
                try:
                    data = message['data']
                    bms_state = data.get('bms_state', {})
                    battery_soc = bms_state.get('soc', None)

                    if battery_soc is not None:
                        self.state.battery_level = battery_soc
                        self.state.last_status_update = time.time()
                        self.logger.debug(f"Battery level updated: {battery_soc}%")
                except Exception as e:
                    self.logger.error(f"Error processing LOW_STATE data: {e}")

            def sportmode_callback(message):
                """Process LF_SPORT_MOD_STATE data for mode and gait type."""
                try:
                    data = message['data']

                    # Extract gait type (0=idle, 1=trot, 2=climb stairs, 3=trot obstacle)
                    gait_type = data.get('gait_type', 0)

                    # Map gait type to user-friendly names
                    gait_names = {
                        0: 'idle',
                        1: 'trot',
                        2: 'climb_stairs',
                        3: 'trot_obstacle'
                    }

                    gait_name = gait_names.get(gait_type, f'gait_{gait_type}')

                    # Only log and update if gait changed
                    if gait_name != self.state.current_mode:
                        self.logger.info(f"Gait type changed: {self.state.current_mode} → {gait_name}")
                        self.state.current_mode = gait_name

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

        except Exception as e:
            self.logger.error(f"Error initializing robot: {e}")
            raise

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


