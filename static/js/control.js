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

    // Initialize speed slider
    initializeSpeedSlider();

    // Initialize RAGE MODE toggle
    initializeRageModeToggle();

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
     * Update display text to show brightness level as percentage
     */
    function updateDisplay(level) {
        lightValue.textContent = `${level * 10}%`;
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
 * Initialize speed slider (connected to mouse wheel control)
 */
function initializeSpeedSlider() {
    const speedSlider = document.getElementById('speed-slider');
    const speedPercentage = document.getElementById('speed-percentage');

    if (!speedSlider || !speedPercentage) return;

    /**
     * Handle speed slider change
     */
    speedSlider.addEventListener('input', (e) => {
        const percentage = parseInt(e.target.value);

        // Update percentage display
        speedPercentage.textContent = `${percentage}%`;

        // Update keyboard/mouse control speed percentage
        if (typeof keyboardMouseControl !== 'undefined' && keyboardMouseControl) {
            keyboardMouseControl.setSpeedPercentage(percentage);
        }
    });

    // Initialize slider to 100% (default speed)
    speedSlider.value = 100;
    speedPercentage.textContent = '100%';

    // Set initial speed in keyboard/mouse control
    if (typeof keyboardMouseControl !== 'undefined' && keyboardMouseControl) {
        keyboardMouseControl.setSpeedPercentage(100);
    }
}

/**
 * Initialize RAGE MODE toggle button
 */
function initializeRageModeToggle() {
    const rageModeBtn = document.getElementById('rage-mode-btn');
    const rageModeModal = document.getElementById('rage-mode-modal');
    const rageModeConfirm = document.getElementById('rage-mode-confirm');
    const rageModeCancel = document.getElementById('rage-mode-cancel');

    // Debug logging
    console.log('🔥 Initializing RAGE MODE toggle...');
    console.log('  - Button found:', !!rageModeBtn);
    console.log('  - Modal found:', !!rageModeModal);
    console.log('  - Confirm button found:', !!rageModeConfirm);
    console.log('  - Cancel button found:', !!rageModeCancel);

    if (!rageModeBtn) {
        console.error('❌ RAGE MODE button not found!');
        return;
    }

    if (!rageModeModal) {
        console.error('❌ RAGE MODE modal not found!');
        return;
    }

    let rageModeEnabled = false;
    let rageModeWarningShown = localStorage.getItem('rage_mode_warning_shown') === 'true';
    console.log('  - Warning already shown:', rageModeWarningShown);

    rageModeBtn.addEventListener('click', (e) => {
        console.log('🔥 RAGE MODE button clicked!');
        console.log('  - Current state:', rageModeEnabled ? 'ENABLED' : 'DISABLED');
        console.log('  - Warning shown:', rageModeWarningShown);

        if (!rageModeEnabled) {
            // Enabling RAGE MODE
            if (!rageModeWarningShown) {
                // Show warning modal on first use
                console.log('  - Showing warning modal...');
                rageModeModal.classList.remove('hidden');
                console.log('  - Modal classes:', rageModeModal.className);
            } else {
                // Already seen warning, enable directly
                console.log('  - Enabling RAGE MODE directly (warning already shown)');
                rageModeEnabled = true;
                if (typeof keyboardMouseControl !== 'undefined' && keyboardMouseControl) {
                    keyboardMouseControl.toggleRageMode(true);
                }
            }
        } else {
            // Disabling RAGE MODE
            console.log('  - Disabling RAGE MODE');
            rageModeEnabled = false;
            if (typeof keyboardMouseControl !== 'undefined' && keyboardMouseControl) {
                keyboardMouseControl.toggleRageMode(false);
            }
        }
    });

    if (rageModeConfirm) {
        rageModeConfirm.addEventListener('click', () => {
            console.log('🔥 RAGE MODE confirmed!');
            rageModeEnabled = true;
            rageModeWarningShown = true;
            localStorage.setItem('rage_mode_warning_shown', 'true');
            rageModeModal.classList.add('hidden');
            if (typeof keyboardMouseControl !== 'undefined' && keyboardMouseControl) {
                keyboardMouseControl.toggleRageMode(true);
            }
        });
    }

    if (rageModeCancel) {
        rageModeCancel.addEventListener('click', () => {
            console.log('🔥 RAGE MODE cancelled');
            rageModeModal.classList.add('hidden');
        });
    }

    console.log('✅ RAGE MODE toggle initialized successfully');
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
            document.getElementById('ping-value').textContent = `${data.ping}`;

            // Update battery fill and color based on level
            updateBatteryDisplay(data.battery);

            // Update WiFi/ping color based on latency
            updatePingDisplay(data.ping);
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
 * Update battery icon fill and color based on battery level
 */
function updateBatteryDisplay(batteryLevel) {
    const batteryIcon = document.getElementById('battery-icon');
    const batteryFill = document.getElementById('battery-fill');
    const batteryText = document.getElementById('battery-level');

    if (!batteryIcon || !batteryFill) return;

    // Calculate fill height (battery is 14px tall internally, from y=5 to y=19)
    const maxHeight = 14;
    const fillHeight = (batteryLevel / 100) * maxHeight;
    const fillY = 5 + (maxHeight - fillHeight); // Start from bottom

    // Update fill dimensions
    batteryFill.setAttribute('height', fillHeight);
    batteryFill.setAttribute('y', fillY);

    // Remove existing color classes from both icon and text
    batteryIcon.classList.remove('battery-high', 'battery-medium', 'battery-low');
    if (batteryText) {
        batteryText.classList.remove('battery-high', 'battery-medium', 'battery-low');
    }

    // Add color class based on battery level to both icon and text
    if (batteryLevel > 50) {
        batteryIcon.classList.add('battery-high');
        if (batteryText) batteryText.classList.add('battery-high');
    } else if (batteryLevel > 20) {
        batteryIcon.classList.add('battery-medium');
        if (batteryText) batteryText.classList.add('battery-medium');
    } else {
        batteryIcon.classList.add('battery-low');
        if (batteryText) batteryText.classList.add('battery-low');
    }
}

/**
 * Update WiFi icon and ping text color based on ping latency
 */
function updatePingDisplay(ping) {
    const wifiIcon = document.getElementById('wifi-icon');
    const pingText = document.getElementById('ping-value');
    if (!wifiIcon) return;

    // Remove existing color classes from both icon and text
    wifiIcon.classList.remove('ping-excellent', 'ping-good', 'ping-fair', 'ping-poor');
    if (pingText) {
        pingText.classList.remove('ping-excellent', 'ping-good', 'ping-fair', 'ping-poor');
    }

    // Add color class based on ping to both icon and text
    if (ping < 100) {
        wifiIcon.classList.add('ping-excellent'); // Green
        if (pingText) pingText.classList.add('ping-excellent');
    } else if (ping < 200) {
        wifiIcon.classList.add('ping-good'); // Yellow
        if (pingText) pingText.classList.add('ping-good');
    } else if (ping < 300) {
        wifiIcon.classList.add('ping-fair'); // Orange
        if (pingText) pingText.classList.add('ping-fair');
    } else {
        wifiIcon.classList.add('ping-poor'); // Red
        if (pingText) pingText.classList.add('ping-poor');
    }
}

/**
 * Handle disconnected state - show error indicators
 */
function handleDisconnectedState() {
    document.getElementById('battery-level').textContent = '--%';
    document.getElementById('ping-value').textContent = '---';

    // Reset battery fill
    const batteryFill = document.getElementById('battery-fill');
    if (batteryFill) {
        batteryFill.setAttribute('height', '0');
    }
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

// ========== AUDIO STREAMING FUNCTIONS ==========
// NOTE: Audio is captured server-side using PyAudio.
// Browser only controls push-to-talk state via SocketIO.

let isTransmitting = false;
let microphoneToggled = false;  // Track if microphone is toggled on via mouse click
let cKeyToggled = false;  // Track if microphone is toggled on via 'C' key
let rightMousePressed = false;  // Track if right mouse button is currently pressed
let audioStreamingEnabled = false;  // Track if user has enabled audio reception

/**
 * Toggle audio RECEPTION (speaker icon) - mute/unmute robot audio playback
 */
async function toggleAudioReception() {
    const enable = !audioStreamingEnabled;

    try {
        const response = await fetch('/api/audio/toggle', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({enable: enable})
        });

        const result = await response.json();

        if (result.status === 'success') {
            audioStreamingEnabled = enable;

            // Update HUD speaker icon
            updateSpeakerIcon(enable);

            // Save preference to localStorage
            localStorage.setItem('audioStreamingEnabled', enable);

            console.log(enable ? '🔊 Audio reception enabled (hearing robot)' : '🔇 Audio reception disabled');
        } else {
            console.error('Failed to toggle audio reception:', result.message);
        }

    } catch (error) {
        console.error('Error toggling audio reception:', error);
    }
}

/**
 * Toggle microphone transmission (mouse click on microphone icon)
 */
function toggleMicrophoneTransmission() {
    microphoneToggled = !microphoneToggled;

    if (microphoneToggled) {
        // Turn on transmission
        cKeyToggled = false;  // Reset C key toggle when using mouse click
        startMicrophone();
        console.log('🎤 Microphone toggled ON (mouse click) - transmitting continuously');
    } else {
        // Turn off transmission (only if right mouse button is not pressed)
        if (!rightMousePressed) {
            stopMicrophone();
            console.log('🎤 Microphone toggled OFF (mouse click)');
        }
    }
}

/**
 * Toggle microphone transmission via 'C' key
 */
function toggleMicrophoneViaCKey() {
    cKeyToggled = !cKeyToggled;

    if (cKeyToggled) {
        // Turn on transmission
        microphoneToggled = false;  // Reset mouse click toggle when using C key
        startMicrophone();
        console.log('🎤 Microphone toggled ON (C key) - transmitting continuously');
    } else {
        // Turn off transmission (only if right mouse button is not pressed)
        if (!rightMousePressed) {
            stopMicrophone();
            console.log('🎤 Microphone toggled OFF (C key)');
        }
    }
}

/**
 * Start transmitting microphone audio
 * Called by: mouse click toggle OR 'C' key press OR right mouse button
 */
function startMicrophone() {
    if (isTransmitting) return;

    // Check if websocketClient is available and has a socket
    if (typeof websocketClient === 'undefined' || !websocketClient.socket) {
        console.error('WebSocket client not initialized - cannot start microphone');
        return;
    }

    isTransmitting = true;
    websocketClient.socket.emit('start_microphone');

    // Update HUD microphone icon
    updateMicrophoneIcon(true);

    console.log('🎤 Microphone transmission started (sending audio to robot)');
}

/**
 * Stop transmitting microphone audio
 * Called by: mouse click toggle OR 'C' key release OR right mouse button release
 */
function stopMicrophone() {
    if (!isTransmitting) return;

    // Check if websocketClient is available and has a socket
    if (typeof websocketClient === 'undefined' || !websocketClient.socket) {
        console.error('WebSocket client not initialized - cannot stop microphone');
        return;
    }

    isTransmitting = false;
    websocketClient.socket.emit('stop_microphone');

    // Update HUD microphone icon
    updateMicrophoneIcon(false);

    console.log('🎤 Microphone transmission stopped');
}

function updateMicrophoneIcon(transmitting) {
    const micIcon = document.getElementById('mic-icon');
    if (!micIcon) return;

    // Remove existing state classes
    micIcon.classList.remove('mic-active', 'mic-inactive');

    // Add appropriate class
    if (transmitting) {
        micIcon.classList.add('mic-active');
    } else {
        micIcon.classList.add('mic-inactive');
    }
}

function updateSpeakerIcon(enabled) {
    const speakerIcon = document.getElementById('speaker-icon');
    if (!speakerIcon) return;

    // Remove existing state classes
    speakerIcon.classList.remove('speaker-active', 'speaker-inactive');

    // Add appropriate class
    if (enabled) {
        speakerIcon.classList.add('speaker-active');
    } else {
        speakerIcon.classList.add('speaker-inactive');
    }
}

// Keyboard event handler for 'C' key toggle
let cKeyLastPressed = 0;  // Track last keydown time to prevent repeated events
const C_KEY_DEBOUNCE = 200;  // 200ms debounce to prevent accidental double-toggles

document.addEventListener('keydown', function(event) {
    // Only handle 'C' key if not in an input field
    if (event.key === 'c' || event.key === 'C') {
        const activeElement = document.activeElement;
        if (activeElement.tagName !== 'INPUT' && activeElement.tagName !== 'TEXTAREA') {
            event.preventDefault();

            // Debounce to prevent repeated keydown events
            const now = Date.now();
            if (now - cKeyLastPressed < C_KEY_DEBOUNCE) return;
            cKeyLastPressed = now;

            // Toggle microphone on/off
            toggleMicrophoneViaCKey();
        }
    }
});

// Right mouse button push-to-talk
document.addEventListener('contextmenu', function(event) {
    // Prevent default context menu
    event.preventDefault();
});

document.addEventListener('mousedown', function(event) {
    // Right mouse button (button 2)
    if (event.button === 2) {
        event.preventDefault();

        // Prevent repeated mousedown events
        if (rightMousePressed) return;

        rightMousePressed = true;
        startMicrophone();
        console.log('🎤 Right mouse button pressed - microphone active (push-to-talk)');
    }
});

document.addEventListener('mouseup', function(event) {
    // Right mouse button (button 2)
    if (event.button === 2) {
        event.preventDefault();

        rightMousePressed = false;

        // Always stop microphone and reset any toggle state when right mouse button is released
        // This provides an "emergency off" functionality
        if (microphoneToggled || cKeyToggled) {
            console.log('🎤 Right mouse button released - canceling toggle and turning OFF');
            microphoneToggled = false;
            cKeyToggled = false;
        } else {
            console.log('🎤 Right mouse button released - microphone inactive');
        }

        stopMicrophone();
    }
});

// Load saved audio streaming preference from localStorage on page load
window.addEventListener('DOMContentLoaded', function() {
    const savedAudioEnabled = localStorage.getItem('audioStreamingEnabled');
    if (savedAudioEnabled !== null) {
        const enable = savedAudioEnabled === 'true';
        audioStreamingEnabled = enable;

        // Update speaker icon to match saved preference
        updateSpeakerIcon(enable);

        console.log(enable ? '✅ Loaded audio preference: ENABLED' : 'ℹ️ Loaded audio preference: DISABLED');

        // Set audio preference on backend
        fetch('/api/audio/toggle', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({enable: enable})
        }).catch(err => console.error('Error setting audio preference:', err));
    }

    // Initialize microphone icon to inactive state
    updateMicrophoneIcon(false);
});
