/**
 * Port selection and connection management
 */

class PortManager {
    constructor() {
        // Singleton pattern - prevent multiple instances
        if (PortManager.instance) {
            console.log('PortManager singleton already exists, returning existing instance');
            return PortManager.instance;
        }
        
        console.log('Initializing PortManager...');
        this.portSelect = document.getElementById('port-select');
        this.connectButton = document.getElementById('connect-btn');
        this.statusElement = document.getElementById('connection-status');
        this.baudSelect = document.getElementById('baud-select');
        
        if (!this.portSelect) {
            console.error('Port select element not found!');
            return;
        }
        
        // Listen for connection state changes
        connectionState.addListener(this.onConnectionStateChange.bind(this));
        
        console.log('Found port select element:', this.portSelect);
        this.init();
        
        // Store the singleton instance
        PortManager.instance = this;
    }
    
    onConnectionStateChange(state) {
        if (state.isConnected) {
            // Update port select to show connected port
            if (state.currentPort && this.portSelect.value !== state.currentPort) {
                this.portSelect.value = state.currentPort;
            }
            // Update baud rate if available
            if (state.currentBaudRate && this.baudSelect) {
                this.baudSelect.value = state.currentBaudRate;
            }
            // Update connect button to show disconnect
            if (this.connectButton && !this.isConnecting) {
                this.connectButton.innerHTML = '<i class="fas fa-unlink"></i> Disconnect';
            }
            this.updateStatus('Connected', 'success');
        } else {
            // Update connect button to show connect
            if (this.connectButton && !this.isConnecting) {
                this.connectButton.innerHTML = '<i class="fas fa-link"></i> Connect';
            }
            this.updateStatus('Not Connected', 'error');
        }
    }
    
    async init() {
        console.log('Starting initialization...');
        
        // Check current connection status first
        try {
            const response = await fetch('/api/connection/status');
            const status = await response.json();
            if (status.success && status.connected) {
                // Make sure the connected port is in the select options
                const option = document.createElement('option');
                option.value = status.port;
                option.textContent = status.port;
                this.portSelect.innerHTML = ''; // Clear default option
                this.portSelect.appendChild(option);
                
                // Update connection state
                connectionState.setState({
                    isConnected: true,
                    currentPort: status.port,
                    currentBaudRate: status.baud_rate
                });
            }
        } catch (error) {
            console.error('Error checking connection status:', error);
        }
        
        // Then load all available ports
        await this.loadPorts();
        this.setupEventListeners();
        console.log('Initialization complete');
    }
    
    async loadPorts() {
        console.log('Loading available ports...');
        try {
            console.log('Fetching ports from /api/ports');
            const response = await fetch('/api/ports');
            console.log('Response received:', response.status);
            const data = await response.json();
            console.log('Port data:', data);
            
            if (data.status === 'success') {
                // Keep the currently selected port if any
                const currentPort = this.portSelect.value;
                
                // Clear and add default option only if no port is currently selected
                if (!currentPort) {
                    this.portSelect.innerHTML = '<option value="">Select port...</option>';
                } else {
                    this.portSelect.innerHTML = '';
                }
                
                // Add all available ports
                data.ports.forEach(port => {
                    // Skip if this port is already in the list (avoid duplicates)
                    if (!this.portSelect.querySelector(`option[value="${port.device}"]`)) {
                        const option = document.createElement('option');
                        option.value = port.device;
                        option.textContent = `${port.device} - ${port.description}`;
                        this.portSelect.appendChild(option);
                    }
                });
                
                // Restore the selected port if it was set
                if (currentPort) {
                    this.portSelect.value = currentPort;
                }
            } else {
                console.error('Failed to load ports:', data.message);
            }
        } catch (error) {
            console.error('Error loading ports:', error);
        }
    }
    
