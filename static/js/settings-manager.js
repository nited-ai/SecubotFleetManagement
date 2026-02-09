/**
 * Settings Manager Module
 * Handles loading, saving, and managing user settings for robot control
 */

const SETTINGS_STORAGE_KEY = 'unitree_settings';

/**
 * Get default settings
 * @returns {Object} Default settings object
 */
function getDefaultSettings() {
    return {
        keyboard_mouse: {
            mouse_yaw_sensitivity: 6.0,  // Balanced for precision-flick control
            mouse_pitch_sensitivity: 3.0,  // Proportional to yaw
            kb_max_linear_velocity: 3.0,   // ~60% of 5.0 hardware limit
            kb_max_strafe_velocity: 0.6,   // ~60% of 1.0 hardware limit
            kb_max_rotation_velocity: 2.0, // ~67% of 3.0 hardware limit
            // Exponential curve settings (Normal preset defaults)
            linear_alpha: 1.0,    // Linear response
            strafe_alpha: 1.0,
            rotation_alpha: 1.0,
            rotation_deadzone: 0.0,  // Deadzone removed (mouse rotation bypasses curve)
            // Backend slew rate limiter settings (acceleration ramp-up time)
            linear_ramp_time: 0.20,    // seconds - time to reach max linear speed
            strafe_ramp_time: 0.20,    // seconds - time to reach max strafe speed
            rotation_ramp_time: 0.20,  // seconds - time to reach max rotation speed
            // Pitch (body tilt) curve settings
            pitch_alpha: 1.0,           // Linear response
            pitch_deadzone: 0.0,        // Deadzone removed (mouse pitch bypasses curve)
            pitch_max_velocity: 0.30,   // Max pitch angle in rad (~17°)
            pitch_ramp_time: 0.20       // seconds - time to reach max pitch angle
        },
        gamepad: {
            deadzone_left_stick: 0.15,
            deadzone_right_stick: 0.15,
            sensitivity_linear: 1.0,
            sensitivity_strafe: 1.0,
            sensitivity_rotation: 1.0,
            speed_multiplier: 1.0,
            max_linear_velocity: 0.6,
            max_strafe_velocity: 0.4,
            max_rotation_velocity: 0.8
        },
        audio: {
            enabled: false
        }
    };
}

/**
 * Clean obsolete settings from a settings object
 * Removes deprecated keys that are no longer used
 * @param {Object} settings - Settings object to clean
 * @returns {Object} Cleaned settings object
 */
function cleanObsoleteSettings(settings) {
    if (!settings) return settings;

    // List of obsolete keys to remove
    const obsoleteKeys = [
        'keyboard_linear_speed',   // Removed: Replaced by speed slider (0-100%)
        'keyboard_strafe_speed'    // Removed: Replaced by speed slider (0-100%)
    ];

    // Clean keyboard_mouse section
    if (settings.keyboard_mouse) {
        obsoleteKeys.forEach(key => {
            if (key in settings.keyboard_mouse) {
                console.log(`🧹 [cleanObsoleteSettings] Removing obsolete key: keyboard_mouse.${key}`);
                delete settings.keyboard_mouse[key];
            }
        });
    }

    return settings;
}

/**
 * Load settings from LocalStorage
 * @returns {Object} Settings object (defaults if not found)
 */
