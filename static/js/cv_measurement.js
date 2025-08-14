/**
 * CV Measurement JavaScript for H743Poten Web Interface
 * Handles Cyclic Voltammetry measurement controls and real-time plotting
 */

class CVMeasurement {
    constructor() {
        this.isRunning = false;
        this.isPaused = false;
        this.currentParams = null;
        this.plotData = {
            x: [], // Potential (V)
            y: [], // Current (A)
            cycle: [], // Cycle number
            direction: [] // Scan direction
        };
        this.dataUpdateInterval = null;
        this.statusUpdateInterval = null;
        this.plotInitialized = false; // Track plot initialization
        
        this.initializeUI();
        this.initializePlot();
    }
    
    initializeUI() {
        console.log('Initializing CV UI...');
        
        // Get CV parameter inputs
        this.beginInput = document.getElementById('cv-begin');
        this.upperInput = document.getElementById('cv-upper');
        this.lowerInput = document.getElementById('cv-lower');
        this.rateInput = document.getElementById('cv-rate');
        this.cyclesInput = document.getElementById('cv-cycles');
        
        console.log('CV inputs found:', {
            begin: !!this.beginInput,
            upper: !!this.upperInput,
            lower: !!this.lowerInput,
            rate: !!this.rateInput,
            cycles: !!this.cyclesInput
        });
        
        // Get CV control buttons
        this.startBtn = document.getElementById('cv-start-btn');
        this.stopBtn = document.getElementById('cv-stop-btn');
        this.pauseBtn = document.getElementById('cv-pause-btn');
        this.exportBtn = document.getElementById('cv-export-btn');
        
        console.log('CV buttons found:', {
            start: !!this.startBtn,
            stop: !!this.stopBtn,
            pause: !!this.pauseBtn,
            export: !!this.exportBtn
        });
        
        // Get status elements
        this.statusText = document.getElementById('cv-status');
        this.progressText = document.getElementById('cv-progress');
        
        // Bind event listeners
        this.startBtn?.addEventListener('click', () => this.startMeasurement());
        this.stopBtn?.addEventListener('click', () => this.stopMeasurement());
        this.pauseBtn?.addEventListener('click', () => this.togglePause());
        this.exportBtn?.addEventListener('click', () => this.exportData());
        
        // Parameter validation on input
        [this.beginInput, this.upperInput, this.lowerInput, this.rateInput, this.cyclesInput]
            .forEach(input => {
                if (input) {
                    input.addEventListener('input', () => {
                        console.log('Input changed:', input.id, input.value);
                        this.validateParameters();
                    });
                }
            });
        
        // Add debug button for manual enable (temporary)
        const debugBtn = document.createElement('button');
        debugBtn.textContent = 'Force Enable CV (Debug)';
        debugBtn.className = 'btn btn-outline-info btn-sm mt-2';
        debugBtn.onclick = () => {
            console.log('Force enabling CV start button...');
            if (this.startBtn) {
                this.startBtn.disabled = false;
                this.showMessage('CV button force enabled for testing', 'info');
            }
        };
        
        // Add plot debug button
        const plotDebugBtn = document.createElement('button');
        plotDebugBtn.textContent = 'Debug Plot Data';
        plotDebugBtn.className = 'btn btn-outline-warning btn-sm mt-2';
        plotDebugBtn.onclick = () => {
            console.log('Plot Debug Info:');
            console.log('Plot data length:', this.plotData.x.length);
            console.log('Plot initialized:', this.plotInitialized);
            console.log('Plot div:', this.plotDiv);
            console.log('Current traces:', this.plotDiv?.data?.length || 0);
            console.log('Cycles in data:', [...new Set(this.plotData.cycle)]);
            console.log('Last 5 points:', {
                x: this.plotData.x.slice(-5),
                y: this.plotData.y.slice(-5),
                cycle: this.plotData.cycle.slice(-5)
            });
            
            // Force recreate plot
            this.createInitialPlot();
            this.showMessage('Plot debug info logged to console', 'info');
        };
        
        // Add to CV controls
        const cvControls = document.getElementById('cv-controls');
        if (cvControls) {
            cvControls.appendChild(debugBtn);
            cvControls.appendChild(plotDebugBtn);
        }
        
        // Initial parameter validation
        setTimeout(() => {
            console.log('Running initial validation...');
            this.validateParameters();
        }, 100);
    }
    
