/**
 * Landing Page JavaScript
 * Handles robot dashboard, add/edit/delete functionality, and settings panel
 */

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Landing page loaded');

    // Initialize settings panel toggle
    initializeSettingsPanel();

    // Initialize preset buttons
    initializePresetButtons();

    // Initialize settings sliders
    initializeSettingsSliders();

    // Initialize add robot button
    initializeAddRobotButton();

    // Initialize modal event listeners
    initializeModalEventListeners();

    // Load and render robot cards
    renderRobotCards();

    // Initialize curve charts
    initializeCurveCharts();
});

/**
 * Initialize collapsible settings panel
 */
function initializeSettingsPanel() {
    const settingsHeader = document.getElementById('settings-header');
    const settingsContent = document.getElementById('settings-content');
    const settingsChevron = document.getElementById('settings-chevron');

    if (settingsHeader && settingsContent && settingsChevron) {
        settingsHeader.addEventListener('click', () => {
            settingsContent.classList.toggle('hidden');
            settingsChevron.classList.toggle('rotate-180');
        });
    }
}

/**
 * Initialize preset buttons
 */
function initializePresetButtons() {
    // Check if settings-manager.js is loaded
    if (typeof applyPreset !== 'function' || typeof getCurrentPreset !== 'function') {
        console.error('settings-manager.js not loaded! Preset buttons will not work.');
        return;
    }

    const presetButtons = document.querySelectorAll('.preset-btn');

    // Set initial active state based on current settings
    updateActivePresetButton();

    // Add click handlers to all preset buttons
    presetButtons.forEach(button => {
        button.addEventListener('click', () => {
            const preset = button.dataset.preset;

            if (preset === 'custom') {
                // Custom preset doesn't apply settings, just shows current state
                return;
            }

            // Apply the preset
            if (applyPreset(preset)) {
                console.log(`Applied ${preset} preset`);

                // Update active button state
                updateActivePresetButton(preset);

                // Reload settings and update all sliders
                const updatedSettings = loadSettings();
                updateAllKeyboardMouseSliders(updatedSettings.keyboard_mouse);
                updateAllGamepadSliders(updatedSettings.gamepad);
            }
        });
    });
}

/**
 * Update active preset button based on current settings
 * @param {string} preset - Optional preset name to set as active
 */
function updateActivePresetButton(preset) {
    if (!preset) {
        // Detect current preset from settings
        preset = typeof getCurrentPreset === 'function' ? getCurrentPreset() : 'custom';
    }

    // Remove active class from all buttons
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.classList.remove('preset-btn-active');
    });

    // Add active class to current preset button
    const activeButton = document.getElementById(`preset-${preset}`);
    if (activeButton) {
        activeButton.classList.add('preset-btn-active');
    }
}

/**
 * Initialize settings sliders and load saved settings
 */
