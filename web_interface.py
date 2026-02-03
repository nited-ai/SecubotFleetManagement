"""
Simple web browser interface for Unitree Go2 robot control and video streaming.
Run this script and open http://localhost:5000 in your browser.
"""

import asyncio
import logging
import threading
import time
import base64
import struct
import fractions
from queue import Queue, Empty
from flask import Flask, render_template, Response, request, jsonify
from flask_socketio import SocketIO, emit
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod
from unitree_webrtc_connect.constants import RTC_TOPIC, SPORT_CMD
from aiortc import MediaStreamTrack, AudioStreamTrack
from aiortc.contrib.media import MediaPlayer
from aiortc.mediastreams import AudioFrame
from av import AudioFrame as AVAudioFrame
import cv2
import numpy as np
import pyaudio

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'unitree_webrtc_secret_key'
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    # Increase buffer sizes for high-frequency audio streaming
    max_http_buffer_size=10 * 1024 * 1024,  # 10MB buffer
    ping_timeout=60,  # 60 seconds
    ping_interval=25,  # 25 seconds
    engineio_logger=False,
    logger=False
)

# Global variables
frame_queue = Queue(maxsize=30)  # Increased buffer size
latest_frame = None  # Store the latest frame
frame_lock = threading.Lock()  # Thread-safe access to latest_frame
connection = None
event_loop = None
loop_thread = None
is_connected = False

# Gamepad control variables
gamepad_enabled = False
gamepad_lock = threading.Lock()
last_command_time = 0
command_interval = 0.016  # ~60Hz command rate (was 0.05/20Hz) for responsive control
emergency_stop_active = False
current_body_height = 1  # 0=low, 1=middle, 2=high
lidar_state = False  # Track lidar on/off state

# Keyboard & Mouse control variables
keyboard_mouse_enabled = False
keyboard_mouse_lock = threading.Lock()

# AI Mode Free functions state tracking
speed_level = 0  # -1=slow, 0=normal, 1=fast
free_bound_active = False  # Bound Run Mode
free_jump_active = False  # Jump Mode
free_avoid_active = False  # Avoidance Mode

# Gamepad sensitivity and velocity settings
gamepad_settings = {
    # Dead zone settings (0.0 to 1.0)
    'deadzone_left_stick': 0.15,   # Dead zone for left stick (movement)
    'deadzone_right_stick': 0.15,  # Dead zone for right stick (rotation)

    # Sensitivity multipliers (0.1 to 2.0)
    'sensitivity_linear': 1.0,      # Forward/backward sensitivity
    'sensitivity_strafe': 1.0,      # Left/right strafe sensitivity
    'sensitivity_rotation': 1.0,    # Yaw rotation sensitivity

    # Maximum velocity limits (m/s and rad/s)
    'max_linear_velocity': 0.6,     # Max forward/backward speed (m/s)
    'max_strafe_velocity': 0.4,     # Max strafe speed (m/s)
    'max_rotation_velocity': 0.8,   # Max rotation speed (rad/s)

    # Speed multiplier preset (0.5 = slow, 1.0 = normal, 1.5 = fast)
    'speed_multiplier': 1.0
}

# Track last sent velocities for zero-velocity detection
last_sent_velocities = {'vx': 0.0, 'vy': 0.0, 'vyaw': 0.0}
zero_velocity_sent = False  # Track if we've sent zero velocity after movement

# Audio streaming variables
audio_enabled = False
audio_lock = threading.Lock()
push_to_talk_active = False
microphone_audio_track = None
pyaudio_instance = None
pyaudio_stream = None
audio_output_queue = Queue(maxsize=100)  # Queue for robot audio to play through speakers

# Audio format constants (matching robot's audio format)
AUDIO_SAMPLE_RATE = 48000
AUDIO_CHANNELS = 2  # Stereo
AUDIO_FORMAT = pyaudio.paInt16
AUDIO_FRAMES_PER_BUFFER = 8192

class MicrophoneAudioTrack(AudioStreamTrack):
    """
    Custom audio track that streams PC microphone audio to the robot.
    Captures audio directly from PC microphone using PyAudio (server-side).
    Based on working example from GitHub issue #483.
    Supports push-to-talk mode.
    """
    def __init__(self):
        super().__init__()
        self.sample_rate = AUDIO_SAMPLE_RATE
        self.channels = AUDIO_CHANNELS
        self.samples_per_frame = 960  # 20ms at 48kHz
        self.audio_samples = 0  # Track timestamps
        self.is_transmitting = False  # Push-to-talk state

        # Initialize PyAudio for microphone capture (server-side)
        self.p = pyaudio.PyAudio()
        self.mic_stream = self.p.open(
            format=AUDIO_FORMAT,
            channels=1,  # Capture mono from microphone
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.samples_per_frame
        )

        logging.info("🎤 MicrophoneAudioTrack initialized - capturing from PC microphone (push-to-talk mode)")

    def start_transmitting(self):
        """Start transmitting microphone audio"""
        self.is_transmitting = True
        logging.info("🎤 Microphone transmission started")

    def stop_transmitting(self):
        """Stop transmitting microphone audio (send silence)"""
        self.is_transmitting = False
        logging.info("🎤 Microphone transmission stopped")

    async def recv(self):
        """
        Generate audio frames from PC microphone for WebRTC transmission.
        Sends silence when not transmitting (push-to-talk).
        """
        try:
            # Always read from microphone to prevent buffer overflow
            mic_data = self.mic_stream.read(self.samples_per_frame, exception_on_overflow=False)

            # If not transmitting, send silence instead
            if not self.is_transmitting:
                silence = np.zeros((1, self.samples_per_frame * self.channels), dtype=np.int16)
                frame = AVAudioFrame.from_ndarray(silence, format='s16', layout='stereo')
                frame.sample_rate = self.sample_rate
                frame.pts = self.audio_samples
                frame.time_base = fractions.Fraction(1, self.sample_rate)
                self.audio_samples += frame.samples
                return frame

            # Convert bytes to numpy array (mono, int16)
            audio_array = np.frombuffer(mic_data, dtype=np.int16)

            # Convert mono to stereo by duplicating the channel
            audio_stereo = np.column_stack((audio_array, audio_array))

            # Reshape to packed format (1, samples*channels)
            total_samples = self.samples_per_frame * self.channels
            audio_packed = audio_stereo.flatten().reshape((1, total_samples))

            # Create audio frame
            frame = AVAudioFrame.from_ndarray(
                audio_packed,
                format='s16',
                layout='stereo'
            )
            frame.sample_rate = self.sample_rate

            # Set proper timestamp
            frame.pts = self.audio_samples
            frame.time_base = fractions.Fraction(1, self.sample_rate)
            self.audio_samples += frame.samples

            return frame

        except Exception as e:
            logging.error(f"Error reading microphone: {e}")
            # Return silence on error
            silence = np.zeros((1, self.samples_per_frame * self.channels), dtype=np.int16)
            frame = AVAudioFrame.from_ndarray(silence, format='s16', layout='stereo')
            frame.sample_rate = self.sample_rate
            frame.pts = self.audio_samples
            frame.time_base = fractions.Fraction(1, self.sample_rate)
            self.audio_samples += frame.samples
            return frame

    def stop(self):
        """Clean up microphone resources"""
        try:
            if self.mic_stream:
                self.mic_stream.stop_stream()
                self.mic_stream.close()
            if self.p:
                self.p.terminate()
            logging.info("🎤 Microphone resources cleaned up")
        except Exception as e:
            logging.error(f"Error cleaning up microphone: {e}")

