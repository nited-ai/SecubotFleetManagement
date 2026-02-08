/**
 * Gamepad Control Module
 * Handles Xbox/PlayStation controller input for robot control
 */

class GamepadControl {
    constructor() {
        this.enabled = false;
        this.gamepadIndex = null;
        this.pollingInterval = null;
        this.lastButtonStates = {};
        this.commandInFlight = false;
        
        // Settings (loaded from localStorage)
        this.settings = this.loadSettings();
        
        // Constants
        this.POLL_RATE = 33; // 30Hz
        this.DEADZONE = 0.1;
        
        // Callbacks
        this.onCommandSend = null; // Callback to send commands
        
        // Add gamepad connection listeners
        this.addConnectionListeners();
    }

    /**
     * Load settings from localStorage
     */
    loadSettings() {
        const saved = localStorage.getItem('gamepadSettings');
        if (saved) {
            return JSON.parse(saved);
        }
        
        // Default settings
        return {
            maxLinear: 0.8,
            maxStrafe: 0.5,
            maxRotation: 1.0,
            invertY: false
        };
    }

    /**
     * Save settings to localStorage
     */
    saveSettings() {
        localStorage.setItem('gamepadSettings', JSON.stringify(this.settings));
    }

    /**
     * Update settings
     */
    updateSettings(newSettings) {
        this.settings = { ...this.settings, ...newSettings };
        this.saveSettings();
    }

    /**
     * Add gamepad connection listeners
     */
    addConnectionListeners() {
        window.addEventListener('gamepadconnected', (e) => {
            console.log('Gamepad connected:', e.gamepad.id);
            this.gamepadIndex = e.gamepad.index;
        });

        window.addEventListener('gamepaddisconnected', (e) => {
            console.log('Gamepad disconnected:', e.gamepad.id);
            if (e.gamepad.index === this.gamepadIndex) {
                this.disable();
                this.gamepadIndex = null;
            }
        });
    }