function initializeSettingsSliders() {
    // Check if settings-manager.js is loaded
    if (typeof loadSettings !== 'function') {
        console.error('settings-manager.js not loaded! Settings panel will not work.');
        return;
    }

    // Load settings from LocalStorage
    const settings = loadSettings();

    // Initialize keyboard/mouse sliders
    initializeSlider('mouse-yaw-sensitivity', 'mouse-yaw-value', settings.keyboard_mouse.mouse_yaw_sensitivity, (value) => {
        updateSetting('keyboard_mouse', 'mouse_yaw_sensitivity', parseFloat(value));
    });

    initializeSlider('mouse-pitch-sensitivity', 'mouse-pitch-value', settings.keyboard_mouse.mouse_pitch_sensitivity, (value) => {
        updateSetting('keyboard_mouse', 'mouse_pitch_sensitivity', parseFloat(value));
    });

    initializeSlider('kb-max-linear-velocity', 'kb-max-linear-value', settings.keyboard_mouse.kb_max_linear_velocity, (value) => {
        updateSetting('keyboard_mouse', 'kb_max_linear_velocity', parseFloat(value));
        // Update linear curve chart if it exists
        if (charts && charts.linear) {
            const fresh = loadSettings().keyboard_mouse;
            updateCurveChart(
                charts.linear,
                'Linear',
                fresh.linear_alpha !== undefined ? fresh.linear_alpha : 1.5,
                fresh.linear_deadzone !== undefined ? fresh.linear_deadzone : 0.10,
                parseFloat(value),
                HARDWARE_LIMITS.linear
            );
        }
    }, ' m/s');

    initializeSlider('kb-max-strafe-velocity', 'kb-max-strafe-value', settings.keyboard_mouse.kb_max_strafe_velocity, (value) => {
        updateSetting('keyboard_mouse', 'kb_max_strafe_velocity', parseFloat(value));
        // Update strafe curve chart if it exists
        if (charts && charts.strafe) {
            const fresh = loadSettings().keyboard_mouse;
            updateCurveChart(
                charts.strafe,
                'Strafe',
                fresh.strafe_alpha !== undefined ? fresh.strafe_alpha : 1.2,
                fresh.strafe_deadzone !== undefined ? fresh.strafe_deadzone : 0.10,
                parseFloat(value),
                HARDWARE_LIMITS.strafe
            );
        }
    }, ' m/s');

    initializeSlider('kb-max-rotation-velocity', 'kb-max-rotation-value', settings.keyboard_mouse.kb_max_rotation_velocity, (value) => {
        updateSetting('keyboard_mouse', 'kb_max_rotation_velocity', parseFloat(value));
        // Update rotation curve chart if it exists
        if (charts && charts.rotation) {
            const fresh = loadSettings().keyboard_mouse;
            updateCurveChart(
                charts.rotation,
                'Rotation',
                fresh.rotation_alpha !== undefined ? fresh.rotation_alpha : 2.5,
                fresh.rotation_deadzone !== undefined ? fresh.rotation_deadzone : 0.10,
                parseFloat(value),
                HARDWARE_LIMITS.rotation
            );
        }
    }, ' rad/s');

    // Initialize gamepad sliders
    initializeSlider('deadzone-left-stick', 'deadzone-left-value', settings.gamepad.deadzone_left_stick, (value) => {
        updateSetting('gamepad', 'deadzone_left_stick', parseFloat(value));
    });

    initializeSlider('deadzone-right-stick', 'deadzone-right-value', settings.gamepad.deadzone_right_stick, (value) => {
        updateSetting('gamepad', 'deadzone_right_stick', parseFloat(value));
    });

    initializeSlider('sensitivity-linear', 'sensitivity-linear-value', settings.gamepad.sensitivity_linear, (value) => {
        updateSetting('gamepad', 'sensitivity_linear', parseFloat(value));
    });

    initializeSlider('sensitivity-strafe', 'sensitivity-strafe-value', settings.gamepad.sensitivity_strafe, (value) => {
        updateSetting('gamepad', 'sensitivity_strafe', parseFloat(value));
    });

    initializeSlider('sensitivity-rotation', 'sensitivity-rotation-value', settings.gamepad.sensitivity_rotation, (value) => {
        updateSetting('gamepad', 'sensitivity_rotation', parseFloat(value));
    });

    initializeSlider('speed-multiplier', 'speed-multiplier-value', settings.gamepad.speed_multiplier, (value) => {
        updateSetting('gamepad', 'speed_multiplier', parseFloat(value));
    });

    initializeSlider('gp-max-linear-velocity', 'gp-max-linear-value', settings.gamepad.max_linear_velocity, (value) => {
        updateSetting('gamepad', 'max_linear_velocity', parseFloat(value));
    }, ' m/s');

    initializeSlider('gp-max-strafe-velocity', 'gp-max-strafe-value', settings.gamepad.max_strafe_velocity, (value) => {
        updateSetting('gamepad', 'max_strafe_velocity', parseFloat(value));
    }, ' m/s');

    initializeSlider('gp-max-rotation-velocity', 'gp-max-rotation-value', settings.gamepad.max_rotation_velocity, (value) => {
        updateSetting('gamepad', 'max_rotation_velocity', parseFloat(value));
    }, ' rad/s');

    // Initialize gamepad preset selector
    const presetSelector = document.getElementById('gamepad-preset');
    if (presetSelector) {
        presetSelector.addEventListener('change', (e) => {
            const preset = e.target.value;
            if (preset && applyGamepadPreset(preset)) {
                console.log(`Applied ${preset} preset`);
                // Reload settings to update sliders
                const updatedSettings = loadSettings();
                updateAllGamepadSliders(updatedSettings.gamepad);
                // Reset selector
                e.target.value = '';
            }
        });
    }

    // Initialize reset button
    const resetBtn = document.getElementById('reset-settings-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            if (confirm('Reset all settings to defaults?')) {
                const defaults = resetSettings();
                console.log('Settings reset to defaults');
                // Update all sliders
                updateAllKeyboardMouseSliders(defaults.keyboard_mouse);
                updateAllGamepadSliders(defaults.gamepad);
            }
        });
    }
}

/**
 * Initialize a single slider with value display and change handler
 * @param {string} sliderId - Slider element ID
 * @param {string} valueId - Value display element ID
 * @param {number} initialValue - Initial slider value
 * @param {Function} onChange - Change handler function
 * @param {string} suffix - Optional suffix for display value (e.g., ' m/s')
 */
function initializeSlider(sliderId, valueId, initialValue, onChange, suffix = '') {
    const slider = document.getElementById(sliderId);
    const valueDisplay = document.getElementById(valueId);

    if (slider && valueDisplay) {
        // Set initial value
        slider.value = initialValue;
        valueDisplay.textContent = initialValue.toFixed(2) + suffix;

        // Update display on input
        slider.addEventListener('input', (e) => {
            valueDisplay.textContent = parseFloat(e.target.value).toFixed(2) + suffix;
        });

        // Save on change
        slider.addEventListener('change', (e) => {
            onChange(e.target.value);
            // Switch to custom preset when user manually adjusts a slider
            updateActivePresetButton('custom');
        });
    }
}

/**
 * Update all keyboard/mouse sliders with new values
 * @param {Object} kbMouseSettings - Keyboard/mouse settings object
 */
