# IP Address Persistence & Lidar Switch Fixes

## ✅ **Both Issues Fixed!**

---

## 🔧 **Fix 1: IP Address Persistence**

### **Problem**
Users had to manually re-enter the robot IP address every time they opened the web interface.

### **Solution**
Implemented localStorage-based IP address persistence that:
- Saves the IP address to browser localStorage on successful connection
- Automatically loads and populates the saved IP address when the page loads
- Persists across browser sessions

### **Changes Made**

**File: `templates/index.html`**

1. **Save IP on successful connection** (lines 477-481):
```javascript
// Save IP address to localStorage on successful connection
if (ip) {
    localStorage.setItem('lastRobotIP', ip);
    console.log('Saved IP address to localStorage:', ip);
}
```

2. **Load IP on page load** (lines 858-863):
```javascript
// Load saved IP address from localStorage
const savedIP = localStorage.getItem('lastRobotIP');
if (savedIP) {
    document.getElementById('ip').value = savedIP;
    console.log('Loaded saved IP address:', savedIP);
}
```

### **How It Works**
1. User enters IP address (e.g., 192.168.178.155) and connects
2. On successful connection, IP is saved to browser's localStorage
3. Next time user opens the interface, the IP field is automatically populated
4. User can simply click "Connect" without re-entering the IP

---

## 🔧 **Fix 2: Lidar Switch Error**

### **Problem**
B button (lidar switch) was failing with error: "Please provide app id"

**Root Cause:** The lidar switch was using `publish_request_new()` with a dictionary parameter `{"switch": True}`, but the correct method is `publish_without_callback()` with a simple string "on" or "off".

### **Solution**
Changed the lidar switch implementation to use the correct API method based on Unitree examples.

### **Changes Made**

**File: `web_interface.py`**

1. **Added lidar state tracking** (line 39):
```python
lidar_state = False  # Track lidar on/off state
```

2. **Updated global variables** (lines 390-393, 402-403):
```python
global emergency_stop_active, current_body_height, lidar_state
```

3. **Fixed lidar switch implementation** (lines 479-502):
```python
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
```

### **Key Differences**

**Before (WRONG):**
```python
await connection.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["ULIDAR_SWITCH"],
    {"switch": True}  # ❌ Wrong format - requires api_id
)
```

**After (CORRECT):**
```python
connection.datachannel.pub_sub.publish_without_callback(
    RTC_TOPIC["ULIDAR_SWITCH"],
    "on"  # ✅ Correct format - simple string
)
```

### **How It Works**
1. First press of B button: Sends "on" to turn lidar on
2. Second press of B button: Sends "off" to turn lidar off
3. State is tracked internally to toggle between on/off
4. No more "Please provide app id" error!

---

## 🚀 **Testing Instructions**

### **Test IP Address Persistence:**
1. Open the web interface in your browser
2. Check if the IP field is pre-populated with your last used IP (if you've connected before)
3. If not, enter the robot IP (e.g., 192.168.178.155)
4. Click "Connect to Robot"
5. After successful connection, close the browser tab
6. Reopen the web interface
7. ✅ The IP field should now be automatically filled with your last used IP!

### **Test Lidar Switch:**
1. Connect to the robot and enable gamepad
2. Press B button (should be button index 1 on Xbox controller)
3. Check Python console - should see: `Toggling lidar to: on` and `Lidar switched on successfully`
4. Press B button again
5. Check Python console - should see: `Toggling lidar to: off` and `Lidar switched off successfully`
6. ✅ No more "Please provide app id" error!

---

## 📋 **Technical Details**

### **localStorage API**
- Browser-based persistent storage
- Data persists across browser sessions
- Specific to the domain (localhost:5000)
- Survives browser restarts
- Can be cleared via browser settings

### **Lidar Switch API**
- **Topic:** `rt/utlidar/switch`
- **Method:** `publish_without_callback()` (fire-and-forget)
- **Data:** Simple string "on" or "off"
- **No api_id required** (unlike sport commands)
- **IMPORTANT:** Must call `disableTrafficSaving(True)` before turning lidar ON
  - This is required for lidar data to be transmitted properly
  - Only needs to be called once when turning lidar on
  - Not needed when turning lidar off

### **Reference Examples**
The correct lidar switch usage is demonstrated in:
- `examples/go2/data_channel/lidar/lidar_stream.py` (line 28)
- `examples/go2/data_channel/lidar/plot_lidar_stream.py` (line 147)

---

## ✅ **Summary**

Both issues are now resolved:
1. ✅ **IP Address Persistence** - Users no longer need to re-enter IP address
2. ✅ **Lidar Switch** - B button now correctly toggles lidar without errors

**All changes are backward compatible and don't affect existing functionality!**

