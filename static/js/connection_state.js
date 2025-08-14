/**
 * Global connection state management
 */
class ConnectionState {
    constructor() {
        this._isConnected = false;
        this._currentPort = null;
        this._currentBaudRate = 115200;
        this._listeners = [];
    }

    // Get current state
    get isConnected() {
        return this._isConnected;
    }

    get currentPort() {
        return this._currentPort;
    }

    get currentBaudRate() {
        return this._currentBaudRate;
    }

    // Update state
    updateState(isConnected, port = null, baudRate = null) {
        this._isConnected = isConnected;
        if (port !== null) this._currentPort = port;
        if (baudRate !== null) this._currentBaudRate = baudRate;
        this._notifyListeners();
    }

    // Add listener for state changes
    addListener(callback) {
        this._listeners.push(callback);
    }

    // Remove listener
    removeListener(callback) {
        this._listeners = this._listeners.filter(cb => cb !== callback);
    }

    // Notify all listeners of state change
    _notifyListeners() {
        const state = {
            isConnected: this._isConnected,
            currentPort: this._currentPort,
            currentBaudRate: this._currentBaudRate
        };
        this._listeners.forEach(callback => callback(state));
    }

    // Initialize state from server
    async initializeFromServer() {
        try {
            const response = await fetch('/api/connection/status');
            const data = await response.json();
            this.updateState(data.connected, data.port, data.baud_rate);
        } catch (error) {
            console.error('Failed to initialize connection state:', error);
        }
    }
}

// Create singleton instance
const connectionState = new ConnectionState();

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    connectionState.initializeFromServer();
});