def run_event_loop(loop):
    """Run asyncio event loop in a separate thread"""
    asyncio.set_event_loop(loop)
    loop.run_forever()

async def initialize_robot():
    """Initialize robot into AI mode and Agile Mode (FreeWalk)"""
    try:
        logging.info(">>> initialize_robot() function started <<<")
        # First, check and set motion mode
        logging.info("Checking motion mode...")
        response = await connection.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["MOTION_SWITCHER"],
            {"api_id": 1001}
        )

        if response and 'data' in response:
            import json
            if 'data' in response['data']:
                data = json.loads(response['data']['data'])
                current_mode = data.get('name', 'unknown')
                logging.info(f"Current motion mode: {current_mode}")

                # Switch to AI mode if not already
                # AI mode uses Move command for speed control, not wireless controller
                if current_mode != "ai":
                    logging.info(f"Switching from {current_mode} to AI mode...")
                    await connection.datachannel.pub_sub.publish_request_new(
                        RTC_TOPIC["MOTION_SWITCHER"],
                        {
                            "api_id": 1002,
                            "parameter": {"name": "ai"}
                        }
                    )
                    await asyncio.sleep(5)  # Wait for mode switch (AI mode takes longer)
                    logging.info("Switched to AI mode")

        # Send FreeWalk command to enter Agile Mode (AI mode with obstacle avoidance)
        logging.info("Sending FreeWalk command to enter Agile Mode...")
        await connection.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["SPORT_MOD"],
            {"api_id": SPORT_CMD["FreeWalk"]}
        )
        await asyncio.sleep(2)  # Wait for robot to enter agile mode
        logging.info("Robot in Agile Mode (FreeWalk) - ready for AI movement with obstacle avoidance")

    except Exception as e:
        logging.error(f"Error initializing robot: {e}")
        import traceback
        logging.error(traceback.format_exc())

async def recv_camera_stream(track: MediaStreamTrack):
    """Receive video frames from the robot and put them in the queue"""
    global latest_frame
    frame_count = 0

    while True:
        try:
            frame = await track.recv()
            img = frame.to_ndarray(format="bgr24")

            frame_count += 1

            # Update the latest frame (thread-safe)
            with frame_lock:
                latest_frame = img.copy()

            # Also add to queue for buffering
            if frame_queue.full():
                # Remove old frame if queue is full
                try:
                    frame_queue.get_nowait()
                except Empty:
                    pass

            frame_queue.put(img)

            # Log every 30 frames
            if frame_count % 30 == 0:
                logging.info(f"Received {frame_count} video frames, queue size: {frame_queue.qsize()}")

        except Exception as e:
            logging.error(f"Error receiving video frame: {e}")
            break

async def recv_audio_stream(frame):
    """
    Receive audio frames from the robot and play them through speakers.
    This callback is triggered when audio frames are received from the robot.
    """
    global pyaudio_stream, audio_enabled

    try:
        if not audio_enabled or pyaudio_stream is None:
            return

        # Convert the frame to audio data (16-bit PCM)
        audio_data = np.frombuffer(frame.to_ndarray(), dtype=np.int16)

        # Play the audio data by writing it to the PyAudio stream
        pyaudio_stream.write(audio_data.tobytes())

    except Exception as e:
        logging.error(f"Error playing audio frame: {e}")

