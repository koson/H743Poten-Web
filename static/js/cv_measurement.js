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
        
        // Plot update throttling
        this.lastPlotUpdate = 0;
        this.plotUpdateThrottle = 500; // Update plot max every 500ms
        
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
        this.startBtn = document.getElementById('cv-start-btn');
        this.stopBtn = document.getElementById('cv-stop-btn');
        this.pauseBtn = document.getElementById('cv-pause-btn');
        this.exportBtn = document.getElementById('cv-export-btn');
        this.fixRangeBtn = document.getElementById('cv-fix-range-btn');
        
        console.log('CV buttons found:', {
            start: !!this.startBtn,
            stop: !!this.stopBtn,
            pause: !!this.pauseBtn,
            export: !!this.exportBtn,
            fixRange: !!this.fixRangeBtn
        });
        
        // Get status elements
        this.statusText = document.getElementById('cv-status');
        this.progressText = document.getElementById('cv-progress');
        
        // Bind event listeners
        this.startBtn?.addEventListener('click', () => this.startMeasurement());
        this.stopBtn?.addEventListener('click', () => this.stopMeasurement());
        this.pauseBtn?.addEventListener('click', () => this.togglePause());
        this.exportBtn?.addEventListener('click', () => this.exportData());
        this.fixRangeBtn?.addEventListener('click', () => this.fixPlotRange());
        
        // Save measurement button
        this.saveBtn = document.getElementById('save-measurement-btn');
        this.saveBtn?.addEventListener('click', () => this.saveMeasurement());
        
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
    
    getCurrentParameters() {
        return {
            begin: this.beginInput ? this.beginInput.value : 0.0,
            upper: this.upperInput ? this.upperInput.value : 0.7,
            lower: this.lowerInput ? this.lowerInput.value : -0.4,
            rate: this.rateInput ? this.rateInput.value : 0.1,
            cycles: this.cyclesInput ? this.cyclesInput.value : 1
        };
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
            
            // Debug: Check if we're missing data by comparing with status
            if (result.status && result.status.data_points_count) {
                const backendCount = result.status.data_points_count;
                const receivedCount = dataPoints.length;
                if (backendCount > receivedCount) {
                    console.warn(`[DEBUG] Data mismatch! Backend has ${backendCount} points but only received ${receivedCount} points`);
                }
            }
            
            // Debug: Check voltage range in received data
            if (dataPoints.length > 0) {
                const voltages = dataPoints.map(p => p.potential);
                const minV = Math.min(...voltages);
                const maxV = Math.max(...voltages);
                console.log(`[DEBUG] Received data voltage range: ${minV.toFixed(4)}V to ${maxV.toFixed(4)}V`);
                
                // Check for negative voltages
                const negativeCount = voltages.filter(v => v < 0).length;
                console.log(`[DEBUG] Negative voltage points: ${negativeCount}/${voltages.length}`);
            }
            
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
                        
                        // Log data range so far
                        if (this.plotData.x.length > 0) {
                            const minV = Math.min(...this.plotData.x);
                            const maxV = Math.max(...this.plotData.x);
                            console.log(`[DEBUG] Current voltage range in plot data: ${minV.toFixed(4)}V to ${maxV.toFixed(4)}V`);
                        }
                    });
                    
                    // Force complete plot update after adding all new points
                    console.log(`[DEBUG] Forcing complete plot update with ${this.plotData.x.length} total points`);
                    this.updatePlotComplete();
                } else if (dataPoints.length < currentDataLength) {
                    // Backend has fewer points than frontend (unusual case)
                    console.log(`[DEBUG] Backend has fewer points (${dataPoints.length}) than frontend (${currentDataLength}) - resyncing`);
                    
                    // Clear and reload all data from backend
                    this.plotData = { x: [], y: [], cycle: [], direction: [] };
                    
                    dataPoints.forEach((point, index) => {
                        this.plotData.x.push(point.potential);
                        this.plotData.y.push(point.current);
                        this.plotData.cycle.push(point.cycle);
                        this.plotData.direction.push(point.direction);
                    });
                    
                    console.log(`[DEBUG] Resynced with ${this.plotData.x.length} points from backend`);
                    this.updatePlotComplete();
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
        
        console.log(`Adding point: V=${newPoint.potential}V, I=${newPoint.current}A, Cycle=${newPoint.cycle}, Dir=${newPoint.direction}`);
        
        // Throttle plot updates to prevent UI freeze
        const now = Date.now();
        if (now - this.lastPlotUpdate > this.plotUpdateThrottle) {
            this.updatePlotComplete();
            this.lastPlotUpdate = now;
        }
    }
    
    updatePlotComplete() {
        if (!this.plotDiv || this.plotData.x.length === 0) return;
        
        console.log(`Updating complete plot with ${this.plotData.x.length} data points`);

        // Calculate actual data range for proper axis scaling
        let minPotential = Math.min(...this.plotData.x);
        let maxPotential = Math.max(...this.plotData.x);
        let minCurrent = Math.min(...this.plotData.y);
        let maxCurrent = Math.max(...this.plotData.y);
        
        // Validate ranges (fallback to default if invalid)
        if (!isFinite(minPotential) || !isFinite(maxPotential)) {
            console.warn('[DEBUG] Invalid potential range, using defaults');
            minPotential = -0.5;
            maxPotential = 0.8;
        }
        if (!isFinite(minCurrent) || !isFinite(maxCurrent)) {
            console.warn('[DEBUG] Invalid current range, using defaults');
            minCurrent = -1e-6;
            maxCurrent = 1e-6;
        }
        
        // Force expand range to include CV parameters if data is limited
        const cvParams = this.getCurrentParameters();
        if (cvParams) {
            const lowerV = parseFloat(cvParams.lower) || -0.4;
            const upperV = parseFloat(cvParams.upper) || 0.7;
            
            // Ensure range includes parameter range even if data doesn't
            minPotential = Math.min(minPotential, lowerV);
            maxPotential = Math.max(maxPotential, upperV);
            
            console.log(`[DEBUG] CV parameters - Lower: ${lowerV}V, Upper: ${upperV}V`);
            console.log(`[DEBUG] Expanded range to include parameters: ${minPotential.toFixed(4)}V to ${maxPotential.toFixed(4)}V`);
        }
        
        // Force minimum range if data is too narrow
        const dataRange = maxPotential - minPotential;
        if (dataRange < 0.5) {
            const center = (minPotential + maxPotential) / 2;
            minPotential = center - 0.6;
            maxPotential = center + 0.6;
            console.log(`[DEBUG] Data range too narrow (${dataRange.toFixed(4)}V), forcing wider range: ${minPotential.toFixed(4)}V to ${maxPotential.toFixed(4)}V`);
        }
        
        // Add 10% padding to ranges for better visualization
        const potentialRange = maxPotential - minPotential;
        const currentRange = Math.abs(maxCurrent - minCurrent);
        const potentialPadding = potentialRange * 0.1;
        const currentPadding = currentRange * 0.1;
        
        console.log(`[DEBUG] Raw data range - Potential: ${minPotential.toFixed(4)}V to ${maxPotential.toFixed(4)}V`);
        console.log(`[DEBUG] Raw data range - Current: ${minCurrent.toExponential(3)}A to ${maxCurrent.toExponential(3)}A`);
        console.log(`[DEBUG] Final plot range - Potential: ${(minPotential - potentialPadding).toFixed(4)}V to ${(maxPotential + potentialPadding).toFixed(4)}V`);
        console.log(`[DEBUG] Plot data sample:`, {
            firstPotential: this.plotData.x[0],
            lastPotential: this.plotData.x[this.plotData.x.length - 1],
            totalPoints: this.plotData.x.length,
            sampleVoltages: this.plotData.x.slice(0, 10)
        });
        
        // Group data by cycle for proper CV curves
        const cycles = [...new Set(this.plotData.cycle)];
        const traces = [];
        
        // Extra debugging for trace data
        console.log(`[DEBUG] Creating traces for ${cycles.length} cycles`);
        console.log(`[DEBUG] All voltage data points:`, this.plotData.x);
        console.log(`[DEBUG] Voltage range check - Min: ${Math.min(...this.plotData.x).toFixed(4)}, Max: ${Math.max(...this.plotData.x).toFixed(4)}`);
        
        cycles.forEach((cycle, cycleIndex) => {
            // Get all points for this cycle
            const cycleIndices = this.plotData.cycle
                .map((c, i) => c === cycle ? i : -1)
                .filter(i => i !== -1);
            
            if (cycleIndices.length === 0) return;
            
            // Separate forward and reverse scans for proper CV appearance
            const forwardIndices = cycleIndices.filter(i => this.plotData.direction[i] === 'forward');
            const reverseIndices = cycleIndices.filter(i => this.plotData.direction[i] === 'reverse');
            
            // Create completely isolated traces with explicit line settings
            const forwardX = forwardIndices.map(i => this.plotData.x[i]);
            const forwardY = forwardIndices.map(i => this.plotData.y[i]);
            const reverseX = reverseIndices.map(i => this.plotData.x[i]);
            const reverseY = reverseIndices.map(i => this.plotData.y[i]);
            
            // Forward scan trace - completely isolated
            if (forwardIndices.length > 0) {
                // Sort forward data (ascending voltage)
                const forwardPairs = forwardX.map((x, i) => ({ x, y: forwardY[i] }));
                forwardPairs.sort((a, b) => a.x - b.x);
                
                console.log(`[DEBUG] Cycle ${cycle} Forward: ${forwardPairs.length} points`);
                
                traces.push({
                    x: forwardPairs.map(p => p.x),
                    y: forwardPairs.map(p => p.y),
                    type: 'scatter',
                    mode: 'markers+lines',
                    name: `Cycle ${cycle}`,
                    line: {
                        width: 2,
                        color: `hsl(${cycleIndex * 60}, 70%, 50%)`,
                        shape: 'linear'
                    },
                    marker: {
                        size: 0.1,  // Extremely small markers
                        color: `hsl(${cycleIndex * 60}, 70%, 50%)`,
                        opacity: 0  // Invisible markers
                    },
                    connectgaps: false,
                    showlegend: true,
                    legendgroup: `cycle${cycle}`,
                    visible: true,
                    hovertemplate: `Cycle ${cycle}<br>V: %{x:.4f}<br>I: %{y:.2e}<extra></extra>`
                });
            }
            
            // Add delay before reverse trace to ensure complete separation
            if (reverseIndices.length > 0) {
                // Sort reverse data (descending voltage)
                const reversePairs = reverseX.map((x, i) => ({ x, y: reverseY[i] }));
                reversePairs.sort((a, b) => b.x - a.x);
                
                console.log(`[DEBUG] Cycle ${cycle} Reverse: ${reversePairs.length} points`);
                
                // Create reverse trace with completely different configuration
                traces.push({
                    x: reversePairs.map(p => p.x),
                    y: reversePairs.map(p => p.y),
                    type: 'scatter',
                    mode: 'markers+lines',
                    name: `Cycle ${cycle} Rev`,
                    line: {
                        width: 2,
                        color: `hsl(${cycleIndex * 60}, 70%, 50%)`,
                        shape: 'linear'
                    },
                    marker: {
                        size: 0.1,  // Extremely small markers
                        color: `hsl(${cycleIndex * 60}, 70%, 50%)`,
                        opacity: 0  // Invisible markers
                    },
                    connectgaps: false,
                    showlegend: false,
                    legendgroup: `cycle${cycle}`,
                    visible: true,
                    hovertemplate: `Cycle ${cycle}<br>V: %{x:.4f}<br>I: %{y:.2e}<extra></extra>`
                });
            }
        });

        // Update layout for proper CV display
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
                range: [minPotential - potentialPadding, maxPotential + potentialPadding],
                autorange: false
            },
            yaxis: {
                title: 'Current (A)', 
                showgrid: true,
                gridcolor: '#f0f0f0',
                zeroline: true,
                zerolinecolor: '#666',
                tickformat: '.2e',
                range: [minCurrent - currentPadding, maxCurrent + currentPadding],
                autorange: false
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
            modeBarButtonsToRemove: ['lasso2d', 'select2d', 'pan2d', 'autoScale2d'],
            // Force no line connections across traces
            plotGlPixelRatio: 2,
            toImageButtonOptions: {
                format: 'png',
                filename: 'cv_measurement',
                height: 500,
                width: 700,
                scale: 1
            }
        };
        
        try {
            console.log(`[DEBUG] Updating Plotly with ${traces.length} traces`);
            console.log(`[DEBUG] X-axis range: [${minPotential - potentialPadding}, ${maxPotential + potentialPadding}]`);
            console.log(`[DEBUG] Y-axis range: [${minCurrent - currentPadding}, ${maxCurrent + currentPadding}]`);
            console.log(`[DEBUG] Sample trace data:`, traces.length > 0 ? {
                traceCount: traces.length,
                firstTrace: {
                    name: traces[0].name,
                    xSample: traces[0].x.slice(0, 5),
                    ySample: traces[0].y.slice(0, 5),
                    totalPoints: traces[0].x.length
                }
            } : 'No traces');
            
            console.log(`[DEBUG] About to call Plotly.react with layout:`, {
                xRange: layout.xaxis.range,
                yRange: layout.yaxis.range,
                tracesCount: traces.length
            });
            
            Plotly.react(this.plotDiv, traces, layout, config);
            console.log(`Plot updated with ${traces.length} traces for ${cycles.length} cycles`);
            
            // Verify the plot was updated correctly
            setTimeout(() => {
                const currentLayout = this.plotDiv.layout;
                console.log(`[DEBUG] Plot verification - Current x-axis range:`, currentLayout.xaxis?.range);
                console.log(`[DEBUG] Plot verification - Current y-axis range:`, currentLayout.yaxis?.range);
            }, 100);
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
            
            // Update status text with connection info
            if (this.statusText) {
                let statusStr = `Status: ${status.is_measuring ? 'Running' : 'Stopped'}`;
                if (status.is_paused) statusStr += ' (Paused)';
                if (status.device_connected !== undefined) {
                    statusStr += ` | Device: ${status.device_connected ? 'Connected' : 'Disconnected'}`;
                }
                this.statusText.textContent = statusStr;
                console.log('[DEBUG] Updated status text:', statusStr);
            }
            
            // Update progress text with timeout info
            if (this.progressText) {
                let progress = `Cycle: ${status.current_cycle} | Direction: ${status.scan_direction} | ` +
                              `Potential: ${status.current_potential?.toFixed(3)}V | ` +
                              `Points: ${status.data_points_count} | ` +
                              `Time: ${status.elapsed_time?.toFixed(1)}s`;
                
                // Add timeout warning if no data received recently
                if (status.is_measuring && status.time_since_last_data !== null && status.time_since_last_data > 5) {
                    progress += ` | WARNING: No data for ${status.time_since_last_data?.toFixed(1)}s`;
                    if (status.time_since_last_data > 8) {
                        progress += ' (May stop soon)';
                    }
                }
                
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
        
        // Update save button state
        this.updateSaveButtonState();
        
        // Update parameter inputs (disable during measurement)
        [this.beginInput, this.upperInput, this.lowerInput, this.rateInput, this.cyclesInput]
            .forEach(input => {
                if (input) {
                    input.disabled = this.isRunning;
                }
            });
    }
    
    fixPlotRange() {
        console.log('[DEBUG] Manually fixing plot range...');
        
        if (!this.plotDiv) {
            console.warn('Plot not initialized');
            this.showMessage('Plot not initialized', 'error');
            return;
        }
        
        // Get current parameters
        const params = this.getCurrentParameters();
        const lowerV = parseFloat(params.lower) || -0.4;
        const upperV = parseFloat(params.upper) || 0.7;
        
        // Force reset plot range to parameter range
        const layout_update = {
            'xaxis.range': [lowerV - 0.1, upperV + 0.1],
            'xaxis.autorange': false
        };
        
        console.log(`[DEBUG] Forcing plot range to: ${lowerV - 0.1}V to ${upperV + 0.1}V`);
        
        Plotly.relayout(this.plotDiv, layout_update).then(() => {
            console.log('[DEBUG] Plot range fixed successfully');
            this.showMessage(`Plot range fixed: ${lowerV}V to ${upperV}V`, 'success');
        }).catch(error => {
            console.error('[DEBUG] Failed to fix plot range:', error);
            this.showMessage('Failed to fix plot range', 'error');
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

// Function to manually fix plot range when automatic detection fails
window.fixPlotRange = function() {
    if (window.cvMeasurement && window.cvMeasurement.fixPlotRange) {
        window.cvMeasurement.fixPlotRange();
    }
};

// Add fixPlotRange method to CVMeasurement prototype
CVMeasurement.prototype.fixPlotRange = function() {
    if (!this.plotDiv || this.plotData.x.length === 0) {
        console.warn('[DEBUG] Cannot fix plot range - no plot data available');
        return;
    }
    
    console.log('[DEBUG] Manual plot range fix initiated');
    
    // Get CV parameters for expected range
    const cvParams = this.getCurrentParameters();
    let lowerV = -0.4, upperV = 0.7;  // Default range
    
    if (cvParams) {
        lowerV = parseFloat(cvParams.lower) || -0.4;
        upperV = parseFloat(cvParams.upper) || 0.7;
    }
    
    // Calculate actual data range
    const minV = Math.min(...this.plotData.x);
    const maxV = Math.max(...this.plotData.x);
    const minI = Math.min(...this.plotData.y);
    const maxI = Math.max(...this.plotData.y);
    
    // Use the wider of parameter range vs data range
    const finalMinV = Math.min(lowerV, minV);
    const finalMaxV = Math.max(upperV, maxV);
    
    console.log(`[DEBUG] Range fix - Data: ${minV.toFixed(4)} to ${maxV.toFixed(4)}V`);
    console.log(`[DEBUG] Range fix - Params: ${lowerV.toFixed(4)} to ${upperV.toFixed(4)}V`);
    console.log(`[DEBUG] Range fix - Final: ${finalMinV.toFixed(4)} to ${finalMaxV.toFixed(4)}V`);
    
    // Update plot layout with explicit range
    const update = {
        'xaxis.range': [finalMinV - 0.05, finalMaxV + 0.05],
        'yaxis.range': [minI - Math.abs(minI) * 0.1, maxI + Math.abs(maxI) * 0.1],
        'xaxis.autorange': false,
        'yaxis.autorange': false
    };
    
    Plotly.relayout(this.plotDiv, update).then(() => {
        console.log('[DEBUG] Manual range fix completed successfully');
        this.showMessage('Plot range fixed manually', 'success');
    }).catch(error => {
        console.error('[DEBUG] Manual range fix failed:', error);
        this.showMessage('Failed to fix plot range', 'error');
    });
};

// Save current measurement data
CVMeasurement.prototype.saveMeasurement = async function() {
    try {
        if (this.plotData.x.length === 0) {
            this.showMessage('No measurement data to save', 'warning');
            return;
        }
        
        // Generate session ID
        const sessionId = `CV_${new Date().toISOString().replace(/[:.]/g, '-')}`;
        
        console.log(`[SAVE] Saving measurement with ${this.plotData.x.length} data points`);
        
        const response = await fetch('/api/data-logging/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            this.showMessage(`Measurement saved as ${data.session_id}`, 'success');
            
            // Disable save button after successful save
            const saveBtn = document.getElementById('save-measurement-btn');
            if (saveBtn) {
                saveBtn.disabled = true;
                saveBtn.innerHTML = '<i class="fas fa-check"></i> Saved';
            }
            
            console.log(`[SAVE] Successfully saved: ${data.session_id}`);
        } else {
            this.showMessage(`Failed to save measurement: ${data.error}`, 'error');
            console.error(`[SAVE] Save failed: ${data.error}`);
        }
        
    } catch (error) {
        console.error('[SAVE] Save measurement error:', error);
        this.showMessage('Failed to save measurement', 'error');
    }
};

// Update save button state based on data availability
CVMeasurement.prototype.updateSaveButtonState = function() {
    const saveBtn = document.getElementById('save-measurement-btn');
    if (saveBtn) {
        const hasData = this.plotData.x.length > 0;
        const isRunning = this.isRunning;
        
        saveBtn.disabled = !hasData || isRunning;
        
        if (hasData && !isRunning) {
            saveBtn.innerHTML = '<i class="fas fa-save"></i> Save Data';
            saveBtn.title = `Save ${this.plotData.x.length} data points`;
        } else if (isRunning) {
            saveBtn.innerHTML = '<i class="fas fa-save"></i> Save Data';
            saveBtn.title = 'Stop measurement to save data';
        } else {
            saveBtn.innerHTML = '<i class="fas fa-save"></i> Save Data';
            saveBtn.title = 'No data to save';
        }
    }
};
