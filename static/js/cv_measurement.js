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
        
        this.initializeUI();
        this.initializePlot();
    }
    
    initializeUI() {
        // Get CV parameter inputs
        this.beginInput = document.getElementById('cv-begin');
        this.upperInput = document.getElementById('cv-upper');
        this.lowerInput = document.getElementById('cv-lower');
        this.rateInput = document.getElementById('cv-rate');
        this.cyclesInput = document.getElementById('cv-cycles');
        
        // Get CV control buttons
        this.startBtn = document.getElementById('cv-start-btn');
        this.stopBtn = document.getElementById('cv-stop-btn');
        this.pauseBtn = document.getElementById('cv-pause-btn');
        this.exportBtn = document.getElementById('cv-export-btn');
        
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
                    input.addEventListener('input', () => this.validateParameters());
                }
            });
        
        // Initial parameter validation
        this.validateParameters();
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
            if (!params) return;
            
            const response = await fetch('/api/cv/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ params })
            });
            
            const result = await response.json();
            
            // Update validation UI
            const validationElement = document.getElementById('cv-validation');
            if (validationElement) {
                if (result.valid) {
                    validationElement.innerHTML = `
                        <div class="alert alert-success">
                            <i class="fas fa-check-circle"></i> ${result.message}
                        </div>
                    `;
                } else {
                    validationElement.innerHTML = `
                        <div class="alert alert-warning">
                            <i class="fas fa-exclamation-triangle"></i> ${result.message}
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
            return false;
        }
    }
    
    getParameters() {
        if (!this.beginInput || !this.upperInput || !this.lowerInput || 
            !this.rateInput || !this.cyclesInput) {
            return null;
        }
        
        return {
            begin: parseFloat(this.beginInput.value) || 0.0,
            upper: parseFloat(this.upperInput.value) || 1.0,
            lower: parseFloat(this.lowerInput.value) || -1.0,
            rate: parseFloat(this.rateInput.value) || 0.1,
            cycles: parseInt(this.cyclesInput.value) || 1
        };
    }
    
    async startMeasurement() {
        try {
            // Check connection
            if (!connectionState.connected) {
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
            
            // Setup measurement
            const setupResponse = await fetch('/api/cv/setup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ params })
            });
            
            const setupResult = await setupResponse.json();
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
            this.showMessage('Failed to start measurement', 'error');
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
                // Add new data points to plot
                dataPoints.forEach(point => {
                    this.plotData.x.push(point.potential);
                    this.plotData.y.push(point.current);
                    this.plotData.cycle.push(point.cycle);
                    this.plotData.direction.push(point.direction);
                });
                
                this.updatePlot();
            }
            
        } catch (error) {
            console.error('Failed to update data:', error);
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
        if (!this.plotDiv || this.plotData.x.length === 0) return;
        
        // Group data by cycle for different traces
        const cycles = [...new Set(this.plotData.cycle)];
        const traces = cycles.map(cycle => {
            const cycleIndices = this.plotData.cycle.map((c, i) => c === cycle ? i : -1).filter(i => i !== -1);
            
            return {
                x: cycleIndices.map(i => this.plotData.x[i]),
                y: cycleIndices.map(i => this.plotData.y[i]),
                type: 'scatter',
                mode: 'lines',
                name: `Cycle ${cycle}`,
                line: {
                    width: 2,
                    color: cycle === 1 ? '#007bff' : `hsl(${(cycle - 1) * 60}, 70%, 50%)`
                }
            };
        });
        
        Plotly.react(this.plotDiv, traces);
    }
    
    clearPlotData() {
        this.plotData = { x: [], y: [], cycle: [], direction: [] };
        if (this.plotDiv) {
            Plotly.react(this.plotDiv, []);
        }
    }
    
    updateUIState() {
        // Update button states
        if (this.startBtn) {
            this.startBtn.disabled = this.isRunning || !connectionState.connected;
        }
        
        if (this.stopBtn) {
            this.stopBtn.disabled = !this.isRunning;
        }
        
        if (this.pauseBtn) {
            this.pauseBtn.disabled = !this.isRunning;
            this.pauseBtn.textContent = this.isPaused ? 'Resume' : 'Pause';
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
        if (typeof connectionState !== 'undefined') {
            connectionState.addEventListener('change', (event) => {
                window.cvMeasurement.updateUIState();
            });
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