function updateAllKeyboardMouseSliders(kbMouseSettings) {
    document.getElementById('mouse-yaw-sensitivity').value = kbMouseSettings.mouse_yaw_sensitivity;
    document.getElementById('mouse-yaw-value').textContent = kbMouseSettings.mouse_yaw_sensitivity.toFixed(2);

    document.getElementById('mouse-pitch-sensitivity').value = kbMouseSettings.mouse_pitch_sensitivity;
    document.getElementById('mouse-pitch-value').textContent = kbMouseSettings.mouse_pitch_sensitivity.toFixed(2);

    document.getElementById('kb-max-linear-velocity').value = kbMouseSettings.kb_max_linear_velocity;
    document.getElementById('kb-max-linear-value').textContent = kbMouseSettings.kb_max_linear_velocity.toFixed(2) + ' m/s';

    document.getElementById('kb-max-strafe-velocity').value = kbMouseSettings.kb_max_strafe_velocity;
    document.getElementById('kb-max-strafe-value').textContent = kbMouseSettings.kb_max_strafe_velocity.toFixed(2) + ' m/s';

    document.getElementById('kb-max-rotation-velocity').value = kbMouseSettings.kb_max_rotation_velocity;
    document.getElementById('kb-max-rotation-value').textContent = kbMouseSettings.kb_max_rotation_velocity.toFixed(2) + ' rad/s';

    // Update alpha sliders
    document.getElementById('linear-alpha').value = kbMouseSettings.linear_alpha;
    document.getElementById('linear-alpha-value').textContent = kbMouseSettings.linear_alpha.toFixed(1);

    document.getElementById('strafe-alpha').value = kbMouseSettings.strafe_alpha;
    document.getElementById('strafe-alpha-value').textContent = kbMouseSettings.strafe_alpha.toFixed(1);

    document.getElementById('rotation-alpha').value = kbMouseSettings.rotation_alpha;
    document.getElementById('rotation-alpha-value').textContent = kbMouseSettings.rotation_alpha.toFixed(1);

    // Update deadzone sliders
    const linearDeadzonePercent = Math.round(kbMouseSettings.linear_deadzone * 100);
    document.getElementById('linear-deadzone').value = linearDeadzonePercent;
    document.getElementById('linear-deadzone-value').textContent = linearDeadzonePercent + '%';

    const strafeDeadzonePercent = Math.round(kbMouseSettings.strafe_deadzone * 100);
    document.getElementById('strafe-deadzone').value = strafeDeadzonePercent;
    document.getElementById('strafe-deadzone-value').textContent = strafeDeadzonePercent + '%';

    const rotationDeadzonePercent = Math.round(kbMouseSettings.rotation_deadzone * 100);
    document.getElementById('rotation-deadzone').value = rotationDeadzonePercent;
    document.getElementById('rotation-deadzone-value').textContent = rotationDeadzonePercent + '%';

    // Update curve graphs
    if (typeof charts !== 'undefined' && charts.linear && charts.strafe && charts.rotation) {
        updateCurveChart(
            charts.linear,
            'Linear',
            kbMouseSettings.linear_alpha,
            kbMouseSettings.linear_deadzone,
            kbMouseSettings.kb_max_linear_velocity,
            HARDWARE_LIMITS.linear
        );

        updateCurveChart(
            charts.strafe,
            'Strafe',
            kbMouseSettings.strafe_alpha,
            kbMouseSettings.strafe_deadzone,
            kbMouseSettings.kb_max_strafe_velocity,
            HARDWARE_LIMITS.strafe
        );

        updateCurveChart(
            charts.rotation,
            'Rotation',
            kbMouseSettings.rotation_alpha,
            kbMouseSettings.rotation_deadzone,
            kbMouseSettings.kb_max_rotation_velocity,
            HARDWARE_LIMITS.rotation
        );
    }
}

/**
 * Update all gamepad sliders with new values
 * @param {Object} gamepadSettings - Gamepad settings object
 */
function updateAllGamepadSliders(gamepadSettings) {
    document.getElementById('deadzone-left-stick').value = gamepadSettings.deadzone_left_stick;
    document.getElementById('deadzone-left-value').textContent = gamepadSettings.deadzone_left_stick.toFixed(2);

    document.getElementById('deadzone-right-stick').value = gamepadSettings.deadzone_right_stick;
    document.getElementById('deadzone-right-value').textContent = gamepadSettings.deadzone_right_stick.toFixed(2);

    document.getElementById('sensitivity-linear').value = gamepadSettings.sensitivity_linear;
    document.getElementById('sensitivity-linear-value').textContent = gamepadSettings.sensitivity_linear.toFixed(2);

    document.getElementById('sensitivity-strafe').value = gamepadSettings.sensitivity_strafe;
    document.getElementById('sensitivity-strafe-value').textContent = gamepadSettings.sensitivity_strafe.toFixed(2);

    document.getElementById('sensitivity-rotation').value = gamepadSettings.sensitivity_rotation;
    document.getElementById('sensitivity-rotation-value').textContent = gamepadSettings.sensitivity_rotation.toFixed(2);

    document.getElementById('speed-multiplier').value = gamepadSettings.speed_multiplier;
    document.getElementById('speed-multiplier-value').textContent = gamepadSettings.speed_multiplier.toFixed(2);

    document.getElementById('gp-max-linear-velocity').value = gamepadSettings.max_linear_velocity;
    document.getElementById('gp-max-linear-value').textContent = gamepadSettings.max_linear_velocity.toFixed(2) + ' m/s';

    document.getElementById('gp-max-strafe-velocity').value = gamepadSettings.max_strafe_velocity;
    document.getElementById('gp-max-strafe-value').textContent = gamepadSettings.max_strafe_velocity.toFixed(2) + ' m/s';

    document.getElementById('gp-max-rotation-velocity').value = gamepadSettings.max_rotation_velocity;
    document.getElementById('gp-max-rotation-value').textContent = gamepadSettings.max_rotation_velocity.toFixed(2) + ' rad/s';
}

