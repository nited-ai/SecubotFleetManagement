# Troubleshooting Guide

## Video Streaming Issues

### Problem: Video Flickering / "Waiting for video..." Message

**Symptoms:**
- Video feed appears briefly then switches to "Waiting for video..." placeholder
- Continuous flickering between actual video and placeholder
- Connection is stable but video is not smooth

**Solution:**
This has been fixed in the latest version of `web_interface.py`. The improvements include:

1. **Increased buffer size** - Queue size increased from 10 to 30 frames
2. **Latest frame caching** - Always keeps the most recent frame available
3. **Smart frame delivery** - Uses cached frame when queue is temporarily empty
4. **Timeout-based placeholder** - Only shows "Waiting for video..." after 2 seconds of no frames

**To apply the fix:**
1. Make sure you're using the latest `web_interface.py`
2. Restart the web server
3. Reconnect to your robot

### Problem: Connection Timeout

**Symptoms:**
- "Connection timeout" error when trying to connect
- Cannot establish connection to robot

**Possible Causes & Solutions:**

1. **Incorrect IP Address**
   - Verify the robot's IP address is correct
   - Use the `test_connection.py` script to verify:
     ```bash
     python test_connection.py 192.168.178.155
     ```

2. **Robot Not Powered On**
   - Make sure the robot is turned on
   - Wait for the robot to fully boot up (30-60 seconds)

3. **Network Issues**
   - Ensure your computer and robot are on the same network
   - Check firewall settings
   - Try pinging the robot: `ping 192.168.178.155`

4. **Wrong Connection Method**
   - For same network: Use "Local STA"
   - For robot's WiFi hotspot: Use "Local AP"
   - For internet connection: Use "Remote"

### Problem: "Robot is connected by another WebRTC client"

**Symptoms:**
- Error message about another client being connected
- Cannot establish connection even though robot is on

**Solution:**
1. Close the Unitree mobile app completely
2. Make sure no other WebRTC connections are active
3. Wait 10 seconds
4. Try connecting again

### Problem: No Video After Connection

**Symptoms:**
- Connection successful
- Status shows "Connected"
- But no video appears (only "Waiting for video..." message)

**Possible Causes & Solutions:**

1. **Video Channel Not Enabled**
   - The web interface automatically enables video
   - Check the browser console for errors (F12)

2. **Browser Compatibility**
   - Use a modern browser (Chrome, Firefox, Edge)
   - Try a different browser if issues persist

3. **Network Bandwidth**
   - Video streaming requires good network bandwidth
   - Try moving closer to the WiFi router
   - Check if other devices are using bandwidth

## Performance Optimization

### Improving Video Quality

The video quality can be adjusted in `web_interface.py`:

```python
# Line ~93 in generate_frames()
ret, buffer = cv2.imencode('.jpg', frame_to_send, [cv2.IMWRITE_JPEG_QUALITY, 85])
```

- Increase the quality value (85-95) for better quality but more bandwidth
- Decrease the quality value (60-80) for lower bandwidth usage

### Adjusting Frame Rate

The frame rate is controlled by the timeout in the generate_frames function:

```python
# Line ~111 in generate_frames()
time.sleep(0.033)  # ~30 FPS
```

- Decrease sleep time for higher FPS (e.g., 0.016 for ~60 FPS)
- Increase sleep time for lower FPS (e.g., 0.066 for ~15 FPS)

### Buffer Size Adjustment

The buffer size can be adjusted for different network conditions:

```python
# Line ~22 in web_interface.py
frame_queue = Queue(maxsize=30)
```

- Increase for more buffering (smoother but more latency)
- Decrease for less latency (but may be less smooth)

## Testing Connection

Use the included test script to verify connectivity:

```bash
python test_connection.py 192.168.178.155
```

This will:
- Test WebRTC connection
- Verify video channel
- Show detailed connection logs
- Help identify connection issues

## Common Error Messages

### "Failed to establish a new connection"
- Robot is not reachable at the specified IP
- Check IP address and network connection

### "Max retries exceeded"
- Network timeout
- Robot may be off or unreachable
- Check network connectivity

### "MediaStreamError"
- Normal when disconnecting
- Can be ignored if it appears during disconnect

## Getting Help

If you continue to experience issues:

1. Check the terminal/console output for detailed error messages
2. Enable debug logging in `web_interface.py`:
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```
3. Check the browser console (F12) for JavaScript errors
4. Visit [TheRoboVerse](https://theroboverse.com) community for support
5. Report issues on the GitHub repository

## System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows, Linux, or macOS
- **Network**: WiFi connection to robot or same local network
- **Browser**: Modern browser with MJPEG support (Chrome, Firefox, Edge)
- **RAM**: At least 2GB available
- **CPU**: Multi-core processor recommended for smooth video

