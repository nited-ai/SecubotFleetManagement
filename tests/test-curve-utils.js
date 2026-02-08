/**
 * Unit Tests for Curve Utilities
 * 
 * Run with: node tests/test-curve-utils.js
 */

// Import the curve utilities
const {
    HARDWARE_LIMITS,
    applyCurve,
    applyLinearCurve,
    applyStrafeCurve,
    applyRotationCurve,
    generateCurveData,
    exceedsHardwareLimit
} = require('../static/js/curve-utils.js');

// Test counter
let testsPassed = 0;
let testsFailed = 0;

// Helper function to assert equality with tolerance
function assertClose(actual, expected, tolerance = 0.01, testName = '') {
    const diff = Math.abs(actual - expected);
    if (diff <= tolerance) {
        console.log(`✅ PASS: ${testName}`);
        testsPassed++;
        return true;
    } else {
        console.error(`❌ FAIL: ${testName}`);
        console.error(`   Expected: ${expected}, Got: ${actual}, Diff: ${diff}`);
        testsFailed++;
        return false;
    }
}

// Helper function to assert exact equality
function assertEqual(actual, expected, testName = '') {
    if (actual === expected) {
        console.log(`✅ PASS: ${testName}`);
        testsPassed++;
        return true;
    } else {
        console.error(`❌ FAIL: ${testName}`);
        console.error(`   Expected: ${expected}, Got: ${actual}`);
        testsFailed++;
        return false;
    }
}

console.log('🧪 Running Curve Utilities Unit Tests...\n');

// Test 1: Deadzone behavior
console.log('Test Group 1: Deadzone Behavior');
assertEqual(applyCurve(0.05, 1.5, 0.10, 1.5, 5.0), 0, 'Input below deadzone (5%) should return 0');
assertEqual(applyCurve(0.09, 1.5, 0.10, 1.5, 5.0), 0, 'Input just below deadzone (9%) should return 0');
assertClose(applyCurve(0.10, 1.5, 0.10, 1.5, 5.0), 0, 0.01, 'Input at deadzone (10%) should return ~0');
console.log('');

// Test 2: Linear curve (alpha = 1.0)
console.log('Test Group 2: Linear Curve (alpha = 1.0)');
assertClose(applyCurve(0.5, 1.0, 0.0, 1.0, 5.0), 0.5, 0.01, 'Linear curve at 50% input should return 50% output');
assertClose(applyCurve(1.0, 1.0, 0.0, 1.0, 5.0), 1.0, 0.01, 'Linear curve at 100% input should return 100% output');
console.log('');

// Test 3: Exponential curve (alpha > 1.0)
console.log('Test Group 3: Exponential Curve (alpha = 2.0)');
// With alpha=2.0, 50% input should give 25% output (0.5^2 = 0.25)
assertClose(applyCurve(0.5, 2.0, 0.0, 1.0, 5.0), 0.25, 0.01, 'Exponential curve (α=2.0) at 50% input should return 25% output');
assertClose(applyCurve(1.0, 2.0, 0.0, 1.0, 5.0), 1.0, 0.01, 'Exponential curve (α=2.0) at 100% input should return 100% output');
console.log('');

// Test 4: Concave curve (alpha < 1.0)
console.log('Test Group 4: Concave Curve (alpha = 0.5)');
// With alpha=0.5 (square root), 25% input should give 50% output (sqrt(0.25) = 0.5)
assertClose(applyCurve(0.25, 0.5, 0.0, 1.0, 5.0), 0.5, 0.01, 'Concave curve (α=0.5) at 25% input should return 50% output');
assertClose(applyCurve(1.0, 0.5, 0.0, 1.0, 5.0), 1.0, 0.01, 'Concave curve (α=0.5) at 100% input should return 100% output');
console.log('');

// Test 5: Hardware limit clamping
console.log('Test Group 5: Hardware Limit Clamping');
assertEqual(applyCurve(1.0, 1.0, 0.0, 10.0, 5.0), 5.0, 'Output should be clamped to hardware limit (5.0)');
assertEqual(applyCurve(1.0, 1.0, 0.0, 3.0, 5.0), 3.0, 'Output below hardware limit should not be clamped');
console.log('');