    /**
     * Enable gamepad control
     */
    async enable() {
        if (this.enabled) return;
        
        // Check if gamepad is connected
        const gamepads = navigator.getGamepads();
        let foundGamepad = false;
        
        for (let i = 0; i < gamepads.length; i++) {
            if (gamepads[i]) {
                this.gamepadIndex = i;
                foundGamepad = true;
                break;
            }
        }
        
        if (!foundGamepad) {
            console.error('No gamepad connected');
            return false;
        }
        
        // Enable gamepad on server
        try {
            const response = await fetch('/api/control/gamepad/enable', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enable: true })
            });
            
            if (!response.ok) {
                throw new Error('Failed to enable gamepad on server');
            }
            
            this.enabled = true;
            console.log('✅ Gamepad control enabled');
            
            // Start polling
            this.pollingInterval = setInterval(() => this.poll(), this.POLL_RATE);
            
            return true;
        } catch (error) {
            console.error('Error enabling gamepad:', error);
            return false;
        }
    }

    /**
     * Disable gamepad control
     */
    async disable() {
        if (!this.enabled) return;
        
        this.enabled = false;
        console.log('❌ Gamepad control disabled');
        
        // Stop polling
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
        
        // Disable gamepad on server
        try {
            await fetch('/api/control/gamepad/enable', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enable: false })
            });
        } catch (error) {
            console.error('Error disabling gamepad:', error);
        }
        
        // Reset state
        this.lastButtonStates = {};
    }

    /**
     * Apply deadzone to value
     */
    applyDeadzone(value) {
        return Math.abs(value) < this.DEADZONE ? 0 : value;
    }

    /**
     * Poll gamepad state and send commands
     */
    poll() {
        if (!this.enabled || this.gamepadIndex === null || this.commandInFlight) return;

        const gamepad = navigator.getGamepads()[this.gamepadIndex];
        if (!gamepad) {
            console.warn('Gamepad disconnected');
            this.disable();
            return;
        }

        // Read analog sticks (Xbox controller layout)
        // Left stick: axes[0] = X (strafe), axes[1] = Y (forward/backward)
        // Right stick: axes[2] = X (rotation), axes[3] = Y (camera pitch - not used)
        let lx = this.applyDeadzone(gamepad.axes[0]);  // Left stick X (strafe)
        let ly = this.applyDeadzone(gamepad.axes[1]);  // Left stick Y (forward/backward)
        let rx = this.applyDeadzone(gamepad.axes[2]);  // Right stick X (rotation)
        let ry = this.applyDeadzone(gamepad.axes[3]);  // Right stick Y (not used)

        // Invert Y axis if setting enabled
        if (this.settings.invertY) {
            ly = -ly;
        }

        // Apply velocity limits from settings
        lx *= this.settings.maxStrafe;
        ly *= this.settings.maxLinear;
        rx *= this.settings.maxRotation;

        // Check if there's any movement
        const velocityMagnitude = Math.sqrt(lx * lx + ly * ly + rx * rx);

        // Send command if there's movement or we need to stop
        if (velocityMagnitude > 0.01 || this.lastVelocityMagnitude > 0.01) {
            this.sendCommand(lx, ly, rx, ry);
        }

        this.lastVelocityMagnitude = velocityMagnitude;

        // Handle button presses
        this.handleButtons(gamepad);

        // Handle triggers for camera control
        this.handleTriggers(gamepad);
    }

    /**
     * Send movement command
     */
    sendCommand(lx, ly, rx, ry) {
        if (this.onCommandSend) {
            this.commandInFlight = true;

            const commandData = {
                lx: lx,
                ly: ly,
                rx: rx,
                ry: ry,
                source: 'gamepad'
            };

            this.onCommandSend(commandData);

            // Reset flag after short delay
            setTimeout(() => {
                this.commandInFlight = false;
            }, 10);
        }
    }

    /**
     * Handle button presses
     */
    handleButtons(gamepad) {
        // Xbox controller button mapping:
        // 0: A, 1: B, 2: X, 3: Y
        // 4: LB, 5: RB, 6: LT, 7: RT
        // 8: Back, 9: Start, 10: L3, 11: R3
        // 12: D-Up, 13: D-Down, 14: D-Left, 15: D-Right

        const buttonActions = {
            0: 'stand_up',        // A button
            1: 'crouch',          // B button
            2: 'hello',           // X button
            3: 'stretch',         // Y button
            4: null,              // LB (reserved)
            5: null,              // RB (reserved)
            8: 'emergency_stop',  // Back button
            9: null,              // Start (reserved)
            12: 'body_height_up', // D-Up
            13: 'body_height_down', // D-Down
        };

        for (const [buttonIndex, action] of Object.entries(buttonActions)) {
            if (action) {
                this.handleButton(gamepad, parseInt(buttonIndex), action);
            }
        }
    }

    /**
     * Handle individual button press
     */
    async handleButton(gamepad, buttonIndex, action) {
        const pressed = gamepad.buttons[buttonIndex].pressed;
        const wasPressed = this.lastButtonStates[buttonIndex] || false;

        // Detect rising edge (button just pressed)
        if (pressed && !wasPressed) {
            console.log('Button pressed:', action);

            try {
                const response = await fetch('/api/control/action', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action })
                });

                if (!response.ok) {
                    console.error('Action failed:', action);
                }
            } catch (error) {
                console.error('Error sending action:', error);
            }
        }

        this.lastButtonStates[buttonIndex] = pressed;
    }

    /**
     * Handle trigger buttons for camera control
     */
    async handleTriggers(gamepad) {
        // LT = button 6, RT = button 7 (or axes 6/7 on some controllers)
        const lt = gamepad.buttons[6]?.value || 0;
        const rt = gamepad.buttons[7]?.value || 0;

        // Calculate camera yaw based on triggers
        const camera_yaw = (rt - lt) * 0.5;

        // Send camera control if triggers are pressed
        if (Math.abs(camera_yaw) > 0.1) {
            try {
                await fetch('/api/control/camera', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ yaw: camera_yaw })
                });
            } catch (error) {
                console.error('Error sending camera command:', error);
            }
        }
    }
}

// Export singleton instance
const gamepadControl = new GamepadControl();

