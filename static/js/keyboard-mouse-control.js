/**
 * Keyboard & Mouse Control Module
 * Handles WASD keyboard movement and mouse rotation via Pointer Lock API
 */

// ============================================================================
// DEBUG LEVEL CONFIGURATION
// ============================================================================
// Level 0 (SILENT): No debug logs
// Level 1 (BASIC): Essential logs only (actions, errors)
// Level 2 (VERBOSE): Include movement commands
// Level 3 (DEEP_DEBUG): All logs including sensitivity calculations
// ============================================================================
const DEBUG_LEVEL = parseInt(localStorage.getItem('DEBUG_LEVEL') || '1');


class KeyboardMouseControl {
    constructor() {
        this.enabled = false;
        this.pollingInterval = null;
        this.keysPressed = {};
        this.mouseMovement = { x: 0, y: 0 };
        this.pointerLocked = false;
        this.commandInFlight = false;

        // Velocity ramping for smooth acceleration/deceleration
        this.currentVelocities = {
            linear: 0.0,
            strafe: 0.0,
            rotation: 0.0,
            pitch: 0.0  // Current pitch angle (rad)
        };

        // Settings (loaded from localStorage)
        this.settings = this.loadSettings();

        // Speed percentage (0-100%, controlled by speed slider)
        // This represents the percentage along the curve (0% = no movement, 100% = full curve)
        this.speedPercentage = 100; // Default to 100%

        // Precision Mode (Shift key) - temporarily reduces speed to 25%
        this.precisionMode = false;
        this.speedBeforeShift = null;  // Store speed before entering precision mode

        // Constants
        this.POLL_RATE = 33; // 30Hz
        this.DEADZONE = 0.1;
        this.WHEEL_STEP = 5;       // Change by 5% per wheel notch
        this.MIN_SPEED = 0;        // Minimum 0% speed
        this.MAX_SPEED = 100;      // Maximum 100% speed

        // Mouse scale factor to convert raw pixel movement to normalized input (0-1 range)
        // Sensitivity is applied POST-CURVE as a velocity multiplier (not pre-curve)
        // This prevents sensitivity from being swallowed by the [0,1] clamp in applyCurve()
        // Typical mouse movement per poll (33ms): slow=10px, normal=50px, fast=100-200px
        // With 0.01 scale: 100px * 0.01 = 1.0 (full curve input)
        //                  50px * 0.01 = 0.5 (half curve input)
        //                  10px * 0.01 = 0.1 (deadzone boundary)
        this.MOUSE_SCALE_FACTOR = 0.01;  // Scale raw pixels to 0-1 range for curve input

        // REMOVED: Frontend smoothing constants (Option B - Direct Assignment)
        // Jump-start (MIN_START_SPEED) and exponential ramping (ACCEL_FACTOR) were removed
        // because the backend's asymmetric slew rate limiter handles all physics smoothing.
        // ACCEL_FACTOR=0.05 was a 2-second anchor that made ramp_time settings meaningless.
        // See docs/analysis/STRAFE_ANALYSIS.md for full analysis.

        // Speed indicator timeout
        this.speedIndicatorTimeout = null;

        // RAGE MODE flag (bypasses all smoothing)
        this.rageMode = false;

        // Pose Mode state (SPACE key hold-to-activate)
        this.poseMode = false;

        // Pose Mode accumulated angles (position-based control)
        // In Pose Mode, WirelessController axes are POSITION (spring-centered joystick).
        // Mouse yaw/pitch ACCUMULATE so the robot holds position when mouse stops.
        // WASD roll/height are VELOCITY-style: spring back to 0 when keys are released.
        // Range: [-1, 1] (normalized joystick position)
        this.poseAngles = { yaw: 0, pitch: 0 };  // Accumulated (mouse) — hold position

        // Pose Mode sensitivity: how fast angles accumulate per poll tick
        // Mouse sensitivity is scaled by speedMultiplier (speed slider)
        this.POSE_MOUSE_SENSITIVITY = 0.003;  // Per raw pixel of mouse movement (base)
        this.POSE_KEY_RATE = 1.0;             // Per poll tick for A/D (roll) and W/S (height) — velocity, not accumulated (1.0 = full joystick range)

        // Callbacks
        this.onCommandSend = null; // Callback to send commands
    }