// Test 6: Deadzone with exponential curve
console.log('Test Group 6: Deadzone + Exponential Curve');
// With deadzone=0.1, input=0.55 maps to normalized=(0.55-0.1)/(1.0-0.1)=0.5
// With alpha=2.0, output=0.5^2=0.25, scaled to max=1.5 gives 0.375
assertClose(applyCurve(0.55, 2.0, 0.10, 1.5, 5.0), 0.375, 0.01, 'Deadzone + exponential curve should work correctly');
console.log('');

// Test 7: Axis-specific functions
console.log('Test Group 7: Axis-Specific Functions');
assertClose(applyLinearCurve(1.0, 1.0, 0.0, 10.0), 5.0, 0.01, 'Linear curve should clamp to 5.0 m/s hardware limit');
assertClose(applyStrafeCurve(1.0, 1.0, 0.0, 10.0), 0.6, 0.01, 'Strafe curve should clamp to 0.6 m/s hardware limit');
assertClose(applyRotationCurve(1.0, 1.0, 0.0, 10.0), 3.0, 0.01, 'Rotation curve should clamp to 3.0 rad/s hardware limit');
console.log('');

// Test 8: Hardware limit detection
console.log('Test Group 8: Hardware Limit Detection');
assertEqual(exceedsHardwareLimit(10.0, 5.0), true, 'Should detect when max velocity exceeds hardware limit');
assertEqual(exceedsHardwareLimit(3.0, 5.0), false, 'Should not flag when max velocity is below hardware limit');
assertEqual(exceedsHardwareLimit(5.0, 5.0), false, 'Should not flag when max velocity equals hardware limit');
console.log('');

// Test 9: Curve data generation
console.log('Test Group 9: Curve Data Generation');
const curveData = generateCurveData(1.5, 0.10, 1.5, 5.0, 10);
assertEqual(curveData.length, 11, 'Should generate correct number of data points (10 intervals = 11 points)');
assertEqual(curveData[0].input, 0, 'First data point should have input=0');
assertEqual(curveData[10].input, 1, 'Last data point should have input=1');
assertEqual(curveData[0].output, 0, 'First data point should have output=0 (below deadzone)');
console.log('');

// Test 10: Real-world scenario - Normal preset
console.log('Test Group 10: Real-World Scenario - Normal Preset');
// Normal preset: linear_alpha=1.5, deadzone=0.10, max=1.5 m/s
// At 50% input (0.5):
// normalized = (0.5 - 0.1) / (1.0 - 0.1) = 0.4 / 0.9 = 0.444
// curved = 0.444^1.5 = 0.296
// output = 0.296 * 1.5 = 0.444 m/s
assertClose(applyLinearCurve(0.5, 1.5, 0.10, 1.5), 0.444, 0.01, 'Normal preset at 50% input should give ~0.44 m/s');
console.log('');

// Test 11: Real-world scenario - Sport preset
console.log('Test Group 11: Real-World Scenario - Sport Preset');
// Sport preset: rotation_alpha=1.5, deadzone=0.05, max=3.0 rad/s
// At 100% input (1.0):
// normalized = (1.0 - 0.05) / (1.0 - 0.05) = 1.0
// curved = 1.0^1.5 = 1.0
// output = 1.0 * 3.0 = 3.0 rad/s (at hardware limit)
assertClose(applyRotationCurve(1.0, 1.5, 0.05, 3.0), 3.0, 0.01, 'Sport preset at 100% input should give 3.0 rad/s');
console.log('');

// Summary
console.log('═══════════════════════════════════════');
console.log(`✅ Tests Passed: ${testsPassed}`);
console.log(`❌ Tests Failed: ${testsFailed}`);
console.log(`📊 Total Tests: ${testsPassed + testsFailed}`);
console.log('═══════════════════════════════════════');

if (testsFailed === 0) {
    console.log('🎉 All tests passed!');
    process.exit(0);
} else {
    console.log('⚠️  Some tests failed!');
    process.exit(1);
}

