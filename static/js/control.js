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
 * Initialize quick settings button and slide-in panel
 */
function initializeQuickSettingsButton() {
    const settingsBtn = document.getElementById('quick-settings-btn');
    const settingsPanel = document.getElementById('settings-panel');
    const settingsBackdrop = document.getElementById('settings-backdrop');
    const settingsCloseBtn = document.getElementById('settings-close-btn');

    let settingsPanelInitialized = false;

    function openSettingsPanel() {
        if (!settingsPanel) return;
        settingsPanel.classList.add('open');
        if (settingsBtn) settingsBtn.classList.add('settings-active');

        // Disable keyboard/mouse control while panel is open to prevent robot movement
        if (typeof keyboardMouseControl !== 'undefined' && keyboardMouseControl) {
            keyboardMouseControl.disable();
        }

        // Lazy-initialize settings panel on first open
        if (!settingsPanelInitialized) {
            initializeSettingsPanelControls();
            settingsPanelInitialized = true;
        } else {
            // Refresh slider values from localStorage on re-open
            refreshSettingsPanelValues();
        }
    }

    function closeSettingsPanel() {
        if (!settingsPanel) return;
        settingsPanel.classList.remove('open');
        if (settingsBtn) settingsBtn.classList.remove('settings-active');

        // Re-enable keyboard/mouse control when panel closes
        if (typeof keyboardMouseControl !== 'undefined' && keyboardMouseControl) {
            keyboardMouseControl.enable();
        }
    }

    if (settingsBtn) {
        settingsBtn.addEventListener('click', () => {
            if (settingsPanel && settingsPanel.classList.contains('open')) {
                closeSettingsPanel();
            } else {
                openSettingsPanel();
            }
        });
    }

    if (settingsCloseBtn) {
        settingsCloseBtn.addEventListener('click', closeSettingsPanel);
    }

    if (settingsBackdrop) {
        settingsBackdrop.addEventListener('click', closeSettingsPanel);
    }

    // ESC key closes panel
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && settingsPanel && settingsPanel.classList.contains('open')) {
            closeSettingsPanel();
        }
    });
}

// ===== Settings Panel Controls =====

/**
 * Helper: initialize a single slider with value display and change handler
 */
function initializeSettingsSlider(sliderId, valueId, initialValue, onChange, suffix = '') {
    const slider = document.getElementById(sliderId);
    const valueDisplay = document.getElementById(valueId);

    if (slider && valueDisplay) {
        slider.value = initialValue;
        valueDisplay.textContent = parseFloat(initialValue).toFixed(2) + suffix;

        slider.addEventListener('input', (e) => {
            valueDisplay.textContent = parseFloat(e.target.value).toFixed(2) + suffix;
        });

        slider.addEventListener('change', (e) => {
            onChange(e.target.value);
            updateActivePresetButtonOnControlPage('custom');
        });
    }
}

/**
 * Update active preset button highlight on control page
 */
function updateActivePresetButtonOnControlPage(preset) {
    if (!preset) {
        preset = typeof getCurrentPreset === 'function' ? getCurrentPreset() : 'custom';
    }
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.classList.remove('preset-btn-active');
    });
    const activeButton = document.getElementById(`preset-${preset}`);
    if (activeButton) {
        activeButton.classList.add('preset-btn-active');
    }
}

/**
 * Update all keyboard/mouse sliders on control page with given settings
 */
