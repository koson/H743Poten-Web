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
        
        // Initialize plot parameters
        const initParams = this.getCurrentParameters();
        this.targetLowerV = parseFloat(initParams?.lower || -0.4);
        this.targetUpperV = parseFloat(initParams?.upper || 0.7);
        this.targetStartV = parseFloat(initParams?.begin || -0.4);
        
        this.initializeUI();
        this.initializePlot();
    }
    
    initializeUI() {
        console.log('Initializing CV UI...');
        
        // Get CV parameter inputs
        this.beginInput = document.getElementById('cv-initial');
        this.upperInput = document.getElementById('cv-final');
        this.lowerInput = document.getElementById('cv-initial');
        this.rateInput = document.getElementById('cv-scan-rate');
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
        this.startBtn = document.getElementById('start-btn');
        this.stopBtn = document.getElementById('stop-btn');
        this.pauseBtn = document.getElementById('pause-btn');
        this.exportBtn = document.getElementById('export-csv-btn');
        this.fixRangeBtn = document.getElementById('reset-zoom-btn');
        
        console.log('CV buttons found:', {
            start: !!this.startBtn,
            stop: !!this.stopBtn,
            pause: !!this.pauseBtn,
            export: !!this.exportBtn,
            fixRange: !!this.fixRangeBtn
        });
        
        // Get status elements
        this.statusText = document.getElementById('connection-status');
        this.progressText = document.getElementById('data-table-body');
        
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
        [this.beginInput, this.upperInput, this.rateInput, this.cyclesInput]
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
        console.log('[CV] Initializing plot...');
        
        // Try both possible plot container IDs
        let plotDiv = document.getElementById('cv-plot');
        if (!plotDiv) {
            plotDiv = document.getElementById('plot-container');
            console.log('[CV] cv-plot not found, using plot-container');
        }
        
        if (!plotDiv) {
            console.error('[CV] No plot container found! Looked for cv-plot and plot-container');
            return;
        }
        
        console.log('[CV] Found plot container:', plotDiv.id);
        
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
        
        try {
            // Initialize empty plot
            Plotly.newPlot(plotDiv, [], layout, config);
            console.log('[CV] Plot initialized successfully');
            
            this.plotDiv = plotDiv;
            this.plotInitialized = true;
        } catch (error) {
            console.error('[CV] Failed to initialize plot:', error);
        }
    }
    
    getCurrentParameters() {
        return {
            begin: this.beginInput ? this.beginInput.value : 0.0,
            upper: this.upperInput ? this.upperInput.value : 0.7,
            lower: this.beginInput ? this.beginInput.value : -0.4,
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
        
        if (!this.beginInput || !this.upperInput || !this.rateInput || !this.cyclesInput) {
            console.error('CV input elements not found');
            return null;
        }
        
        const params = {
            begin: parseFloat(this.beginInput.value) || 0.0,
            upper: parseFloat(this.upperInput.value) || 0.7,
            lower: parseFloat(this.beginInput.value) || -0.4,
            rate: parseFloat(this.rateInput.value) || 0.1,
            cycles: parseInt(this.cyclesInput.value) || 1
        };
        
        console.log('CV parameters:', params);
        return params;
    }
    
    async startMeasurement() {
        try {
            // Check connection status or simulation mode
            let isConnected = false;
            let isSimulation = this.simulationToggle?.checked || false;
            
            console.log('[DEBUG] Checking connection state:', {
                simulationMode: isSimulation,
                simulationToggleExists: !!this.simulationToggle
            });
            
            // Allow start if in simulation mode
            if (isSimulation) {
                isConnected = true;
                console.log('[DEBUG] Simulation mode active, bypassing connection check');
            } 
            // Otherwise check real connection
            else if (window.portManager && typeof window.portManager.isConnected === 'boolean') {
                isConnected = window.portManager.isConnected;
            } else {
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
            
            // Make sure plot is initialized
            if (!this.plotInitialized || !this.plotDiv) {
                console.log('[CV] Plot not initialized, initializing now...');
                this.initializePlot();
            }
            
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
            
            // Check measurement status for auto-save
            const status = result.status || {};
            const isMeasuring = status.is_measuring || false;
            const dataPointsCount = status.data_points_count || 0;
            
            // Auto-save when measurement stops and we have data
            if (this.isRunning && !isMeasuring && dataPointsCount > 0) {
                console.log('[AUTO-SAVE] Measurement completed, auto-saving data...');
                this.isRunning = false;
                this.updateUIState();
                this.stopDataUpdates();
                this.showMessage('CV measurement completed - Auto-saving data...', 'success');
                
                // Auto-save the measurement
                await this.saveMeasurement(true); // true = auto-save mode
            }
            
            if (dataPoints.length > 0) {
                // Get only new points since last update
                const currentDataLength = this.plotData.x.length;
                
                console.log(`[DEBUG] Total points from server: ${dataPoints.length}, Current local points: ${currentDataLength}`);
                
                // If server has more points than we have locally, add the new ones
                if (dataPoints.length > currentDataLength) {
                    const newPoints = dataPoints.slice(currentDataLength);
                    console.log(`[DEBUG] Adding ${newPoints.length} new data points:`, newPoints.slice(0, 3));
                    
                    // Add new data points to plot
                    newPoints.forEach((point, index) => {
                        this.plotData.x.push(point.potential);
                        this.plotData.y.push(point.current);
                        this.plotData.cycle.push(point.cycle);
                        this.plotData.direction.push(point.direction);
                    });
                    
                    // Force complete plot update after adding all new points
                    console.log(`[DEBUG] Forcing complete plot update with ${this.plotData.x.length} total points`);
                    console.log(`[DEBUG] Plot container exists:`, !!this.plotDiv);
                    console.log(`[DEBUG] Plot initialized:`, this.plotInitialized);
                    
                    if (this.plotDiv && this.plotInitialized) {
                        this.updatePlotComplete();
                    } else {
                        console.error('[DEBUG] Cannot update plot - container or initialization missing');
                    }
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

        // Use stored voltage parameters
        const currentLowerV = this.targetLowerV;
        const currentUpperV = this.targetUpperV;
        const targetStartV = parseFloat(currentParams?.begin || -0.4);
        
        console.log(`[DEBUG] CV Target Range: ${targetLowerV}V to ${targetUpperV}V, Start: ${targetStartV}V`);
        
        // Helper function to find cycle transition points
        const findTransitionPoints = (voltages) => {
            if (voltages.length < 2) return { minPoints: [], maxPoints: [] };
            
            // Find local extrema
            const minPoints = [];
            const maxPoints = [];
            const threshold = 0.05;
            
            for (let i = 1; i < voltages.length - 1; i++) {
                if (Math.abs(voltages[i] - targetLowerV) < threshold) {
                    minPoints.push(i);
                }
                if (Math.abs(voltages[i] - targetUpperV) < threshold) {
                    maxPoints.push(i);
                }
            }
            
            return { minPoints, maxPoints };
        };

        // Find cycle transition points
        const { minPoints, maxPoints } = findTransitionPoints(this.plotData.x);
        console.log(`[DEBUG] Found transitions:`, 
            `${minPoints.length} at lower voltage,`,
            `${maxPoints.length} at upper voltage`);
            
        // Calculate actual ranges for axis scaling
        let minPotential = Math.min(...this.plotData.x);
        let maxPotential = Math.max(...this.plotData.x);
        let minCurrent = Math.min(...this.plotData.y);
        let maxCurrent = Math.max(...this.plotData.y);
        
        // Default ranges if data is invalid
        if (!isFinite(minPotential) || !isFinite(maxPotential)) {
            minPotential = -0.5;
            maxPotential = 0.8;
            console.warn('[DEBUG] Using default potential range');
        }
        if (!isFinite(minCurrent) || !isFinite(maxCurrent)) {
            minCurrent = -1e-6;
            maxCurrent = 1e-6;
            console.warn('[DEBUG] Using default current range');
        }
        
        // Ensure range includes target voltages and add minimal padding
        minPotential = Math.min(minPotential, targetLowerV - 0.1);
        maxPotential = Math.max(maxPotential, targetUpperV + 0.1);
        
        // Force minimal range if data is too narrow
        if (maxPotential - minPotential < 0.5) {
            const center = (minPotential + maxPotential) / 2;
            minPotential = center - 0.3;
            maxPotential = center + 0.3;
            console.log('[DEBUG] Expanded narrow voltage range');
        }
        
        // Add padding to ranges for visualization
        const potentialPadding = (maxPotential - minPotential) * 0.1;
        const currentPadding = Math.abs(maxCurrent - minCurrent) * 0.1;
        
        // Log range information for debugging
        console.log(`[DEBUG] Range Analysis:`, {
            potential: {
                min: minPotential.toFixed(3),
                max: maxPotential.toFixed(3),
                padded: {
                    min: (minPotential - potentialPadding).toFixed(3),
                    max: (maxPotential + potentialPadding).toFixed(3)
                }
            },
            current: {
                min: minCurrent.toExponential(2),
                max: maxCurrent.toExponential(2),
                padded: {
                    min: (minCurrent - currentPadding).toExponential(2),
                    max: (maxCurrent + currentPadding).toExponential(2)
                }
            },
            transitions: {
                lowerCount: minPoints.length,
                upperCount: maxPoints.length,
                firstLower: minPoints[0],
                firstUpper: maxPoints[0]
            }
        });

        // Group data by cycle for proper CV curves
        const cycles = [...new Set(this.plotData.cycle)];
        const traces = [];

        // Get voltage range parameters
        const cvParams = this.getCurrentParameters();
        const targetLowerV = parseFloat(cvParams?.lower || -0.4);
        const targetUpperV = parseFloat(cvParams?.upper || 0.7);
        
        console.log(`[DEBUG] CV Target Range: ${targetLowerV}V to ${targetUpperV}V`);
        console.log(`[DEBUG] Creating traces for ${cycles.length} cycles`);

        // Helper function to find extreme points
        const findExtremePoints = (points, isMin) => {
            if (points.length === 0) return [];
            const extremeV = isMin ? 
                Math.min(...points.map(p => p.x)) :
                Math.max(...points.map(p => p.x));
            return points.filter(p => Math.abs(p.x - extremeV) < 0.05);
        };

        // Process each cycle
        cycles.forEach((cycle, cycleIndex) => {
            // Get points for this cycle
            const cyclePoints = Array.from({length: this.plotData.x.length}, (_, i) => ({
                x: this.plotData.x[i],
                y: this.plotData.y[i],
                cycle: this.plotData.cycle[i],
                direction: this.plotData.direction[i],
                index: i
            })).filter(p => p.cycle === cycle);

            // Create single trace for each cycle with proper voltage-based organization
            let cycleData;
            if (this.isRunning) {
                // Organize data based on measurement state and cycle boundaries
            let organizedPoints;
            if (this.isRunning) {
                // During measurement, maintain chronological order
                organizedPoints = cyclePoints;
            } else {
                // For completed measurements, organize proper CV loop
                const forward = cyclePoints.filter(p => p.direction === 1);
                const reverse = cyclePoints.filter(p => p.direction === -1);
                
                // Find closest points to target voltages
                const findClosestTo = (points, target) => points.reduce((prev, curr) => 
                    Math.abs(curr.x - target) < Math.abs(prev.x - target) ? curr : prev
                );
                
                const closestToLower = findClosestTo(cyclePoints, targetLowerV);
                const closestToUpper = findClosestTo(cyclePoints, targetUpperV);

                // Organize data based on CV parameters and scan direction
                if (Math.abs(targetStartV - targetLowerV) < Math.abs(targetStartV - targetUpperV)) {
                    // CV starts from lower voltage
                    const forward = [...lowerRegion, ...middleRegion.filter(p => p.direction === 'forward'), ...upperRegion]
                        .sort((a, b) => a.x - b.x);
                    const reverse = [...upperRegion, ...middleRegion.filter(p => p.direction === 'reverse'), ...lowerRegion]
                        .sort((a, b) => b.x - a.x);
                    
                    // Ensure proper cycle starts from the lowest voltage point
                    const lowestPoint = Math.min(...forward.map(p => p.x));
                    const forwardStart = forward.findIndex(p => Math.abs(p.x - lowestPoint) < 0.05);
                    
                    if (forwardStart > 0) {
                        // Rotate array to start from lowest voltage
                        const rotatedForward = [
                            ...forward.slice(forwardStart),
                            ...forward.slice(0, forwardStart)
                        ];
                        cycleData = [...rotatedForward, ...reverse];
                    } else {
                        cycleData = [...forward, ...reverse];
                    }
                } else {
                    // CV starts from upper voltage
                    const reverse = [...upperRegion, ...middleRegion.filter(p => p.direction === 'reverse'), ...lowerRegion]
                        .sort((a, b) => b.x - a.x);
                    const forward = [...lowerRegion, ...middleRegion.filter(p => p.direction === 'forward'), ...upperRegion]
                        .sort((a, b) => a.x - b.x);
                    
                    // Ensure proper cycle starts from the highest voltage point
                    const highestPoint = Math.max(...reverse.map(p => p.x));
                    const reverseStart = reverse.findIndex(p => Math.abs(p.x - highestPoint) < 0.05);
                    
                    if (reverseStart > 0) {
                        // Rotate array to start from highest voltage
                        const rotatedReverse = [
                            ...reverse.slice(reverseStart),
                            ...reverse.slice(0, reverseStart)
                        ];
                        cycleData = [...rotatedReverse, ...forward];
                    } else {
                        cycleData = [...reverse, ...forward];
                    }
                }
                }
            }
            
            console.log(`[DEBUG] Cycle ${cycle}: ${cycleData.length} points${this.isRunning ? ' (chronological)' : ' (smart CV loop)'}`);
            if (!this.isRunning && cycleData.length > 0) {
                console.log(`[DEBUG] Cycle ${cycle} voltage range: ${Math.min(...cycleData.map(p => p.x)).toFixed(3)}V to ${Math.max(...cycleData.map(p => p.x)).toFixed(3)}V`);
            }
            
            // Single trace per cycle for continuous CV curve
            // Helper function to get hue for cycle coloring
            const getTraceHue = (cycleIndex, totalCycles) => {
                // Start with blue (240°), progress through spectrum
                return 240 - (cycleIndex * 300 / (totalCycles || 1));
            };

            // Organize and create trace for this cycle
            const cyclePoints = Array.from({length: this.plotData.x.length}, (_, i) => ({
                x: this.plotData.x[i],
                y: this.plotData.y[i],
                cycle: this.plotData.cycle[i],
                direction: this.plotData.direction[i],
                index: i
            })).filter(p => p.cycle === cycle);

            if (cyclePoints.length === 0) return;

            // Organize points into proper CV loop based on cycle boundaries
            const cycleTrace = this.isRunning ? cyclePoints : (() => {
                // Separate points by direction
                const forward = cyclePoints.filter(p => p.direction === 1);
                const reverse = cyclePoints.filter(p => p.direction === -1);
                
                // For cycle 1, ensure proper start from target voltage
                if (cycle === 1) {
                    if (Math.abs(cyclePoints[0]?.x - targetLowerV) < 0.1) {
                        // First cycle starts from lower voltage, maintain chronological order
                        return cyclePoints;
                    } else {
                        // Adjust cycle 1 to start from proper voltage
                        return Math.abs(cyclePoints[0]?.x - targetUpperV) < 0.1 ?
                            cyclePoints : 
                            [...reverse.sort((a, b) => b.x - a.x), ...forward.sort((a, b) => a.x - b.x)];
                    }
                }
                
                // For subsequent cycles, ensure they start at voltage extremes
                const voltageExtreme = forward[0]?.x < reverse[0]?.x ? 
                    Math.min(...forward.map(p => p.x)) : 
                    Math.max(...forward.map(p => p.x));
                
                // Organize based on where this cycle naturally starts
                if (Math.abs(voltageExtreme - targetLowerV) < 0.1) {
                    return [...forward.sort((a, b) => a.x - b.x), 
                            ...reverse.sort((a, b) => b.x - a.x)];
                } else {
                    return [...reverse.sort((a, b) => b.x - a.x), 
                            ...forward.sort((a, b) => a.x - b.x)];
                }
            })();
            
            // Log cycle trace information for debugging
            console.log(`[DEBUG] Cycle ${cycle} analysis:`, {
                points: cycleTrace.length,
                voltageRange: {
                    min: Math.min(...cycleTrace.map(p => p.x)).toFixed(3),
                    max: Math.max(...cycleTrace.map(p => p.x)).toFixed(3)
                },
                directions: {
                    forward: cycleTrace.filter(p => p.direction === 1).length,
                    reverse: cycleTrace.filter(p => p.direction === -1).length
                },
                isRunning: this.isRunning
            });
            
            // Create color-coded trace
            const traceHue = getTraceHue(cycleIndex, cycles.length);
            const traceColor = `hsl(${traceHue}, 70%, 50%)`;
            
            traces.push({
                x: cycleTrace.map(p => p.x),
                y: cycleTrace.map(p => p.y),
                type: 'scatter',
                mode: 'lines',
                name: `Cycle ${cycle}`,
                line: {
                    width: 2,
                    color: traceColor,
                    shape: 'linear'
                },
                marker: {
                    size: 2,
                    color: traceColor,
                    opacity: 0.5
                },
                connectgaps: false,
                showlegend: true,
                hovertemplate: `Cycle ${cycle}<br>V: %{x:.4f}V<br>I: %{y:.2e}A<extra></extra>`
            });
        });

        // Calculate optimal plot ranges based on CV parameters and data
        const plotRanges = {
            x: {
                min: Math.min(minPotential, targetLowerV) - potentialPadding,
                max: Math.max(maxPotential, targetUpperV) + potentialPadding
            },
            y: {
                min: minCurrent - currentPadding,
                max: maxCurrent + currentPadding
            }
        };
        
        // Create layout optimized for CV display
        const layout = {
            title: {
                text: 'Cyclic Voltammetry',
                font: { size: 16 }
            },
            xaxis: {
                title: {
                    text: 'Potential (V)',
                    font: { size: 14 }
                },
                showgrid: true,
                gridcolor: '#f0f0f0',
                zeroline: true,
                zerolinecolor: '#666',
                range: [plotRanges.x.min, plotRanges.x.max],
                autorange: false,
                tickmode: 'linear',
                dtick: 0.2,  // Show ticks every 0.2V
                tickformat: '.2f'
            },
            yaxis: {
                title: {
                    text: 'Current (A)',
                    font: { size: 14 }
                },
                showgrid: true,
                gridcolor: '#f0f0f0',
                zeroline: true,
                zerolinecolor: '#666',
                tickformat: '.2e',
                range: [plotRanges.y.min, plotRanges.y.max],
                autorange: false,
                showexponent: 'all',
                exponentformat: 'e'
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
        console.log('[CV] Clearing plot data...');
        this.plotData = { x: [], y: [], cycle: [], direction: [] };
        
        if (this.plotDiv && this.plotInitialized) {
            // Clear the plot data but keep the plot structure
            try {
                Plotly.react(this.plotDiv, [], {
                    title: 'Cyclic Voltammetry',
                    xaxis: { title: 'Potential (V)', showgrid: true },
                    yaxis: { title: 'Current (A)', showgrid: true },
                    showlegend: true,
                    autosize: true,
                    margin: { l: 60, r: 40, t: 40, b: 60 }
                });
                console.log('[CV] Plot cleared successfully');
            } catch (error) {
                console.error('[CV] Error clearing plot:', error);
            }
        }
    }
    
    updateUIState() {
        // Check connection state and simulation mode
        let isConnected = false;
        let isSimulation = this.simulationToggle?.checked || false;
        
        console.log('[CV] updateUIState called:', {
            simulationMode: isSimulation,
            isRunning: this.isRunning,
            isPaused: this.isPaused
        });
        
        // Always consider connected in simulation mode
        if (isSimulation) {
            isConnected = true;
            console.log('[CV] Simulation mode active - connection state bypassed');
        }
        // Otherwise check real connection state
        else if (window.portManager && typeof window.portManager.isConnected === 'boolean') {
            isConnected = window.portManager.isConnected;
            console.log('[CV] PortManager connection state:', isConnected);
        }
        else if (typeof connectionState !== 'undefined' && typeof connectionState.isConnected === 'boolean') {
            isConnected = connectionState.isConnected;
            console.log('[CV] Global connection state:', isConnected);
        }
        else {
            const statusElement = document.getElementById('connection-status');
            if (statusElement) {
                isConnected = statusElement.textContent.includes('Connected');
                console.log('[CV] DOM connection state:', isConnected);
            }
        }
        
        console.log('[CV] Final connection state:', isConnected);
        console.log('[CV] Current UI state:', {
            isRunning: this.isRunning,
            isPaused: this.isPaused,
            isConnected: isConnected,
            startBtnExists: !!this.startBtn,
            startBtnDisabled: this.startBtn ? this.startBtn.disabled : 'N/A'
        });
        
        // Update button states
        if (this.startBtn) {
            const shouldDisable = this.isRunning || !isConnected;
            this.startBtn.disabled = shouldDisable;
            console.log('[CV] Start button - should disable:', shouldDisable, 'reasons:', {
                isRunning: this.isRunning,
                notConnected: !isConnected
            });
            
            // Visual feedback
            if (!shouldDisable) {
                this.startBtn.classList.remove('btn-secondary');
                this.startBtn.classList.add('btn-success');
            } else {
                this.startBtn.classList.remove('btn-success');
                this.startBtn.classList.add('btn-secondary');
            }
        } else {
            console.log('[CV] Start button not found!');
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
        [this.beginInput, this.upperInput, this.rateInput, this.cyclesInput]
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
        const currentCVParams = this.getCurrentParameters();
        const lowerV = parseFloat(currentCVParams.lower) || -0.4;
        const upperV = parseFloat(currentCVParams.upper) || 0.7;
        
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
    console.log('[CV] DOM loaded, checking for cv-controls...');
    
    // Wait a bit for other scripts to initialize
    setTimeout(() => {
        if (document.getElementById('cv-controls')) {
            console.log('[CV] Found cv-controls, initializing CV measurement...');
            window.cvMeasurement = new CVMeasurement();
            
            // Load defaults on page load
            window.cvMeasurement.loadDefaults();
        } else {
            console.log('[CV] cv-controls not found, looking for start-btn...');
            if (document.getElementById('start-btn')) {
                console.log('[CV] Found start-btn, initializing CV measurement for measurement page...');
                window.cvMeasurement = new CVMeasurement();
                
                // Force check connection state every second
                setInterval(() => {
                    if (window.cvMeasurement) {
                        console.log('[CV] Periodic UI update check...');
                        window.cvMeasurement.updateUIState();
                    }
                }, 1000);
            } else {
                console.log('[CV] Neither cv-controls nor start-btn found, skipping CV initialization');
            }
        }
        
        // Update UI state based on connection
        // Check if connectionState exists and has addEventListener
        if (typeof connectionState !== 'undefined' && connectionState.addListener) {
            console.log('[CV] Setting up connectionState listener...');
            connectionState.addListener((state) => {
                console.log('[CV] Connection state changed:', state);
                if (window.cvMeasurement) {
                    window.cvMeasurement.updateUIState();
                }
            });
        } else {
            console.log('[CV] connectionState not available, using fallback periodic check');
            // Fallback: Check connection state periodically
            setInterval(() => {
                if (window.cvMeasurement) {
                    window.cvMeasurement.updateUIState();
                }
            }, 1000);
        }
    }, 500); // Wait 500ms for other scripts
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
            const currentParams = this.getCurrentParameters();
            let lowerV = -0.4, upperV = 0.7;  // Default range
            
            if (currentParams) {
                lowerV = parseFloat(currentParams.lower) || -0.4;
                upperV = parseFloat(currentParams.upper) || 0.7;
            }    // Calculate actual data range
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
CVMeasurement.prototype.saveMeasurement = async function(isAutoSave = false) {
    try {
        if (this.plotData.x.length === 0) {
            this.showMessage('No measurement data to save', 'warning');
            return;
        }
        
        // Generate session ID with auto-save prefix if needed
        const prefix = isAutoSave ? 'AUTO_CV_' : 'CV_';
        const sessionId = `${prefix}${new Date().toISOString().replace(/[:.]/g, '-')}`;
        
        console.log(`[SAVE] ${isAutoSave ? 'Auto-' : ''}Saving measurement with ${this.plotData.x.length} data points`);
        
        // Show appropriate message
        if (isAutoSave) {
            this.showMessage('Auto-saving measurement data...', 'info');
        }
        
        // Prepare data points in the format expected by backend
        const dataPoints = [];
        for (let i = 0; i < this.plotData.x.length; i++) {
            dataPoints.push({
                potential: this.plotData.x[i],
                current: this.plotData.y[i],
                cycle: this.plotData.cycle[i] || 1,
                direction: this.plotData.direction[i] || 'forward',
                timestamp: Date.now() / 1000 + i * 0.1  // Approximate timestamps
            });
        }
        
        // Get current parameters
        const currentCVParams = this.getCurrentParameters();
        
        const requestData = {
            session_id: sessionId,
            data_points: dataPoints,
            parameters: {
                begin: currentCVParams.begin,
                upper: currentCVParams.upper,
                lower: currentCVParams.lower || currentCVParams.begin,  // Use begin as lower if not available
                rate: currentCVParams.rate,
                cycles: currentCVParams.cycles,
                measurement_type: 'CV',
                total_points: dataPoints.length
            }
        };
        
        console.log(`[SAVE] Sending data:`, {
            session_id: sessionId,
            data_points_count: dataPoints.length,
            parameters: requestData.parameters
        });
        
        const response = await fetch('/api/data-logging/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            const saveMessage = isAutoSave ? 
                `Measurement auto-saved as ${data.session_id}` : 
                `Measurement saved as ${data.session_id}`;
            this.showMessage(saveMessage, 'success');
            
            // Disable save button after successful save (but not for auto-save)
            if (!isAutoSave) {
                const saveBtn = document.getElementById('save-measurement-btn');
                if (saveBtn) {
                    saveBtn.disabled = true;
                    saveBtn.innerHTML = '<i class="fas fa-check"></i> Saved';
                }
            }
            
            console.log(`[SAVE] Successfully ${isAutoSave ? 'auto-' : ''}saved: ${data.session_id}`);
        } else {
            const errorMessage = isAutoSave ? 
                `Failed to auto-save measurement: ${data.error}` : 
                `Failed to save measurement: ${data.error}`;
            this.showMessage(errorMessage, 'error');
            console.error(`[SAVE] Save failed: ${data.error}`);
        }
        
    } catch (error) {
        console.error('[SAVE] Save measurement error:', error);
        this.showMessage('Failed to save measurement: ' + error.message, 'error');
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