    /**
     * Load settings from localStorage
     */
    loadSettings() {
        // Try new settings format first (from landing page settings-manager.js)
        const newSettings = localStorage.getItem('unitree_settings');

        if (newSettings) {
            try {
                const parsed = JSON.parse(newSettings);

                if (parsed.keyboard_mouse) {
                    const km = parsed.keyboard_mouse;
                    return {
                        maxLinear: parseFloat(km.kb_max_linear_velocity || 1.5),
                        maxStrafe: parseFloat(km.kb_max_strafe_velocity || 1.5),
                        maxRotation: parseFloat(km.kb_max_rotation_velocity || 3.0),
                        acceleration: parseFloat(km.acceleration !== undefined ? km.acceleration : 1.15),
                        deceleration: parseFloat(km.deceleration !== undefined ? km.deceleration : 0.5),
                        mouseSensitivity: parseFloat(km.mouse_yaw_sensitivity || 6.0),
                        // Curve parameters - Use !== undefined to correctly handle 0 values
                        linearAlpha: parseFloat(km.linear_alpha !== undefined ? km.linear_alpha : 1.0),
                        linearDeadzone: parseFloat(km.linear_deadzone !== undefined ? km.linear_deadzone : 0.10),
                        strafeAlpha: parseFloat(km.strafe_alpha !== undefined ? km.strafe_alpha : 1.0),
                        strafeDeadzone: parseFloat(km.strafe_deadzone !== undefined ? km.strafe_deadzone : 0.10),
                        rotationAlpha: parseFloat(km.rotation_alpha !== undefined ? km.rotation_alpha : 1.0),
                        rotationDeadzone: parseFloat(km.rotation_deadzone !== undefined ? km.rotation_deadzone : 0.0),
                        // Backend slew rate limiter parameters (acceleration ramp-up time)
                        linearRampTime: parseFloat(km.linear_ramp_time !== undefined ? km.linear_ramp_time : 0.20),
                        strafeRampTime: parseFloat(km.strafe_ramp_time !== undefined ? km.strafe_ramp_time : 0.20),
                        rotationRampTime: parseFloat(km.rotation_ramp_time !== undefined ? km.rotation_ramp_time : 0.20),
                        // Pitch parameters
                        pitchAlpha: parseFloat(km.pitch_alpha !== undefined ? km.pitch_alpha : 1.0),
                        pitchDeadzone: parseFloat(km.pitch_deadzone !== undefined ? km.pitch_deadzone : 0.0),
                        pitchMaxVelocity: parseFloat(km.pitch_max_velocity !== undefined ? km.pitch_max_velocity : 0.30),
                        pitchRampTime: parseFloat(km.pitch_ramp_time !== undefined ? km.pitch_ramp_time : 0.20),
                        mousePitchSensitivity: parseFloat(km.mouse_pitch_sensitivity || 3.0)
                    };
                }
            } catch (e) {
                console.error('❌ [loadSettings] Error parsing unitree_settings:', e);
            }
        }

        // Fallback to old format (from old index.html)
        const oldSettings = localStorage.getItem('keyboardMouseSettings');

        if (oldSettings) {
            try {
                const settings = JSON.parse(oldSettings);

                // IMPORTANT: Don't use keyboard_linear_speed as maxLinear!
                // keyboard_linear_speed is the keyboard multiplier (0.2), not max velocity
                // Use kb_max_linear_velocity instead
                return {
                    maxLinear: parseFloat(settings.kb_max_linear_velocity || settings.maxLinear || 1.5),
                    maxStrafe: parseFloat(settings.kb_max_strafe_velocity || settings.maxStrafe || 1.0),
                    maxRotation: parseFloat(settings.kb_max_rotation_velocity || settings.maxRotation || 3.0),
                    acceleration: parseFloat(settings.acceleration || 0.15),
                    deceleration: parseFloat(settings.deceleration || 0.2),
                    mouseSensitivity: parseFloat(settings.mouse_yaw_sensitivity || settings.mouseSensitivity || 0.5),
                    // Default curve parameters (not in old format)
                    linearAlpha: 1.0,
                    linearDeadzone: 0.10,
                    strafeAlpha: 1.0,
                    strafeDeadzone: 0.10,
                    rotationAlpha: 1.0,
                    rotationDeadzone: 0.0,
                    pitchAlpha: 1.0,
                    pitchDeadzone: 0.0,
                    pitchMaxVelocity: 0.30,
                    pitchRampTime: 0.20,
                    mousePitchSensitivity: 3.0
                };
            } catch (e) {
                console.error('❌ [loadSettings] Error parsing keyboardMouseSettings:', e);
            }
        }

        // Default settings (match "normal" preset from settings-manager.js)
        return {
            maxLinear: 3.0,
            maxStrafe: 1.0,
            maxRotation: 3.0,
            acceleration: 0.15,
            deceleration: 0.2,
            mouseSensitivity: 6.0,
            // Default curve parameters (Normal preset)
            linearAlpha: 1.0,
            linearDeadzone: 0.10,
            strafeAlpha: 1.0,
            strafeDeadzone: 0.10,
            rotationAlpha: 1.0,
            rotationDeadzone: 0.0,
            pitchAlpha: 1.0,
            pitchDeadzone: 0.0,
            pitchMaxVelocity: 0.30,
            pitchRampTime: 0.20,
            mousePitchSensitivity: 3.0
        };
    }

    /**
     * Save settings to localStorage
     */
    saveSettings() {
        localStorage.setItem('keyboardMouseSettings', JSON.stringify(this.settings));
    }

    /**
     * Update settings
     */
    updateSettings(newSettings) {
        this.settings = { ...this.settings, ...newSettings };
        this.saveSettings();
    }