    initializePlot() {
        const plotDiv = document.getElementById('cv-plot');
        if (!plotDiv) return;
        
        const layout = {
            title: 'Cyclic Voltammetry',
            xaxis: {
                title: 'Potential (V)',
                showgrid: true
            },
            yaxis: {
                title: 'Current (A)', 
                showgrid: true
            },
            showlegend: true,
            autosize: true,
            margin: { l: 60, r: 40, t: 40, b: 60 }
        };
        
        const config = {
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['lasso2d', 'select2d']
        };
        
        // Initialize empty plot
        Plotly.newPlot(plotDiv, [], layout, config);
        
        this.plotDiv = plotDiv;
    }
    
    async validateParameters() {
        try {
            const params = this.getParameters();
            if (!params) {
                console.warn('Cannot get parameters for validation');
                return false;
            }
            
            const response = await fetch('/api/cv/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ params })
            });
            
            if (!response.ok) {
                console.error('Validation request failed:', response.status);
                this.showValidationError('Validation request failed');
                return false;
            }
            
            const result = await response.json();
            console.log('Validation result:', result);
            
            // Update validation UI
            const validationElement = document.getElementById('cv-validation');
            if (validationElement) {
                if (result.valid) {
                    validationElement.innerHTML = `
                        <div class="alert alert-success">
                            <i class="fas fa-check-circle"></i> ${result.message || 'Parameters valid'}
                        </div>
                    `;
                } else {
                    validationElement.innerHTML = `
                        <div class="alert alert-warning">
                            <i class="fas fa-exclamation-triangle"></i> ${result.message || 'Invalid parameters'}
                        </div>
                    `;
                }
            }
            
            // Enable/disable start button
            if (this.startBtn) {
                this.startBtn.disabled = !result.valid || this.isRunning;
            }
            
            return result.valid;
            
        } catch (error) {
            console.error('Parameter validation failed:', error);
            this.showValidationError('Validation failed: ' + error.message);
            return false;
        }
    }
    
    showValidationError(message) {
        const validationElement = document.getElementById('cv-validation');
        if (validationElement) {
            validationElement.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle"></i> ${message}
                </div>
            `;
        }
        
        if (this.startBtn) {
            this.startBtn.disabled = true;
        }
    }
    
    getParameters() {
        console.log('Getting CV parameters...');
        
        if (!this.beginInput || !this.upperInput || !this.lowerInput || 
            !this.rateInput || !this.cyclesInput) {
            console.error('CV input elements not found');
            return null;
        }
        
        const params = {
            begin: parseFloat(this.beginInput.value) || 0.0,
            upper: parseFloat(this.upperInput.value) || 1.0,
            lower: parseFloat(this.lowerInput.value) || -1.0,
            rate: parseFloat(this.rateInput.value) || 0.1,
            cycles: parseInt(this.cyclesInput.value) || 1
        };
        
        console.log('CV parameters:', params);
        return params;
    }
    
    async startMeasurement() {
        try {
            // Check connection using multiple methods
            let isConnected = false;
            
            // Method 1: PortManager
            if (window.portManager && typeof window.portManager.isConnected === 'boolean') {
                isConnected = window.portManager.isConnected;
            }
            // Method 2: API call to check connection
            else {
                try {
                    const response = await fetch('/api/connection/status');
                    const status = await response.json();
                    isConnected = status.connected;
                } catch (e) {
                    console.warn('Failed to check connection status:', e);
                }
            }
            
            console.log('Connection check result:', isConnected);
            
            if (!isConnected) {
                this.showMessage('Please connect to device first', 'warning');
                return;
            }
            
            // Validate parameters
            const isValid = await this.validateParameters();
            if (!isValid) {
                this.showMessage('Please fix parameter validation errors', 'warning');
                return;
            }
            
            const params = this.getParameters();
            this.currentParams = params;
            
            console.log('Starting CV measurement with params:', params);
            
            // Setup measurement
            const setupResponse = await fetch('/api/cv/setup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ params })
            });
            
            const setupResult = await setupResponse.json();
            console.log('CV setup result:', setupResult);
            
            if (!setupResult.success) {
                this.showMessage(`Setup failed: ${setupResult.message}`, 'error');
                return;
            }
            
            // Start measurement
            const startResponse = await fetch('/api/cv/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const startResult = await startResponse.json();
            console.log('CV start result:', startResult);
            
            if (!startResult.success) {
                this.showMessage(`Start failed: ${startResult.message}`, 'error');
                return;
            }
            
            // Update UI state
            this.isRunning = true;
            this.isPaused = false;
            this.updateUIState();
            
            // Clear previous data
            this.clearPlotData();
            
            // Start data updates
            this.startDataUpdates();
            
            this.showMessage('CV measurement started', 'success');
            
        } catch (error) {
            console.error('Failed to start CV measurement:', error);
            this.showMessage('Failed to start measurement: ' + error.message, 'error');
        }
    }
    
    async stopMeasurement() {
        try {
            const response = await fetch('/api/cv/stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            if (!result.success) {
                this.showMessage(`Stop failed: ${result.message}`, 'error');
                return;
            }
            
            // Update UI state
            this.isRunning = false;
            this.isPaused = false;
            this.updateUIState();
            
            // Stop data updates
            this.stopDataUpdates();
            
            this.showMessage('CV measurement stopped', 'info');
            
        } catch (error) {
            console.error('Failed to stop CV measurement:', error);
            this.showMessage('Failed to stop measurement', 'error');
        }
    }
    
    async togglePause() {
        try {
            const endpoint = this.isPaused ? '/api/cv/resume' : '/api/cv/pause';
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            if (!result.success) {
                this.showMessage(`${this.isPaused ? 'Resume' : 'Pause'} failed: ${result.message}`, 'error');
                return;
            }
            
            this.isPaused = !this.isPaused;
            this.updateUIState();
            
            this.showMessage(`CV measurement ${this.isPaused ? 'paused' : 'resumed'}`, 'info');
            
        } catch (error) {
            console.error('Failed to toggle pause:', error);
            this.showMessage('Failed to toggle pause', 'error');
        }
    }
    
    async exportData() {
        try {
            const response = await fetch('/api/cv/export/csv');
            
            if (!response.ok) {
                const error = await response.json();
                this.showMessage(`Export failed: ${error.error}`, 'error');
                return;
            }
            
            // Create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `cv_measurement_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            this.showMessage('Data exported successfully', 'success');
            
        } catch (error) {
            console.error('Failed to export data:', error);
            this.showMessage('Failed to export data', 'error');
        }
    }
    
    startDataUpdates() {
        // Update data every 100ms for real-time plotting
        this.dataUpdateInterval = setInterval(async () => {
            await this.updateData();
        }, 100);
        
        // Update status every 500ms
        this.statusUpdateInterval = setInterval(async () => {
            await this.updateStatus();
        }, 500);
    }
    
    stopDataUpdates() {
        if (this.dataUpdateInterval) {
            clearInterval(this.dataUpdateInterval);
            this.dataUpdateInterval = null;
        }
        
        if (this.statusUpdateInterval) {
            clearInterval(this.statusUpdateInterval);
            this.statusUpdateInterval = null;
        }
    }
    
    async updateData() {
        try {
            const response = await fetch('/api/cv/data/stream');
            if (!response.ok) return;
            
            const result = await response.json();
            const dataPoints = result.data_points || [];
            
            if (dataPoints.length > 0) {
                // Get only new points since last update
                const currentDataLength = this.plotData.x.length;
                
                console.log(`Total points from server: ${dataPoints.length}, Current local points: ${currentDataLength}`);
                
                // If server has more points than we have locally, add the new ones
                if (dataPoints.length > currentDataLength) {
                    const newPoints = dataPoints.slice(currentDataLength);
                    console.log(`Adding ${newPoints.length} new data points`);
                    
                    // Add new data points to plot
                    newPoints.forEach((point, index) => {
                        this.plotData.x.push(point.potential);
                        this.plotData.y.push(point.current);
                        this.plotData.cycle.push(point.cycle);
                        this.plotData.direction.push(point.direction);
                        
                        // Update plot for each new point
                        this.updatePlotIncremental(point);
                    });
                }
            }
            
        } catch (error) {
            console.error('Failed to update data:', error);
        }
    }
    
    updatePlotIncremental(newPoint) {
        if (!this.plotDiv) return;
        
        const traceIndex = newPoint.cycle - 1; // Cycles start from 1, traces from 0
        const currentTraces = this.plotDiv.data || [];
        
        console.log(`Adding point to cycle ${newPoint.cycle}, trace index ${traceIndex}`);
        
        // Check if we need to add a new trace for a new cycle
        if (traceIndex >= currentTraces.length) {
            console.log(`Creating new trace for cycle ${newPoint.cycle}`);
            
            const newTrace = {
                x: [newPoint.potential],
                y: [newPoint.current],
                type: 'scatter',
                mode: 'lines+markers',
                name: `Cycle ${newPoint.cycle}`,
                line: {
                    width: 2,
                    color: newPoint.cycle === 1 ? '#007bff' : `hsl(${(newPoint.cycle - 1) * 60}, 70%, 50%)`
                },
                marker: {
                    size: 3
                }
            };
            
            try {
                Plotly.addTraces(this.plotDiv, [newTrace]);
            } catch (error) {
                console.error('Failed to add new trace:', error);
                this.createInitialPlot();
            }
        } else {
            // Extend existing trace
            try {
                Plotly.extendTraces(this.plotDiv, {
                    x: [[newPoint.potential]],
                    y: [[newPoint.current]]
                }, [traceIndex]);
            } catch (error) {
                console.error('Failed to extend trace:', error);
                this.createInitialPlot();
            }
        }
    }
    
    async updateStatus() {
        try {
            const response = await fetch('/api/cv/status');
            if (!response.ok) return;
            
            const status = await response.json();
            
            // Update status text
            if (this.statusText) {
                let statusStr = `Status: ${status.is_measuring ? 'Running' : 'Stopped'}`;
                if (status.is_paused) statusStr += ' (Paused)';
                this.statusText.textContent = statusStr;
            }
            
            // Update progress text
            if (this.progressText) {
                const progress = `Cycle: ${status.current_cycle} | Direction: ${status.scan_direction} | ` +
                              `Potential: ${status.current_potential?.toFixed(3)}V | ` +
                              `Points: ${status.data_points_count} | ` +
                              `Time: ${status.elapsed_time?.toFixed(1)}s`;
                this.progressText.textContent = progress;
            }
            
            // Update UI state if status changed
            if (this.isRunning !== status.is_measuring || this.isPaused !== status.is_paused) {
                this.isRunning = status.is_measuring;
                this.isPaused = status.is_paused;
                this.updateUIState();
                
                // Stop data updates if measurement ended
                if (!this.isRunning) {
                    this.stopDataUpdates();
                }
            }
            
        } catch (error) {
            console.error('Failed to update status:', error);
        }
    }
    
    updatePlot() {
        // This method is now mainly used for initial plot creation
        if (!this.plotDiv || this.plotData.x.length === 0) return;
        
        console.log('Creating full plot with all data');
        this.createInitialPlot();
    }
    
    createInitialPlot() {
        if (!this.plotDiv) return;
        
        console.log(`Creating initial plot with ${this.plotData.x.length} data points`);
        
        // Start with empty plot or create traces for existing data
        const traces = [];
        
        if (this.plotData.x.length > 0) {
            // Group data by cycle for different traces
            const cycles = [...new Set(this.plotData.cycle)];
            console.log('Cycles found:', cycles);
            
            cycles.forEach(cycle => {
                const cycleIndices = this.plotData.cycle.map((c, i) => c === cycle ? i : -1).filter(i => i !== -1);
                
                console.log(`Cycle ${cycle}: ${cycleIndices.length} points`);
                
                traces.push({
                    x: cycleIndices.map(i => this.plotData.x[i]),
                    y: cycleIndices.map(i => this.plotData.y[i]),
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: `Cycle ${cycle}`,
                    line: {
                        width: 2,
                        color: cycle === 1 ? '#007bff' : `hsl(${(cycle - 1) * 60}, 70%, 50%)`
                    },
                    marker: {
                        size: 3
                    }
                });
            });
        }
        
        try {
            Plotly.react(this.plotDiv, traces);
            this.plotInitialized = true;
            console.log('Plot created successfully');
        } catch (error) {
            console.error('Failed to create plot:', error);
        }
    }
    
    clearPlotData() {
        this.plotData = { x: [], y: [], cycle: [], direction: [] };
        this.plotInitialized = false;
        
        if (this.plotDiv) {
            // Clear the plot completely
            Plotly.react(this.plotDiv, []);
        }
    }
    
    updateUIState() {
        // Get connection state from multiple sources with better detection
        let isConnected = false;
        
        // Method 1: Check PortManager directly
        if (window.portManager && typeof window.portManager.isConnected === 'boolean') {
            isConnected = window.portManager.isConnected;
        }
        // Method 2: Check global connectionState
        else if (typeof connectionState !== 'undefined' && typeof connectionState.connected === 'boolean') {
            isConnected = connectionState.connected;
        }
        // Method 3: Check connection status from DOM
        else {
            const statusElement = document.getElementById('connection-status');
            if (statusElement) {
                isConnected = statusElement.textContent.includes('Connected');
            }
        }
        
        console.log('Updating CV UI state:', {
            isRunning: this.isRunning,
            isPaused: this.isPaused,
            isConnected: isConnected,
            portManager: !!window.portManager,
            connectionState: typeof connectionState !== 'undefined' ? connectionState : 'undefined'
        });
        
        // Update button states
        if (this.startBtn) {
            this.startBtn.disabled = this.isRunning || !isConnected;
            console.log('Start button disabled:', this.startBtn.disabled, 'Reasons:', {
                isRunning: this.isRunning,
                notConnected: !isConnected
            });
        }
        
        if (this.stopBtn) {
            this.stopBtn.disabled = !this.isRunning;
        }
        
        if (this.pauseBtn) {
            this.pauseBtn.disabled = !this.isRunning;
            this.pauseBtn.innerHTML = this.isPaused ? 
                '<i class="fas fa-play"></i> Resume' : 
                '<i class="fas fa-pause"></i> Pause';
        }
        
        if (this.exportBtn) {
            this.exportBtn.disabled = this.plotData.x.length === 0;
        }
        
        // Update parameter inputs (disable during measurement)
        [this.beginInput, this.upperInput, this.lowerInput, this.rateInput, this.cyclesInput]
            .forEach(input => {
                if (input) {
                    input.disabled = this.isRunning;
                }
            });
    }
    
    showMessage(message, type = 'info') {
        // Show toast notification
        if (typeof showToast === 'function') {
            showToast(message, type);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }
    
    // Load default parameters
    async loadDefaults() {
        try {
            const response = await fetch('/api/cv/defaults');
            const defaults = await response.json();
            
            if (this.beginInput) this.beginInput.value = defaults.begin;
            if (this.upperInput) this.upperInput.value = defaults.upper;
            if (this.lowerInput) this.lowerInput.value = defaults.lower;
            if (this.rateInput) this.rateInput.value = defaults.rate;
            if (this.cyclesInput) this.cyclesInput.value = defaults.cycles;
            
            this.validateParameters();
            
        } catch (error) {
            console.error('Failed to load defaults:', error);
        }
    }
}

// Initialize CV measurement when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('cv-controls')) {
        window.cvMeasurement = new CVMeasurement();
        
        // Load defaults on page load
        window.cvMeasurement.loadDefaults();
        
        // Update UI state based on connection
        // Check if connectionState exists and has addEventListener
        if (typeof connectionState !== 'undefined' && connectionState.addEventListener) {
            connectionState.addEventListener('change', (event) => {
                window.cvMeasurement.updateUIState();
            });
        } else {
            // Fallback: Check connection state periodically
            setInterval(() => {
                if (window.cvMeasurement) {
                    window.cvMeasurement.updateUIState();
                }
            }, 1000);
        }
    }
});

// Add default button handler
document.addEventListener('DOMContentLoaded', () => {
    const defaultsBtn = document.getElementById('cv-defaults-btn');
    if (defaultsBtn && window.cvMeasurement) {
        defaultsBtn.addEventListener('click', () => {
            window.cvMeasurement.loadDefaults();
        });
    }
});