/**
 * Initialize add robot button
 */
function initializeAddRobotButton() {
    const addRobotBtn = document.getElementById('add-robot-btn');

    if (addRobotBtn) {
        addRobotBtn.addEventListener('click', () => {
            console.log('Add robot button clicked');
            openAddRobotModal();
        });
    }
}

/**
 * Initialize modal event listeners
 */
function initializeModalEventListeners() {
    const modal = document.getElementById('robot-modal');
    const modalOverlay = modal?.querySelector('.modal-overlay');
    const closeBtn = document.getElementById('modal-close-btn');
    const cancelBtn = document.getElementById('modal-cancel-btn');
    const form = document.getElementById('robot-form');
    const connectionMethodSelect = document.getElementById('connection-method');

    // Close modal when clicking overlay
    if (modalOverlay) {
        modalOverlay.addEventListener('click', closeModal);
    }

    // Close modal when clicking close button
    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }

    // Close modal when clicking cancel button
    if (cancelBtn) {
        cancelBtn.addEventListener('click', closeModal);
    }

    // Handle form submission
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }

    // Handle connection method change
    if (connectionMethodSelect) {
        connectionMethodSelect.addEventListener('change', updateConnectionMethodFields);
    }

    // Close modal on Escape key
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && modal && !modal.classList.contains('hidden')) {
            closeModal();
        }
    });
}

/**
 * Render robot cards from LocalStorage
 */
function renderRobotCards() {
    const container = document.getElementById('robot-cards-container');
    if (!container) {
        console.error('Robot cards container not found');
        return;
    }

    // Load robots from LocalStorage
    const robots = loadRobots();

    // Clear container
    container.innerHTML = '';

    // If no robots, show empty state
    if (robots.length === 0) {
        container.innerHTML = `
            <div class="card text-center py-12 col-span-full">
                <p class="text-gray-400">No robots added yet. Click "Add Robot" to get started.</p>
            </div>
        `;
        return;
    }

    // Render each robot card
    robots.forEach(robot => {
        const card = createRobotCard(robot);
        container.appendChild(card);
    });

    console.log(`Rendered ${robots.length} robot card(s)`);
}

/**
 * Create a robot card element
 * @param {Object} robot - Robot object
 * @returns {HTMLElement} Robot card element
 */
function createRobotCard(robot) {
    const card = document.createElement('div');
    card.className = 'card hover:shadow-xl transition-shadow duration-300';
    card.dataset.robotId = robot.id;

    // Format last connected time
    const lastConnected = robot.lastConnected
        ? formatRelativeTime(robot.lastConnected)
        : 'Never';

    // Connection method badge color
    const methodColors = {
        'LocalAP': 'bg-blue-500',
        'LocalSTA': 'bg-green-500',
        'Remote': 'bg-purple-500'
    };
    const badgeColor = methodColors[robot.connectionMethod] || 'bg-gray-500';

    card.innerHTML = `
        <div class="flex justify-between items-start mb-4">
            <div>
                <h3 class="text-xl font-semibold text-white">${escapeHtml(robot.name || 'Unnamed Robot')}</h3>
                <span class="inline-block ${badgeColor} text-white text-xs px-2 py-1 rounded mt-2">
                    ${escapeHtml(robot.connectionMethod)}
                </span>
            </div>
            <div class="flex gap-2">
                <button class="btn-icon-secondary edit-robot-btn" data-robot-id="${robot.id}" title="Edit Robot">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                    </svg>
                </button>
                <button class="btn-icon-danger delete-robot-btn" data-robot-id="${robot.id}" title="Delete Robot">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                </button>
            </div>
        </div>

        <div class="space-y-2 text-sm text-gray-300 mb-4">
            <div class="flex items-center">
                <svg class="w-4 h-4 mr-2 text-unitree-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"></path>
                </svg>
                <span class="font-mono">${escapeHtml(robot.ip)}</span>
            </div>
            <div class="flex items-center">
                <svg class="w-4 h-4 mr-2 text-unitree-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
                </svg>
                <span class="font-mono text-xs">${escapeHtml(robot.serialNumber)}</span>
            </div>
            <div class="flex items-center text-gray-400">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span>Last connected: ${lastConnected}</span>
            </div>
        </div>

        <button class="btn-primary w-full connect-robot-btn" data-robot-id="${robot.id}">
            <svg class="w-5 h-5 inline-block mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
            </svg>
            Connect
        </button>
    `;

    // Add event listeners
    const editBtn = card.querySelector('.edit-robot-btn');
    const deleteBtn = card.querySelector('.delete-robot-btn');
    const connectBtn = card.querySelector('.connect-robot-btn');

    editBtn.addEventListener('click', () => handleEditRobot(robot.id));
    deleteBtn.addEventListener('click', () => handleDeleteRobot(robot.id));
    connectBtn.addEventListener('click', () => handleConnectRobot(robot.id));

    return card;
}