function updateAllControlPageSliders(km) {
    const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.value = val; };
    const setTxt = (id, txt) => { const el = document.getElementById(id); if (el) el.textContent = txt; };

    setVal('mouse-yaw-sensitivity', km.mouse_yaw_sensitivity);
    setTxt('mouse-yaw-value', km.mouse_yaw_sensitivity.toFixed(2));

    setVal('mouse-pitch-sensitivity', km.mouse_pitch_sensitivity);
    setTxt('mouse-pitch-value', km.mouse_pitch_sensitivity.toFixed(2));

    setVal('kb-max-linear-velocity', km.kb_max_linear_velocity);
    setTxt('kb-max-linear-value', km.kb_max_linear_velocity.toFixed(2) + ' m/s');

    setVal('kb-max-strafe-velocity', km.kb_max_strafe_velocity);
    setTxt('kb-max-strafe-value', km.kb_max_strafe_velocity.toFixed(2) + ' m/s');

    setVal('kb-max-rotation-velocity', km.kb_max_rotation_velocity);
    setTxt('kb-max-rotation-value', km.kb_max_rotation_velocity.toFixed(2) + ' rad/s');

    setVal('linear-alpha', km.linear_alpha);
    setTxt('linear-alpha-value', (km.linear_alpha || 1.5).toFixed(1));

    setVal('strafe-alpha', km.strafe_alpha);
    setTxt('strafe-alpha-value', (km.strafe_alpha || 1.2).toFixed(1));

    setVal('rotation-alpha', km.rotation_alpha);
    setTxt('rotation-alpha-value', (km.rotation_alpha || 2.5).toFixed(1));

    setVal('linear-ramp-time', km.linear_ramp_time);
    setTxt('linear-ramp-time-value', `${(km.linear_ramp_time || 0.20).toFixed(2)}s`);

    setVal('strafe-ramp-time', km.strafe_ramp_time);
    setTxt('strafe-ramp-time-value', `${(km.strafe_ramp_time || 0.20).toFixed(2)}s`);

    setVal('rotation-ramp-time', km.rotation_ramp_time);
    setTxt('rotation-ramp-time-value', `${(km.rotation_ramp_time || 0.20).toFixed(2)}s`);

    // Pitch sliders
    setVal('pitch-max-velocity', km.pitch_max_velocity);
    setTxt('pitch-max-value', (km.pitch_max_velocity || 0.35).toFixed(2) + ' rad');

    setVal('pitch-alpha', km.pitch_alpha);
    setTxt('pitch-alpha-value', (km.pitch_alpha || 2.0).toFixed(1));

    setVal('pitch-ramp-time', km.pitch_ramp_time);
    setTxt('pitch-ramp-time-value', `${(km.pitch_ramp_time || 0.20).toFixed(2)}s`);

    // Update curve charts
    if (charts.linear && charts.strafe && charts.rotation) {
        updateCurveChart(charts.linear, 'Linear', km.linear_alpha, 0.0, km.kb_max_linear_velocity, HARDWARE_LIMITS.linear);
        updateCurveChart(charts.strafe, 'Strafe', km.strafe_alpha, 0.0, km.kb_max_strafe_velocity, HARDWARE_LIMITS.strafe);
        updateCurveChart(charts.rotation, 'Rotation', km.rotation_alpha, 0.0, km.kb_max_rotation_velocity, HARDWARE_LIMITS.rotation);
    }
    if (charts.pitch) {
        updateCurveChart(charts.pitch, 'Pitch', km.pitch_alpha, 0.0, km.pitch_max_velocity, HARDWARE_LIMITS.pitch);
    }
}

/**
 * Refresh panel values from localStorage (called on re-open)
 */
function refreshSettingsPanelValues() {
    const settings = loadSettings();
    updateAllControlPageSliders(settings.keyboard_mouse);
    updateActivePresetButtonOnControlPage();
}

/**
 * Initialize settings panel controls (called once on first panel open)
 * Sets up charts, sliders, presets, and reset button
 */
