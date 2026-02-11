/**
 * WebSocket Client Module
 * Handles Socket.IO connection and command transmission
 */

class WebSocketClient {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.useWebSocket = true;
        this.currentCommandStartTime = 0;
        this.commandLatencies = [];
        this.onLatencyUpdate = null; // Callback for latency updates
    }

    /**
     * Initialize Socket.IO connection
     */
    initialize() {
        // Load Socket.IO from CDN
        if (typeof io === 'undefined') {
            console.error('Socket.IO library not loaded');
            return false;
        }

        this.socket = io();

        // Connection event handlers
        this.socket.on('connect', () => {
            console.log('✅ WebSocket connected');
            this.connected = true;
            this.useWebSocket = true;
        });

        this.socket.on('disconnect', () => {
            console.log('❌ WebSocket disconnected');
            this.connected = false;
            this.useWebSocket = false; // Fallback to HTTP
        });

        this.socket.on('reconnect', () => {
            console.log('🔄 WebSocket reconnected');
            this.connected = true;
            this.useWebSocket = true;
        });

        // Command response handler for latency measurement
        this.socket.on('command_response', (data) => {
            if (this.currentCommandStartTime > 0) {
                const latency = performance.now() - this.currentCommandStartTime;
                this.updateLatency(latency, 'WebSocket');
                this.currentCommandStartTime = 0;
            }
        });

        // Obstacle avoidance state update handler
        this.socket.on('obstacle_avoid_state_update', (data) => {
            if (typeof updateObstacleAvoidanceState === 'function') {
                updateObstacleAvoidanceState(data.enabled);
            }
        });

        console.log('WebSocket client initialized');
        return true;
    }

    /**
     * Send control command via WebSocket
     * @param {Object} commandData - Command data {lx, ly, rx, ry, ...}
     * @returns {boolean} - Success status
     */
    sendCommand(commandData) {
        if (!this.connected) {
            console.warn('[WebSocket] Not connected, cannot send command');
            return false;
        }

        // Track start time for latency measurement
        this.currentCommandStartTime = performance.now();

        // High-frequency log (30-60Hz) - commented out to reduce console noise
        // Uncomment for debugging control flow/latency issues
        // console.log('[WebSocket] Emitting control_command:', commandData);

        // Emit command
        this.socket.emit('control_command', commandData);

        return true;
    }

    /**
     * Update latency tracking
     * @param {number} latency - Latency in milliseconds
     * @param {string} method - 'WebSocket' or 'HTTP'
     */
    updateLatency(latency, method) {
        // Track latency history (last 10 commands)
        this.commandLatencies.push(latency);
        if (this.commandLatencies.length > 10) {
            this.commandLatencies.shift();
        }

        // Calculate average latency
        const avgLatency = this.commandLatencies.reduce((a, b) => a + b, 0) / this.commandLatencies.length;

        // Call callback if provided
        if (this.onLatencyUpdate) {
            this.onLatencyUpdate({
                current: latency,
                average: avgLatency,
                method: method
            });
        }

        // High-frequency log (30-60Hz) - commented out to reduce console noise
        // Uncomment for debugging control flow/latency issues
        // console.log(`Latency (${method}): ${latency.toFixed(0)}ms (avg: ${avgLatency.toFixed(0)}ms)`);
    }

    /**
     * Check if WebSocket is connected
     * @returns {boolean}
     */
    isConnected() {
        return this.connected;
    }

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.connected = false;
        }
    }
}

// Export singleton instance
const websocketClient = new WebSocketClient();

