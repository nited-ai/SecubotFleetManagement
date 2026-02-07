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
            mouse_yaw_sensitivity: 5.0,  // Increased for precision-flick control
            mouse_pitch_sensitivity: 2.5,  // Increased proportionally
            kb_max_linear_velocity: 1.5,
            kb_max_strafe_velocity: 0.6,  // Fixed: hardware limit
            kb_max_rotation_velocity: 3.0,
            // Exponential curve settings (Normal preset defaults)
            // NOTE: Linear/strafe deadzone removed (keyboard is digital), but rotation deadzone kept (mouse is analog)
            linear_alpha: 1.5,
            strafe_alpha: 1.2,
            rotation_alpha: 2.5,
            rotation_deadzone: 0.10  // Mouse rotation needs deadzone to prevent drift
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
                mouse_yaw_sensitivity: 3.0,  // Lower for beginners, but still allows fast flicks
                mouse_pitch_sensitivity: 1.5,  // Proportionally lower
                kb_max_linear_velocity: 1.0,
                kb_max_strafe_velocity: 0.6,  // Fixed: was 0.8, exceeds 0.6 m/s hardware limit
                kb_max_rotation_velocity: 2.0,
                // Beginner curve: Smooth, forgiving (linear/strafe deadzone removed, rotation deadzone kept)
                linear_alpha: 1.8,
                strafe_alpha: 1.5,
                rotation_alpha: 3.0,  // High exponential suppresses jitter from sensitivity
                rotation_deadzone: 0.15  // Higher deadzone for beginners to prevent accidental rotation
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
                mouse_yaw_sensitivity: 5.0,  // Balanced for precision-flick control
                mouse_pitch_sensitivity: 2.5,  // Proportional to yaw
                kb_max_linear_velocity: 1.5,
                kb_max_strafe_velocity: 0.6,  // Fixed: was 1.2, exceeds 0.6 m/s hardware limit
                kb_max_rotation_velocity: 3.0,
                // Normal curve: Balanced, default values (linear/strafe deadzone removed, rotation deadzone kept)
                linear_alpha: 1.5,
                strafe_alpha: 1.2,
                rotation_alpha: 2.5,  // Exponential curve for smooth precision-flick
                rotation_deadzone: 0.10  // Mouse rotation needs deadzone to prevent drift
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
                mouse_yaw_sensitivity: 8.0,  // Higher for advanced users
                mouse_pitch_sensitivity: 4.0,  // Proportional to yaw
                kb_max_linear_velocity: 1.8,
                kb_max_strafe_velocity: 0.6,  // Fixed: was 1.5, exceeds 0.6 m/s hardware limit
                kb_max_rotation_velocity: 3.0,  // Fixed: was 3.5, exceeds 3.0 rad/s hardware limit
                // Advanced curve: More responsive (linear/strafe deadzone removed, rotation deadzone kept)
                linear_alpha: 1.2,
                strafe_alpha: 1.0,
                rotation_alpha: 2.0,  // Lower exponential for more linear response
                rotation_deadzone: 0.05  // Lower deadzone for advanced users (more responsive)
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
                mouse_yaw_sensitivity: 12.0,  // Highest for sport/competitive use
                mouse_pitch_sensitivity: 6.0,  // Proportional to yaw
                kb_max_linear_velocity: 2.0,
                kb_max_strafe_velocity: 0.6,  // Fixed: was 1.8, exceeds 0.6 m/s hardware limit
                kb_max_rotation_velocity: 3.0,  // Fixed: was 4.0, exceeds 3.0 rad/s hardware limit
                // Sport curve: Linear/aggressive (linear/strafe deadzone removed, rotation deadzone kept)
                linear_alpha: 1.0,
                strafe_alpha: 0.8,
                rotation_alpha: 1.5,  // Lower exponential for near-linear response
                rotation_deadzone: 0.05  // Minimal deadzone for sport/competitive use
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
                mouse_yaw_sensitivity: 0.3,
                mouse_pitch_sensitivity: 0.15,
                kb_max_linear_velocity: 1.0,
                kb_max_strafe_velocity: 0.8,
                kb_max_rotation_velocity: 2.0
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
                mouse_yaw_sensitivity: 0.5,
                mouse_pitch_sensitivity: 0.25,
                kb_max_linear_velocity: 1.5,
                kb_max_strafe_velocity: 1.2,
                kb_max_rotation_velocity: 3.0
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
                mouse_yaw_sensitivity: 0.8,
                mouse_pitch_sensitivity: 0.4,
                kb_max_linear_velocity: 1.8,
                kb_max_strafe_velocity: 1.5,
                kb_max_rotation_velocity: 3.5
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
                mouse_yaw_sensitivity: 1.2,
                mouse_pitch_sensitivity: 0.6,
                kb_max_linear_velocity: 2.0,
                kb_max_strafe_velocity: 1.8,
                kb_max_rotation_velocity: 4.0
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