def generate_frames():
    """Generate frames for MJPEG streaming"""
    global latest_frame
    last_frame_time = time.time()
    blank_frame = None

    while True:
        try:
            frame_to_send = None

            # Try to get frame from queue with timeout
            try:
                frame_to_send = frame_queue.get(timeout=0.1)
            except Empty:
                # If queue is empty, use the latest frame we have
                with frame_lock:
                    if latest_frame is not None:
                        frame_to_send = latest_frame.copy()

            if frame_to_send is not None:
                # We have a valid frame to send
                last_frame_time = time.time()

                # Encode frame as JPEG with good quality
                ret, buffer = cv2.imencode('.jpg', frame_to_send, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                # Only show "waiting" message if we haven't received frames for a while
                if time.time() - last_frame_time > 2.0:
                    # Create blank frame only once
                    if blank_frame is None:
                        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                        cv2.putText(blank_frame, "Waiting for video...", (150, 240),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                    ret, buffer = cv2.imencode('.jpg', blank_frame)
                    if ret:
                        frame_bytes = buffer.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                else:
                    # Just wait a bit and try again
                    time.sleep(0.033)  # ~30 FPS

        except Exception as e:
            logging.error(f"Error generating frame: {e}")
            time.sleep(0.1)

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/connect', methods=['POST'])
def connect():
    """Connect to the robot"""
    global connection, event_loop, loop_thread, is_connected
    
    try:
        data = request.json
        connection_method = data.get('method')
        ip = data.get('ip', '')
        serial_number = data.get('serial_number', '')
        username = data.get('username', '')
        password = data.get('password', '')
        
        # Create event loop if not exists
        if event_loop is None or not event_loop.is_running():
            event_loop = asyncio.new_event_loop()
            loop_thread = threading.Thread(target=run_event_loop, args=(event_loop,), daemon=True)
            loop_thread.start()
        
        # Create connection based on method
        if connection_method == 'LocalAP':
            conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalAP)
        elif connection_method == 'LocalSTA':
            if ip:
                conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip=ip)
            elif serial_number:
                conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, serialNumber=serial_number)
            else:
                return jsonify({'status': 'error', 'message': 'IP or Serial Number required for LocalSTA'}), 400
        elif connection_method == 'Remote':
            if not all([serial_number, username, password]):
                return jsonify({'status': 'error', 'message': 'Serial Number, Username, and Password required for Remote'}), 400
            conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.Remote, 
                                          serialNumber=serial_number, 
                                          username=username, 
                                          password=password)
        else:
            return jsonify({'status': 'error', 'message': 'Invalid connection method'}), 400
        
        # Connect asynchronously
        async def setup_connection():
            global connection, is_connected, microphone_audio_track, pyaudio_instance, pyaudio_stream, audio_enabled
            try:
                await conn.connect()

                # Setup video
                conn.video.switchVideoChannel(True)
                conn.video.add_track_callback(recv_camera_stream)

                # Initialize PyAudio for audio reception
                pyaudio_instance = pyaudio.PyAudio()
                pyaudio_stream = pyaudio_instance.open(
                    format=AUDIO_FORMAT,
                    channels=AUDIO_CHANNELS,
                    rate=AUDIO_SAMPLE_RATE,
                    output=True,
                    frames_per_buffer=AUDIO_FRAMES_PER_BUFFER
                )

                # Setup audio - add microphone track immediately after connection
                # Use addTrack() like the examples do (stream_radio.py, play_mp3.py)
                microphone_audio_track = MicrophoneAudioTrack()
                conn.pc.addTrack(microphone_audio_track)
                logging.info("🎤 Microphone track added to peer connection")

                # Enable audio reception (robot → user)
                conn.audio.switchAudioChannel(True)
                conn.audio.add_track_callback(recv_audio_stream)
                logging.info("🎤 Audio reception enabled")

                audio_enabled = True
                connection = conn
                is_connected = True
                logging.info("Successfully connected to robot (video + audio)")
            except Exception as e:
                logging.error(f"Error connecting to robot: {e}")
                raise
        
        # Schedule connection in event loop
        future = asyncio.run_coroutine_threadsafe(setup_connection(), event_loop)
        future.result(timeout=30)  # Wait up to 30 seconds for connection

        return jsonify({'status': 'success', 'message': 'Connected to robot'})

    except asyncio.TimeoutError:
        logging.error("Connection timeout - robot may be unreachable")
        return jsonify({'status': 'error', 'message': 'Connection timeout. Check if robot is powered on and IP is correct.'}), 500
    except Exception as e:
        logging.error(f"Connection error: {e}")
        error_msg = str(e)
        if "reject" in error_msg.lower():
            error_msg = "Robot is already connected to another client. Close the Unitree mobile app and try again."
        elif "unreachable" in error_msg.lower() or "timeout" in error_msg.lower():
            error_msg = f"Cannot reach robot at the specified address. Check IP and network connection. Error: {error_msg}"
        return jsonify({'status': 'error', 'message': error_msg}), 500

