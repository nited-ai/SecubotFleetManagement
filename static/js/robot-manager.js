/**
 * Robot Manager Module
 * Handles CRUD operations for robot data in LocalStorage
 * 
 * LocalStorage Schema:
 * Key: 'unitree_robots'
 * Value: { robots: [...] }
 */

const STORAGE_KEY = 'unitree_robots';

/**
 * Load all robots from LocalStorage
 * @returns {Array} Array of robot objects
 */
function loadRobots() {
    try {
        const data = localStorage.getItem(STORAGE_KEY);
        if (!data) {
            // Initialize with empty array if no data exists
            const initialData = { robots: [] };
            localStorage.setItem(STORAGE_KEY, JSON.stringify(initialData));
            return [];
        }
        const parsed = JSON.parse(data);
        return parsed.robots || [];
    } catch (error) {
        console.error('Error loading robots from LocalStorage:', error);
        return [];
    }
}

/**
 * Save a robot to LocalStorage (create or update)
 * @param {Object} robot - Robot object to save
 * @param {string} robot.id - UUID (optional for new robots, will be generated)
 * @param {string} robot.name - Robot name
 * @param {string} robot.connectionMethod - Connection method (LocalAP, LocalSTA, Remote)
 * @param {string} robot.ip - Robot IP address
 * @param {string} robot.serialNumber - Robot serial number
 * @param {string} robot.username - Username (for Remote only)
 * @param {string} robot.password - Password (for Remote only)
 * @returns {Object} Saved robot object with ID
 */
function saveRobot(robot) {
    try {
        const robots = loadRobots();
        
        // If no ID, this is a new robot - generate UUID and timestamps
        if (!robot.id) {
            robot.id = crypto.randomUUID();
            robot.createdAt = new Date().toISOString();
            robot.lastConnected = null;
            robots.push(robot);
        } else {
            // Update existing robot
            const index = robots.findIndex(r => r.id === robot.id);
            if (index !== -1) {
                // Preserve createdAt and lastConnected if not provided
                robot.createdAt = robot.createdAt || robots[index].createdAt;
                robot.lastConnected = robot.lastConnected || robots[index].lastConnected;
                robots[index] = robot;
            } else {
                console.error(`Robot with ID ${robot.id} not found`);
                return null;
            }
        }
        
        // Save to LocalStorage
        localStorage.setItem(STORAGE_KEY, JSON.stringify({ robots }));
        console.log('Robot saved:', robot);
        return robot;
    } catch (error) {
        console.error('Error saving robot to LocalStorage:', error);
        return null;
    }
}

/**
 * Delete a robot from LocalStorage
 * @param {string} robotId - UUID of robot to delete
 * @returns {boolean} True if deleted successfully
 */
function deleteRobot(robotId) {
    try {
        const robots = loadRobots();
        const index = robots.findIndex(r => r.id === robotId);
        
        if (index === -1) {
            console.error(`Robot with ID ${robotId} not found`);
            return false;
        }
        
        robots.splice(index, 1);
        localStorage.setItem(STORAGE_KEY, JSON.stringify({ robots }));
        console.log(`Robot ${robotId} deleted`);
        return true;
    } catch (error) {
        console.error('Error deleting robot from LocalStorage:', error);
        return false;
    }
}

/**
 * Get a single robot by ID
 * @param {string} robotId - UUID of robot to retrieve
 * @returns {Object|null} Robot object or null if not found
 */
function getRobot(robotId) {
    try {
        const robots = loadRobots();
        const robot = robots.find(r => r.id === robotId);
        return robot || null;
    } catch (error) {
        console.error('Error getting robot from LocalStorage:', error);
        return null;
    }
}

/**
 * Update the lastConnected timestamp for a robot
 * @param {string} robotId - UUID of robot to update
 * @returns {boolean} True if updated successfully
 */
function updateLastConnected(robotId) {
    try {
        const robot = getRobot(robotId);
        if (!robot) {
            console.error(`Robot with ID ${robotId} not found`);
            return false;
        }
        
        robot.lastConnected = new Date().toISOString();
        saveRobot(robot);
        console.log(`Updated lastConnected for robot ${robotId}`);
        return true;
    } catch (error) {
        console.error('Error updating lastConnected:', error);
        return false;
    }
}

// Export functions for use in other modules
// (In a module system, these would be exported. For now, they're global)
console.log('Robot Manager module loaded');

