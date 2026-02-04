/**
 * Control Interface JavaScript
 * Handles fullscreen video, status HUD, light control, and exit functionality
 */

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Control page loaded');

    // Initialize WebSocket client
    initializeWebSocket();

    // Initialize control modules
    initializeControlModules();

    // Initialize exit button
    initializeExitButton();

    // Initialize quick settings button
    initializeQuickSettingsButton();

    // Initialize light level slider
    initializeLightSlider();

    // Initialize status polling
    initializeStatusPolling();

    // Initialize latency display
    initializeLatencyDisplay();
});

/**
 * Initialize exit button
 */
function initializeExitButton() {
    const exitBtn = document.getElementById('exit-btn');

    if (exitBtn) {
        exitBtn.addEventListener('click', async () => {
            console.log('Exit button clicked');

            if (confirm('Are you sure you want to disconnect and return to the dashboard?')) {
                try {
                    console.log('Disconnecting from robot...');

                    // Disable keyboard/mouse control
                    if (typeof keyboardMouseControl !== 'undefined') {
                        keyboardMouseControl.disable();
                    }

                    // Disable gamepad control
                    if (typeof gamepadControl !== 'undefined') {
                        await gamepadControl.disable();
                    }

                    // Call disconnect API
                    const response = await fetch('/api/disconnect', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });

                    const data = await response.json();

                    if (data.status === 'success') {
                        console.log('✅ Disconnected successfully');
                        // Redirect to landing page
                        window.location.href = '/';
                    } else {
                        console.error('❌ Disconnect failed:', data.message);
                        alert('Failed to disconnect: ' + data.message);
                    }

                } catch (error) {
                    console.error('❌ Disconnect error:', error);
                    alert('Error disconnecting from robot: ' + error.message);
                }
            }
        });
    }
}

/**
 * Initialize quick settings button
 */
function initializeQuickSettingsButton() {
    const quickSettingsBtn = document.getElementById('quick-settings-btn');
    
    if (quickSettingsBtn) {
        quickSettingsBtn.addEventListener('click', () => {
            console.log('Quick settings button clicked');
            // Modal functionality will be added in later task
            alert('Quick settings modal will be implemented in a later task');
        });
    }
}

/**
 * Initialize light level slider with keyboard controls
 */
function initializeLightSlider() {
    const lightSlider = document.getElementById('light-level-slider');
    const lightValue = document.getElementById('light-level-value');
    const lightIcon = document.getElementById('light-icon');

    if (!lightSlider || !lightValue) return;

    // Current brightness level (0-10)
    let currentBrightness = parseInt(lightSlider.value);

    /**
     * Update display text to show brightness level
     */
    function updateDisplay(level) {
        lightValue.textContent = `${level}`;
        currentBrightness = level;
    }

    /**
     * Send brightness level to robot via API
     */
    async function setBrightness(level) {
        console.log(`Setting light level to ${level}/10`);

        try {
            const response = await fetch('/api/robot/light', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ level: level })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                console.log(`✓ Light level set to ${data.level}/10`);
                // Visual feedback - brief highlight
                if (lightIcon) {
                    lightIcon.classList.add('scale-125');
                    setTimeout(() => {
                        lightIcon.classList.remove('scale-125');
                    }, 200);
                }
            } else {
                console.error('Failed to set light level:', data.message);
            }
        } catch (error) {
            console.error('Error setting light level:', error);
        }
    }

    // Update display value in real-time as user drags slider
    lightSlider.addEventListener('input', (e) => {
        const level = parseInt(e.target.value);
        updateDisplay(level);
    });

    // Send API request when user releases slider (debounced)
    let debounceTimer;
    lightSlider.addEventListener('change', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            const level = parseInt(e.target.value);
            setBrightness(level);
        }, 300);
    });

    // Keyboard controls: Left/Right arrow keys
    document.addEventListener('keydown', (e) => {
        // Only handle arrow keys if not typing in an input field
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        let newLevel = currentBrightness;

        if (e.key === 'ArrowRight') {
            // Increment brightness (max 10)
            e.preventDefault();
            newLevel = Math.min(currentBrightness + 1, 10);
        } else if (e.key === 'ArrowLeft') {
            // Decrement brightness (min 0)
            e.preventDefault();
            newLevel = Math.max(currentBrightness - 1, 0);
        } else {
            return; // Not an arrow key we care about
        }

        // Update slider position and display
        lightSlider.value = newLevel;
        updateDisplay(newLevel);

        // Send API request immediately (no debounce for keyboard)
        setBrightness(newLevel);
    });

    // Initialize display
    updateDisplay(currentBrightness);
}

/**
 * Initialize status polling
 * Fetches robot status every 2 seconds and updates HUD
 */
function initializeStatusPolling() {
    // Fetch status immediately on load
    fetchRobotStatus();

    // Poll status every 2 seconds
    setInterval(fetchRobotStatus, 2000);
}

