# Product Mission

> Last Updated: 2026-02-03
> Version: 1.0.0

## Pitch

**Unitree WebRTC Connect** is a web-based robot fleet management platform that helps enterprise customers and surveillance/security companies remotely control and monitor Unitree Go2 robots by providing real-time video streaming, bidirectional audio communication, and intuitive control interfaces accessible from any web browser.

---

## Users

### Primary Customers

- **Enterprise Customers**: Organizations deploying robot fleets for surveillance, security, inspection, or facility management
- **Surveillance/Security Companies**: Security firms using robots for patrol, monitoring, and incident response
- **Fleet Operators**: Teams managing multiple robots across different locations or facilities

### User Personas

**Security Operations Manager** (35-50 years old)
- **Role:** Security Operations Manager / Fleet Supervisor
- **Context:** Manages 5-20 robots deployed across multiple facilities for 24/7 surveillance and patrol
- **Pain Points:** 
  - Needs to monitor multiple robots simultaneously
  - Requires quick response to security incidents
  - Must manage robot assignments to different zones/objects
  - Needs reliable remote control during critical situations
- **Goals:** 
  - Maximize robot uptime and coverage
  - Respond quickly to security alerts
  - Efficiently manage robot fleet assignments
  - Ensure operators have reliable control interfaces

**Security Operator** (25-40 years old)
- **Role:** Security Operator / Robot Pilot
- **Context:** Remotely controls robots for patrol, investigation, and incident response
- **Pain Points:**
  - Needs low-latency control for real-time navigation
  - Requires clear video feed and audio communication
  - Must quickly switch between multiple robots
  - Needs intuitive controls that work under pressure
- **Goals:**
  - Navigate robots efficiently through facilities
  - Communicate with people via robot speakers
  - Respond quickly to security incidents
  - Monitor robot status (battery, connection, sensors)

**Viewer/Stakeholder** (30-60 years old)
- **Role:** Facility Manager / Security Stakeholder
- **Context:** Monitors robot operations and reviews footage/data
- **Pain Points:**
  - Needs read-only access to robot feeds
  - Requires overview of fleet status
  - Must review incident recordings
- **Goals:**
  - Monitor overall security coverage
  - Review robot patrol footage
  - Verify robot assignments and status

---

## The Problem

### Remote Robot Fleet Management is Complex and Fragmented

Current robot control solutions require proprietary mobile apps, lack web accessibility, and don't scale for fleet management. Security companies need to manage multiple robots across different locations, but existing tools are designed for single-robot hobbyist use.

**Our Solution:** A web-based platform that provides enterprise-grade fleet management with real-time control, multi-user access levels, and centralized robot assignment to monitored objects/zones.

### Real-Time Control Requires Low Latency and Reliability

Security operations demand instant response times. Network latency, video lag, or control delays can compromise security effectiveness and operator safety.

**Our Solution:** WebRTC-based architecture with WebSocket commands provides sub-100ms latency for video, audio, and control. Optimized event loop management prevents blocking operations from degrading performance.

### Multi-User Access and Role Management

Security operations require different access levels: administrators manage robot fleet, operators control robots, and viewers monitor operations. Current solutions lack proper role-based access control.

**Our Solution:** Planned login system with three access levels (Organization/Admin, Operator, Viewer) ensures proper access control and audit trails.

### Robot-to-Object Assignment and Tracking

Security companies need to assign robots to specific objects, zones, or patrol routes. Current solutions lack this organizational capability.

**Our Solution:** Planned object management system allows creating objects (buildings, zones, patrol routes) and assigning robots to them for organized fleet deployment.

---

## Differentiators

### Web-Based, No Installation Required

Unlike proprietary mobile apps (Unitree Go2 app), our platform runs in any modern web browser. This enables:
- **Multi-platform access** (Windows, Mac, Linux, tablets)
- **No app installation** or updates required
- **Centralized deployment** with instant updates
- **Remote access** from anywhere with internet connection

This results in faster operator onboarding, reduced IT overhead, and better accessibility for distributed teams.

### Enterprise-Grade Fleet Management

Unlike hobbyist tools focused on single-robot control, we provide:
- **Multi-robot management** with centralized dashboard
- **Role-based access control** (Admin, Operator, Viewer)
- **Robot-to-object assignment** for organized deployment
- **Fleet status monitoring** (battery, connection, location)

This results in scalable operations for security companies managing 10-100+ robots across multiple facilities.

### Optimized for Low-Latency Real-Time Control

Unlike traditional web apps with HTTP polling, we use:
- **WebRTC** for sub-100ms video/audio streaming
- **WebSocket** for low-latency control commands
- **Async event loop optimization** preventing blocking operations
- **Fire-and-forget commands** for minimal control latency

This results in responsive control suitable for security operations and incident response.

---

## Key Features

### Core Features (Already Implemented)

- **WebRTC Connection Management:** Connect to robots via LocalSTA (WiFi), LocalAP (Direct), or Remote (Internet) methods
- **Real-Time Video Streaming:** H.264 video with frame buffering and automatic quality adjustment
- **Bidirectional Audio:** Robot-to-user audio playback with instant mute/unmute, user-to-robot push-to-talk communication
- **Gamepad Control:** HTML5 Gamepad API support with configurable sensitivity and presets (beginner, normal, advanced, sport)
- **Keyboard/Mouse Control:** WASD movement, mouse pointer lock for rotation, mouse wheel for speed control
- **WebSocket Commands:** Low-latency movement control via persistent WebSocket connection
- **AI Mode Integration:** FreeWalk (Agile Mode) with obstacle avoidance, advanced modes (FreeBound, FreeJump, FreeAvoid)
- **Robot Actions:** Emergency stop, stand up, sit, crouch, speed level control, LIDAR toggle
- **Settings Management:** Configurable dead zones, sensitivity, velocity limits with preset configurations

### Planned Fleet Management Features

- **Robot Registration:** Add robots with IP addresses, serial numbers, connection methods; edit and delete robot entries
- **Object Management:** Create objects (buildings, zones, patrol routes) and assign robots to them
- **Multi-User Login:** Organization/Admin, Operator, and Viewer roles with appropriate access controls
- **Robot Overview Dashboard:** Fleet status, robot assignments, battery levels, connection status

### Planned Control Enhancements

- **Additional Keyboard Controls:** Ctrl (crouch), Shift (slow walk), Space (pose/look around), R (rage mode), Q (crouch down), E (recovery stand)
- **Camera Control:** Mouse X/Y for yaw and pitch control
- **Volume Control:** Arrow up/down for audio volume adjustment
- **Light Control:** Adjustable robot light intensity (1-100%)

### Planned UI Features

- **Fullscreen Video:** Immersive video streaming interface
- **LIDAR Point Cloud Visualization:** Real-time 3D point cloud display
- **Status Indicators:** Battery, connection/ping, temperatures, avoidance status, current mode
- **Screenshot Capture:** Save current video frame to download folder
- **Video Recording:** Save video streams for later review

### Advanced Features (Future)

- **DimOS Click Navigation:** Costmap creation and autonomous navigation
- **Autonomous Bot Notifications:** Alerts from robots operating in autonomous mode
- **Predefined Audio:** Sirens, instructions, movement sounds for security operations