    /**
     * Enable keyboard/mouse control
     */
    async enable() {
        if (this.enabled) return;

        // Enable keyboard/mouse control on backend
        try {
            const response = await fetch('/api/control/keyboard_mouse/enable', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enable: true })
            });

            if (!response.ok) {
                throw new Error('Failed to enable keyboard/mouse control on backend');
            }

            console.log('✅ Keyboard/Mouse control enabled on backend');
        } catch (error) {
            console.error('Error enabling keyboard/mouse control:', error);
            return;
        }

        this.enabled = true;
        console.log('✅ Keyboard/Mouse control enabled (frontend)');

        // Start polling
        this.pollingInterval = setInterval(() => this.poll(), this.POLL_RATE);

        // Add event listeners
        this.addEventListeners();
    }

    /**
     * Disable keyboard/mouse control
     */
    disable() {
        if (!this.enabled) return;

        this.enabled = false;
        console.log('❌ Keyboard/Mouse control disabled');

        // Stop polling
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }

        // Remove event listeners
        this.removeEventListeners();

        // Exit pointer lock
        if (this.pointerLocked) {
            document.exitPointerLock();
        }

        // Reset state
        this.keysPressed = {};
        this.mouseMovement = { x: 0, y: 0 };
        this.currentVelocities = { linear: 0.0, strafe: 0.0, rotation: 0.0, pitch: 0.0 };
        this.poseAngles = { yaw: 0, pitch: 0 };
    }

    /**
     * Add event listeners
     */
    addEventListeners() {
        document.addEventListener('keydown', this.handleKeyDown);
        document.addEventListener('keyup', this.handleKeyUp);
        document.addEventListener('pointerlockchange', this.handlePointerLockChange);
        document.addEventListener('mousemove', this.handleMouseMove);
        document.addEventListener('mousedown', this.handleMouseDown);
        document.addEventListener('wheel', this.handleMouseWheel, { passive: false });

        // Request pointer lock when clicking on video feed
        const videoFeed = document.getElementById('video-feed');
        if (videoFeed) {
            videoFeed.addEventListener('click', this.requestPointerLock);
            console.log('✅ Pointer Lock click listener attached to video feed');
        } else {
            console.error('❌ Video feed element not found (id="video-feed")');
        }
    }

    /**
     * Remove event listeners
     */
    removeEventListeners() {
        document.removeEventListener('keydown', this.handleKeyDown);
        document.removeEventListener('keyup', this.handleKeyUp);
        document.removeEventListener('pointerlockchange', this.handlePointerLockChange);
        document.removeEventListener('mousemove', this.handleMouseMove);
        document.removeEventListener('mousedown', this.handleMouseDown);
        document.removeEventListener('wheel', this.handleMouseWheel);

        const videoFeed = document.getElementById('video-feed');
        if (videoFeed) {
            videoFeed.removeEventListener('click', this.requestPointerLock);
        }
    }

    /**
     * Request pointer lock
     */
    requestPointerLock = () => {
        if (!this.enabled) {
            console.warn('Pointer Lock requested but keyboard/mouse control is disabled');
            return;
        }
        console.log('Requesting Pointer Lock...');
        document.body.requestPointerLock();
    }

    /**
     * Handle pointer lock change
     */
    handlePointerLockChange = () => {
        this.pointerLocked = document.pointerLockElement === document.body;

        if (this.pointerLocked) {
            console.log('Pointer locked - mouse control active');
        } else {
            console.log('Pointer unlocked - mouse control inactive');
            this.mouseMovement = { x: 0, y: 0 };
        }
    }

    /**
     * Handle key down
     */
    handleKeyDown = (e) => {
        if (!this.enabled) return;

        // Ignore if typing in input field
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        const key = e.key.toLowerCase();

        // Prevent default for control keys
        if (['w', 'a', 's', 'd', 'q', 'e', 'r', ' ', 'escape', 'arrowleft', 'arrowright', 'shift'].includes(key)) {
            e.preventDefault();
        }

        this.keysPressed[key] = true;

        // Debug logging for WASD keys
        if (['w', 'a', 's', 'd'].includes(key)) {
            console.log(`[KB] Key pressed: ${key.toUpperCase()}`);
        }

        // Handle Shift key for Precision Mode
        if (key === 'shift') {
            // Guard against keydown repeat events
            if (e.repeat) return;
            // Only activate when pointer is locked
            if (!this.pointerLocked) return;

            if (!this.precisionMode) {
                this.precisionMode = true;

                // Store current speed before switching to precision mode
                this.speedBeforeShift = this.speedPercentage;

                // Set speed to 25% for precision control
                this.speedPercentage = 25;

                // Update speed slider UI
                const speedSlider = document.getElementById('speed-slider');
                const speedPercentageDisplay = document.getElementById('speed-percentage');
                if (speedSlider) {
                    speedSlider.value = 25;
                }
                if (speedPercentageDisplay) {
                    speedPercentageDisplay.textContent = '25%';
                }

                // Show visual feedback
                this.showSpeedIndicator(25);

                console.log(`🎯 [PRECISION MODE] Activated - Speed reduced to 25% (was ${this.speedBeforeShift}%)`);
            }
        }

        // Handle action keys (non-movement)
        if (e.key === ' ') {
            // SPACE: Hold-to-activate Pose Mode
            // Guard against keydown repeat events (held keys fire repeated keydown)
            if (e.repeat) return;
            if (!this.poseMode) {
                this.poseMode = true;
                this.handleAction('enter_pose_mode');
                console.log('🎯 [POSE MODE] Entering - SPACE held');
                this.updatePoseModeIndicator(true);
            }
        } else if (key === 'escape') {
            // ESC: Emergency stop (relocated from SPACE)
            this.handleAction('emergency_stop');
            // If in pose mode, also exit it
            if (this.poseMode) {
                this.poseMode = false;
                this.poseAngles = { yaw: 0, pitch: 0 };
                this.handleAction('exit_pose_mode');
                console.log('🛑 [POSE MODE] Emergency exit via ESC');
                this.updatePoseModeIndicator(false);
            }
        } else if (key === 'e') {
            this.handleAction('stand_up');
        } else if (key === 'q') {
            this.handleAction('crouch');
        } else if (key === 'r') {
            this.handleAction('toggle_lidar');
        // Height adjustment disabled - BodyHeight API (1013) returns code 3203 in AI mode
        // } else if (key === 'arrowup' && !this.poseMode) {
        //     if (e.repeat) return;
        //     this.handleHeightAction('increase_height');
        // } else if (key === 'arrowdown' && !this.poseMode) {
        //     if (e.repeat) return;
        //     this.handleHeightAction('decrease_height');
        }
    }

    /**
     * Handle key up
     */
    handleKeyUp = (e) => {
        if (!this.enabled) return;

        const key = e.key.toLowerCase();
        this.keysPressed[key] = false;

        // Shift release: Exit Precision Mode
        if (key === 'shift' && this.precisionMode) {
            this.precisionMode = false;

            // Restore previous speed
            const restoredSpeed = this.speedBeforeShift !== null ? this.speedBeforeShift : 100;
            this.speedPercentage = restoredSpeed;
            this.speedBeforeShift = null;

            // Update speed slider UI
            const speedSlider = document.getElementById('speed-slider');
            const speedPercentageDisplay = document.getElementById('speed-percentage');
            if (speedSlider) {
                speedSlider.value = restoredSpeed;
            }
            if (speedPercentageDisplay) {
                speedPercentageDisplay.textContent = `${restoredSpeed}%`;
            }

            // Show visual feedback
            this.showSpeedIndicator(restoredSpeed);

            console.log(`🎯 [PRECISION MODE] Deactivated - Speed restored to ${restoredSpeed}%`);
        }

        // SPACE release: Exit Pose Mode
        if (e.key === ' ' && this.poseMode) {
            this.poseMode = false;
            this.poseAngles = { yaw: 0, pitch: 0 };
            this.handleAction('exit_pose_mode');
            console.log('🎯 [POSE MODE] Exiting - SPACE released');
            this.updatePoseModeIndicator(false);
        }
    }

    /**
     * Handle mouse movement
     */
    handleMouseMove = (e) => {
        if (!this.enabled || !this.pointerLocked) return;

        this.mouseMovement.x += e.movementX;
        this.mouseMovement.y += e.movementY;
    }

    /**
     * Handle mouse button clicks
     */
    handleMouseDown = (e) => {
        // Only respond to left mouse button (button 0)
        if (e.button !== 0) return;

        // Check that keyboard/mouse control is enabled
        if (!this.enabled) return;

        // Check that pointer lock is active
        if (!this.pointerLocked) return;

        // Prevent default action
        e.preventDefault();

        // Send "Hello" action (wave gesture)
        this.handleAction('hello');
        console.log('🖱️ Left mouse click - sending Hello gesture');
    }

    /**
     * Handle action commands (emergency stop, stand up, etc.)
     */
    async handleAction(action) {
        try {
            const response = await fetch('/api/control/action', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action })
            });

            if (!response.ok) {
                console.error('Action failed:', action);
            } else {
                console.log('Action sent:', action);
            }
        } catch (error) {
            console.error('Error sending action:', error);
        }
    }

    // Height adjustment disabled - BodyHeight API (1013) returns code 3203 in AI mode
    // async handleHeightAction(action) { ... }
    // showHeightIndicator(level, name) { ... }

    /**
     * Apply deadzone to value
     */
    applyDeadzone(value) {
        return Math.abs(value) < this.DEADZONE ? 0 : value;
    }

    /**
     * Poll keyboard/mouse state and send commands
     */
    poll() {
        if (!this.enabled) return;
        if (this.commandInFlight) return;

        // Re-read settings from localStorage on every tick so slider changes apply immediately
        this.settings = this.loadSettings();

        // ═══════════════════════════════════════════════════════════════════════
        // POSE MODE: Mixed position/velocity control
        // Mouse yaw/pitch: ACCUMULATED position — robot holds angle when mouse stops
        // WASD roll/height: VELOCITY (spring-back) — returns to 0 when keys released
        // Speed slider scales mouse sensitivity for precision control.
        // ═══════════════════════════════════════════════════════════════════════
        if (this.poseMode) {
            // Require pointer lock for Pose Mode control
            if (!this.pointerLocked) return;

            // Speed slider scales mouse sensitivity (lower speed = more precise)
            const speedMultiplier = this.speedPercentage / 100;

            // --- Accumulate mouse deltas into yaw/pitch (HOLD position) ---
            if (this.mouseMovement.x !== 0) {
                // Mouse right (positive pixels) → increase yaw
                this.poseAngles.yaw += this.mouseMovement.x * this.POSE_MOUSE_SENSITIVITY * speedMultiplier;
                this.mouseMovement.x = 0;
            }
            if (this.mouseMovement.y !== 0) {
                // Mouse up (negative pixels) → increase pitch
                this.poseAngles.pitch += this.mouseMovement.y * this.POSE_MOUSE_SENSITIVITY * speedMultiplier;
                this.mouseMovement.y = 0;
            }

            // --- WASD: Velocity-style (spring-back to 0 when released) ---
            let roll = 0;
            let height = 0;
            if (this.keysPressed['a']) roll -= this.POSE_KEY_RATE;
            if (this.keysPressed['d']) roll += this.POSE_KEY_RATE;
            if (this.keysPressed['w']) height += this.POSE_KEY_RATE;
            if (this.keysPressed['s']) height -= this.POSE_KEY_RATE;

            // --- Clamp accumulated angles to [-1, 1] ---
            this.poseAngles.yaw   = Math.max(-1, Math.min(1, this.poseAngles.yaw));
            this.poseAngles.pitch = Math.max(-1, Math.min(1, this.poseAngles.pitch));

            // Debug logging (only when values are non-zero)
            const hasValue = Math.abs(this.poseAngles.yaw) > 0.001 || Math.abs(this.poseAngles.pitch) > 0.001
                          || Math.abs(roll) > 0.001 || Math.abs(height) > 0.001;
            if (hasValue) {
                console.log(`🎯 [POSE] yaw=${this.poseAngles.yaw.toFixed(3)}, pitch=${this.poseAngles.pitch.toFixed(3)}, roll=${roll.toFixed(3)}, height=${height.toFixed(3)}`);
            }

            // Send: accumulated yaw/pitch + velocity roll/height
            // WirelessController Pose Mode axis mapping:
            //   lx = roll, ly = height, rx = yaw, ry = pitch
            if (this.onCommandSend) {
                const commandData = {
                    lx: roll,                    // Velocity (spring-back)
                    ly: height,                  // Velocity (spring-back)
                    rx: this.poseAngles.yaw,     // Accumulated (hold position)
                    ry: this.poseAngles.pitch,   // Accumulated (hold position)
                    pose_mode: true,   // Flag: bypass backend velocity pipeline
                    source: 'keyboard_mouse'
                };
                this.onCommandSend(commandData);
                this.commandInFlight = false;
            }
            return;  // Skip normal velocity pipeline
        }

        // ═══════════════════════════════════════════════════════════════════════
        // NORMAL AI MODE: Velocity-based control (existing pipeline)
        // Require pointer lock for all movement commands
        // ═══════════════════════════════════════════════════════════════════════
        if (!this.pointerLocked) return;

        // Calculate movement from keyboard
        let forward = 0;
        let strafe = 0;

        if (this.keysPressed['w']) forward += 1;
        if (this.keysPressed['s']) forward -= 1;
        // Note: A/D keys use negative/positive here, but will be inverted later to match backend expectations
        if (this.keysPressed['a']) strafe -= 1;  // A key = strafe left (negative)
        if (this.keysPressed['d']) strafe += 1;  // D key = strafe right (positive)

        // Calculate rotation from mouse (horizontal movement)
        let rotation = 0;
        if (this.pointerLocked && this.mouseMovement.x !== 0) {
            // CRITICAL: Scale raw pixel movement to normalized range for curve input
            // Old interface used 0.08 scale factor for instant responsive rotation
            // Example: 50 pixels * 0.08 * 0.5 sensitivity = 2.0 → clamped to 1.0 (max rotation)
            //          100 pixels * 0.08 * 0.5 sensitivity = 4.0 → clamped to 1.0 (max rotation)
            // Mouse movement is NOT inverted here - will be inverted when sending to backend
            const rawPixels = this.mouseMovement.x;
            // NOTE: Sensitivity is NOT applied here - it's applied post-curve to prevent
            // the [0,1] clamp in applyCurve() from swallowing the sensitivity effect
            rotation = rawPixels * this.MOUSE_SCALE_FACTOR;

            // DIAGNOSTIC LOGGING: Track sensitivity through pipeline (Level 3: Deep Debug)
            if (DEBUG_LEVEL >= 3) {
                console.log(`[SENSITIVITY DEBUG Step 1] Raw Pixels: ${rawPixels}, MOUSE_SCALE_FACTOR: ${this.MOUSE_SCALE_FACTOR}, rotation (pre-curve): ${rotation.toFixed(3)}, mouseSensitivity: ${this.settings.mouseSensitivity} (applied post-curve)`);
            }

            this.mouseMovement.x = 0; // Reset after reading
        }

        // Calculate pitch from mouse (vertical movement)
        let pitch = 0;
        if (this.pointerLocked && this.mouseMovement.y !== 0) {
            // Scale vertical mouse movement to normalized range for curve input
            // Positive mouseMovement.y = mouse moved down → pitch down (negative angle)
            // Negative mouseMovement.y = mouse moved up → pitch up (positive angle)
            const rawPixelsY = this.mouseMovement.y;
            // Invert Y axis: mouse up (negative pixels) = pitch up (positive angle)
            pitch = -rawPixelsY * this.MOUSE_SCALE_FACTOR;

            this.mouseMovement.y = 0; // Reset after reading
        }

        // Apply speed percentage (0-100%) to inputs
        // This represents the percentage along the curve
        const speedMultiplier = this.speedPercentage / 100;
        forward *= speedMultiplier;
        strafe *= speedMultiplier;
        rotation *= speedMultiplier;
        pitch *= speedMultiplier;

        // DIAGNOSTIC LOGGING: Track speed multiplier effect (Level 3: Deep Debug)
        if (DEBUG_LEVEL >= 3 && rotation !== 0) {
            console.log(`[SENSITIVITY DEBUG Step 2] speedPercentage: ${this.speedPercentage}, speedMultiplier: ${speedMultiplier}, rotation (after speed): ${rotation.toFixed(3)}`);
        }

        // RAGE MODE: Bypass all smoothing (curves, ramping, deadzone)
        // Use HARDWARE_LIMITS (absolute max) instead of user's slider settings
        if (this.rageMode) {
            const maxLinear = HARDWARE_LIMITS.linear;     // 5.0 m/s
            const maxStrafe = HARDWARE_LIMITS.strafe;     // 1.0 m/s
            const maxRotation = HARDWARE_LIMITS.rotation; // 3.0 rad/s
            const maxPitch = HARDWARE_LIMITS.pitch;       // 0.35 rad
            // Apply sensitivity post-curve (normalized around 5.0 = "normal" preset for yaw, 2.5 for pitch)
            const sensitivityFactor = this.settings.mouseSensitivity / 5.0;
            const pitchSensitivityFactor = this.settings.mousePitchSensitivity / 2.5;
            const vx = forward * maxLinear;
            const vy = -strafe * maxStrafe;  // Invert strafe
            const vyawRaw = -rotation * maxRotation * sensitivityFactor;
            const vyaw = Math.max(-maxRotation, Math.min(maxRotation, vyawRaw));
            const vpitchRaw = pitch * maxPitch * pitchSensitivityFactor;
            const vpitch = Math.max(-maxPitch, Math.min(maxPitch, vpitchRaw));

            console.log(`🔥 [RAGE MODE] RAW (HW MAX): vx=${vx.toFixed(2)}, vy=${vy.toFixed(2)}, vyaw=${vyaw.toFixed(2)}, vpitch=${vpitch.toFixed(2)}`);
            this.sendCommand(vx, vy, vyaw, vpitch, true);  // Pass rageMode flag
            return;
        }

        // Apply exponential curves to keyboard input, then direct-assign to backend
        // NOTE: Linear/strafe deadzone removed (keyboard is digital), rotation deadzone kept (mouse is analog)
        // NOTE: 'deceleration' no longer destructured — frontend smoothing removed (Option B).
        //        Backend asymmetric slew rate limiter handles all acceleration/deceleration.
        const { maxLinear, maxStrafe, maxRotation,
                linearAlpha, strafeAlpha } = this.settings;
        const linearDeadzone = 0.0;  // Keyboard input - no deadzone needed
        const strafeDeadzone = 0.0;  // Keyboard input - no deadzone needed
        // NOTE: rotationAlpha and rotationDeadzone no longer used — mouse rotation
        // bypasses applyCurve() entirely (Solution 3: Direct Linear Mapping)

        // --- LINEAR: Direct Assignment (Option B - bypasses frontend smoothing) ---
        // Same pattern as strafe: backend asymmetric slew rate limiter handles all physics.
        // Frontend smoothing (ACCEL_FACTOR=0.05) was a 2-second anchor that made
        // linear_ramp_time meaningless. Removing it lets the backend setting work.
        const linearInput = Math.abs(forward);
        const curvedLinear = linearInput > 0
            ? applyLinearCurve(linearInput, linearAlpha, linearDeadzone, maxLinear) * Math.sign(forward)
            : 0;

        // Debug logging for curve output
        if (linearInput > 0.01) {
            console.log(`[applyCurve Linear] input=${linearInput.toFixed(3)}, curved=${curvedLinear.toFixed(3)}, maxLinear=${maxLinear}, alpha=${linearAlpha}, deadzone=${linearDeadzone}`);
        }

        // Direct assignment: send curve output straight to backend
        // No jump-start needed (no slow ramp to overcome)
        // No exponential ramping (backend slew rate limiter handles smoothing)
        if (Math.abs(curvedLinear) > 0.001) {
            this.currentVelocities.linear = curvedLinear;
        } else {
            this.currentVelocities.linear = 0;  // Instant stop on key release
        }

        // --- STRAFE: Direct Assignment (Option B - bypasses frontend smoothing) ---
        // The backend's asymmetric slew rate limiter handles all physics:
        //   - Acceleration: smooth ramp controlled by strafe_ramp_time setting
        //   - Deceleration: instant (FPS convention)
        // Frontend smoothing (ACCEL_FACTOR=0.05) was a 2-second anchor that made
        // strafe_ramp_time meaningless. Removing it lets the backend setting work.
        // See docs/analysis/STRAFE_ANALYSIS.md for full analysis.
        const strafeInput = Math.abs(strafe);
        const curvedStrafe = strafeInput > 0
            ? applyStrafeCurve(strafeInput, strafeAlpha, strafeDeadzone, maxStrafe) * Math.sign(strafe)
            : 0;

        // Direct assignment: send curve output straight to backend
        // No jump-start needed (no slow ramp to overcome)
        // No exponential ramping (backend slew rate limiter handles smoothing)
        if (Math.abs(curvedStrafe) > 0.001) {
            this.currentVelocities.strafe = curvedStrafe;
        } else {
            this.currentVelocities.strafe = 0;  // Instant stop on key release
        }

        // --- MOUSE ROTATION: Direct Linear Mapping (Solution 3 - bypasses applyCurve) ---
        // Fixes: alpha suppression, [0,1] clamp destroying fast flicks, non-proportional scaling
        // See docs/analysis/MOUSE_ROTATION_ANALYSIS.md for full analysis
        //
        // Speed slider acts as "Global Volume Knob":
        //   1. Lowers sensitivity (slope) - mouse must move further for same speed
        //   2. Lowers ceiling (max speed) - even fast flicks hit a lower limit
        //
        // rotation = rawPixels * MOUSE_SCALE_FACTOR * speedMultiplier (from lines 418 + 444)
        // Formula: rotation * mouseSensitivity * maxRotation
        //        = rawPixels * MOUSE_SCALE_FACTOR * speedMultiplier * mouseSensitivity * maxRotation
        let targetRadPerSec = rotation * this.settings.mouseSensitivity * maxRotation;

        // Safety ceiling: speed slider controls the maximum velocity
        const safetyCeiling = maxRotation * speedMultiplier;
        targetRadPerSec = Math.max(-safetyCeiling, Math.min(safetyCeiling, targetRadPerSec));

        // DIAGNOSTIC LOGGING: Track direct linear mapping
        if (Math.abs(rotation) > 0.001) {
            console.log(`[ROTATION Direct Linear] rotation=${rotation.toFixed(4)}, sensitivity=${this.settings.mouseSensitivity}, maxRotation=${maxRotation}, speedMult=${speedMultiplier.toFixed(2)}, target=${targetRadPerSec.toFixed(3)}, ceiling=${safetyCeiling.toFixed(2)}`);
        }

        // Instant assignment - FPS "Call of Duty" style (no momentum/decay)
        // Backend slew rate limiter handles smoothing for the physical robot
        if (Math.abs(targetRadPerSec) > 0.05) {
            this.currentVelocities.rotation = targetRadPerSec;
        } else {
            this.currentVelocities.rotation = 0; // Instant stop
        }

        // Pitch control - apply exponential curve
        const pitchInput = Math.abs(pitch);
        const { pitchAlpha, pitchDeadzone, pitchMaxVelocity, mousePitchSensitivity } = this.settings;

        const curvedPitchRaw = pitchInput > 0
            ? applyPitchCurve(pitchInput, pitchAlpha, pitchDeadzone, pitchMaxVelocity) * Math.sign(pitch)
            : 0;

        // Apply mouse pitch sensitivity as post-curve multiplier (normalized around 2.5 = "normal" preset)
        const pitchSensitivityFactor = mousePitchSensitivity / 2.5;
        const curvedPitch = Math.max(-pitchMaxVelocity, Math.min(pitchMaxVelocity, curvedPitchRaw * pitchSensitivityFactor));
        const targetPitch = curvedPitch;

        // Pitch uses INSTANT response (no ramping) like rotation
        this.currentVelocities.pitch = targetPitch;

        // Invert axes to match backend expectations
        // (matching old interface behavior from templates/index.html lines 2064-2066)
        // NOTE: Deadzone is already applied in applyCurve() functions, no need to apply again
        const vx = this.currentVelocities.linear;
        const vy = -this.currentVelocities.strafe;  // Backend inverts for correct direction
        const vyaw = -this.currentVelocities.rotation;  // Backend inverts for correct direction
        const vpitch = this.currentVelocities.pitch;  // Pitch angle (rad), not inverted

        // Calculate velocity magnitude for debug logging
        const velocityMagnitude = Math.sqrt(vx * vx + vy * vy + vyaw * vyaw);

        // Debug logging (Level 2: Verbose)
        if (DEBUG_LEVEL >= 2 && (velocityMagnitude > 0.01 || Math.abs(vpitch) > 0.01)) {
            console.log(`[KB/Mouse Poll] forward=${forward}, strafe=${strafe}, rotation=${rotation.toFixed(3)}, pitch=${pitch.toFixed(3)} → vx=${vx.toFixed(2)}, vy=${vy.toFixed(2)}, vyaw=${vyaw.toFixed(2)}, vpitch=${vpitch.toFixed(2)}`);
        }

        // CRITICAL: Always send command (even zero velocity) to match old interface behavior
        // This ensures smooth deceleration and immediate stop when keys are released
        this.sendCommand(vx, vy, vyaw, vpitch);

        this.lastVelocityMagnitude = velocityMagnitude;
    }

    /**
     * Send movement command
     */
    sendCommand(vx, vy, vyaw, vpitch = 0, rageMode = false) {
        if (this.onCommandSend) {
            // CRITICAL: Normalize velocities and pre-invert axes to match backend expectations
            // Backend inverts lx and rx, so we pre-invert them here
            // In RAGE MODE: use hardware limits for normalization and max values
            const maxLinear = rageMode ? HARDWARE_LIMITS.linear : this.settings.maxLinear;
            const maxStrafe = rageMode ? HARDWARE_LIMITS.strafe : this.settings.maxStrafe;
            const maxRotation = rageMode ? HARDWARE_LIMITS.rotation : this.settings.maxRotation;
            const maxPitch = rageMode ? HARDWARE_LIMITS.pitch : this.settings.pitchMaxVelocity;

            const lx = maxStrafe > 0 ? -vy / maxStrafe : 0;  // Backend inverts, so we pre-invert
            const ly = maxLinear > 0 ? vx / maxLinear : 0;
            const rx = maxRotation > 0 ? -vyaw / maxRotation : 0;  // Backend inverts, so we pre-invert
            const ry = maxPitch > 0 ? vpitch / maxPitch : 0;  // Pitch angle (normalized)

            // DIAGNOSTIC LOGGING: Track normalization (Level 3: Deep Debug)
            if (DEBUG_LEVEL >= 3 && Math.abs(vyaw) > 0.01) {
                console.log(`[SENSITIVITY DEBUG Step 4] vyaw (before norm): ${vyaw.toFixed(3)}, maxRotation: ${maxRotation}, rx (normalized): ${rx.toFixed(3)}`);
            }

            const commandData = {
                lx, ly, rx, ry,
                max_linear: maxLinear,
                max_strafe: maxStrafe,
                max_rotation: maxRotation,
                max_pitch: maxPitch,
                // Backend slew rate limiter parameters (acceleration ramp-up time)
                linear_ramp_time: this.settings.linearRampTime || 0.20,
                strafe_ramp_time: this.settings.strafeRampTime || 0.20,
                rotation_ramp_time: this.settings.rotationRampTime || 0.20,
                pitch_ramp_time: this.settings.pitchRampTime || 0.20,
                // RAGE MODE flag (bypasses backend slew rate limiter)
                rage_mode: rageMode,
                source: 'keyboard_mouse'
            };

            // Enhanced debug logging (Level 2: Verbose)
            if (DEBUG_LEVEL >= 2 && (Math.abs(vx) > 0.01 || Math.abs(vy) > 0.01 || Math.abs(vyaw) > 0.01)) {
                console.log(`[sendCommand] vx=${vx.toFixed(3)}, vy=${vy.toFixed(3)}, vyaw=${vyaw.toFixed(3)} → Normalized: ly=${ly.toFixed(3)}, lx=${lx.toFixed(3)}, rx=${rx.toFixed(3)} | max_linear=${maxLinear}, max_rotation=${maxRotation}`);
            }
            this.onCommandSend(commandData);

            // CRITICAL: Don't block on WebSocket - reset flag immediately (matches old interface)
            this.commandInFlight = false;
        } else {
            console.error('[KB/Mouse] onCommandSend callback not set!');
        }
    }

    /**
     * Handle mouse wheel for speed adjustment
     */
    handleMouseWheel = (e) => {
        // Only respond when keyboard/mouse control is enabled AND pointer is locked
        if (!this.enabled || !this.pointerLocked) return;

        e.preventDefault();  // Prevent page scroll

        // Calculate new speed percentage (wheel up = increase, wheel down = decrease)
        let newSpeed;
        if (e.deltaY < 0) {
            // Wheel up - increase speed
            newSpeed = Math.min(this.MAX_SPEED, this.speedPercentage + this.WHEEL_STEP);
        } else {
            // Wheel down - decrease speed
            newSpeed = Math.max(this.MIN_SPEED, this.speedPercentage - this.WHEEL_STEP);
        }

        // Update internal speed percentage
        this.speedPercentage = newSpeed;

        // Update speed slider UI if it exists
        const speedSlider = document.getElementById('speed-slider');
        const speedPercentageDisplay = document.getElementById('speed-percentage');
        if (speedSlider) {
            speedSlider.value = newSpeed;
        }
        if (speedPercentageDisplay) {
            speedPercentageDisplay.textContent = `${newSpeed}%`;
        }

        // Show visual feedback
        this.showSpeedIndicator(newSpeed);

        console.log(`🎡 Mouse wheel speed adjustment: ${newSpeed}% (input percentage along curve)`);
    }

    /**
     * Show speed indicator overlay
     */
    showSpeedIndicator(speedPercentage) {
        const indicator = document.getElementById('speedIndicator');
        const speedValue = document.getElementById('speedValue');

        if (!indicator || !speedValue) return;

        // Update display (speedPercentage is already 0-100)
        speedValue.textContent = `${speedPercentage}%`;
        indicator.style.display = 'block';

        // Auto-hide after 2 seconds
        clearTimeout(this.speedIndicatorTimeout);
        this.speedIndicatorTimeout = setTimeout(() => {
            indicator.style.display = 'none';
        }, 2000);
    }

    /**
     * Set speed percentage from external source (e.g., speed slider)
     */
    setSpeedPercentage(percentage) {
        this.speedPercentage = Math.max(this.MIN_SPEED, Math.min(this.MAX_SPEED, percentage));
        console.log(`🎚️ Speed set to ${this.speedPercentage}% (input percentage along curve)`);
    }

    /**
     * Toggle RAGE MODE (bypasses all smoothing for raw control)
     */
    toggleRageMode(enabled) {
        this.rageMode = enabled;
        console.log(`🔥 RAGE MODE ${enabled ? 'ENABLED' : 'DISABLED'}`);

        // Update UI (SVG element is the button now)
        const btn = document.getElementById('rage-mode-btn');
        const iconPath = document.getElementById('rage-mode-icon');
        if (btn) {
            if (enabled) {
                if (iconPath) iconPath.setAttribute('fill', '#ef4444');  // Red
                btn.style.filter = 'drop-shadow(0 0 8px rgba(239, 68, 68, 0.6))';  // Red glow
            } else {
                if (iconPath) iconPath.setAttribute('fill', '#00E8DA');  // Teal
                btn.style.filter = 'drop-shadow(0 0 2px black)';  // Default shadow
            }
        }
    }

    /**
     * Update Pose Mode visual indicator on HUD
     * Changes the running human icon to a standing human icon (green) when active.
     */
    updatePoseModeIndicator(active) {
        const iconPath = document.getElementById('rage-mode-icon');
        const iconSvg = document.getElementById('rage-mode-btn');
        if (!iconPath || !iconSvg) return;

        // Standing person SVG path (pose mode active)
        const STANDING_PERSON_PATH = 'M130.914,61.404c16.928,0,30.701-13.771,30.701-30.699C161.615,13.774,147.842,0,130.914,0c-16.93,0-30.703,13.774-30.703,30.705C100.211,47.633,113.984,61.404,130.914,61.404z M130.914,15c8.657,0,15.701,7.045,15.701,15.705c0,8.656-7.044,15.699-15.701,15.699c-8.659,0-15.703-7.043-15.703-15.699C115.211,22.045,122.255,15,130.914,15z M142.779,68.914h-23.54c-16.518,0-29.956,13.439-29.956,29.959v50.484c0,9.509,4.495,18.307,11.966,23.924v81.238c0,4.143,3.358,7.5,7.5,7.5c4.142,0,7.5-3.357,7.5-7.5v-85.316c0-2.879-1.623-5.376-4.003-6.633c-4.912-2.623-7.963-7.684-7.963-13.213V98.873c0-8.248,6.709-14.959,14.956-14.959h23.54c8.248,0,14.957,6.711,14.957,14.959v50.484c0,5.53-3.054,10.592-7.971,13.216c-2.377,1.258-3.998,3.753-3.998,6.63v85.316c0,4.143,3.358,7.5,7.5,7.5c4.142,0,7.5-3.357,7.5-7.5V173.28c7.473-5.616,11.969-14.415,11.969-23.923V98.873C172.736,82.354,159.298,68.914,142.779,68.914z';
        // Running person SVG path (normal mode)
        const RUNNING_PERSON_PATH = 'M13,2 C14.6569,2 16,3.34315 16,5 C16,6.4374176 14.989097,7.6387305 13.6394248,7.93171628 L13.469,7.96356 L14.9049,10.261 L16.6286,9.57152 C17.1414,9.36641 17.7234,9.61583 17.9285,10.1286 C18.11895,10.6047714 17.9175097,11.1406102 17.4771844,11.3789437 L17.3714,11.4285 L15.6477,12.118 C14.8018647,12.4562588 13.842291,12.1788775 13.3046353,11.4607677 L13.2089,11.321 L13.0463,11.0609 L12.4403,13.4851 C12.38606,13.7019 12.298348,13.901548 12.184076,14.0798456 L12.0935,14.2095 L13.7468,15.4376 C14.1430667,15.732 14.4146519,16.161037 14.5132351,16.640361 L14.542,16.8223 L14.895,20 L15,20 C15.5523,20 16,20.4477 16,21 C16,21.51285 15.613973,21.9355092 15.1166239,21.9932725 L15,22 L14.0895,22 C13.5690357,22 13.1258286,21.63665 13.0156081,21.1386974 L12.9962,21.0215 L12.5542,17.0431 L9.40368,14.7028 C9.34671,14.6605 9.29553,14.6132 9.2503,14.5621 C8.69851333,14.1200733 8.40463653,13.4019044 8.52705735,12.6715052 L8.55972,12.5149 L9.35399,9.33783 L7.78454,9.80867 L6.94868,12.3162 C6.77404,12.8402 6.20772,13.1233 5.68377,12.9487 C5.19725429,12.7864786 4.9183499,12.286602 5.0208232,11.7965551 L5.05132,11.6838 L5.88717,9.17621 C6.07583833,8.61019583 6.50617896,8.16078701 7.05678434,7.94576318 L7.20984,7.89302 L10.6474,6.86174 C10.2421,6.3502 10,5.70337 10,5 C10,3.34315 11.3431,2 13,2 Z M8.2,15.4 C8.53137,14.9582 9.15817,14.8686 9.6,15.2 C10.0078154,15.5059077 10.1155314,16.0635172 9.86903487,16.4949808 L9.8,16.6 L8.5838,18.2216 C8.13599375,18.8186938 7.32402148,18.990309 6.67848165,18.6455613 L6.55175,18.5697 L4.62197,17.2832 C4.22939,17.5957 3.65616,17.5704 3.29289,17.2071 C2.93241,16.8466385 2.90468077,16.2793793 3.20970231,15.8871027 L3.29289,15.7929 L3.7871,15.2987 C4.09658182,14.9892455 4.56555124,14.9173942 4.94922239,15.107564 L5.06152,15.1725 L7.26759,16.6432 L8.2,15.4 Z M13,4 C12.4477,4 12,4.44772 12,5 C12,5.55228 12.4477,6 13,6 C13.5523,6 14,5.55228 14,5 C14,4.44772 13.5523,4 13,4 Z';

        if (active) {
            // Switch to standing person icon — green
            iconPath.setAttribute('d', STANDING_PERSON_PATH);
            iconPath.setAttribute('fill', '#00E8DA');
            iconPath.setAttribute('stroke', '#00E8DA');
            iconPath.setAttribute('stroke-width', '10');
            iconPath.setAttribute('stroke-linecap', 'round');
            iconPath.setAttribute('stroke-linejoin', 'round');
            iconSvg.setAttribute('viewBox', '0 0 262.02 262.02');
            iconSvg.style.filter = 'drop-shadow(0 0 6px rgba(34, 197, 94, 0.5))';
            iconSvg.title = 'POSE MODE ACTIVE — Release SPACE to exit';
        } else {
            // Restore running person icon
            iconPath.setAttribute('d', RUNNING_PERSON_PATH);
            iconPath.removeAttribute('stroke');
            iconPath.removeAttribute('stroke-width');
            iconPath.removeAttribute('stroke-linecap');
            iconPath.removeAttribute('stroke-linejoin');
            iconSvg.setAttribute('viewBox', '0 0 24 24');
            iconSvg.title = 'RAGE MODE: Bypass all smoothing for raw control (DANGEROUS!)';

            // Restore RAGE MODE visual state if active, otherwise restore normal state
            if (this.rageMode) {
                // RAGE MODE is active - restore red color and glow
                iconPath.setAttribute('fill', '#ef4444');  // Red
                iconSvg.style.filter = 'drop-shadow(0 0 8px rgba(239, 68, 68, 0.6))';  // Red glow
            } else {
                // Normal mode - restore teal color and default shadow
                iconPath.setAttribute('fill', '#00E8DA');  // Teal
                iconSvg.style.filter = 'drop-shadow(0 0 2px black)';  // Default shadow
            }
        }
    }
}

// Export singleton instance
const keyboardMouseControl = new KeyboardMouseControl();