/**
 * Fetch robot status from API and update HUD
 */
async function fetchRobotStatus() {
    try {
        const response = await fetch('/api/robot/status');
        const data = await response.json();

        if (response.ok && data.connected) {
            // Update HUD elements
            document.getElementById('battery-level').textContent = `${data.battery}%`;
            document.getElementById('ping-value').textContent = `${data.ping} ms`;
            // Mode display temporarily disabled - investigating LF_SPORT_MOD_STATE subscription
            // document.getElementById('robot-mode').textContent = data.mode;

            // Update battery color based on level
            updateBatteryColor(data.battery);
        } else {
            console.error('Failed to fetch robot status:', data.message);
            // Show disconnected state
            handleDisconnectedState();
        }
    } catch (error) {
        console.error('Status polling error:', error);
        // Show disconnected state on network error
        handleDisconnectedState();
    }
}

/**
 * Update battery icon color based on battery level
 */
function updateBatteryColor(batteryLevel) {
    const batteryIcon = document.querySelector('.battery-icon');
    if (!batteryIcon) return;

    // Remove existing color classes
    batteryIcon.classList.remove('text-green-400', 'text-yellow-400', 'text-red-400');

    // Add color based on battery level
    if (batteryLevel > 50) {
        batteryIcon.classList.add('text-green-400');
    } else if (batteryLevel > 20) {
        batteryIcon.classList.add('text-yellow-400');
    } else {
        batteryIcon.classList.add('text-red-400');
    }
}

/**
 * Handle disconnected state - show error indicators
 */
function handleDisconnectedState() {
    document.getElementById('battery-level').textContent = '--';
    document.getElementById('ping-value').textContent = '-- ms';
    // Mode display is temporarily disabled
    // document.getElementById('robot-mode').textContent = 'Disconnected';
}

/**
 * Initialize WebSocket client
 */
function initializeWebSocket() {
    if (typeof websocketClient === 'undefined') {
        console.error('WebSocket client module not loaded');
        return;
    }

    websocketClient.initialize();

    // Set latency update callback
    websocketClient.onLatencyUpdate = (latencyData) => {
        updateLatencyDisplay(latencyData);
    };

    console.log('✅ WebSocket client initialized');
}

/**
 * Initialize control modules (keyboard/mouse and gamepad)
 */
function initializeControlModules() {
    if (typeof keyboardMouseControl === 'undefined' || typeof gamepadControl === 'undefined') {
        console.error('Control modules not loaded');
        return;
    }

    // Set command send callback for keyboard/mouse control
    keyboardMouseControl.onCommandSend = (commandData) => {
        sendControlCommand(commandData);
    };

    // Set command send callback for gamepad control
    gamepadControl.onCommandSend = (commandData) => {
        sendControlCommand(commandData);
    };

    // Auto-enable keyboard/mouse control on page load
    keyboardMouseControl.enable();

    console.log('✅ Control modules initialized');
}

/**
 * Send control command via WebSocket or HTTP fallback
 */
async function sendControlCommand(commandData) {
    const startTime = performance.now();

    console.log(`[Control.js] Sending command via ${websocketClient.isConnected() ? 'WebSocket' : 'HTTP'}:`, commandData);

    // Try WebSocket first
    if (websocketClient.isConnected()) {
        websocketClient.sendCommand(commandData);
    } else {
        // HTTP fallback
        console.log('[Control.js] WebSocket not connected, using HTTP fallback');
        try {
            const response = await fetch('/api/control/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(commandData)
            });

            const latency = performance.now() - startTime;

            if (response.ok) {
                console.log('[Control.js] HTTP command successful');
                websocketClient.updateLatency(latency, 'HTTP');
            } else {
                console.error('[Control.js] Control command failed:', response.status);
            }
        } catch (error) {
            console.error('[Control.js] Error sending control command:', error);
        }
    }
}

/**
 * Initialize latency display
 */
function initializeLatencyDisplay() {
    // Latency display will be updated via websocketClient.onLatencyUpdate callback
    console.log('✅ Latency display initialized');
}

/**
 * Update latency display with color coding
 */
function updateLatencyDisplay(latencyData) {
    const pingElement = document.getElementById('ping-value');
    if (!pingElement) return;

    const { current, average, method } = latencyData;

    // Update display
    pingElement.textContent = `${Math.round(current)} ms`;

    // Color coding based on latency
    pingElement.classList.remove('text-green-400', 'text-yellow-400', 'text-orange-400', 'text-red-400');

    if (current < 100) {
        pingElement.classList.add('text-green-400');  // Excellent
    } else if (current < 200) {
        pingElement.classList.add('text-yellow-400'); // Good
    } else if (current < 300) {
        pingElement.classList.add('text-orange-400'); // Acceptable
    } else {
        pingElement.classList.add('text-red-400');    // Poor
    }

    console.log(`Latency: ${Math.round(current)}ms (avg: ${Math.round(average)}ms) via ${method}`);
}
