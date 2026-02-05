/**
 * Curve Visualizer Module
 * Creates and updates Chart.js graphs for exponential response curves
 */

// Store chart instances
const charts = {
    linear: null,
    strafe: null,
    rotation: null
};

/**
 * Create a curve chart for a specific axis
 * @param {string} canvasId - Canvas element ID
 * @param {string} axisName - Axis name (Linear, Strafe, Rotation)
 * @param {string} unit - Unit of measurement (m/s or rad/s)
 * @param {number} alpha - Exponential factor
 * @param {number} deadzone - Deadzone threshold (0.0 to 0.3)
 * @param {number} maxVelocity - Maximum velocity
 * @param {number} hardwareLimit - Hardware limit
 * @returns {Chart} Chart.js instance
 */
function createCurveChart(canvasId, axisName, unit, alpha, deadzone, maxVelocity, hardwareLimit) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error(`Canvas not found: ${canvasId}`);
        return null;
    }

    const ctx = canvas.getContext('2d');
    
    // Generate curve data
    const curveData = generateCurveData(alpha, deadzone, maxVelocity, hardwareLimit, 100);
    
    // Extract x and y values
    const inputPercentages = curveData.map(d => d.input * 100);
    const outputVelocities = curveData.map(d => d.output);
    
    // Create chart
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: inputPercentages,
            deadzone: deadzone, // Store deadzone for plugin access
            datasets: [{
                label: `${axisName} Output (${unit})`,
                data: outputVelocities,
                borderColor: '#00E8DA',
                backgroundColor: 'rgba(0, 232, 218, 0.2)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `${axisName} (α=${alpha.toFixed(1)})`,
                    color: '#ffffff',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.parsed.x.toFixed(0)}% input → ${context.parsed.y.toFixed(2)} ${unit}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Input (%)',
                        color: '#ffffff'
                    },
                    ticks: {
                        color: '#ffffff',
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: `Output (${unit})`,
                        color: '#ffffff'
                    },
                    ticks: {
                        color: '#ffffff'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    beginAtZero: true,
                    max: Math.max(maxVelocity, hardwareLimit) * 1.1
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        },
        plugins: [{
            id: 'deadzoneLine',
            afterDraw: (chart) => {
                // Get current deadzone from chart's custom data
                const currentDeadzone = chart.config._config.data.deadzone || 0;
                if (currentDeadzone > 0) {
                    const ctx = chart.ctx;
                    const xAxis = chart.scales.x;
                    const yAxis = chart.scales.y;
                    const deadzoneX = xAxis.getPixelForValue(currentDeadzone * 100);

                    ctx.save();
                    ctx.strokeStyle = '#ef4444';
                    ctx.lineWidth = 2;
                    ctx.setLineDash([5, 5]);
                    ctx.beginPath();
                    ctx.moveTo(deadzoneX, yAxis.top);
                    ctx.lineTo(deadzoneX, yAxis.bottom);
                    ctx.stroke();
                    ctx.restore();
                }
            }
        }]
    });
    
    return chart;
}

/**
 * Update an existing curve chart
 * @param {Chart} chart - Chart.js instance
 * @param {string} axisName - Axis name
 * @param {number} alpha - Exponential factor
 * @param {number} deadzone - Deadzone threshold
 * @param {number} maxVelocity - Maximum velocity
 * @param {number} hardwareLimit - Hardware limit
 */
function updateCurveChart(chart, axisName, alpha, deadzone, maxVelocity, hardwareLimit) {
    if (!chart) return;

    // Generate new curve data
    const curveData = generateCurveData(alpha, deadzone, maxVelocity, hardwareLimit, 100);
    const outputVelocities = curveData.map(d => d.output);

    // Update chart data
    chart.data.datasets[0].data = outputVelocities;
    chart.data.deadzone = deadzone; // Update deadzone for plugin
    chart.options.plugins.title.text = `${axisName} (α=${alpha.toFixed(1)})`;
    chart.options.scales.y.max = Math.max(maxVelocity, hardwareLimit) * 1.1;

    // Update chart
    chart.update('none'); // 'none' for instant update without animation
}