function initializeSettingsPanelControls() {
    console.log('⚙️ Initializing settings panel controls...');

    const settings = loadSettings();
    const km = settings.keyboard_mouse;

    // --- Create curve charts ---
    charts.linear = createCurveChart('linear-curve-chart', 'Linear', 'm/s',
        km.linear_alpha || 1.5, 0.0, km.kb_max_linear_velocity || 1.5, HARDWARE_LIMITS.linear);
    charts.strafe = createCurveChart('strafe-curve-chart', 'Strafe', 'm/s',
        km.strafe_alpha || 1.2, 0.0, km.kb_max_strafe_velocity || 1.0, HARDWARE_LIMITS.strafe);
    charts.rotation = createCurveChart('rotation-curve-chart', 'Rotation', 'rad/s',
        km.rotation_alpha || 2.5, 0.0, km.kb_max_rotation_velocity || 3.0, HARDWARE_LIMITS.rotation);
    charts.pitch = createCurveChart('pitch-curve-chart', 'Pitch', 'rad',
        km.pitch_alpha || 2.0, 0.0, km.pitch_max_velocity || 0.35, HARDWARE_LIMITS.pitch);

    // --- Helper to get fresh settings ---
    const getFresh = () => loadSettings().keyboard_mouse;

    // --- Velocity sliders ---
    initializeSettingsSlider('mouse-yaw-sensitivity', 'mouse-yaw-value', km.mouse_yaw_sensitivity, (v) => {
        updateSetting('keyboard_mouse', 'mouse_yaw_sensitivity', parseFloat(v));
    });
    initializeSettingsSlider('mouse-pitch-sensitivity', 'mouse-pitch-value', km.mouse_pitch_sensitivity, (v) => {
        updateSetting('keyboard_mouse', 'mouse_pitch_sensitivity', parseFloat(v));
    });
    initializeSettingsSlider('kb-max-linear-velocity', 'kb-max-linear-value', km.kb_max_linear_velocity, (v) => {
        updateSetting('keyboard_mouse', 'kb_max_linear_velocity', parseFloat(v));
        if (charts.linear) {
            const f = getFresh();
            updateCurveChart(charts.linear, 'Linear', f.linear_alpha || 1.5, 0.0, parseFloat(v), HARDWARE_LIMITS.linear);
        }
    }, ' m/s');
    initializeSettingsSlider('kb-max-strafe-velocity', 'kb-max-strafe-value', km.kb_max_strafe_velocity, (v) => {
        updateSetting('keyboard_mouse', 'kb_max_strafe_velocity', parseFloat(v));
        if (charts.strafe) {
            const f = getFresh();
            updateCurveChart(charts.strafe, 'Strafe', f.strafe_alpha || 1.2, 0.0, parseFloat(v), HARDWARE_LIMITS.strafe);
        }
    }, ' m/s');
    initializeSettingsSlider('kb-max-rotation-velocity', 'kb-max-rotation-value', km.kb_max_rotation_velocity, (v) => {
        updateSetting('keyboard_mouse', 'kb_max_rotation_velocity', parseFloat(v));
        if (charts.rotation) {
            const f = getFresh();
            updateCurveChart(charts.rotation, 'Rotation', f.rotation_alpha || 2.5, 0.0, parseFloat(v), HARDWARE_LIMITS.rotation);
        }
    }, ' rad/s');

    // --- Alpha sliders ---
    const linearAlphaSlider = document.getElementById('linear-alpha');
    const linearAlphaValue = document.getElementById('linear-alpha-value');
    if (linearAlphaSlider && linearAlphaValue) {
        linearAlphaSlider.value = km.linear_alpha || 1.5;
        linearAlphaValue.textContent = (km.linear_alpha || 1.5).toFixed(1);
        linearAlphaSlider.addEventListener('input', (e) => {
            const a = parseFloat(e.target.value);
            linearAlphaValue.textContent = a.toFixed(1);
            updateSetting('keyboard_mouse', 'linear_alpha', a);
            const f = getFresh();
            updateCurveChart(charts.linear, 'Linear', a, 0.0, f.kb_max_linear_velocity || 1.5, HARDWARE_LIMITS.linear);
        });
    }

    const strafeAlphaSlider = document.getElementById('strafe-alpha');
    const strafeAlphaValue = document.getElementById('strafe-alpha-value');
    if (strafeAlphaSlider && strafeAlphaValue) {
        strafeAlphaSlider.value = km.strafe_alpha || 1.2;
        strafeAlphaValue.textContent = (km.strafe_alpha || 1.2).toFixed(1);
        strafeAlphaSlider.addEventListener('input', (e) => {
            const a = parseFloat(e.target.value);
            strafeAlphaValue.textContent = a.toFixed(1);
            updateSetting('keyboard_mouse', 'strafe_alpha', a);
            const f = getFresh();
            updateCurveChart(charts.strafe, 'Strafe', a, 0.0, f.kb_max_strafe_velocity || 1.0, HARDWARE_LIMITS.strafe);
        });
    }

    const rotationAlphaSlider = document.getElementById('rotation-alpha');
    const rotationAlphaValue = document.getElementById('rotation-alpha-value');
    if (rotationAlphaSlider && rotationAlphaValue) {
        rotationAlphaSlider.value = km.rotation_alpha || 2.5;
        rotationAlphaValue.textContent = (km.rotation_alpha || 2.5).toFixed(1);
        rotationAlphaSlider.addEventListener('input', (e) => {
            const a = parseFloat(e.target.value);
            rotationAlphaValue.textContent = a.toFixed(1);
            updateSetting('keyboard_mouse', 'rotation_alpha', a);
            const f = getFresh();
            updateCurveChart(charts.rotation, 'Rotation', a, 0.0, f.kb_max_rotation_velocity || 3.0, HARDWARE_LIMITS.rotation);
        });
    }

    // --- Ramp time sliders ---
    const linearRampSlider = document.getElementById('linear-ramp-time');
    const linearRampValue = document.getElementById('linear-ramp-time-value');
    if (linearRampSlider && linearRampValue) {
        linearRampSlider.value = km.linear_ramp_time || 0.20;
        linearRampValue.textContent = `${(km.linear_ramp_time || 0.20).toFixed(2)}s`;
        linearRampSlider.addEventListener('input', (e) => {
            const v = parseFloat(e.target.value);
            linearRampValue.textContent = `${v.toFixed(2)}s`;
            updateSetting('keyboard_mouse', 'linear_ramp_time', v);
        });
    }

    const strafeRampSlider = document.getElementById('strafe-ramp-time');
    const strafeRampValue = document.getElementById('strafe-ramp-time-value');
    if (strafeRampSlider && strafeRampValue) {
        strafeRampSlider.value = km.strafe_ramp_time || 0.20;
        strafeRampValue.textContent = `${(km.strafe_ramp_time || 0.20).toFixed(2)}s`;
        strafeRampSlider.addEventListener('input', (e) => {
            const v = parseFloat(e.target.value);
            strafeRampValue.textContent = `${v.toFixed(2)}s`;
            updateSetting('keyboard_mouse', 'strafe_ramp_time', v);
        });
    }

    const rotRampSlider = document.getElementById('rotation-ramp-time');
    const rotRampValue = document.getElementById('rotation-ramp-time-value');
    if (rotRampSlider && rotRampValue) {
        rotRampSlider.value = km.rotation_ramp_time || 0.20;
        rotRampValue.textContent = `${(km.rotation_ramp_time || 0.20).toFixed(2)}s`;
        rotRampSlider.addEventListener('input', (e) => {
            const v = parseFloat(e.target.value);
            rotRampValue.textContent = `${v.toFixed(2)}s`;
            updateSetting('keyboard_mouse', 'rotation_ramp_time', v);
        });
    }

    // --- Pitch sliders ---
    initializeSettingsSlider('pitch-max-velocity', 'pitch-max-value', km.pitch_max_velocity || 0.35, (v) => {
        updateSetting('keyboard_mouse', 'pitch_max_velocity', parseFloat(v));
        if (charts.pitch) {
            const f = getFresh();
            updateCurveChart(charts.pitch, 'Pitch', f.pitch_alpha || 2.0, 0.0, parseFloat(v), HARDWARE_LIMITS.pitch);
        }
    }, ' rad');

    const pitchAlphaSlider = document.getElementById('pitch-alpha');
    const pitchAlphaValue = document.getElementById('pitch-alpha-value');
    if (pitchAlphaSlider && pitchAlphaValue) {
        pitchAlphaSlider.value = km.pitch_alpha || 2.0;
        pitchAlphaValue.textContent = (km.pitch_alpha || 2.0).toFixed(1);
        pitchAlphaSlider.addEventListener('input', (e) => {
            const a = parseFloat(e.target.value);
            pitchAlphaValue.textContent = a.toFixed(1);
            updateSetting('keyboard_mouse', 'pitch_alpha', a);
            const f = getFresh();
            updateCurveChart(charts.pitch, 'Pitch', a, 0.0, f.pitch_max_velocity || 0.35, HARDWARE_LIMITS.pitch);
        });
    }

    const pitchRampSlider = document.getElementById('pitch-ramp-time');
    const pitchRampValue = document.getElementById('pitch-ramp-time-value');
    if (pitchRampSlider && pitchRampValue) {
        pitchRampSlider.value = km.pitch_ramp_time || 0.20;
        pitchRampValue.textContent = `${(km.pitch_ramp_time || 0.20).toFixed(2)}s`;
        pitchRampSlider.addEventListener('input', (e) => {
            const v = parseFloat(e.target.value);
            pitchRampValue.textContent = `${v.toFixed(2)}s`;
            updateSetting('keyboard_mouse', 'pitch_ramp_time', v);
        });
    }

    // --- Preset buttons ---
    const presetButtons = document.querySelectorAll('.preset-btn');
    updateActivePresetButtonOnControlPage();

    presetButtons.forEach(button => {
        button.addEventListener('click', () => {
            const preset = button.dataset.preset;
            if (preset === 'custom') return;

            if (typeof applyPreset === 'function' && applyPreset(preset)) {
                console.log(`⚙️ Applied ${preset} preset`);
                updateActivePresetButtonOnControlPage(preset);
                const updated = loadSettings();
                updateAllControlPageSliders(updated.keyboard_mouse);
            }
        });
    });

    console.log('✅ Settings panel controls initialized');
}

