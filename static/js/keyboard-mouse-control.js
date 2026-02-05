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
            rotation: 0.0
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

        // Speed indicator timeout
        this.speedIndicatorTimeout = null;

        // Callbacks
        this.onCommandSend = null; // Callback to send commands
    }

    /**
     * Load settings from localStorage
     */
    loadSettings() {
        console.log('🔧 [loadSettings] Loading settings from localStorage...');

        // Try new settings format first (from landing page settings-manager.js)
        const newSettings = localStorage.getItem('unitree_settings');
        console.log('🔧 [loadSettings] Raw unitree_settings:', newSettings);

        if (newSettings) {
            try {
                const parsed = JSON.parse(newSettings);
                console.log('🔧 [loadSettings] Parsed unitree_settings:', parsed);

                if (parsed.keyboard_mouse) {
                    const km = parsed.keyboard_mouse;
                    const settings = {
                        maxLinear: parseFloat(km.kb_max_linear_velocity || 1.5),
                        maxStrafe: parseFloat(km.kb_max_strafe_velocity || 0.6),
                        maxRotation: parseFloat(km.kb_max_rotation_velocity || 3.0),
                        acceleration: parseFloat(km.acceleration || 0.15),
                        deceleration: parseFloat(km.deceleration || 0.2),
                        mouseSensitivity: parseFloat(km.mouse_yaw_sensitivity || 0.5),
                        // Curve parameters
                        linearAlpha: parseFloat(km.linear_alpha || 1.5),
                        linearDeadzone: parseFloat(km.linear_deadzone || 0.10),
                        strafeAlpha: parseFloat(km.strafe_alpha || 1.2),
                        strafeDeadzone: parseFloat(km.strafe_deadzone || 0.10),
                        rotationAlpha: parseFloat(km.rotation_alpha || 2.5),
                        rotationDeadzone: parseFloat(km.rotation_deadzone || 0.10)
                    };
                    console.log('✅ [loadSettings] Loaded settings from unitree_settings:', settings);
                    return settings;
                }
            } catch (e) {
                console.error('❌ [loadSettings] Error parsing unitree_settings:', e);
            }
        }

        // Fallback to old format (from old index.html)
        console.log('⚠️ [loadSettings] unitree_settings not found, trying old format...');
        const oldSettings = localStorage.getItem('keyboardMouseSettings');
        console.log('🔧 [loadSettings] Raw keyboardMouseSettings:', oldSettings);

        if (oldSettings) {
            try {
                const settings = JSON.parse(oldSettings);
                console.log('🔧 [loadSettings] Parsed keyboardMouseSettings:', settings);

                // IMPORTANT: Don't use keyboard_linear_speed as maxLinear!
                // keyboard_linear_speed is the keyboard multiplier (0.2), not max velocity
                // Use kb_max_linear_velocity instead
                const fallbackSettings = {
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
                    rotationDeadzone: 0.10
                };
                console.log('✅ [loadSettings] Loaded settings from keyboardMouseSettings:', fallbackSettings);
                return fallbackSettings;
            } catch (e) {
                console.error('❌ [loadSettings] Error parsing keyboardMouseSettings:', e);
            }
        }

        // Default settings (match "normal" preset from settings-manager.js)
        console.log('⚠️ [loadSettings] No settings found, using defaults');
        const defaultSettings = {
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
            rotationDeadzone: 0.10
        };
        console.log('✅ [loadSettings] Using default settings:', defaultSettings);
        return defaultSettings;
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
        this.currentVelocities = { linear: 0.0, strafe: 0.0, rotation: 0.0 };
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

        // Calculate movement from keyboard
        let forward = 0;
        let strafe = 0;

        if (this.keysPressed['w']) forward += 1;
        if (this.keysPressed['s']) forward -= 1;
        // Note: A/D keys use negative/positive here, but will be inverted later to match backend expectations
        if (this.keysPressed['a']) strafe -= 1;  // A key = strafe left (negative)
        if (this.keysPressed['d']) strafe += 1;  // D key = strafe right (positive)

        // Calculate rotation from mouse
        let rotation = 0;
        if (this.pointerLocked && this.mouseMovement.x !== 0) {
            // Mouse movement is NOT inverted here - will be inverted when sending to backend
            rotation = this.mouseMovement.x * this.settings.mouseSensitivity;
            this.mouseMovement.x = 0; // Reset after reading
        }

        // Apply speed percentage (0-100%) to inputs
        // This represents the percentage along the curve
        const speedMultiplier = this.speedPercentage / 100;
        forward *= speedMultiplier;
        strafe *= speedMultiplier;
        rotation *= speedMultiplier;

        // Apply velocity ramping (smooth acceleration/deceleration) with exponential curves
        const { maxLinear, maxStrafe, maxRotation, acceleration, deceleration,
                linearAlpha, linearDeadzone, strafeAlpha, strafeDeadzone,
                rotationAlpha, rotationDeadzone } = this.settings;

        // Linear velocity (forward/backward) - apply exponential curve
        // Convert input (-1 to 1) to absolute percentage (0 to 1), apply curve, then restore sign
        const linearInput = Math.abs(forward);
        const curvedLinear = linearInput > 0
            ? applyLinearCurve(linearInput, linearAlpha, linearDeadzone, maxLinear) * Math.sign(forward)
            : 0;
        const targetLinear = curvedLinear;
        if (Math.abs(targetLinear) > 0.01) {
            this.currentVelocities.linear += (targetLinear - this.currentVelocities.linear) * acceleration;
        } else {
            this.currentVelocities.linear *= (1 - deceleration);
        }

        // Strafe velocity (left/right) - apply exponential curve
        const strafeInput = Math.abs(strafe);
        const curvedStrafe = strafeInput > 0
            ? applyStrafeCurve(strafeInput, strafeAlpha, strafeDeadzone, maxStrafe) * Math.sign(strafe)
            : 0;
        const targetStrafe = curvedStrafe;
        if (Math.abs(targetStrafe) > 0.01) {
            this.currentVelocities.strafe += (targetStrafe - this.currentVelocities.strafe) * acceleration;
        } else {
            this.currentVelocities.strafe *= (1 - deceleration);
        }

        // Rotation velocity - apply exponential curve
        const rotationInput = Math.abs(rotation);
        const curvedRotation = rotationInput > 0
            ? applyRotationCurve(rotationInput, rotationAlpha, rotationDeadzone, maxRotation) * Math.sign(rotation)
            : 0;
        const targetRotation = curvedRotation;
        if (Math.abs(targetRotation) > 0.01) {
            this.currentVelocities.rotation += (targetRotation - this.currentVelocities.rotation) * acceleration;
        } else {
            this.currentVelocities.rotation *= (1 - deceleration);
        }

        // Apply deadzone and invert axes to match backend expectations
        // (matching old interface behavior from templates/index.html lines 2064-2066)
        const vx = this.applyDeadzone(this.currentVelocities.linear);
        const vy = -this.applyDeadzone(this.currentVelocities.strafe);  // Backend inverts for correct direction
        const vyaw = -this.applyDeadzone(this.currentVelocities.rotation);  // Backend inverts for correct direction

        // Calculate velocity magnitude for debug logging
        const velocityMagnitude = Math.sqrt(vx * vx + vy * vy + vyaw * vyaw);

        // Debug logging (only when there's movement)
        if (velocityMagnitude > 0.01) {
            console.log(`[KB/Mouse Poll] forward=${forward}, strafe=${strafe}, rotation=${rotation.toFixed(3)} → vx=${vx.toFixed(2)}, vy=${vy.toFixed(2)}, vyaw=${vyaw.toFixed(2)}`);
        }

        // CRITICAL: Always send command (even zero velocity) to match old interface behavior
        // This ensures smooth deceleration and immediate stop when keys are released
        this.sendCommand(vx, vy, vyaw);

        this.lastVelocityMagnitude = velocityMagnitude;
    }

    /**
     * Send movement command
     */
    sendCommand(vx, vy, vyaw) {
        if (this.onCommandSend) {
            // CRITICAL: Normalize velocities and pre-invert axes to match backend expectations
            // Backend inverts lx and rx, so we pre-invert them here
            const { maxLinear, maxStrafe, maxRotation } = this.settings;

            const lx = maxStrafe > 0 ? -vy / maxStrafe : 0;  // Backend inverts, so we pre-invert
            const ly = maxLinear > 0 ? vx / maxLinear : 0;
            const rx = maxRotation > 0 ? -vyaw / maxRotation : 0;  // Backend inverts, so we pre-invert
            const ry = 0;  // Pitch not used for movement

            const commandData = {
                lx, ly, rx, ry,
                max_linear: maxLinear,
                max_strafe: maxStrafe,
                max_rotation: maxRotation,
                source: 'keyboard_mouse'
            };

            console.log(`[KB/Mouse] Sending command: lx=${lx.toFixed(2)}, ly=${ly.toFixed(2)}, rx=${rx.toFixed(2)}, ry=${ry.toFixed(2)}`);
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
}

// Export singleton instance
const keyboardMouseControl = new KeyboardMouseControl();

