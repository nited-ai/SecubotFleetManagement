# Unitree Go2 Web Interface

A simple web browser interface to connect to your Unitree Go2 robot and view the live video stream.

## Features

- 🌐 **Browser-based control** - No need to install additional software
- 📹 **Live video streaming** - View the robot's camera feed in real-time
- 🔌 **Multiple connection methods** - Support for Local AP, Local STA, and Remote connections
- 🎨 **Modern UI** - Clean and responsive interface

## Requirements

The web interface requires Flask, which is already included in the project dependencies via `flask-socketio`.

If you need to install Flask separately:
```bash
pip install flask
```

## Quick Start

1. **Run the web interface:**
   ```bash
   python web_interface.py
   ```

2. **Open your browser:**
   Navigate to `http://localhost:5000`

3. **Connect to your robot:**
   - Select your connection method
   - Fill in the required information
   - Click "Connect to Robot"

## Connection Methods

### 1. Local AP (Robot WiFi)
Connect directly to the robot's WiFi hotspot.

- **Requirements:** None (just select this option)
- **Use case:** Direct connection when near the robot

### 2. Local STA (Same Network)
Connect when both your computer and robot are on the same network.

- **Requirements:** 
  - Robot IP address (e.g., `192.168.8.181`), OR
  - Robot serial number (e.g., `B42D2000XXXXXXXX`)
- **Use case:** When both devices are on the same local network

### 3. Remote (Internet)
Connect to your robot over the internet using Unitree's TURN server.

- **Requirements:**
  - Robot serial number
  - Unitree account email
  - Unitree account password
- **Use case:** Control your robot from anywhere

## Troubleshooting

### Connection Issues

1. **"Connection failed" error:**
   - Make sure the robot is powered on
   - Verify you're using the correct connection method
   - Check that no other app (like Unitree mobile app) is connected to the robot

2. **No video appearing:**
   - Wait a few seconds after connecting
   - Check your network connection
   - Try refreshing the browser page

3. **"Robot is connected by another WebRTC client" error:**
   - Close the Unitree mobile app
   - Disconnect any other WebRTC clients
   - Try connecting again

### Network Issues

- **Local AP:** Make sure you're connected to the robot's WiFi hotspot
- **Local STA:** Ensure both devices are on the same network
- **Remote:** Check your internet connection and Unitree account credentials

## Technical Details

- **Backend:** Flask (Python web framework)
- **Video Streaming:** MJPEG over HTTP
- **WebRTC:** aiortc library for robot communication
- **Video Processing:** OpenCV for frame handling

## Notes

- Video streaming is only available on **Go2 robots** (not G1)
- The web interface runs on port 5000 by default
- Multiple browser tabs can view the stream, but only one connection to the robot is maintained
- The interface automatically checks connection status every 2 seconds

## Advanced Usage

### Change the port:
Edit `web_interface.py` and modify the last line:
```python
app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
```

### Access from other devices on your network:
The interface is accessible from other devices on your network at:
```
http://YOUR_COMPUTER_IP:5000
```

Replace `YOUR_COMPUTER_IP` with your computer's local IP address.

## Support

For issues and questions:
- Check the main [README.md](README.md) for general project information
- Visit [TheRoboVerse](https://theroboverse.com) community
- Report bugs on the GitHub repository

