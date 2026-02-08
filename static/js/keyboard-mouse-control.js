/**
 * Keyboard & Mouse Control Module
 * Handles WASD keyboard movement and mouse rotation via Pointer Lock API
 */

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

        // Jump-start behavior constants (fixes "wait-then-jump" deadzone-ramping conflict)
        // When a key is first pressed, snap to minimum viable speed for immediate feedback
        // This bypasses the deadzone wait and provides instant visual response
        this.MIN_START_SPEED = 0.15;  // 15% - instant jump-start velocity
        this.ACCEL_FACTOR = 0.05;     // Lower = smoother ramp (tune this)

        // Speed indicator timeout
        this.speedIndicatorTimeout = null;

        // RAGE MODE flag (bypasses all smoothing)
        this.rageMode = false;

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
                        mouseSensitivity: parseFloat(km.mouse_yaw_sensitivity || 0.5),
                        // Curve parameters - Use !== undefined to correctly handle 0 values
                        linearAlpha: parseFloat(km.linear_alpha !== undefined ? km.linear_alpha : 1.5),
                        linearDeadzone: parseFloat(km.linear_deadzone !== undefined ? km.linear_deadzone : 0.10),
                        strafeAlpha: parseFloat(km.strafe_alpha !== undefined ? km.strafe_alpha : 1.2),
                        strafeDeadzone: parseFloat(km.strafe_deadzone !== undefined ? km.strafe_deadzone : 0.10),
                        rotationAlpha: parseFloat(km.rotation_alpha !== undefined ? km.rotation_alpha : 2.5),
                        rotationDeadzone: parseFloat(km.rotation_deadzone !== undefined ? km.rotation_deadzone : 0.10),
                        // Backend slew rate limiter parameters (acceleration ramp-up time)
                        linearRampTime: parseFloat(km.linear_ramp_time !== undefined ? km.linear_ramp_time : 1.0),
                        strafeRampTime: parseFloat(km.strafe_ramp_time !== undefined ? km.strafe_ramp_time : 0.2),
                        rotationRampTime: parseFloat(km.rotation_ramp_time !== undefined ? km.rotation_ramp_time : 0.9),
                        // Pitch parameters
                        pitchAlpha: parseFloat(km.pitch_alpha !== undefined ? km.pitch_alpha : 2.0),
                        pitchDeadzone: parseFloat(km.pitch_deadzone !== undefined ? km.pitch_deadzone : 0.10),
                        pitchMaxVelocity: parseFloat(km.pitch_max_velocity !== undefined ? km.pitch_max_velocity : 0.35),
                        pitchRampTime: parseFloat(km.pitch_ramp_time !== undefined ? km.pitch_ramp_time : 0.8),
                        mousePitchSensitivity: parseFloat(km.mouse_pitch_sensitivity || 2.5)
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
                    maxStrafe: parseFloat(settings.kb_max_strafe_velocity || settings.maxStrafe || 0.6),
                    maxRotation: parseFloat(settings.kb_max_rotation_velocity || settings.maxRotation || 3.0),
                    acceleration: parseFloat(settings.acceleration || 0.15),
                    deceleration: parseFloat(settings.deceleration || 0.2),
                    mouseSensitivity: parseFloat(settings.mouse_yaw_sensitivity || settings.mouseSensitivity || 0.5),
                    // Default curve parameters (not in old format)
                    linearAlpha: 1.5,
                    linearDeadzone: 0.10,
                    strafeAlpha: 1.2,
                    strafeDeadzone: 0.10,
                    rotationAlpha: 2.5,
                    rotationDeadzone: 0.10,
                    pitchAlpha: 2.0,
                    pitchDeadzone: 0.10,
                    pitchMaxVelocity: 0.35,
                    pitchRampTime: 0.8,
                    mousePitchSensitivity: 2.5
                };
            } catch (e) {
                console.error('❌ [loadSettings] Error parsing keyboardMouseSettings:', e);
            }
        }

        // Default settings (match "normal" preset from settings-manager.js)
        return {
            maxLinear: 1.5,
            maxStrafe: 0.6,  // Fixed: hardware limit
            maxRotation: 3.0,
            acceleration: 0.15,
            deceleration: 0.2,
            mouseSensitivity: 0.5,
            // Default curve parameters (Normal preset)
            linearAlpha: 1.5,
            linearDeadzone: 0.10,
            strafeAlpha: 1.2,
            strafeDeadzone: 0.10,
            rotationAlpha: 2.5,
            rotationDeadzone: 0.10,
            pitchAlpha: 2.0,
            pitchDeadzone: 0.10,
            pitchMaxVelocity: 0.35,
            pitchRampTime: 0.8,
            mousePitchSensitivity: 2.5
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
    }

    /**
     * Add event listeners
     */
    addEventListeners() {
        document.addEventListener('keydown', this.handleKeyDown);
        document.addEventListener('keyup', this.handleKeyUp);
        document.addEventListener('pointerlockchange', this.handlePointerLockChange);
        document.addEventListener('mousemove', this.handleMouseMove);
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
        if (['w', 'a', 's', 'd', 'q', 'e', 'r', ' ', 'arrowleft', 'arrowright'].includes(key)) {
            e.preventDefault();
        }

        this.keysPressed[key] = true;

        // Debug logging for WASD keys
        if (['w', 'a', 's', 'd'].includes(key)) {
            console.log(`[KB] Key pressed: ${key.toUpperCase()}`);
        }

        // Handle action keys (non-movement)
        if (e.key === ' ') {
            this.handleAction('emergency_stop');
        } else if (key === 'e') {
            this.handleAction('stand_up');
        } else if (key === 'q') {
            this.handleAction('crouch');
        } else if (key === 'r') {
            this.handleAction('toggle_lidar');
        }
    }

    /**
     * Handle key up
     */
    handleKeyUp = (e) => {
        if (!this.enabled) return;

        const key = e.key.toLowerCase();
        this.keysPressed[key] = false;
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

            // DIAGNOSTIC LOGGING: Track sensitivity through pipeline
            console.log(`[SENSITIVITY DEBUG Step 1] Raw Pixels: ${rawPixels}, MOUSE_SCALE_FACTOR: ${this.MOUSE_SCALE_FACTOR}, rotation (pre-curve): ${rotation.toFixed(3)}, mouseSensitivity: ${this.settings.mouseSensitivity} (applied post-curve)`);

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

        // DIAGNOSTIC LOGGING: Track speed multiplier effect (Task 35.1)
        if (rotation !== 0) {
            console.log(`[SENSITIVITY DEBUG Step 2] speedPercentage: ${this.speedPercentage}, speedMultiplier: ${speedMultiplier}, rotation (after speed): ${rotation.toFixed(3)}`);
        }

        // RAGE MODE: Bypass all smoothing (curves, ramping, deadzone)
        if (this.rageMode) {
            const { maxLinear, maxStrafe, maxRotation, pitchMaxVelocity } = this.settings;
            // Apply sensitivity post-curve (normalized around 5.0 = "normal" preset for yaw, 2.5 for pitch)
            const sensitivityFactor = this.settings.mouseSensitivity / 5.0;
            const pitchSensitivityFactor = this.settings.mousePitchSensitivity / 2.5;
            const vx = forward * maxLinear;
            const vy = -strafe * maxStrafe;  // Invert strafe
            const vyawRaw = -rotation * maxRotation * sensitivityFactor;
            const vyaw = Math.max(-maxRotation, Math.min(maxRotation, vyawRaw));
            const vpitchRaw = pitch * pitchMaxVelocity * pitchSensitivityFactor;
            const vpitch = Math.max(-pitchMaxVelocity, Math.min(pitchMaxVelocity, vpitchRaw));

            console.log(`🔥 [RAGE MODE] RAW: vx=${vx.toFixed(2)}, vy=${vy.toFixed(2)}, vyaw=${vyaw.toFixed(2)}, vpitch=${vpitch.toFixed(2)}`);
            this.sendCommand(vx, vy, vyaw, vpitch, true);  // Pass rageMode flag
            return;
        }

        // Apply velocity ramping (smooth acceleration/deceleration) with exponential curves
        // NOTE: Linear/strafe deadzone removed (keyboard is digital), rotation deadzone kept (mouse is analog)
        const { maxLinear, maxStrafe, maxRotation, deceleration,
                linearAlpha, strafeAlpha } = this.settings;
        const linearDeadzone = 0.0;  // Keyboard input - no deadzone needed
        const strafeDeadzone = 0.0;  // Keyboard input - no deadzone needed
        // NOTE: rotationAlpha and rotationDeadzone no longer used — mouse rotation
        // bypasses applyCurve() entirely (Solution 3: Direct Linear Mapping)

        // Linear velocity (forward/backward) - apply exponential curve
        // Convert input (-1 to 1) to absolute percentage (0 to 1), apply curve, then restore sign
        const linearInput = Math.abs(forward);
        const curvedLinear = linearInput > 0
            ? applyLinearCurve(linearInput, linearAlpha, linearDeadzone, maxLinear) * Math.sign(forward)
            : 0;
        const targetLinear = curvedLinear;

        // Debug logging for curve output
        if (linearInput > 0.01) {
            console.log(`[applyCurve Linear] input=${linearInput.toFixed(3)}, curved=${curvedLinear.toFixed(3)}, maxLinear=${maxLinear}, alpha=${linearAlpha}, deadzone=${linearDeadzone}`);
        }

        // Jump-start logic: When starting from standstill, snap to minimum viable speed
        // This fixes the "wait-then-jump" deadzone-ramping conflict
        // CRITICAL: Jump-start velocity must be a PERCENTAGE of maxLinear, not absolute value
        // Before: W key → 0.0 → 0.005 (blocked by deadzone) → 0.009 (blocked) → 0.011 (move!) = 500ms delay
        // After: W key → snap to 15% of maxLinear (move immediately!) → ramp to 100% = 0ms delay
        if (Math.abs(targetLinear) > 0.001 && Math.abs(this.currentVelocities.linear) < 0.001) {
            // Jump-start: snap to minimum viable speed (percentage of max velocity)
            // Example: maxLinear=3.0 → 0.15*3.0 = 0.45 m/s, maxLinear=5.0 → 0.15*5.0 = 0.75 m/s
            this.currentVelocities.linear = Math.sign(targetLinear) * this.MIN_START_SPEED * maxLinear;
            console.log(`🚀 [Jump-Start Linear] Snapped to ${this.currentVelocities.linear.toFixed(3)} (${(this.MIN_START_SPEED*100).toFixed(0)}% of ${maxLinear})`);
        }

        // Apply exponential ramping (smooth acceleration/deceleration)
        if (Math.abs(targetLinear) > 0.01) {
            this.currentVelocities.linear += (targetLinear - this.currentVelocities.linear) * this.ACCEL_FACTOR;
        } else {
            this.currentVelocities.linear *= (1 - deceleration);
            // Snap to zero when below threshold to prevent infinite tiny values (e.g. 1e-214)
            if (Math.abs(this.currentVelocities.linear) < 0.001) this.currentVelocities.linear = 0;
        }

        // Strafe velocity (left/right) - apply exponential curve
        const strafeInput = Math.abs(strafe);
        const curvedStrafe = strafeInput > 0
            ? applyStrafeCurve(strafeInput, strafeAlpha, strafeDeadzone, maxStrafe) * Math.sign(strafe)
            : 0;
        const targetStrafe = curvedStrafe;

        // Jump-start logic for strafe (same as linear - percentage of max velocity)
        if (Math.abs(targetStrafe) > 0.001 && Math.abs(this.currentVelocities.strafe) < 0.001) {
            this.currentVelocities.strafe = Math.sign(targetStrafe) * this.MIN_START_SPEED * maxStrafe;
            console.log(`🚀 [Jump-Start Strafe] Snapped to ${this.currentVelocities.strafe.toFixed(3)} (${(this.MIN_START_SPEED*100).toFixed(0)}% of ${maxStrafe})`);
        }

        // Apply exponential ramping
        if (Math.abs(targetStrafe) > 0.01) {
            this.currentVelocities.strafe += (targetStrafe - this.currentVelocities.strafe) * this.ACCEL_FACTOR;
        } else {
            this.currentVelocities.strafe *= (1 - deceleration);
            // Snap to zero when below threshold to prevent infinite tiny values (e.g. 1e-214)
            if (Math.abs(this.currentVelocities.strafe) < 0.001) this.currentVelocities.strafe = 0;
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

        // Debug logging (only when there's movement)
        if (velocityMagnitude > 0.01 || Math.abs(vpitch) > 0.01) {
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
            const { maxLinear, maxStrafe, maxRotation, pitchMaxVelocity } = this.settings;

            const lx = maxStrafe > 0 ? -vy / maxStrafe : 0;  // Backend inverts, so we pre-invert
            const ly = maxLinear > 0 ? vx / maxLinear : 0;
            const rx = maxRotation > 0 ? -vyaw / maxRotation : 0;  // Backend inverts, so we pre-invert
            const ry = pitchMaxVelocity > 0 ? vpitch / pitchMaxVelocity : 0;  // Pitch angle (normalized)

            // DIAGNOSTIC LOGGING: Track normalization (Task 35.3)
            if (Math.abs(vyaw) > 0.01) {
                console.log(`[SENSITIVITY DEBUG Step 4] vyaw (before norm): ${vyaw.toFixed(3)}, maxRotation: ${maxRotation}, rx (normalized): ${rx.toFixed(3)}`);
            }

            const commandData = {
                lx, ly, rx, ry,
                max_linear: maxLinear,
                max_strafe: maxStrafe,
                max_rotation: maxRotation,
                max_pitch: pitchMaxVelocity,
                // Backend slew rate limiter parameters (acceleration ramp-up time)
                linear_ramp_time: this.settings.linearRampTime || 1.0,
                strafe_ramp_time: this.settings.strafeRampTime || 0.2,
                rotation_ramp_time: this.settings.rotationRampTime || 0.9,
                pitch_ramp_time: this.settings.pitchRampTime || 0.8,
                // RAGE MODE flag (bypasses backend slew rate limiter)
                rage_mode: rageMode,
                source: 'keyboard_mouse'
            };

            // Enhanced debug logging
            if (Math.abs(vx) > 0.01 || Math.abs(vy) > 0.01 || Math.abs(vyaw) > 0.01) {
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
        if (btn) {
            if (enabled) {
                btn.style.color = '#ef4444';  // Red
                btn.style.filter = 'drop-shadow(0 0 8px rgba(239, 68, 68, 0.6))';  // Red glow
            } else {
                btn.style.color = '#00E8DA';  // Teal (matches other HUD icons)
                btn.style.filter = 'drop-shadow(0 0 2px black)';  // Default shadow
            }
        }
    }
}

// Export singleton instance
const keyboardMouseControl = new KeyboardMouseControl();