/**
 * Format relative time (e.g., "2 hours ago")
 * @param {string} isoTimestamp - ISO timestamp string
 * @returns {string} Formatted relative time
 */
function formatRelativeTime(isoTimestamp) {
    const date = new Date(isoTimestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);

    if (diffSec < 60) return 'Just now';
    if (diffMin < 60) return `${diffMin} minute${diffMin > 1 ? 's' : ''} ago`;
    if (diffHour < 24) return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`;
    if (diffDay < 7) return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`;

    // Format as date if older than a week
    return date.toLocaleDateString();
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Handle edit robot button click
 * @param {string} robotId - Robot ID
 */
function handleEditRobot(robotId) {
    console.log('Edit robot:', robotId);
    openEditRobotModal(robotId);
}

/**
 * Open modal in "add" mode
 */
function openAddRobotModal() {
    const modal = document.getElementById('robot-modal');
    const modalTitle = document.getElementById('modal-title');
    const form = document.getElementById('robot-form');

    if (!modal || !modalTitle || !form) {
        console.error('Modal elements not found');
        return;
    }

    // Set modal title
    modalTitle.textContent = 'Add Robot';

    // Reset form
    form.reset();
    form.dataset.mode = 'add';
    delete form.dataset.robotId;

    // Hide username/password fields initially
    updateConnectionMethodFields();

    // Show modal
    modal.classList.remove('hidden');

    console.log('Add robot modal opened');
}

/**
 * Open modal in "edit" mode with pre-filled data
 * @param {string} robotId - Robot ID to edit
 */
function openEditRobotModal(robotId) {
    const modal = document.getElementById('robot-modal');
    const modalTitle = document.getElementById('modal-title');
    const form = document.getElementById('robot-form');

    if (!modal || !modalTitle || !form) {
        console.error('Modal elements not found');
        return;
    }

    // Get robot data
    const robot = getRobot(robotId);
    if (!robot) {
        console.error('Robot not found:', robotId);
        return;
    }

    // Set modal title
    modalTitle.textContent = 'Edit Robot';

    // Set form mode and robot ID
    form.dataset.mode = 'edit';
    form.dataset.robotId = robotId;

    // Pre-fill form fields
    document.getElementById('robot-name').value = robot.name || '';
    document.getElementById('connection-method').value = robot.connectionMethod || 'LocalSTA';
    document.getElementById('robot-ip').value = robot.ip || '';
    document.getElementById('robot-serial').value = robot.serialNumber || '';
    document.getElementById('robot-username').value = robot.username || '';
    document.getElementById('robot-password').value = robot.password || '';

    // Update field visibility based on connection method
    updateConnectionMethodFields();

    // Show modal
    modal.classList.remove('hidden');

    console.log('Edit robot modal opened for:', robotId);
}

/**
 * Close modal and reset form
 */
function closeModal() {
    const modal = document.getElementById('robot-modal');
    const form = document.getElementById('robot-form');

    if (modal) {
        modal.classList.add('hidden');
    }

    if (form) {
        form.reset();
        delete form.dataset.mode;
        delete form.dataset.robotId;
    }

    console.log('Modal closed');
}

/**
 * Update connection method field visibility
 * Show username/password only for Remote connections
 */
function updateConnectionMethodFields() {
    const connectionMethod = document.getElementById('connection-method').value;
    const usernameGroup = document.getElementById('username-group');
    const passwordGroup = document.getElementById('password-group');
    const usernameInput = document.getElementById('robot-username');
    const passwordInput = document.getElementById('robot-password');

    if (connectionMethod === 'Remote') {
        usernameGroup.classList.remove('hidden');
        passwordGroup.classList.remove('hidden');
        usernameInput.required = true;
        passwordInput.required = true;
    } else {
        usernameGroup.classList.add('hidden');
        passwordGroup.classList.add('hidden');
        usernameInput.required = false;
        passwordInput.required = false;
        usernameInput.value = '';
        passwordInput.value = '';
    }
}

/**
 * Validate IP address format
 * @param {string} ip - IP address to validate
 * @returns {boolean} True if valid
 */
function validateIpAddress(ip) {
    const ipPattern = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!ipPattern.test(ip)) {
        return false;
    }

    const parts = ip.split('.');
    return parts.every(part => {
        const num = parseInt(part, 10);
        return num >= 0 && num <= 255;
    });
}

/**
 * Handle form submission
 * @param {Event} event - Form submit event
 */