@app.route('/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from the robot"""
    global connection, is_connected, latest_frame, frame_queue

    try:
        if connection:
            async def close_connection():
                global is_connected
                await connection.disconnect()
                is_connected = False

            if event_loop and event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(close_connection(), event_loop)
                future.result(timeout=10)

            connection = None

        # Clear video buffers
        with frame_lock:
            latest_frame = None

        # Clear the queue
        while not frame_queue.empty():
            try:
                frame_queue.get_nowait()
            except Empty:
                break

        return jsonify({'status': 'success', 'message': 'Disconnected from robot'})

    except Exception as e:
        logging.error(f"Disconnect error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/gamepad/enable', methods=['POST'])
def enable_gamepad():
    """Enable or disable gamepad control"""
    global gamepad_enabled, emergency_stop_active

    try:
        data = request.json
        enable = data.get('enable', False)

        if not is_connected:
            return jsonify({'status': 'error', 'message': 'Robot not connected'}), 400

        with gamepad_lock:
            gamepad_enabled = enable
            if enable:
                emergency_stop_active = False
                logging.info("=" * 50)
                logging.info("GAMEPAD CONTROL ENABLED")
                logging.info("=" * 50)

                # Initialize robot asynchronously
                if event_loop and event_loop.is_running():
                    logging.info("Starting robot initialization...")
                    asyncio.run_coroutine_threadsafe(initialize_robot(), event_loop)
                else:
                    logging.error(f"Event loop not running! event_loop={event_loop}, is_running={event_loop.is_running() if event_loop else 'N/A'}")
            else:
                logging.info("Gamepad control disabled")

        return jsonify({'status': 'success', 'enabled': gamepad_enabled})

    except Exception as e:
        logging.error(f"Enable gamepad error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/keyboard_mouse/enable', methods=['POST'])
def enable_keyboard_mouse():
    """Enable or disable keyboard/mouse control"""
    global keyboard_mouse_enabled, emergency_stop_active

    try:
        data = request.json
        enable = data.get('enable', False)

        if not is_connected:
            return jsonify({'status': 'error', 'message': 'Robot not connected'}), 400

        with keyboard_mouse_lock:
            keyboard_mouse_enabled = enable
            if enable:
                emergency_stop_active = False
                logging.info("=" * 50)
                logging.info("KEYBOARD/MOUSE CONTROL ENABLED")
                logging.info("=" * 50)

                # Initialize robot asynchronously (same as gamepad)
                if event_loop and event_loop.is_running():
                    logging.info("Starting robot initialization for keyboard/mouse control...")
                    asyncio.run_coroutine_threadsafe(initialize_robot(), event_loop)
                else:
                    logging.error(f"Event loop not running! event_loop={event_loop}, is_running={event_loop.is_running() if event_loop else 'N/A'}")
            else:
                logging.info("Keyboard/mouse control disabled")

        return jsonify({'status': 'success', 'enabled': keyboard_mouse_enabled})

    except Exception as e:
        logging.error(f"Enable keyboard/mouse error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/audio/test', methods=['POST'])
def test_audio():
    """Test audio playback with a simple beep/tone"""
    global connection, event_loop

    try:
        if not is_connected:
            return jsonify({'status': 'error', 'message': 'Robot not connected'}), 400

        async def play_test_audio():
            try:
                # Create a simple sine wave audio file URL (you can also use a local file)
                # For now, let's use a test tone generator
                import wave
                import tempfile
                import os

                # Generate a 1-second 440Hz sine wave (A note)
                sample_rate = 48000
                duration = 1.0
                frequency = 440.0

                # Generate samples
                t = np.linspace(0, duration, int(sample_rate * duration))
                samples = np.sin(2 * np.pi * frequency * t)

                # Convert to 16-bit PCM
                samples = (samples * 32767).astype(np.int16)

                # Create temporary WAV file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                temp_path = temp_file.name
                temp_file.close()

                # Write WAV file
                with wave.open(temp_path, 'w') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(samples.tobytes())

                logging.info(f"🔊 Playing test audio file: {temp_path}")

                # Use MediaPlayer to play the file
                player = MediaPlayer(temp_path)
                audio_track = player.audio

                # Add track to connection
                connection.pc.addTrack(audio_track)

                logging.info("✅ Test audio track added to WebRTC connection")

                # Wait for playback to complete
                await asyncio.sleep(duration + 0.5)

                # Cleanup
                os.unlink(temp_path)
                logging.info("🔊 Test audio playback completed")

            except Exception as e:
                logging.error(f"Error playing test audio: {e}")
                import traceback
                logging.error(traceback.format_exc())
                raise

        if event_loop and event_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(play_test_audio(), event_loop)
            future.result(timeout=10)

        return jsonify({'status': 'success', 'message': 'Test audio played'})

    except Exception as e:
        logging.error(f"Test audio error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/audio/enable', methods=['POST'])
def enable_audio():
    """Enable or disable audio streaming"""
    global audio_enabled, pyaudio_instance, pyaudio_stream, microphone_audio_track

    try:
        data = request.json
        enable = data.get('enable', False)

        if not is_connected:
            return jsonify({'status': 'error', 'message': 'Robot not connected'}), 400

        with audio_lock:
            if enable and not audio_enabled:
                # Initialize PyAudio for receiving robot audio
                pyaudio_instance = pyaudio.PyAudio()
                pyaudio_stream = pyaudio_instance.open(
                    format=AUDIO_FORMAT,
                    channels=AUDIO_CHANNELS,
                    rate=AUDIO_SAMPLE_RATE,
                    output=True,
                    frames_per_buffer=AUDIO_FRAMES_PER_BUFFER
                )

                # Enable audio channel and add callback for receiving audio
                async def setup_audio():
                    global microphone_audio_track
                    try:
                        # Create microphone track first
                        microphone_audio_track = MicrophoneAudioTrack()

                        # Get the audio transceiver that was created during connection
                        # The WebRTCAudioChannel already created a transceiver with direction="sendrecv"
                        transceivers = connection.pc.getTransceivers()
                        audio_transceiver = None
                        for transceiver in transceivers:
                            if transceiver.kind == "audio":
                                audio_transceiver = transceiver
                                break

                        if audio_transceiver:
                            # Check if sender already has a track
                            current_track = audio_transceiver.sender.track
                            logging.info(f"🎤 Found audio transceiver, current sender track: {current_track}")
                            logging.info(f"🎤 Transceiver direction: {audio_transceiver.direction}")

                            # Replace the track (works even if current_track is None)
                            logging.info(f"🎤 Replacing sender track with microphone track...")
                            audio_transceiver.sender.replaceTrack(microphone_audio_track)

                            # Verify the track was set
                            new_track = audio_transceiver.sender.track
                            logging.info(f"✅ Sender track after replace: {new_track}")
                            logging.info(f"✅ Track is our microphone: {new_track is microphone_audio_track}")
                        else:
                            # Fallback: add track directly (this will create a new transceiver)
                            logging.warning("⚠️ No audio transceiver found, adding track directly")
                            connection.pc.addTrack(microphone_audio_track)

                        # Enable audio channel and add callback for receiving audio
                        connection.audio.switchAudioChannel(True)
                        connection.audio.add_track_callback(recv_audio_stream)

                        logging.info("Audio streaming enabled")
                    except Exception as e:
                        logging.error(f"Error setting up audio: {e}")
                        import traceback
                        logging.error(traceback.format_exc())
                        raise

                if event_loop and event_loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(setup_audio(), event_loop)
                    future.result(timeout=10)

                audio_enabled = True
                logging.info("Audio enabled - receiving from robot and ready to transmit")

            elif not enable and audio_enabled:
                # Disable audio
                async def stop_audio():
                    try:
                        connection.audio.switchAudioChannel(False)
                        logging.info("Audio streaming disabled")
                    except Exception as e:
                        logging.error(f"Error stopping audio: {e}")

                if event_loop and event_loop.is_running():
                    asyncio.run_coroutine_threadsafe(stop_audio(), event_loop)

                # Stop and close PyAudio stream
                if pyaudio_stream:
                    pyaudio_stream.stop_stream()
                    pyaudio_stream.close()
                    pyaudio_stream = None

                if pyaudio_instance:
                    pyaudio_instance.terminate()
                    pyaudio_instance = None

                audio_enabled = False
                logging.info("Audio disabled")

        return jsonify({'status': 'success', 'enabled': audio_enabled})

    except Exception as e:
        logging.error(f"Enable audio error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/gamepad/command', methods=['POST'])
def gamepad_command():
    """Send gamepad or keyboard/mouse movement command to robot"""
    global last_command_time, emergency_stop_active, last_sent_velocities, zero_velocity_sent

    request_start_time = time.time()  # Track request processing time

    try:
        # Allow command if either gamepad OR keyboard/mouse is enabled
        if not is_connected or (not gamepad_enabled and not keyboard_mouse_enabled) or emergency_stop_active:
            return jsonify({'status': 'error', 'message': 'Control not active'}), 400

        # Rate limiting - reduced for more responsive control
        # Only enforce rate limit for non-zero velocity commands
        # Zero velocity commands should always go through immediately
        current_time = time.time()
        time_since_last = current_time - last_command_time

        # Skip rate limiting check - we'll let commands through faster
        # The robot's internal controller will handle command rate
        last_command_time = current_time

        data = request.json
        lx = float(data.get('lx', 0.0))  # Lateral (strafe)
        ly = float(data.get('ly', 0.0))  # Linear (forward/back)
        rx = float(data.get('rx', 0.0))  # Yaw (rotation)
        ry = float(data.get('ry', 0.0))  # Pitch (head up/down)

        # Apply dead zones
        deadzone_left = gamepad_settings['deadzone_left_stick']
        deadzone_right = gamepad_settings['deadzone_right_stick']

        # Apply dead zone to left stick
        if abs(lx) < deadzone_left:
            lx = 0.0
        if abs(ly) < deadzone_left:
            ly = 0.0

        # Apply dead zone to right stick
        if abs(rx) < deadzone_right:
            rx = 0.0
        if abs(ry) < deadzone_right:
            ry = 0.0

        # Apply sensitivity multipliers
        ly *= gamepad_settings['sensitivity_linear']
        lx *= gamepad_settings['sensitivity_strafe']
        rx *= gamepad_settings['sensitivity_rotation']

        # Apply speed multiplier
        speed_mult = gamepad_settings['speed_multiplier']
        ly *= speed_mult
        lx *= speed_mult
        rx *= speed_mult

        # Apply velocity limits and axis mapping
        # Axis mapping corrections based on testing:
        # - Forward/back: ly as-is (positive = forward)
        # - Strafe: -lx (invert for correct left/right)
        # - Rotation: -rx (invert for correct left/right rotation)

        # Use velocity limits from command data if provided (keyboard/mouse), otherwise use gamepad settings
        max_linear = data.get('max_linear', gamepad_settings['max_linear_velocity'])
        max_strafe = data.get('max_strafe', gamepad_settings['max_strafe_velocity'])
        max_rotation = data.get('max_rotation', gamepad_settings['max_rotation_velocity'])

        vx = max(-max_linear, min(max_linear, ly))      # Forward/back from left stick Y
        vy = max(-max_strafe, min(max_strafe, -lx))     # Strafe from left stick X (inverted)
        vyaw = max(-max_rotation, min(max_rotation, -rx))  # Yaw from right stick X (inverted)

        # Check if all velocities are zero (joysticks centered)
        is_zero_velocity = (abs(vx) < 0.01 and abs(vy) < 0.01 and abs(vyaw) < 0.01)

        # ALWAYS send commands for continuous movement control
        # The robot needs continuous commands to maintain movement
        # Only skip sending if we've already sent a zero-velocity stop command
        should_send = True
        if is_zero_velocity and zero_velocity_sent:
            # Already sent zero velocity, no need to send again
            should_send = False

        # Only send command if needed
        if not should_send:
            return jsonify({'status': 'success', 'message': 'No change'}), 200

        # Send Move command asynchronously (fire-and-forget for minimal latency)
        # We don't wait for the response to avoid blocking
        async def send_movement():
            try:
                # Create task without awaiting to avoid blocking
                asyncio.create_task(
                    connection.datachannel.pub_sub.publish_request_new(
                        RTC_TOPIC["SPORT_MOD"],
                        {
                            "api_id": SPORT_CMD["Move"],
                            "parameter": {
                                "x": vx,
                                "y": vy,
                                "z": vyaw
                            }
                        }
                    )
                )

                # Log zero velocity commands for debugging
                if is_zero_velocity:
                    logging.info("✓ Zero velocity command sent - robot should stop immediately")

            except Exception as e:
                logging.error(f"Error sending Move command: {e}")

        if event_loop and event_loop.is_running():
            # Fire and forget - don't wait for completion
            asyncio.run_coroutine_threadsafe(send_movement(), event_loop)

        # Update tracking variables
        last_sent_velocities['vx'] = vx
        last_sent_velocities['vy'] = vy
        last_sent_velocities['vyaw'] = vyaw
        zero_velocity_sent = is_zero_velocity

        # Log processing time for performance monitoring
        processing_time = (time.time() - request_start_time) * 1000  # Convert to ms
        if processing_time > 10:  # Log if processing takes more than 10ms
            logging.warning(f"Slow gamepad command processing: {processing_time:.1f}ms")

        return jsonify({
            'status': 'success',
            'zero_velocity': is_zero_velocity,
            'velocities': {'vx': round(vx, 3), 'vy': round(vy, 3), 'vyaw': round(vyaw, 3)},
            'processing_time_ms': round(processing_time, 2)
        })

    except Exception as e:
        logging.error(f"Gamepad command error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ========== WEBSOCKET GAMEPAD COMMAND HANDLER ==========

@socketio.on('gamepad_command')
def handle_websocket_gamepad_command(data):
    """
    WebSocket handler for gamepad or keyboard/mouse movement commands
    This provides lower latency than HTTP by using persistent WebSocket connection
    """
    global last_command_time, emergency_stop_active, last_sent_velocities, zero_velocity_sent

    request_start_time = time.time()

    try:
        # Allow command if either gamepad OR keyboard/mouse is enabled
        if not is_connected or (not gamepad_enabled and not keyboard_mouse_enabled) or emergency_stop_active:
            emit('command_response', {
                'status': 'error',
                'message': 'Control not active'
            })
            return

        # Rate limiting
        current_time = time.time()
        last_command_time = current_time

        # Get gamepad values
        lx = float(data.get('lx', 0.0))  # Lateral (strafe)
        ly = float(data.get('ly', 0.0))  # Linear (forward/back)
        rx = float(data.get('rx', 0.0))  # Yaw (rotation)
        ry = float(data.get('ry', 0.0))  # Pitch (head up/down)

        # Apply dead zones
        deadzone_left = gamepad_settings['deadzone_left_stick']
        deadzone_right = gamepad_settings['deadzone_right_stick']

        if abs(lx) < deadzone_left:
            lx = 0.0
        if abs(ly) < deadzone_left:
            ly = 0.0
        if abs(rx) < deadzone_right:
            rx = 0.0
        if abs(ry) < deadzone_right:
            ry = 0.0

        # Apply sensitivity multipliers
        ly *= gamepad_settings['sensitivity_linear']
        lx *= gamepad_settings['sensitivity_strafe']
        rx *= gamepad_settings['sensitivity_rotation']

        # Apply speed multiplier
        speed_mult = gamepad_settings['speed_multiplier']
        ly *= speed_mult
        lx *= speed_mult
        rx *= speed_mult

        # Apply velocity limits and axis mapping
        # Use velocity limits from command data if provided (keyboard/mouse), otherwise use gamepad settings
        max_linear = data.get('max_linear', gamepad_settings['max_linear_velocity'])
        max_strafe = data.get('max_strafe', gamepad_settings['max_strafe_velocity'])
        max_rotation = data.get('max_rotation', gamepad_settings['max_rotation_velocity'])

        vx = max(-max_linear, min(max_linear, ly))
        vy = max(-max_strafe, min(max_strafe, -lx))
        vyaw = max(-max_rotation, min(max_rotation, -rx))

        # Check if all velocities are zero
        is_zero_velocity = (abs(vx) < 0.01 and abs(vy) < 0.01 and abs(vyaw) < 0.01)

        # ALWAYS send commands for continuous movement control
        # The robot needs continuous commands to maintain movement
        # Only skip sending if we've already sent a zero-velocity stop command
        should_send = True
        if is_zero_velocity and zero_velocity_sent:
            # Already sent zero velocity, no need to send again
            should_send = False

        if not should_send:
            emit('command_response', {
                'status': 'success',
                'message': 'No change',
                'zero_velocity': is_zero_velocity
            })
            return

        # Send Move command asynchronously (fire-and-forget)
        async def send_movement():
            try:
                asyncio.create_task(
                    connection.datachannel.pub_sub.publish_request_new(
                        RTC_TOPIC["SPORT_MOD"],
                        {
                            "api_id": SPORT_CMD["Move"],
                            "parameter": {
                                "x": vx,
                                "y": vy,
                                "z": vyaw
                            }
                        }
                    )
                )

                if is_zero_velocity:
                    logging.info("✓ [WebSocket] Zero velocity command sent")

            except Exception as e:
                logging.error(f"Error sending WebSocket Move command: {e}")

        if event_loop and event_loop.is_running():
            asyncio.run_coroutine_threadsafe(send_movement(), event_loop)

        # Update tracking variables
        last_sent_velocities['vx'] = vx
        last_sent_velocities['vy'] = vy
        last_sent_velocities['vyaw'] = vyaw
        zero_velocity_sent = is_zero_velocity

        # Calculate processing time
        processing_time = (time.time() - request_start_time) * 1000

        # Send response back to client
        emit('command_response', {
            'status': 'success',
            'zero_velocity': is_zero_velocity,
            'velocities': {'vx': round(vx, 3), 'vy': round(vy, 3), 'vyaw': round(vyaw, 3)},
            'processing_time_ms': round(processing_time, 2)
        })

    except Exception as e:
        logging.error(f"WebSocket gamepad command error: {e}")
        emit('command_response', {
            'status': 'error',
            'message': str(e)
        })

# ========== WEBSOCKET AUDIO HANDLERS ==========

@socketio.on('start_microphone')
def handle_start_microphone():
    """Start transmitting microphone audio (push-to-talk pressed)"""
    global microphone_audio_track
    try:
        if microphone_audio_track:
            microphone_audio_track.start_transmitting()
            emit('microphone_status', {'transmitting': True})
        else:
            logging.error("❌ Microphone track not initialized")
            emit('microphone_status', {'transmitting': False, 'error': 'Microphone not initialized'})
    except Exception as e:
        logging.error(f"Error starting microphone: {e}")
        emit('microphone_status', {'transmitting': False, 'error': str(e)})

@socketio.on('stop_microphone')
def handle_stop_microphone():
    """Stop transmitting microphone audio (push-to-talk released)"""
    global microphone_audio_track
    try:
        if microphone_audio_track:
            microphone_audio_track.stop_transmitting()
            emit('microphone_status', {'transmitting': False})
        else:
            logging.error("❌ Microphone track not initialized")
    except Exception as e:
        logging.error(f"Error stopping microphone: {e}")

@app.route('/gamepad/settings', methods=['GET'])
def get_gamepad_settings():
    """Get current gamepad settings"""
    return jsonify({'status': 'success', 'settings': gamepad_settings})

@app.route('/gamepad/settings', methods=['POST'])
def update_gamepad_settings():
    """Update gamepad settings"""
    global gamepad_settings
    try:
        data = request.json

        # Update settings with validation
        if 'deadzone_left_stick' in data:
            gamepad_settings['deadzone_left_stick'] = max(0.0, min(1.0, float(data['deadzone_left_stick'])))
        if 'deadzone_right_stick' in data:
            gamepad_settings['deadzone_right_stick'] = max(0.0, min(1.0, float(data['deadzone_right_stick'])))
        if 'sensitivity_linear' in data:
            gamepad_settings['sensitivity_linear'] = max(0.1, min(2.0, float(data['sensitivity_linear'])))
        if 'sensitivity_strafe' in data:
            gamepad_settings['sensitivity_strafe'] = max(0.1, min(2.0, float(data['sensitivity_strafe'])))
        if 'sensitivity_rotation' in data:
            gamepad_settings['sensitivity_rotation'] = max(0.1, min(2.0, float(data['sensitivity_rotation'])))
        if 'max_linear_velocity' in data:
            gamepad_settings['max_linear_velocity'] = max(0.1, min(1.0, float(data['max_linear_velocity'])))
        if 'max_strafe_velocity' in data:
            gamepad_settings['max_strafe_velocity'] = max(0.1, min(0.8, float(data['max_strafe_velocity'])))
        if 'max_rotation_velocity' in data:
            gamepad_settings['max_rotation_velocity'] = max(0.1, min(1.5, float(data['max_rotation_velocity'])))
        if 'speed_multiplier' in data:
            gamepad_settings['speed_multiplier'] = max(0.1, min(2.0, float(data['speed_multiplier'])))

        logging.info(f"Gamepad settings updated: {gamepad_settings}")
        return jsonify({'status': 'success', 'settings': gamepad_settings})

    except Exception as e:
        logging.error(f"Error updating gamepad settings: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/gamepad/settings/preset', methods=['POST'])
def apply_gamepad_preset():
    """Apply a preset configuration"""
    global gamepad_settings
    try:
        data = request.json
        preset = data.get('preset', 'normal')

        presets = {
            'beginner': {
                'deadzone_left_stick': 0.20,
                'deadzone_right_stick': 0.20,
                'sensitivity_linear': 0.7,
                'sensitivity_strafe': 0.7,
                'sensitivity_rotation': 0.7,
                'max_linear_velocity': 0.4,
                'max_strafe_velocity': 0.3,
                'max_rotation_velocity': 0.5,
                'speed_multiplier': 0.7
            },
            'normal': {
                'deadzone_left_stick': 0.15,
                'deadzone_right_stick': 0.15,
                'sensitivity_linear': 1.0,
                'sensitivity_strafe': 1.0,
                'sensitivity_rotation': 1.0,
                'max_linear_velocity': 0.6,
                'max_strafe_velocity': 0.4,
                'max_rotation_velocity': 0.8,
                'speed_multiplier': 1.0
            },
            'advanced': {
                'deadzone_left_stick': 0.10,
                'deadzone_right_stick': 0.10,
                'sensitivity_linear': 1.3,
                'sensitivity_strafe': 1.3,
                'sensitivity_rotation': 1.3,
                'max_linear_velocity': 0.6,
                'max_strafe_velocity': 0.4,
                'max_rotation_velocity': 0.8,
                'speed_multiplier': 1.3
            },
            'sport': {
                'deadzone_left_stick': 0.08,
                'deadzone_right_stick': 0.08,
                'sensitivity_linear': 1.5,
                'sensitivity_strafe': 1.5,
                'sensitivity_rotation': 1.5,
                'max_linear_velocity': 0.6,
                'max_strafe_velocity': 0.4,
                'max_rotation_velocity': 0.8,
                'speed_multiplier': 1.5
            }
        }

        if preset in presets:
            gamepad_settings.update(presets[preset])
            logging.info(f"Applied '{preset}' preset: {gamepad_settings}")
            return jsonify({'status': 'success', 'preset': preset, 'settings': gamepad_settings})
        else:
            return jsonify({'status': 'error', 'message': 'Invalid preset'}), 400

    except Exception as e:
        logging.error(f"Error applying preset: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/gamepad/action', methods=['POST'])
def gamepad_action():
    """Handle gamepad button actions"""
    global emergency_stop_active, current_body_height, lidar_state

    try:
        if not is_connected:
            return jsonify({'status': 'error', 'message': 'Robot not connected'}), 400

        data = request.json
        action = data.get('action')

        async def send_action():
            global emergency_stop_active, current_body_height, lidar_state
            global speed_level, free_bound_active, free_jump_active, free_avoid_active

            try:
                if action == 'emergency_stop':
                    # Emergency stop - damp all motors
                    emergency_stop_active = True
                    await connection.datachannel.pub_sub.publish_request_new(
                        RTC_TOPIC["SPORT_MOD"],
                        {"api_id": SPORT_CMD["Damp"]}
                    )
                    logging.warning("EMERGENCY STOP ACTIVATED")

                elif action == 'clear_emergency':
                    emergency_stop_active = False
                    logging.info("Emergency stop cleared")

                elif action == 'free_walk':
                    # Enter Free Walk mode (Agile Mode) - AI mode obstacle avoidance
                    await connection.datachannel.pub_sub.publish_request_new(
                        RTC_TOPIC["SPORT_MOD"],
                        {"api_id": SPORT_CMD["FreeWalk"]}
                    )
                    logging.info("FreeWalk (Agile Mode) command sent - obstacle avoidance enabled")

                elif action == 'stand_up':
                    # Stand up first
                    await connection.datachannel.pub_sub.publish_request_new(
                        RTC_TOPIC["SPORT_MOD"],
                        {"api_id": SPORT_CMD["StandUp"]}
                    )
                    logging.info("Stand up command sent")

                    # Wait for stand up to complete, then enter BalanceStand for AI mode movement
                    await asyncio.sleep(1.5)
                    await connection.datachannel.pub_sub.publish_request_new(
                        RTC_TOPIC["SPORT_MOD"],
                        {"api_id": SPORT_CMD["BalanceStand"]}
                    )
                    logging.info("BalanceStand command sent - robot ready for AI movement")

                elif action == 'crouch':
                    # Crouch down (StandDown)
                    await connection.datachannel.pub_sub.publish_request_new(
                        RTC_TOPIC["SPORT_MOD"],
                        {"api_id": SPORT_CMD["StandDown"]}
                    )
                    logging.info("Crouch command sent")

                elif action == 'sit_down':
                    # Sit down
                    await connection.datachannel.pub_sub.publish_request_new(
                        RTC_TOPIC["SPORT_MOD"],
                        {"api_id": SPORT_CMD["Sit"]}
                    )
                    logging.info("Sit down command sent")

                elif action == 'toggle_height':
                    # Note: BodyHeight may not work in AI mode - AI mode has limited sport commands
                    # Cycle through heights: 0 (low), 1 (middle), 2 (high)
                    current_body_height = (current_body_height + 1) % 3
                    height_values = [-0.18, 0.0, 0.15]  # Low, middle, high
                    height_value = height_values[current_body_height]
                    height_name = ['low', 'middle', 'high'][current_body_height]

                    logging.info(f"Attempting to change body height to: {height_name} ({height_value})")
                    logging.warning("Note: BodyHeight command may not work in AI mode")

                    try:
                        response = await connection.datachannel.pub_sub.publish_request_new(
                            RTC_TOPIC["SPORT_MOD"],
                            {
                                "api_id": SPORT_CMD["BodyHeight"],
                                "parameter": {"height": height_value}
                            }
                        )
                        logging.info(f"Body height command sent. Response: {response}")

                        if response and 'data' in response:
                            logging.info(f"Body height changed to: {height_name}")
                        else:
                            logging.warning(f"Body height command may have failed - no response data")
                    except Exception as e:
                        logging.error(f"Error changing body height: {e}")

                elif action == 'lidar_switch':
                    # Toggle lidar using publish_without_callback (correct method per examples)
                    # Lidar switch uses simple "on"/"off" string, not api_id format
                    # IMPORTANT: Must disable traffic saving before turning lidar on
                    lidar_state = not lidar_state
                    switch_value = "on" if lidar_state else "off"

                    logging.info(f"Toggling lidar to: {switch_value}")
                    try:
                        # If turning lidar ON, must disable traffic saving first
                        if lidar_state:
                            logging.info("Disabling traffic saving for lidar...")
                            await connection.datachannel.disableTrafficSaving(True)
                            logging.info("Traffic saving disabled")

                        # Now toggle the lidar
                        connection.datachannel.pub_sub.publish_without_callback(
                            RTC_TOPIC["ULIDAR_SWITCH"],
                            switch_value
                        )
                        logging.info(f"Lidar switched {switch_value} successfully")
                    except Exception as e:
                        logging.error(f"Error toggling lidar: {e}")
                        lidar_state = not lidar_state  # Revert state on error

                elif action == 'stop_move':
                    # Stop all movement
                    await connection.datachannel.pub_sub.publish_request_new(
                        RTC_TOPIC["SPORT_MOD"],
                        {"api_id": SPORT_CMD["StopMove"]}
                    )
                    logging.info("Stop move command sent")

                elif action == 'enable_walk_mode':
                    # In AI mode, robot is already in BalanceStand which allows movement
                    # No need to send additional commands
                    logging.info("Walk mode enabled - robot ready to move (AI mode)")

                elif action == 'disable_walk_mode':
                    # Stop movement by sending Move command with zero velocities
                    logging.info("Walk mode disabled - stopping movement")
                    await connection.datachannel.pub_sub.publish_request_new(
                        RTC_TOPIC["SPORT_MOD"],
                        {
                            "api_id": SPORT_CMD["Move"],
                            "parameter": {
                                "x": 0.0,
                                "y": 0.0,
                                "z": 0.0
                            }
                        }
                    )

                elif action == 'speed_level_up':
                    # Increase speed level
                    speed_level = min(1, speed_level + 1)  # Clamp to max 1
                    await connection.datachannel.pub_sub.publish_request_new(
                        RTC_TOPIC["SPORT_MOD"],
                        {
                            "api_id": SPORT_CMD["SpeedLevel"],
                            "parameter": {"level": speed_level}
                        }
                    )
                    speed_name = {-1: "slow", 0: "normal", 1: "fast"}[speed_level]
                    logging.info(f"Speed level set to: {speed_level} ({speed_name})")

                elif action == 'speed_level_down':
                    # Decrease speed level
                    speed_level = max(-1, speed_level - 1)  # Clamp to min -1
                    await connection.datachannel.pub_sub.publish_request_new(
                        RTC_TOPIC["SPORT_MOD"],
                        {
                            "api_id": SPORT_CMD["SpeedLevel"],
                            "parameter": {"level": speed_level}
                        }
                    )
                    speed_name = {-1: "slow", 0: "normal", 1: "fast"}[speed_level]
                    logging.info(f"Speed level set to: {speed_level} ({speed_name})")

                elif action == 'toggle_free_bound':
                    # Toggle FreeBound mode (Bound Run Mode)
                    free_bound_active = not free_bound_active
                    await connection.datachannel.pub_sub.publish_request_new(
                        RTC_TOPIC["SPORT_MOD"],
                        {
                            "api_id": SPORT_CMD["FreeBound"],
                            "parameter": {"data": free_bound_active}
                        }
                    )
                    logging.info(f"FreeBound (Bound Run) mode: {'enabled' if free_bound_active else 'disabled (returned to Agile Mode)'}")

                elif action == 'toggle_free_jump':
                    # Toggle FreeJump mode (Jump Mode)
                    free_jump_active = not free_jump_active
                    await connection.datachannel.pub_sub.publish_request_new(
                        RTC_TOPIC["SPORT_MOD"],
                        {
                            "api_id": SPORT_CMD["FreeJump"],
                            "parameter": {"data": free_jump_active}
                        }
                    )
                    logging.info(f"FreeJump (Jump) mode: {'enabled' if free_jump_active else 'disabled (returned to Agile Mode)'}")

                elif action == 'toggle_free_avoid':
                    # Toggle FreeAvoid mode (Avoidance Mode)
                    free_avoid_active = not free_avoid_active
                    await connection.datachannel.pub_sub.publish_request_new(
                        RTC_TOPIC["SPORT_MOD"],
                        {
                            "api_id": SPORT_CMD["FreeAvoid"],
                            "parameter": {"data": free_avoid_active}
                        }
                    )
                    logging.info(f"FreeAvoid (Avoidance) mode: {'enabled' if free_avoid_active else 'disabled (returned to Agile Mode)'}")

                elif action == 'toggle_walk_pose':
                    # Toggle between walk and pose mode (legacy - kept for compatibility)
                    await connection.datachannel.pub_sub.publish_request_new(
                        RTC_TOPIC["SPORT_MOD"],
                        {"api_id": SPORT_CMD["Pose"]}
                    )
                    logging.info("Walk/Pose mode toggled")

            except Exception as e:
                logging.error(f"Error sending action command: {e}")
                raise

        if event_loop and event_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(send_action(), event_loop)
            future.result(timeout=5)

        return jsonify({'status': 'success', 'action': action})

    except Exception as e:
        logging.error(f"Gamepad action error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/gamepad/camera', methods=['POST'])
def gamepad_camera():
    """Handle gamepad camera control (LT/RT triggers)"""
    try:
        if not is_connected:
            return jsonify({'status': 'error', 'message': 'Robot not connected'}), 400

        if not gamepad_enabled:
            return jsonify({'status': 'error', 'message': 'Gamepad not enabled'}), 400

        data = request.json
        yaw = float(data.get('yaw', 0.0))

        # Send camera control command asynchronously
        async def send_camera_control():
            try:
                await connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {
                        "api_id": SPORT_CMD["Euler"],
                        "parameter": {"roll": 0.0, "pitch": 0.0, "yaw": yaw}
                    }
                )
            except Exception as e:
                logging.error(f"Error sending camera control command: {e}")

        if event_loop and event_loop.is_running():
            asyncio.run_coroutine_threadsafe(send_camera_control(), event_loop)

        return jsonify({'status': 'success'})

    except Exception as e:
        logging.error(f"Gamepad camera control error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/status')
def status():
    """Get connection status"""
    return jsonify({
        'connected': is_connected,
        'gamepad_enabled': gamepad_enabled,
        'keyboard_mouse_enabled': keyboard_mouse_enabled,
        'emergency_stop': emergency_stop_active
    })

@app.route('/ping')
def ping():
    """Lightweight ping endpoint for network latency testing"""
    return jsonify({'pong': time.time()})

@app.route('/webrtc/test_direct_command', methods=['POST'])
def webrtc_test_direct_command():
    """
    Test endpoint to send a command directly via WebRTC data channel
    This bypasses HTTP for the actual command, only using HTTP to trigger it
    Used for latency comparison testing
    """
    global connection, event_loop

    try:
        if not is_connected:
            return jsonify({'status': 'error', 'message': 'Not connected to robot'}), 400

        data = request.json
        vx = float(data.get('vx', 0.0))
        vy = float(data.get('vy', 0.0))
        vyaw = float(data.get('vyaw', 0.0))

        # Record start time for latency measurement
        start_time = time.time()

        # Send command directly via WebRTC
        async def send_direct_command():
            try:
                # Send Move command via WebRTC data channel
                await connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {
                        "api_id": SPORT_CMD["Move"],
                        "parameter": {"x": vx, "y": vy, "z": vyaw}
                    }
                )
                logging.info(f"✓ Direct WebRTC command sent: vx={vx}, vy={vy}, vyaw={vyaw}")
            except Exception as e:
                logging.error(f"Error sending direct WebRTC command: {e}")

        if event_loop and event_loop.is_running():
            # Send command asynchronously
            future = asyncio.run_coroutine_threadsafe(send_direct_command(), event_loop)
            # Wait for completion to measure round-trip time
            future.result(timeout=1.0)

        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000

        return jsonify({
            'status': 'success',
            'latency_ms': round(latency_ms, 2),
            'velocities': {'vx': vx, 'vy': vy, 'vyaw': vyaw}
        })

    except Exception as e:
        logging.error(f"WebRTC test command error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Unitree Go2 Web Interface')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the web server on (default: 5000)')
    args = parser.parse_args()

    port = args.port

    print("=" * 70)
    print(f"Starting Unitree Go2 Web Interface on port {port}")
    print("=" * 70)
    print(f"Open http://localhost:{port} in your browser")
    print("WebSocket enabled for low-latency gamepad control")
    print("Push-to-talk: Hold 'C' key or click 'Hold to Talk' button")
    print("=" * 70)
    print()

    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)