function loadSettings() {
    try {
        const stored = localStorage.getItem(SETTINGS_STORAGE_KEY);
        if (stored) {
            let settings = JSON.parse(stored);

            // Clean obsolete settings before merging
            settings = cleanObsoleteSettings(settings);

            // Merge with defaults to ensure all keys exist
            const defaults = getDefaultSettings();
            const merged = {
                keyboard_mouse: { ...defaults.keyboard_mouse, ...settings.keyboard_mouse },
                gamepad: { ...defaults.gamepad, ...settings.gamepad },
                audio: { ...defaults.audio, ...settings.audio }
            };

            // Save cleaned settings back to localStorage
            saveSettings(merged);

            return merged;
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }
    return getDefaultSettings();
}

/**
 * Save settings to LocalStorage
 * @param {Object} settings - Settings object to save
 * @returns {boolean} Success status
 */
function saveSettings(settings) {
    try {
        localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
        console.log('Settings saved:', settings);
        return true;
    } catch (error) {
        console.error('Error saving settings:', error);
        return false;
    }
}

/**
 * Update a specific setting value
 * @param {string} category - Setting category (keyboard_mouse, gamepad, audio)
 * @param {string} key - Setting key
 * @param {*} value - New value
 * @returns {boolean} Success status
 */
function updateSetting(category, key, value) {
    const settings = loadSettings();
    if (settings[category] && key in settings[category]) {
        settings[category][key] = value;
        return saveSettings(settings);
    }
    console.error(`Invalid setting: ${category}.${key}`);
    return false;
}

/**
 * Reset settings to defaults
 * @returns {Object} Default settings
 */
function resetSettings() {
    const defaults = getDefaultSettings();
    saveSettings(defaults);
    return defaults;
}

/**
 * Apply preset to both keyboard/mouse and gamepad
 * @param {string} preset - Preset name (beginner, normal, advanced, custom)
 * @returns {boolean} Success status
 */
function applyPreset(preset) {
    const presets = {
        beginner: {
            keyboard_mouse: {
                mouse_yaw_sensitivity: 4.5,   // Moderate for beginners
                mouse_pitch_sensitivity: 2.0,  // Proportional to yaw
                kb_max_linear_velocity: 2.5,   // ~50% of 5.0 hardware limit
                kb_max_strafe_velocity: 0.5,   // ~50% of 1.0 hardware limit
                kb_max_rotation_velocity: 1.5, // ~50% of 3.0 hardware limit
                // Beginner curve: Linear to slightly convex (gentle start)
                linear_alpha: 1.2,
                strafe_alpha: 1.2,
                rotation_alpha: 1.2,
                rotation_deadzone: 0.0,
                // Beginner ramp-up time: Smooth acceleration
                linear_ramp_time: 0.40,
                strafe_ramp_time: 0.40,
                rotation_ramp_time: 0.40,
                // Beginner pitch: Smooth, limited range
                pitch_alpha: 1.2,
                pitch_deadzone: 0.0,
                pitch_max_velocity: 0.20,
                pitch_ramp_time: 0.40
            },
            gamepad: {
                deadzone_left_stick: 0.15,
                deadzone_right_stick: 0.15,
                sensitivity_linear: 0.7,
                sensitivity_strafe: 0.7,
                sensitivity_rotation: 0.7,
                max_linear_velocity: 0.4,
                max_strafe_velocity: 0.3,
                max_rotation_velocity: 0.5,
                speed_multiplier: 0.7
            }
        },
        normal: {
            keyboard_mouse: {
                mouse_yaw_sensitivity: 6.0,   // Balanced for precision-flick control
                mouse_pitch_sensitivity: 3.0,  // Proportional to yaw
                kb_max_linear_velocity: 3.0,   // ~60% of 5.0 hardware limit
                kb_max_strafe_velocity: 0.6,   // ~60% of 1.0 hardware limit
                kb_max_rotation_velocity: 2.0, // ~67% of 3.0 hardware limit
                // Normal curve: Linear response
                linear_alpha: 1.0,
                strafe_alpha: 1.0,
                rotation_alpha: 1.0,
                rotation_deadzone: 0.0,
                // Normal ramp-up time: Balanced
                linear_ramp_time: 0.20,
                strafe_ramp_time: 0.20,
                rotation_ramp_time: 0.20,
                // Normal pitch: Balanced
                pitch_alpha: 1.0,
                pitch_deadzone: 0.0,
                pitch_max_velocity: 0.30,
                pitch_ramp_time: 0.20
            },
            gamepad: {
                deadzone_left_stick: 0.1,
                deadzone_right_stick: 0.1,
                sensitivity_linear: 1.0,
                sensitivity_strafe: 1.0,
                sensitivity_rotation: 1.0,
                max_linear_velocity: 0.6,
                max_strafe_velocity: 0.4,
                max_rotation_velocity: 0.8,
                speed_multiplier: 1.0
            }
        },
        advanced: {
            keyboard_mouse: {
                mouse_yaw_sensitivity: 10.0,  // High for advanced users
                mouse_pitch_sensitivity: 5.0,  // Proportional to yaw
                kb_max_linear_velocity: 4.5,   // ~90% of 5.0 hardware limit
                kb_max_strafe_velocity: 0.9,   // ~90% of 1.0 hardware limit
                kb_max_rotation_velocity: 3.0, // 100% of 3.0 hardware limit
                // Advanced curve: Slightly concave (fast start, responsive)
                linear_alpha: 0.9,
                strafe_alpha: 0.9,
                rotation_alpha: 0.9,
                rotation_deadzone: 0.0,
                // Advanced ramp-up time: Snappy acceleration
                linear_ramp_time: 0.10,
                strafe_ramp_time: 0.10,
                rotation_ramp_time: 0.10,
                // Advanced pitch: Responsive
                pitch_alpha: 0.9,
                pitch_deadzone: 0.0,
                pitch_max_velocity: 0.35,
                pitch_ramp_time: 0.10
            },
            gamepad: {
                deadzone_left_stick: 0.05,
                deadzone_right_stick: 0.05,
                sensitivity_linear: 1.3,
                sensitivity_strafe: 1.3,
                sensitivity_rotation: 1.3,
                max_linear_velocity: 0.6,
                max_strafe_velocity: 0.4,
                max_rotation_velocity: 0.8,
                speed_multiplier: 1.3
            }
        },
        sport: {
            keyboard_mouse: {
                mouse_yaw_sensitivity: 15.0,  // Highest for sport/competitive use
                mouse_pitch_sensitivity: 7.5,  // Proportional to yaw
                kb_max_linear_velocity: 5.0,   // 100% of 5.0 hardware limit
                kb_max_strafe_velocity: 1.0,   // 100% of 1.0 hardware limit
                kb_max_rotation_velocity: 3.0, // 100% of 3.0 hardware limit
                // Sport curve: Concave (fast start, aggressive)
                linear_alpha: 0.8,
                strafe_alpha: 0.8,
                rotation_alpha: 0.8,
                rotation_deadzone: 0.0,
                // Sport ramp-up time: Near-instant for competitive response
                linear_ramp_time: 0.05,
                strafe_ramp_time: 0.05,
                rotation_ramp_time: 0.05,
                // Sport pitch: Near-instant, full range
                pitch_alpha: 0.8,
                pitch_deadzone: 0.0,
                pitch_max_velocity: 0.35,
                pitch_ramp_time: 0.05
            },
            gamepad: {
                deadzone_left_stick: 0.05,
                deadzone_right_stick: 0.05,
                sensitivity_linear: 1.5,
                sensitivity_strafe: 1.5,
                sensitivity_rotation: 1.5,
                max_linear_velocity: 0.8,
                max_strafe_velocity: 0.6,
                max_rotation_velocity: 1.0,
                speed_multiplier: 1.5
            }
        }
    };

    if (presets[preset]) {
        const settings = loadSettings();
        settings.keyboard_mouse = { ...settings.keyboard_mouse, ...presets[preset].keyboard_mouse };
        settings.gamepad = { ...settings.gamepad, ...presets[preset].gamepad };
        return saveSettings(settings);
    }
    console.error(`Invalid preset: ${preset}`);
    return false;
}

/**
 * Get current active preset (if any)
 * @returns {string|null} Preset name or null if custom
 */
function getCurrentPreset() {
    const settings = loadSettings();
    const presets = ['beginner', 'normal', 'advanced', 'sport'];

    for (const preset of presets) {
        const presetSettings = getPresetSettings(preset);
        if (presetSettings &&
            JSON.stringify(settings.keyboard_mouse) === JSON.stringify(presetSettings.keyboard_mouse) &&
            JSON.stringify(settings.gamepad) === JSON.stringify(presetSettings.gamepad)) {
            return preset;
        }
    }
    return 'custom';
}

/**
 * Get preset settings
 * @param {string} preset - Preset name
 * @returns {Object|null} Preset settings or null
 */
function getPresetSettings(preset) {
    const presets = {
        beginner: {
            keyboard_mouse: {
                mouse_yaw_sensitivity: 4.5,
                mouse_pitch_sensitivity: 2.0,
                kb_max_linear_velocity: 2.5,
                kb_max_strafe_velocity: 0.5,
                kb_max_rotation_velocity: 1.5
            },
            gamepad: {
                deadzone_left_stick: 0.15,
                deadzone_right_stick: 0.15,
                sensitivity_linear: 0.7,
                sensitivity_strafe: 0.7,
                sensitivity_rotation: 0.7,
                max_linear_velocity: 0.4,
                max_strafe_velocity: 0.3,
                max_rotation_velocity: 0.5,
                speed_multiplier: 0.7
            }
        },
        normal: {
            keyboard_mouse: {
                mouse_yaw_sensitivity: 6.0,
                mouse_pitch_sensitivity: 3.0,
                kb_max_linear_velocity: 3.0,
                kb_max_strafe_velocity: 0.6,
                kb_max_rotation_velocity: 2.0
            },
            gamepad: {
                deadzone_left_stick: 0.1,
                deadzone_right_stick: 0.1,
                sensitivity_linear: 1.0,
                sensitivity_strafe: 1.0,
                sensitivity_rotation: 1.0,
                max_linear_velocity: 0.6,
                max_strafe_velocity: 0.4,
                max_rotation_velocity: 0.8,
                speed_multiplier: 1.0
            }
        },
        advanced: {
            keyboard_mouse: {
                mouse_yaw_sensitivity: 10.0,
                mouse_pitch_sensitivity: 5.0,
                kb_max_linear_velocity: 4.5,
                kb_max_strafe_velocity: 0.9,
                kb_max_rotation_velocity: 3.0
            },
            gamepad: {
                deadzone_left_stick: 0.05,
                deadzone_right_stick: 0.05,
                sensitivity_linear: 1.3,
                sensitivity_strafe: 1.3,
                sensitivity_rotation: 1.3,
                max_linear_velocity: 0.6,
                max_strafe_velocity: 0.4,
                max_rotation_velocity: 0.8,
                speed_multiplier: 1.3
            }
        },
        sport: {
            keyboard_mouse: {
                mouse_yaw_sensitivity: 15.0,
                mouse_pitch_sensitivity: 7.5,
                kb_max_linear_velocity: 5.0,
                kb_max_strafe_velocity: 1.0,
                kb_max_rotation_velocity: 3.0
            },
            gamepad: {
                deadzone_left_stick: 0.05,
                deadzone_right_stick: 0.05,
                sensitivity_linear: 1.5,
                sensitivity_strafe: 1.5,
                sensitivity_rotation: 1.5,
                max_linear_velocity: 0.8,
                max_strafe_velocity: 0.6,
                max_rotation_velocity: 1.0,
                speed_multiplier: 1.5
            }
        }
    };

    return presets[preset] || null;
}

