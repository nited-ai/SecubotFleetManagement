"""
Simple web browser interface for Unitree Go2 robot control and video streaming.
Run this script and open http://localhost:5000 in your browser.
"""

import logging
import os
from flask import Flask
from flask_socketio import SocketIO

# Import services
from app.services import StateService, ConnectionService, VideoService, AudioService, ControlService

# Import route blueprints
from app.routes import views_bp, api_bp, register_websocket_handlers

# ============================================================================
# DEBUG LEVEL CONFIGURATION
# ============================================================================
# Level 0 (SILENT): Only errors/warnings
# Level 1 (BASIC): Essential logs only (connection status, actions, errors)
# Level 2 (VERBOSE): Include movement commands and state changes
# Level 3 (DEEP_DEBUG): All logs including sensitivity calculations, normalization
# ============================================================================
DEBUG_LEVEL = int(os.getenv('DEBUG_LEVEL', '1'))  # Default to Level 1 (Basic)

# Configure logging based on DEBUG_LEVEL
if DEBUG_LEVEL == 0:
    logging.basicConfig(level=logging.WARNING)  # Silent mode
elif DEBUG_LEVEL == 1:
    logging.basicConfig(level=logging.INFO)     # Basic mode
else:
    logging.basicConfig(level=logging.DEBUG)    # Verbose/Deep Debug mode

# Reduce Werkzeug HTTP request logging verbosity
# This suppresses routine GET/POST request logs like "/api/robot/status"
# while keeping ERROR and WARNING logs visible
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.WARNING)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'unitree_webrtc_secret_key'
app.config['DEBUG_LEVEL'] = DEBUG_LEVEL  # Make DEBUG_LEVEL accessible to services

# Initialize SocketIO
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

# Initialize services
state = StateService()
connection_service = ConnectionService(state, debug_level=DEBUG_LEVEL)
video_service = VideoService(state)
audio_service = AudioService(state)
control_service = ControlService(state)

# Store services in app config for blueprint access
app.config['STATE_SERVICE'] = state
app.config['CONNECTION_SERVICE'] = connection_service
app.config['VIDEO_SERVICE'] = video_service
app.config['AUDIO_SERVICE'] = audio_service
app.config['CONTROL_SERVICE'] = control_service

# Register blueprints
app.register_blueprint(views_bp)
app.register_blueprint(api_bp, url_prefix='/api')

# Register WebSocket handlers
register_websocket_handlers(socketio)


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