/**
 * Initialize light level slider with keyboard controls
 */
function initializeLightSlider() {
    const lightSlider = document.getElementById('light-level-slider');
    const lightValue = document.getElementById('light-level-value');
    const lightIconOn = document.getElementById('light-icon-on');
    const lightIconOff = document.getElementById('light-icon-off');

    if (!lightSlider || !lightValue) return;

    // Current brightness level (0-10)
    let currentBrightness = parseInt(lightSlider.value);

    /**
     * Toggle flashlight on/off icons based on brightness level
     */
    function updateLightIcon(level) {
        if (lightIconOn && lightIconOff) {
            if (level > 0) {
                lightIconOn.style.display = '';
                lightIconOff.style.display = 'none';
            } else {
                lightIconOn.style.display = 'none';
                lightIconOff.style.display = '';
            }
        }
    }

    /**
     * Update display text to show brightness level as percentage
     */
    function updateDisplay(level) {
        lightValue.textContent = `${level * 10}%`;
        currentBrightness = level;
        updateLightIcon(level);
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

    // Query current brightness from robot on page load
    async function syncBrightnessFromRobot() {
        try {
            const response = await fetch('/api/robot/light');
            const data = await response.json();

            if (response.ok && data.success) {
                const level = parseInt(data.level);
                console.log(`💡 Synced light level from robot: ${level}/10`);
                lightSlider.value = level;
                updateDisplay(level);
            }
        } catch (error) {
            // Not connected yet or query failed - keep default value
            console.debug('Could not sync light level from robot:', error.message);
        }
    }

    // Sync after a short delay to allow connection to establish
    setTimeout(syncBrightnessFromRobot, 2000);
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

    rageModeBtn.addEventListener('click', (e) => {
        console.log('🔥 RAGE MODE button clicked!');
        console.log('  - Current state:', rageModeEnabled ? 'ENABLED' : 'DISABLED');

        if (!rageModeEnabled) {
            // Enabling RAGE MODE — always show warning modal
            console.log('  - Showing warning modal...');
            rageModeModal.classList.remove('hidden');
            console.log('  - Modal classes:', rageModeModal.className);
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
            document.getElementById('ping-value').textContent = `${data.ping}ms`;

            // Update battery fill and color based on level
            updateBatteryDisplay(data.battery);

            // Update WiFi/ping color based on latency
            updatePingDisplay(data.ping);

            // Update temperature display
            if (data.temperature !== undefined) {
                const tempEl = document.getElementById('temp-value');
                if (tempEl) tempEl.textContent = `${Math.round(data.temperature)}°C`;
                updateTemperatureDisplay(data.temperature);
            }
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
 * Battery rect: x=11, width=2, stroke-width=3 → visible from y=9 (full) to y=17 (empty), max height=8
 */
function updateBatteryDisplay(batteryLevel) {
    const batteryFill = document.getElementById('battery-fill');
    const batteryText = document.getElementById('battery-level');

    if (!batteryFill) return;

    // Calculate fill height (battery inner area: y=9 to y=17, max height=8)
    const maxHeight = 8;
    const fillHeight = Math.max(0.5, (batteryLevel / 100) * maxHeight);
    const fillY = 9 + (maxHeight - fillHeight); // Start from bottom

    // Update fill dimensions
    batteryFill.setAttribute('height', fillHeight);
    batteryFill.setAttribute('y', fillY);

    // Determine color based on battery level
    let color;
    let textClass;
    if (batteryLevel > 50) {
        color = '#10b981'; // Green
        textClass = 'battery-high';
    } else if (batteryLevel > 20) {
        color = '#f59e0b'; // Yellow
        textClass = 'battery-medium';
    } else {
        color = '#ef4444'; // Red
        textClass = 'battery-low';
    }

    // Update fill color directly on SVG element
    batteryFill.setAttribute('fill', color);
    batteryFill.setAttribute('stroke', color);

    // Update text color class
    if (batteryText) {
        batteryText.classList.remove('battery-high', 'battery-medium', 'battery-low');
        batteryText.classList.add(textClass);
    }
}

/**
 * Update WiFi icon wave colors and ping text based on ping latency.
 * Sets fill attribute directly on wave path elements.
 */
function updatePingDisplay(ping) {
    const pingText = document.getElementById('ping-value');
    const wavePaths = document.querySelectorAll('#wifi-icon .wifi-waves path');

    // Determine color based on ping
    let color, textClass;
    if (ping < 100) {
        color = '#10b981'; textClass = 'ping-excellent'; // Green
    } else if (ping < 200) {
        color = '#ffee00'; textClass = 'ping-good';      // Yellow
    } else if (ping < 300) {
        color = '#fb923c'; textClass = 'ping-fair';      // Orange
    } else {
        color = '#ef4444'; textClass = 'ping-poor';      // Red
    }

    // Update wave fill colors directly
    wavePaths.forEach(path => path.setAttribute('fill', color));

    // Update text color class
    if (pingText) {
        pingText.classList.remove('ping-excellent', 'ping-good', 'ping-fair', 'ping-poor');
        pingText.classList.add(textClass);
    }
}

/**
 * Update temperature icon inner fill color and text based on temperature.
 * Sets fill/stroke directly on the inner fill path element.
 */
function updateTemperatureDisplay(temperature) {
    const tempFill = document.getElementById('temp-fill');
    const tempText = document.getElementById('temp-value');

    // Determine color based on temperature
    let color, textClass;
    if (temperature < 50) {
        color = '#10b981'; textClass = 'temp-excellent'; // Green
    } else if (temperature < 65) {
        color = '#ffee00'; textClass = 'temp-good';      // Yellow
    } else if (temperature < 80) {
        color = '#fb923c'; textClass = 'temp-fair';      // Orange
    } else {
        color = '#ef4444'; textClass = 'temp-poor';      // Red
    }

    // Update inner fill color directly
    if (tempFill) {
        tempFill.setAttribute('fill', color);
        tempFill.setAttribute('stroke', color);
    }

    // Update text color class
    if (tempText) {
        tempText.classList.remove('temp-excellent', 'temp-good', 'temp-fair', 'temp-poor');
        tempText.classList.add(textClass);
    }
}

/**
 * Handle disconnected state - show error indicators
 */
function handleDisconnectedState() {
    document.getElementById('battery-level').textContent = '--%';
    document.getElementById('ping-value').textContent = '---';
    const tempEl = document.getElementById('temp-value');
    if (tempEl) tempEl.textContent = '--°C';

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

    // WebSocket latency callback DISABLED to prevent overwriting robot ping display
    // The WebSocket latency (3-6ms) measures browser ↔ server communication only,
    // NOT the actual robot network latency (14-30ms measured server ↔ robot).
    // Only the robot ping from fetchRobotStatus() should update the HUD display.
    // websocketClient.onLatencyUpdate = (latencyData) => {
    //     updateLatencyDisplay(latencyData);
    // };

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

    // High-frequency log (30-60Hz) - commented out to reduce console noise
    // Uncomment for debugging control flow/latency issues
    // console.log(`[Control.js] Sending command via ${websocketClient.isConnected() ? 'WebSocket' : 'HTTP'}:`, commandData);

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
 * Update latency display with color coding.
 * Sets fill directly on WiFi wave paths + text color class.
 */
function updateLatencyDisplay(latencyData) {
    const pingElement = document.getElementById('ping-value');
    if (!pingElement) return;

    const { current } = latencyData;

    // Update display
    pingElement.textContent = `${Math.round(current)}ms`;

    // Determine color based on latency
    let color, textClass;
    if (current < 100) {
        color = '#10b981'; textClass = 'ping-excellent'; // Green
    } else if (current < 200) {
        color = '#ffee00'; textClass = 'ping-good';      // Yellow
    } else if (current < 300) {
        color = '#fb923c'; textClass = 'ping-fair';      // Orange
    } else {
        color = '#ef4444'; textClass = 'ping-poor';      // Red
    }

    // Update wave fill colors directly
    const wavePaths = document.querySelectorAll('#wifi-icon .wifi-waves path');
    wavePaths.forEach(path => path.setAttribute('fill', color));

    // Update text color class
    pingElement.classList.remove('ping-excellent', 'ping-good', 'ping-fair', 'ping-poor');
    pingElement.classList.add(textClass);

    // High-frequency log (30-60Hz) - commented out to reduce console noise
    // Uncomment for debugging control flow/latency issues
    // console.log(`Latency: ${Math.round(current)}ms (avg: ${Math.round(average)}ms) via ${method}`);
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
    const strikethrough = document.getElementById('mic-strikethrough');
    if (!micIcon) return;

    // Toggle button classes for styling
    micIcon.classList.remove('mic-active', 'mic-inactive');
    micIcon.classList.add(transmitting ? 'mic-active' : 'mic-inactive');

    // Show/hide the red strikethrough line
    if (strikethrough) {
        strikethrough.style.display = transmitting ? 'none' : '';
    }
}

function updateSpeakerIcon(enabled) {
    const speakerIcon = document.getElementById('speaker-icon');
    const waveOuter = document.getElementById('speaker-wave-outer');
    const waveInner = document.getElementById('speaker-wave-inner');
    const speakerX = document.getElementById('speaker-x');
    if (!speakerIcon) return;

    // Toggle button classes for styling
    speakerIcon.classList.remove('speaker-active', 'speaker-inactive');
    speakerIcon.classList.add(enabled ? 'speaker-active' : 'speaker-inactive');

    // Show waves + hide X when active, hide waves + show X when inactive
    if (waveOuter) waveOuter.style.display = enabled ? '' : 'none';
    if (waveInner) waveInner.style.display = enabled ? '' : 'none';
    if (speakerX) speakerX.style.display = enabled ? 'none' : '';
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

/**
 * Send robot action command
 */
async function sendRobotAction(action) {
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
 * Toggle Leash Mode (Lead Follow mode)
 */
let leashModeActive = false;

async function toggleLeashMode() {
    try {
        // Send leash_mode action to backend
        const response = await fetch('/api/control/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'leash_mode' })
        });

        if (response.ok) {
            // Toggle state
            leashModeActive = !leashModeActive;

            // Update icon color
            const icon = document.getElementById('leash-mode-icon');
            if (icon) {
                const newColor = leashModeActive ? '#ef4444' : '#00E8DA';
                icon.setAttribute('fill', newColor);
            }

            console.log('Leash Mode toggled:', leashModeActive ? 'ACTIVE' : 'INACTIVE');
        } else {
            console.error('Leash Mode toggle failed');
        }
    } catch (error) {
        console.error('Error toggling Leash Mode:', error);
    }
}