function handleFormSubmit(event) {
    event.preventDefault();

    const form = document.getElementById('robot-form');
    const mode = form.dataset.mode;
    const robotId = form.dataset.robotId;

    // Get form values
    const name = document.getElementById('robot-name').value.trim();
    const connectionMethod = document.getElementById('connection-method').value;
    const ip = document.getElementById('robot-ip').value.trim();
    const serialNumber = document.getElementById('robot-serial').value.trim();
    const username = document.getElementById('robot-username').value.trim();
    const password = document.getElementById('robot-password').value.trim();

    // Validation based on connection method
    if (connectionMethod === 'Remote') {
        // For Remote: Serial Number, Username, and Password are required
        if (!serialNumber) {
            alert('Serial Number is required for Remote connections');
            return;
        }
        if (!username) {
            alert('Username is required for Remote connections');
            return;
        }
        if (!password) {
            alert('Password is required for Remote connections');
            return;
        }
    } else if (connectionMethod === 'LocalSTA') {
        // For LocalSTA: Either IP or Serial Number is required
        if (!ip && !serialNumber) {
            alert('Either IP Address or Serial Number is required for LocalSTA connections');
            return;
        }
        // Validate IP address format only if IP is provided
        if (ip && !validateIpAddress(ip)) {
            alert('Please enter a valid IP address (e.g., 192.168.8.181)');
            return;
        }
    } else if (connectionMethod === 'LocalAP') {
        // For LocalAP: No specific requirements (connects to robot's WiFi at 192.168.12.1)
        // No validation needed
    }

    // Create robot object
    const robotData = {
        name,
        connectionMethod,
        ip,
        serialNumber,
        username,
        password
    };

    // If editing, include the robot ID
    if (mode === 'edit' && robotId) {
        robotData.id = robotId;
    }

    // Save robot
    const savedRobot = saveRobot(robotData);

    if (savedRobot) {
        console.log(`Robot ${mode === 'edit' ? 'updated' : 'created'}:`, savedRobot);

        // Close modal
        closeModal();

        // Re-render robot cards
        renderRobotCards();
    } else {
        alert('Failed to save robot. Please try again.');
    }
}

/**
 * Handle delete robot button click
 * @param {string} robotId - Robot ID
 */
function handleDeleteRobot(robotId) {
    const robot = getRobot(robotId);
    if (!robot) {
        console.error('Robot not found:', robotId);
        return;
    }

    // Confirm deletion
    const confirmed = confirm(`Are you sure you want to delete "${robot.name}"?`);
    if (!confirmed) return;

    // Delete robot
    const success = deleteRobot(robotId);
    if (success) {
        console.log('Robot deleted:', robotId);
        // Re-render cards
        renderRobotCards();
    } else {
        alert('Failed to delete robot. Please try again.');
    }
}

/**
 * Handle connect robot button click
 * @param {string} robotId - Robot ID
 */
async function handleConnectRobot(robotId) {
    const robot = getRobot(robotId);
    if (!robot) {
        console.error('Robot not found:', robotId);
        alert('Robot not found. Please try again.');
        return;
    }

    console.log('Connecting to robot:', robot);

    // Show loading state on the connect button
    const connectBtn = document.querySelector(`[data-robot-id="${robotId}"] .connect-btn`);
    if (connectBtn) {
        connectBtn.disabled = true;
        connectBtn.innerHTML = `
            <svg class="animate-spin w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            Connecting...
        `;
    }

    try {
        // Prepare connection request
        const connectionData = {
            connection_method: robot.connectionMethod,
            ip: robot.ip || '',
            serial_number: robot.serialNumber || '',
            username: robot.username || '',
            password: robot.password || ''
        };

        console.log('Sending connection request:', connectionData);

        // Call /api/connect endpoint
        const response = await fetch('/api/connect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(connectionData)
        });

        const result = await response.json();

        if (response.ok && result.status === 'success') {
            console.log('Connection successful:', result);

            // Update last connected timestamp
            updateLastConnected(robotId);

            // Store robot ID in sessionStorage for control page
            sessionStorage.setItem('current_robot_id', robotId);

            // Redirect to control page
            window.location.href = '/control';
        } else {
            // Connection failed
            console.error('Connection failed:', result);
            alert(`Failed to connect to robot: ${result.message || 'Unknown error'}`);

            // Restore connect button
            if (connectBtn) {
                connectBtn.disabled = false;
                connectBtn.innerHTML = `
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                    </svg>
                    Connect
                `;
            }
        }
    } catch (error) {
        console.error('Connection error:', error);
        alert(`Connection error: ${error.message}`);

        // Restore connect button
        if (connectBtn) {
            connectBtn.disabled = false;
            connectBtn.innerHTML = `
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                </svg>
                Connect
            `;
        }
    }
}

/**
 * Initialize curve visualization charts
 */
function initializeCurveCharts() {
    // Check if curve utilities are loaded
    if (typeof createCurveChart !== 'function' || typeof updateCurveChart !== 'function') {
        console.error('Curve visualizer not loaded');
        return;
    }

    // Load current settings
    const settings = loadSettings();
    const km = settings.keyboard_mouse;

    // Create charts
    charts.linear = createCurveChart(
        'linear-curve-chart',
        'Linear',
        'm/s',
        km.linear_alpha || 1.5,
        km.linear_deadzone || 0.10,
        km.kb_max_linear_velocity || 1.5,
        HARDWARE_LIMITS.linear
    );

    charts.strafe = createCurveChart(
        'strafe-curve-chart',
        'Strafe',
        'm/s',
        km.strafe_alpha || 1.2,
        km.strafe_deadzone || 0.10,
        km.kb_max_strafe_velocity || 0.6,
        HARDWARE_LIMITS.strafe
    );

    charts.rotation = createCurveChart(
        'rotation-curve-chart',
        'Rotation',
        'rad/s',
        km.rotation_alpha || 2.5,
        km.rotation_deadzone || 0.10,
        km.kb_max_rotation_velocity || 3.0,
        HARDWARE_LIMITS.rotation
    );

    // Initialize curve control sliders
    initializeCurveSliders();
}

/**
 * Initialize curve adjustment sliders
 */
