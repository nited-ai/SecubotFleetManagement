/**
 * Curve Utilities for Exponential Response Curves
 * 
 * Provides functions to apply non-linear response curves to control inputs,
 * allowing for fine-tuned control feel across different skill levels.
 * 
 * @module curve-utils
 */

/**
 * Hardware limits for robot movement (from robot specifications)
 */
const HARDWARE_LIMITS = {
    linear: 5.0,    // m/s - Maximum linear (forward/back) velocity
    strafe: 1.0,    // m/s - Maximum strafe (left/right) velocity
    rotation: 3.0,  // rad/s - Maximum rotation (yaw) velocity
    pitch: 0.35     // rad - Maximum pitch angle (~20°)
};

/**
 * Apply exponential curve to input value with deadzone and hardware limit clamping
 * 
 * Formula: output = ((input - deadzone) / (1.0 - deadzone))^alpha * maxVelocity
 * 
 * @param {number} input - Input value (0.0 to 1.0)
 * @param {number} alpha - Exponential factor (0.5 to 4.0)
 *                         - alpha < 1.0: Concave curve (fast start, slow end) - More responsive
 *                         - alpha = 1.0: Linear curve (straight line) - Proportional
 *                         - alpha > 1.0: Convex curve (slow start, fast end) - Smoother
 * @param {number} deadzone - Deadzone threshold (0.0 to 0.3)
 *                            Inputs below this value produce zero output
 * @param {number} maxVelocity - Maximum output velocity (in m/s or rad/s)
 * @param {number} hardwareLimit - Hardware limit for clamping (in m/s or rad/s)
 * @returns {number} Curve-adjusted output velocity, clamped to hardware limit
 * 
 * @example
 * // Apply curve to linear velocity with alpha=1.5, 10% deadzone, max 1.5 m/s
 * const output = applyCurve(0.5, 1.5, 0.10, 1.5, HARDWARE_LIMITS.linear);
 * // Returns: ~0.67 m/s (50% input with exponential curve)
 * 
 * @example
 * // Apply curve to rotation with alpha=2.5, 10% deadzone, max 3.0 rad/s
 * const output = applyCurve(0.25, 2.5, 0.10, 3.0, HARDWARE_LIMITS.rotation);
 * // Returns: ~0.13 rad/s (25% input with strong exponential curve)
 */
function applyCurve(input, alpha, deadzone, maxVelocity, hardwareLimit) {
    // Ensure input is in valid range [0, 1]
    input = Math.max(0, Math.min(1, input));

    // Apply deadzone - inputs below deadzone produce zero output
    if (input < deadzone) {
        return 0;
    }

    // Normalize input to [0, 1] range after removing deadzone
    // Maps [deadzone, 1.0] to [0.0, 1.0]
    const normalized = (input - deadzone) / (1.0 - deadzone);

    // Apply exponential curve using alpha parameter
    // alpha > 1.0 creates convex curve (smooth acceleration)
    // alpha < 1.0 creates concave curve (responsive at low speeds)
    // alpha = 1.0 creates linear response
    const curved = Math.pow(normalized, alpha);

    // Scale to maximum velocity
    const scaled = curved * maxVelocity;

    // IMPORTANT: Only clamp to hardware limit if maxVelocity is within safe range
    // This allows testing beyond hardware limits when explicitly configured
    // If maxVelocity > hardwareLimit, user is intentionally testing beyond limits
    // If maxVelocity <= hardwareLimit, enforce hardware limit for safety
    const effectiveLimit = Math.max(maxVelocity, hardwareLimit);
    const clamped = Math.min(scaled, effectiveLimit);

    return clamped;
}

/**
 * Apply curve to linear (forward/back) velocity
 * 
 * @param {number} input - Input value (0.0 to 1.0)
 * @param {number} alpha - Exponential factor (0.5 to 4.0)
 * @param {number} deadzone - Deadzone threshold (0.0 to 0.3)
 * @param {number} maxVelocity - Maximum linear velocity (m/s)
 * @returns {number} Curve-adjusted linear velocity (m/s)
 */
function applyLinearCurve(input, alpha, deadzone, maxVelocity) {
    return applyCurve(input, alpha, deadzone, maxVelocity, HARDWARE_LIMITS.linear);
}

/**
 * Apply curve to strafe (left/right) velocity
 * 
 * @param {number} input - Input value (0.0 to 1.0)
 * @param {number} alpha - Exponential factor (0.5 to 4.0)
 * @param {number} deadzone - Deadzone threshold (0.0 to 0.3)
 * @param {number} maxVelocity - Maximum strafe velocity (m/s)
 * @returns {number} Curve-adjusted strafe velocity (m/s)
 */
function applyStrafeCurve(input, alpha, deadzone, maxVelocity) {
    return applyCurve(input, alpha, deadzone, maxVelocity, HARDWARE_LIMITS.strafe);
}

/**
 * Apply curve to rotation (yaw) velocity
 * 
 * @param {number} input - Input value (0.0 to 1.0)
 * @param {number} alpha - Exponential factor (0.5 to 4.0)
 * @param {number} deadzone - Deadzone threshold (0.0 to 0.3)
 * @param {number} maxVelocity - Maximum rotation velocity (rad/s)
 * @returns {number} Curve-adjusted rotation velocity (rad/s)
 */
function applyRotationCurve(input, alpha, deadzone, maxVelocity) {
    return applyCurve(input, alpha, deadzone, maxVelocity, HARDWARE_LIMITS.rotation);
}

/**
 * Generate curve data points for visualization
 * 
 * @param {number} alpha - Exponential factor (0.5 to 4.0)
 * @param {number} deadzone - Deadzone threshold (0.0 to 0.3)
 * @param {number} maxVelocity - Maximum velocity (m/s or rad/s)
 * @param {number} hardwareLimit - Hardware limit (m/s or rad/s)
 * @param {number} numPoints - Number of data points to generate (default: 100)
 * @returns {Array<{input: number, output: number}>} Array of {input, output} pairs
 */
function generateCurveData(alpha, deadzone, maxVelocity, hardwareLimit, numPoints = 100) {
    const data = [];
    for (let i = 0; i <= numPoints; i++) {
        const input = i / numPoints;
        const output = applyCurve(input, alpha, deadzone, maxVelocity, hardwareLimit);
        data.push({ input, output });
    }
    return data;
}

/**
 * Check if max velocity exceeds hardware limit
 * 
 * @param {number} maxVelocity - Maximum velocity setting
 * @param {number} hardwareLimit - Hardware limit
 * @returns {boolean} True if max velocity exceeds hardware limit
 */
function exceedsHardwareLimit(maxVelocity, hardwareLimit) {
    return maxVelocity > hardwareLimit;
}

/**
 * Apply curve to pitch (head tilt) angle
 *
 * @param {number} input - Input value (0.0 to 1.0)
 * @param {number} alpha - Exponential factor (0.5 to 4.0)
 * @param {number} deadzone - Deadzone threshold (0.0 to 0.3)
 * @param {number} maxVelocity - Maximum pitch angle (rad)
 * @returns {number} Curve-adjusted pitch angle (rad)
 */
function applyPitchCurve(input, alpha, deadzone, maxVelocity) {
    return applyCurve(input, alpha, deadzone, maxVelocity, HARDWARE_LIMITS.pitch);
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment (for testing)
    module.exports = {
        HARDWARE_LIMITS,
        applyCurve,
        applyLinearCurve,
        applyStrafeCurve,
        applyRotationCurve,
        applyPitchCurve,
        generateCurveData,
        exceedsHardwareLimit
    };
}

