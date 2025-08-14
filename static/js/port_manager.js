/**
 * Port selection and connection management
 */

class PortManager {
    constructor() {
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
            this.updateStatus('Connected', 'success');
        } else {
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
        this.portSelect.addEventListener('change', async () => {
            const selectedPort = this.portSelect.value;
            if (selectedPort) {
                await this.testPort(selectedPort);
            }
        });
        
        if (this.connectButton) {
            this.connectButton.addEventListener('click', async () => {
                const selectedPort = this.portSelect.value;
                if (selectedPort) {
                    await this.connect(selectedPort);
                }
            });
        }
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
            
            // Try connecting up to 3 times
            for (let attempt = 1; attempt <= 3; attempt++) {
                console.log(`Connection attempt ${attempt}/3`);
                
                try {
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
                        this.isConnecting = false;
                        return; // Successfully connected
                    }
                } catch (error) {
                    console.error(`Attempt ${attempt} failed:`, error);
                    if (attempt < 3) {
                        await new Promise(resolve => setTimeout(resolve, 100)); // Wait 100ms before retry
                    }
                }
            }
            
            // If we get here, all attempts failed
            connectionState.updateState(false, null, null);
            this.updateStatus('Connection failed after 3 attempts', 'error');
        } catch (error) {
            console.error('Error in connect process:', error);
            connectionState.updateState(false, null, null);
            this.updateStatus('Connection error', 'error');
        } finally {
            this.isConnecting = false;
        }
    }
    
    updateStatus(message, type = 'info') {
        if (this.statusElement) {
            this.statusElement.textContent = message;
            this.statusElement.className = `status status-${type}`;
        }
    }
}

// Initialize port manager when page loads
document.addEventListener('DOMContentLoaded', () => {
    new PortManager();
});