function initializeCurveSliders() {
    // Helper function to get fresh settings
    const getFreshSettings = () => {
        const settings = loadSettings();
        return settings.keyboard_mouse;
    };

    const settings = loadSettings();
    const km = settings.keyboard_mouse;

    // Linear alpha slider
    const linearAlphaSlider = document.getElementById('linear-alpha');
    const linearAlphaValue = document.getElementById('linear-alpha-value');
    if (linearAlphaSlider && linearAlphaValue) {
        linearAlphaSlider.value = km.linear_alpha || 1.5;
        linearAlphaValue.textContent = (km.linear_alpha || 1.5).toFixed(1);

        linearAlphaSlider.addEventListener('input', (e) => {
            const alpha = parseFloat(e.target.value);
            linearAlphaValue.textContent = alpha.toFixed(1);
            updateSetting('keyboard_mouse', 'linear_alpha', alpha);

            // Get fresh settings after update
            const fresh = getFreshSettings();
            updateCurveChart(
                charts.linear,
                'Linear',
                alpha,
                fresh.linear_deadzone !== undefined ? fresh.linear_deadzone : 0.10,
                fresh.kb_max_linear_velocity !== undefined ? fresh.kb_max_linear_velocity : 1.5,
                HARDWARE_LIMITS.linear
            );
        });
    }

    // Linear deadzone slider
    const linearDeadzoneSlider = document.getElementById('linear-deadzone');
    const linearDeadzoneValue = document.getElementById('linear-deadzone-value');
    if (linearDeadzoneSlider && linearDeadzoneValue) {
        const deadzonePercent = Math.round((km.linear_deadzone || 0.10) * 100);
        linearDeadzoneSlider.value = deadzonePercent;
        linearDeadzoneValue.textContent = deadzonePercent + '%';

        linearDeadzoneSlider.addEventListener('input', (e) => {
            const deadzonePercent = parseInt(e.target.value);
            const deadzone = deadzonePercent / 100.0;
            linearDeadzoneValue.textContent = deadzonePercent + '%';
            updateSetting('keyboard_mouse', 'linear_deadzone', deadzone);

            // Get fresh settings after update
            const fresh = getFreshSettings();
            updateCurveChart(
                charts.linear,
                'Linear',
                fresh.linear_alpha !== undefined ? fresh.linear_alpha : 1.5,
                deadzone,
                fresh.kb_max_linear_velocity !== undefined ? fresh.kb_max_linear_velocity : 1.5,
                HARDWARE_LIMITS.linear
            );
        });
    }

    // Strafe alpha slider
    const strafeAlphaSlider = document.getElementById('strafe-alpha');
    const strafeAlphaValue = document.getElementById('strafe-alpha-value');
    if (strafeAlphaSlider && strafeAlphaValue) {
        strafeAlphaSlider.value = km.strafe_alpha || 1.2;
        strafeAlphaValue.textContent = (km.strafe_alpha || 1.2).toFixed(1);

        strafeAlphaSlider.addEventListener('input', (e) => {
            const alpha = parseFloat(e.target.value);
            strafeAlphaValue.textContent = alpha.toFixed(1);
            updateSetting('keyboard_mouse', 'strafe_alpha', alpha);

            // Get fresh settings after update
            const fresh = getFreshSettings();
            updateCurveChart(
                charts.strafe,
                'Strafe',
                alpha,
                fresh.strafe_deadzone !== undefined ? fresh.strafe_deadzone : 0.10,
                fresh.kb_max_strafe_velocity !== undefined ? fresh.kb_max_strafe_velocity : 0.6,
                HARDWARE_LIMITS.strafe
            );
        });
    }

    // Strafe deadzone slider
    const strafeDeadzoneSlider = document.getElementById('strafe-deadzone');
    const strafeDeadzoneValue = document.getElementById('strafe-deadzone-value');
    if (strafeDeadzoneSlider && strafeDeadzoneValue) {
        const deadzonePercent = Math.round((km.strafe_deadzone || 0.10) * 100);
        strafeDeadzoneSlider.value = deadzonePercent;
        strafeDeadzoneValue.textContent = deadzonePercent + '%';

        strafeDeadzoneSlider.addEventListener('input', (e) => {
            const deadzonePercent = parseInt(e.target.value);
            const deadzone = deadzonePercent / 100.0;
            strafeDeadzoneValue.textContent = deadzonePercent + '%';
            updateSetting('keyboard_mouse', 'strafe_deadzone', deadzone);

            // Get fresh settings after update
            const fresh = getFreshSettings();
            updateCurveChart(
                charts.strafe,
                'Strafe',
                fresh.strafe_alpha !== undefined ? fresh.strafe_alpha : 1.2,
                deadzone,
                fresh.kb_max_strafe_velocity !== undefined ? fresh.kb_max_strafe_velocity : 0.6,
                HARDWARE_LIMITS.strafe
            );
        });
    }

    // Rotation alpha slider
    const rotationAlphaSlider = document.getElementById('rotation-alpha');
    const rotationAlphaValue = document.getElementById('rotation-alpha-value');
    if (rotationAlphaSlider && rotationAlphaValue) {
        rotationAlphaSlider.value = km.rotation_alpha || 2.5;
        rotationAlphaValue.textContent = (km.rotation_alpha || 2.5).toFixed(1);

        rotationAlphaSlider.addEventListener('input', (e) => {
            const alpha = parseFloat(e.target.value);
            rotationAlphaValue.textContent = alpha.toFixed(1);
            updateSetting('keyboard_mouse', 'rotation_alpha', alpha);

            // Get fresh settings after update
            const fresh = getFreshSettings();
            updateCurveChart(
                charts.rotation,
                'Rotation',
                alpha,
                fresh.rotation_deadzone !== undefined ? fresh.rotation_deadzone : 0.10,
                fresh.kb_max_rotation_velocity !== undefined ? fresh.kb_max_rotation_velocity : 3.0,
                HARDWARE_LIMITS.rotation
            );
        });
    }

    // Rotation deadzone slider
    const rotationDeadzoneSlider = document.getElementById('rotation-deadzone');
    const rotationDeadzoneValue = document.getElementById('rotation-deadzone-value');
    if (rotationDeadzoneSlider && rotationDeadzoneValue) {
        const deadzonePercent = Math.round((km.rotation_deadzone || 0.10) * 100);
        rotationDeadzoneSlider.value = deadzonePercent;
        rotationDeadzoneValue.textContent = deadzonePercent + '%';

        rotationDeadzoneSlider.addEventListener('input', (e) => {
            const deadzonePercent = parseInt(e.target.value);
            const deadzone = deadzonePercent / 100.0;
            rotationDeadzoneValue.textContent = deadzonePercent + '%';
            updateSetting('keyboard_mouse', 'rotation_deadzone', deadzone);

            // Get fresh settings after update
            const fresh = getFreshSettings();
            updateCurveChart(
                charts.rotation,
                'Rotation',
                fresh.rotation_alpha !== undefined ? fresh.rotation_alpha : 2.5,
                deadzone,
                fresh.kb_max_rotation_velocity !== undefined ? fresh.kb_max_rotation_velocity : 3.0,
                HARDWARE_LIMITS.rotation
            );
        });
    }

    // Reset curves button
    const resetCurvesBtn = document.getElementById('reset-curves-btn');
    if (resetCurvesBtn) {
        resetCurvesBtn.addEventListener('click', () => {
            const defaults = getDefaultSettings();
            const defaultKm = defaults.keyboard_mouse;

            // Reset linear
            updateSetting('keyboard_mouse', 'linear_alpha', defaultKm.linear_alpha);
            updateSetting('keyboard_mouse', 'linear_deadzone', defaultKm.linear_deadzone);
            if (linearAlphaSlider) linearAlphaSlider.value = defaultKm.linear_alpha;
            if (linearAlphaValue) linearAlphaValue.textContent = defaultKm.linear_alpha.toFixed(1);
            if (linearDeadzoneSlider) linearDeadzoneSlider.value = Math.round(defaultKm.linear_deadzone * 100);
            if (linearDeadzoneValue) linearDeadzoneValue.textContent = Math.round(defaultKm.linear_deadzone * 100) + '%';
            updateCurveChart(
                charts.linear,
                'Linear',
                defaultKm.linear_alpha,
                defaultKm.linear_deadzone,
                defaultKm.kb_max_linear_velocity,
                HARDWARE_LIMITS.linear
            );

            // Reset strafe
            updateSetting('keyboard_mouse', 'strafe_alpha', defaultKm.strafe_alpha);
            updateSetting('keyboard_mouse', 'strafe_deadzone', defaultKm.strafe_deadzone);
            if (strafeAlphaSlider) strafeAlphaSlider.value = defaultKm.strafe_alpha;
            if (strafeAlphaValue) strafeAlphaValue.textContent = defaultKm.strafe_alpha.toFixed(1);
            if (strafeDeadzoneSlider) strafeDeadzoneSlider.value = Math.round(defaultKm.strafe_deadzone * 100);
            if (strafeDeadzoneValue) strafeDeadzoneValue.textContent = Math.round(defaultKm.strafe_deadzone * 100) + '%';
            updateCurveChart(
                charts.strafe,
                'Strafe',
                defaultKm.strafe_alpha,
                defaultKm.strafe_deadzone,
                defaultKm.kb_max_strafe_velocity,
                HARDWARE_LIMITS.strafe
            );

            // Reset rotation
            updateSetting('keyboard_mouse', 'rotation_alpha', defaultKm.rotation_alpha);
            updateSetting('keyboard_mouse', 'rotation_deadzone', defaultKm.rotation_deadzone);
            if (rotationAlphaSlider) rotationAlphaSlider.value = defaultKm.rotation_alpha;
            if (rotationAlphaValue) rotationAlphaValue.textContent = defaultKm.rotation_alpha.toFixed(1);
            if (rotationDeadzoneSlider) rotationDeadzoneSlider.value = Math.round(defaultKm.rotation_deadzone * 100);
            if (rotationDeadzoneValue) rotationDeadzoneValue.textContent = Math.round(defaultKm.rotation_deadzone * 100) + '%';
            updateCurveChart(
                charts.rotation,
                'Rotation',
                defaultKm.rotation_alpha,
                defaultKm.rotation_deadzone,
                defaultKm.kb_max_rotation_velocity,
                HARDWARE_LIMITS.rotation
            );

            console.log('✅ Curves reset to defaults');
        });
    }
}