    setupEventListeners() {
        // Remove any existing event listeners first to prevent duplicates
        if (this.connectButton) {
            // Clone the button to remove all event listeners
            const newButton = this.connectButton.cloneNode(true);
            this.connectButton.parentNode.replaceChild(newButton, this.connectButton);
            this.connectButton = newButton;
            
            this.connectButton.addEventListener('click', async () => {
                // Check if we're currently connected
                if (connectionState.isConnected) {
                    await this.disconnect();
                } else {
                    const selectedPort = this.portSelect.value;
                    if (selectedPort) {
                        await this.connect(selectedPort);
                    }
                }
            });
        }
        
        this.portSelect.addEventListener('change', async () => {
            const selectedPort = this.portSelect.value;
            if (selectedPort) {
                await this.testPort(selectedPort);
            }
        });
    }
    
    // Static method to clear singleton instance
    static clearInstance() {
        PortManager.instance = null;
    }
    
    async testPort(port) {
        try {
            const response = await fetch(`/api/ports/test/${port}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.updateStatus('Port available', 'success');
            } else {
                this.updateStatus('Port not available', 'error');
            }
        } catch (error) {
            console.error('Error testing port:', error);
            this.updateStatus('Error testing port', 'error');
        }
    }
    
    // Flag to track connection attempt in progress
    isConnecting = false;

    async connect(port) {
        // If already trying to connect, return
        if (this.isConnecting) {
            console.log('Connection attempt already in progress');
            return;
        }
        
        this.isConnecting = true;
        
        try {
            const baudRate = this.baudSelect ? parseInt(this.baudSelect.value) : 115200;
            
            // Update UI to show connecting state
            if (this.connectButton) {
                this.connectButton.disabled = true;
                this.connectButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting...';
            }
            if (this.portSelect) this.portSelect.disabled = true;
            if (this.baudSelect) this.baudSelect.disabled = true;
            
            console.log(`Attempting to connect to ${port} at ${baudRate} baud`);
            
            const response = await fetch('/api/connection/connect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    port,
                    baud_rate: baudRate
                })
            });
            
            const data = await response.json();
            if (data.success) {
                // Update global connection state
                connectionState.updateState(true, port, baudRate);
                this.updateStatus('Connected', 'success');
            } else {
                throw new Error(data.error || 'Connection failed');
            }
        } catch (error) {
            console.error('Connection error:', error);
            connectionState.updateState(false, null, null);
            this.updateStatus(`Connection failed: ${error.message}`, 'error');
        } finally {
            this.isConnecting = false;
            // Re-enable UI elements
            if (this.connectButton) {
                this.connectButton.disabled = false;
                this.connectButton.innerHTML = connectionState.isConnected ? 
                    '<i class="fas fa-unlink"></i> Disconnect' : 
                    '<i class="fas fa-link"></i> Connect';
            }
            if (this.portSelect) this.portSelect.disabled = false;
            if (this.baudSelect) this.baudSelect.disabled = false;
        }
    }
    
    async disconnect() {
        if (this.isConnecting) {
            console.log('Connection operation in progress, cannot disconnect');
            return;
        }
        
        this.isConnecting = true;
        
        try {
            // Update UI to show disconnecting state
            if (this.connectButton) {
                this.connectButton.disabled = true;
                this.connectButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Disconnecting...';
            }
            
            console.log('Attempting to disconnect');
            
            const response = await fetch('/api/connection/disconnect', {
                method: 'POST'
            });
            
            const data = await response.json();
            if (data.success) {
                // Update global connection state
                connectionState.updateState(false, null, null);
                this.updateStatus('Disconnected', 'info');
            } else {
                throw new Error(data.error || 'Disconnection failed');
            }
        } catch (error) {
            console.error('Disconnection error:', error);
            this.updateStatus(`Disconnection failed: ${error.message}`, 'error');
        } finally {
            this.isConnecting = false;
            // Re-enable UI elements
            if (this.connectButton) {
                this.connectButton.disabled = false;
                this.connectButton.innerHTML = connectionState.isConnected ? 
                    '<i class="fas fa-unlink"></i> Disconnect' : 
                    '<i class="fas fa-link"></i> Connect';
            }
        }
    }
    
    updateStatus(message, type = 'info') {
        if (this.statusElement) {
            this.statusElement.textContent = message;
            this.statusElement.className = `status status-${type}`;
        }
    }
}

// Initialize port manager when page loads (singleton pattern)
document.addEventListener('DOMContentLoaded', () => {
    // Clear any existing instance first
    PortManager.clearInstance();
    new PortManager();
});
