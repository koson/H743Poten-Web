/**
 * CV Measurement JavaScript for H743Poten Web Interface
 * Handles Cyclic Voltammetry measurement controls and real-time plotting
 */

class CVMeasurement {
    constructor() {
        console.log('CVMeasurement constructor called');
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
        
        // Plot update throttling
        this.lastPlotUpdate = 0;
        this.plotUpdateThrottle = 500; // Update plot max every 500ms
        
        // Wait for PortManager to be available
        if (window.portManager) {
            this.setupPortManagerListeners();
        } else {
            // Wait for PortManager to be initialized
            const checkInterval = setInterval(() => {
                if (window.portManager) {
                    this.setupPortManagerListeners();
                    clearInterval(checkInterval);
                }
            }, 100);
        }
        
        this.initializeUI();
        this.initializePlot();
        
        // Force initial validation
        setTimeout(() => this.validateParameters(), 500);
    }
    
    initializeUI() {
        console.log('Initializing CV UI...');
        
        // Get CV parameter inputs
        this.beginInput = document.getElementById('cv-initial');      // Changed from cv-begin
        this.upperInput = document.getElementById('cv-final');        // Changed from cv-upper
        this.lowerInput = document.getElementById('cv-initial');      // Changed to use initial
        this.rateInput = document.getElementById('cv-scan-rate');     // Changed from cv-rate
        this.cyclesInput = document.getElementById('cv-cycles');
        this.simulationToggle = document.getElementById('cv-simulation-mode');
        
        console.log('CV inputs found:', {
            begin: !!this.beginInput,
            upper: !!this.upperInput,
            lower: !!this.lowerInput,
            rate: !!this.rateInput,
            cycles: !!this.cyclesInput,
            simulation: !!this.simulationToggle
        });
        
        // Get CV control buttons
        this.startBtn = document.getElementById('start-btn');        // Changed from cv-start-btn
        this.stopBtn = document.getElementById('stop-btn');         // Changed from cv-stop-btn
        this.pauseBtn = document.getElementById('pause-btn');       // Changed from cv-pause-btn
        this.exportBtn = document.getElementById('export-csv-btn'); // Changed from cv-export-btn
        
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
        
        // Add simulation mode toggle event
        if (this.simulationToggle) {
            this.simulationToggle.addEventListener('change', () => {
                this.setSimulationMode(this.simulationToggle.checked);
            });
        }
        
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
        console.log('Validating parameters...');
        try {
            const params = this.getParameters();
            if (!params) {
                console.warn('Cannot get parameters for validation');
                this.showValidationError('Cannot get parameters');
                return false;
            }
            
            console.log('Sending parameters for validation:', params);
            
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
            console.log('Validation response:', result);
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
            
            // Track validation state in the start button
            if (this.startBtn) {
                console.log('Validation result:', result);
                
                if (result.valid) {
                    console.log('Parameters are valid, enabling start button');
                    this.startBtn.removeAttribute('data-invalid-params');
                } else {
                    console.log('Parameters are invalid, disabling start button');
                    this.startBtn.setAttribute('data-invalid-params', 'true');
                }
                
                // Debug current button state
                console.log('Start button state after validation:', {
                    disabled: this.startBtn.disabled,
                    hasInvalidParams: this.startBtn.hasAttribute('data-invalid-params'),
                    validationResult: result.valid
                });
                
                // Call updateUIState to properly update button state
                this.updateUIState();
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

    setupPortManagerListeners() {
        console.log('Setting up PortManager listeners');
        
        window.portManager.addEventListener('connected', async () => {
            console.log('PortManager: Device connected');
            await this.validateParameters();
            await this.updateUIState();
        });

        window.portManager.addEventListener('disconnected', async () => {
            console.log('PortManager: Device disconnected');
            if (this.startBtn) {
                this.startBtn.disabled = true;
            }
            await this.updateUIState();
        });

        // Handle initial connection state
        if (window.portManager.isConnected) {
            console.log('PortManager: Already connected on setup');
            this.validateParameters();
            this.updateUIState();
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
            upper: parseFloat(this.upperInput.value) || 0.7,
            lower: parseFloat(this.lowerInput.value) || -0.4,
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
        // Update data every 200ms for real-time plotting (reduced frequency)
        this.dataUpdateInterval = setInterval(async () => {
            await this.updateData();
        }, 200);
        
        // Update status every 1000ms (reduced frequency)
        this.statusUpdateInterval = setInterval(async () => {
            await this.updateStatus();
        }, 1000);
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
            console.log('[DEBUG] Fetching data from /api/cv/data/stream...');
            const response = await fetch('/api/cv/data/stream');
            
            console.log('[DEBUG] Response status:', response.status, response.statusText);
            
            if (!response.ok) {
                console.warn('[DEBUG] Response not OK, skipping data update');
                return;
            }
            
            const result = await response.json();
            console.log('[DEBUG] Full response from server:', result);
            
            const dataPoints = result.data_points || [];
            console.log('[DEBUG] Data points extracted:', dataPoints.length, 'points');
            
            if (dataPoints.length > 0) {
                // Get only new points since last update
                const currentDataLength = this.plotData.x.length;
                
                console.log(`[DEBUG] Total points from server: ${dataPoints.length}, Current local points: ${currentDataLength}`);
                
                // Log last few points for inspection
                if (dataPoints.length > 0) {
                    console.log('[DEBUG] Latest server data points:', dataPoints.slice(-3));
                }
                
                // If server has more points than we have locally, add the new ones
                if (dataPoints.length > currentDataLength) {
                    const newPoints = dataPoints.slice(currentDataLength);
                    console.log(`[DEBUG] Adding ${newPoints.length} new data points:`, newPoints);
                    
                    // Add new data points to plot
                    newPoints.forEach((point, index) => {
                        this.plotData.x.push(point.potential);
                        this.plotData.y.push(point.current);
                        this.plotData.cycle.push(point.cycle);
                        this.plotData.direction.push(point.direction);
                        
                        console.log(`[DEBUG] Added point ${index + 1}/${newPoints.length}:`, {
                            potential: point.potential,
                            current: point.current,
                            cycle: point.cycle,
                            direction: point.direction
                        });
                        
                        // Update plot for each new point
                        this.updatePlotIncremental(point);
                    });
                } else {
                    console.log('[DEBUG] No new data points to add');
                }
            } else {
                console.log('[DEBUG] No data points in response');
            }
            
        } catch (error) {
            console.error('[DEBUG] Failed to update data:', error);
        }
    }
    
    updatePlotIncremental(newPoint) {
        if (!this.plotDiv) return;

        console.log(`Adding point: V=${newPoint.potential}V, I=${newPoint.current}A, Cycle=${newPoint.cycle}`);
        
        // Add point to data arrays
        this.plotData.x.push(newPoint.potential);
        this.plotData.y.push(newPoint.current);
        this.plotData.cycle.push(newPoint.cycle);
        
        // Throttle plot updates to prevent UI freeze
        const now = Date.now();
        if (now - this.lastPlotUpdate > this.plotUpdateThrottle) {
            this.updatePlotComplete();
            this.lastPlotUpdate = now;
            console.log('Plot updated after throttle');
        }
    }    updatePlotComplete() {
        if (!this.plotDiv || this.plotData.x.length === 0) return;
        
        console.log(`Updating complete plot with ${this.plotData.x.length} data points`);

        // Group data by cycle for proper CV curves
        const cycles = [...new Set(this.plotData.cycle)];
        const traces = [];

        cycles.forEach((cycle, cycleIndex) => {
            // Get all points for this cycle
            const cyclePoints = this.plotData.cycle
                .map((c, i) => ({
                    index: i,
                    potential: this.plotData.x[i],
                    current: this.plotData.y[i],
                    time: i  // Use index as time reference since points are added sequentially
                }))
                .filter((point, i) => this.plotData.cycle[i] === cycle);

            if (cyclePoints.length === 0) return;

            // Sort points by time to maintain scanning order
            cyclePoints.sort((a, b) => a.time - b.time);

            // Create single trace for the entire cycle
            traces.push({
                x: cyclePoints.map(p => p.potential),
                y: cyclePoints.map(p => p.current),
                type: 'scatter',
                mode: 'lines+markers',
                name: `Cycle ${cycle}`,
                line: {
                    width: 2,
                    color: `hsl(${cycleIndex * 60}, 70%, 50%)`,
                },
                marker: {
                    size: 3,
                    color: `hsl(${cycleIndex * 60}, 70%, 50%)`
                },
                showlegend: true
            });
        });        // Update layout for proper CV display
        const layout = {
            title: {
                text: 'Cyclic Voltammetry',
                font: { size: 16 }
            },
            xaxis: {
                title: 'Potential (V)',
                showgrid: true,
                gridcolor: '#f0f0f0',
                zeroline: true,
                zerolinecolor: '#666',
                autorange: true
            },
            yaxis: {
                title: 'Current (A)', 
                showgrid: true,
                gridcolor: '#f0f0f0',
                zeroline: true,
                zerolinecolor: '#666',
                tickformat: '.2e',
                autorange: true
            },
            showlegend: true,
            legend: {
                x: 1.02,
                y: 1,
                xanchor: 'left',
                bgcolor: 'rgba(255,255,255,0.8)',
                bordercolor: '#ccc',
                borderwidth: 1
            },
            autosize: true,
            margin: { l: 80, r: 120, t: 60, b: 60 }
        };
        
        const config = {
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['lasso2d', 'select2d', 'pan2d', 'autoScale2d']
        };
        
        try {
            Plotly.react(this.plotDiv, traces, layout, config);
            console.log(`Plot updated with ${traces.length} traces for ${cycles.length} cycles`);
        } catch (error) {
            console.error('Failed to update plot:', error);
            // Fallback: clear and recreate
            this.clearPlotData();
            this.initializePlot();
        }
    }
    
    async updateStatus() {
        try {
            console.log('[DEBUG] Fetching status from /api/cv/status...');
            const response = await fetch('/api/cv/status');
            
            if (!response.ok) {
                console.warn('[DEBUG] Status response not OK:', response.status);
                return;
            }
            
            const status = await response.json();
            console.log('[DEBUG] Status response:', status);
            
            // Update status text
            if (this.statusText) {
                let statusStr = `Status: ${status.is_measuring ? 'Running' : 'Stopped'}`;
                if (status.is_paused) statusStr += ' (Paused)';
                this.statusText.textContent = statusStr;
                console.log('[DEBUG] Updated status text:', statusStr);
            }
            
            // Update progress text
            if (this.progressText) {
                const progress = `Cycle: ${status.current_cycle} | Direction: ${status.scan_direction} | ` +
                              `Potential: ${status.current_potential?.toFixed(3)}V | ` +
                              `Points: ${status.data_points_count} | ` +
                              `Time: ${status.elapsed_time?.toFixed(1)}s`;
                this.progressText.textContent = progress;
                console.log('[DEBUG] Updated progress text:', progress);
            }
            
            // Update UI state if status changed
            if (this.isRunning !== status.is_measuring || this.isPaused !== status.is_paused) {
                console.log('[DEBUG] Status changed - updating UI state');
                this.isRunning = status.is_measuring;
                this.isPaused = status.is_paused;
                this.updateUIState();
                
                // Stop data updates if measurement ended
                if (!this.isRunning) {
                    console.log('[DEBUG] Measurement ended - stopping data updates');
                    this.stopDataUpdates();
                }
            }
            
        } catch (error) {
            console.error('[DEBUG] Failed to update status:', error);
        }
    }
    
    updatePlot() {
        // Use the complete plot update method for consistent display
        this.updatePlotComplete();
    }
    
    createInitialPlot() {
        if (!this.plotDiv) return;
        
        console.log(`Creating initial plot with ${this.plotData.x.length} data points`);
        
        // Use the complete plot update for consistency
        if (this.plotData.x.length > 0) {
            this.updatePlotComplete();
        } else {
            // Create empty plot with proper layout
            const layout = {
                title: {
                    text: 'Cyclic Voltammetry',
                    font: { size: 16 }
                },
                xaxis: {
                    title: 'Potential (V)',
                    showgrid: true,
                    gridcolor: '#f0f0f0',
                    zeroline: true,
                    zerolinecolor: '#666'
                },
                yaxis: {
                    title: 'Current (A)', 
                    showgrid: true,
                    gridcolor: '#f0f0f0',
                    zeroline: true,
                    zerolinecolor: '#666',
                    tickformat: '.2e'
                },
                showlegend: true,
                legend: {
                    x: 1.02,
                    y: 1,
                    xanchor: 'left'
                },
                autosize: true,
                margin: { l: 80, r: 120, t: 60, b: 60 }
            };
            
            const config = {
                responsive: true,
                displayModeBar: true,
                displaylogo: false,
                modeBarButtonsToRemove: ['lasso2d', 'select2d', 'pan2d', 'autoScale2d']
            };
            
            try {
                Plotly.react(this.plotDiv, [], layout, config);
                this.plotInitialized = true;
                console.log('Empty plot created successfully');
            } catch (error) {
                console.error('Failed to create empty plot:', error);
            }
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
    
    async updateUIState() {
        // Get connection state from multiple sources with better detection
        let isConnected = false;
        
        // Method 1: Check PortManager directly
        if (window.portManager && typeof window.portManager.isConnected === 'boolean') {
            isConnected = window.portManager.isConnected;
            console.log('Connection state from PortManager:', isConnected);
        }
        // Method 2: Check API directly
        try {
            const response = await fetch('/api/connection/status');
            if (response.ok) {
                const status = await response.json();
                isConnected = status.connected;
                console.log('Connection state from API:', isConnected);
            }
        } catch (e) {
            console.warn('Failed to check connection via API:', e);
        }
        
        // Method 3: Check global connectionState
        if (typeof connectionState !== 'undefined' && typeof connectionState.connected === 'boolean') {
            isConnected = isConnected || connectionState.connected;
            console.log('Connection state from global:', connectionState.connected);
        }
        
        // Debug connection state
        console.log('Connection Status Debug:', {
            portManagerExists: !!window.portManager,
            portManagerConnected: window.portManager?.isConnected,
            globalConnectionState: typeof connectionState !== 'undefined' ? connectionState.connected : 'undefined',
            finalIsConnected: isConnected
        });
        
        // Update button states
        if (this.startBtn) {
            // Only enable if connected, not running, and parameters are valid
            const paramsValid = !this.startBtn.hasAttribute('data-invalid-params');
            this.startBtn.disabled = this.isRunning || !isConnected || !paramsValid;
            console.log('Start button state:', {
                disabled: this.startBtn.disabled,
                isRunning: this.isRunning,
                isConnected: isConnected,
                paramsValid: paramsValid
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
            
            // Clear any existing validation state
            if (this.startBtn) {
                this.startBtn.removeAttribute('data-invalid-params');
            }
            
            // Validate parameters and update UI
            await this.validateParameters();
            this.updateUIState();
            
        } catch (error) {
            console.error('Failed to load defaults:', error);
            this.showMessage('Failed to load default parameters', 'error');
        }
    }
}

// Initialize CV measurement when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    if (document.getElementById('cv-controls')) {
        window.cvMeasurement = new CVMeasurement();
        
        // Initial connection check and setup
        console.log('Initial connection check...');
        
        // Load defaults on page load
        await window.cvMeasurement.loadDefaults();
        
        // Force an immediate UI state update
        await window.cvMeasurement.updateUIState();
        
        // Listen for port manager events if available
        if (window.portManager) {
            window.portManager.addEventListener('connected', async () => {
                console.log('PortManager connected event');
                await window.cvMeasurement.updateUIState();
            });
            
            window.portManager.addEventListener('disconnected', async () => {
                console.log('PortManager disconnected event');
                await window.cvMeasurement.updateUIState();
            });
        }
        
        // Listen for global connection state changes
        if (typeof connectionState !== 'undefined' && connectionState.addEventListener) {
            connectionState.addEventListener('change', async (event) => {
                console.log('Connection state changed:', event);
                await window.cvMeasurement.updateUIState();
            });
        }
        
        // Periodic state check as fallback
        setInterval(async () => {
            if (window.cvMeasurement) {
                await window.cvMeasurement.updateUIState();
            }
        }, 1000);
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

// Add global method to CVMeasurement prototype for simulation mode
CVMeasurement.prototype.setSimulationMode = async function(enabled) {
    console.log(`Setting simulation mode: ${enabled}`);
    
    try {
        const response = await fetch('/api/cv/simulation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ enabled: enabled })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('Simulation mode changed:', result.message);
            this.showMessage(result.message, 'info');
            
            // Update UI to reflect simulation mode
            const label = this.simulationToggle?.nextElementSibling;
            if (label) {
                const icon = label.querySelector('i');
                if (icon) {
                    icon.className = enabled ? 'fas fa-flask text-warning' : 'fas fa-flask';
                }
            }
        } else {
            console.error('Failed to set simulation mode:', result.error);
            this.showMessage(`Error: ${result.error}`, 'error');
            
            // Revert toggle state
            if (this.simulationToggle) {
                this.simulationToggle.checked = !enabled;
            }
        }
    } catch (error) {
        console.error('Network error setting simulation mode:', error);
        this.showMessage('Network error: Could not change simulation mode', 'error');
        
        // Revert toggle state
        if (this.simulationToggle) {
            this.simulationToggle.checked = !enabled;
        }
    }
};
