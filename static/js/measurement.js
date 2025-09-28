// Global variables
let isConnected = false;
let isMeasuring = false;
let currentMode = 'CV';
let plot = null;
let dataPoints = [];

// DOM Elements
const connectBtn = document.getElementById('connect-btn');
const portSelect = document.getElementById('port-select');
const baudSelect = document.getElementById('baud-select');
const connectionStatus = document.getElementById('connection-status');
const modeSelect = document.getElementById('mode-select');
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const plotContainer = document.getElementById('plot-container');
const currentRange = document.getElementById('current-range');

// Update connection status based on global state
connectionState.addListener((state) => {
    if (state.isConnected) {
        isConnected = true;
        connectBtn.innerHTML = '<i class="fas fa-unlink"></i> Disconnect';
        connectionStatus.className = 'badge bg-success';
        connectionStatus.innerHTML = '<i class="fas fa-plug"></i> Connected';
        startBtn.disabled = false;
        
        // Update port and baud rate selects
        if (state.currentPort && portSelect.value !== state.currentPort) {
            portSelect.value = state.currentPort;
        }
        if (state.currentBaudRate && baudSelect.value !== state.currentBaudRate.toString()) {
            baudSelect.value = state.currentBaudRate.toString();
        }
    } else {
        isConnected = false;
        connectBtn.innerHTML = '<i class="fas fa-link"></i> Connect';
        connectionStatus.className = 'badge bg-secondary';
        connectionStatus.innerHTML = '<i class="fas fa-plug"></i> Disconnected';
        startBtn.disabled = true;
        stopBtn.disabled = true;
    }
});

// Initialize Plotly graph
function initializePlot() {
    const layout = {
        showlegend: true,
        xaxis: { title: 'Potential (V)' },
        yaxis: { title: 'Current (A)' },
        margin: { t: 20 },
        hovermode: 'closest'
    };

    plot = Plotly.newPlot('plot-container', [], layout, {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['lasso2d', 'select2d']
    });
}

// Update plot based on measurement mode
function updatePlot(data) {
    let traces = [];
    
    switch(currentMode) {
        case 'CV':
            traces = [{
                x: data.potential,
                y: data.current,
                mode: 'lines',
                name: 'CV Scan'
            }];
            break;
            
        case 'DPV':
        case 'SWV':
            traces = [{
                x: data.potential,
                y: data.current,
                mode: 'lines+markers',
                name: 'Voltammogram'
            }];
            break;
            
        case 'CA':
            traces = [{
                x: data.time,
                y: data.current,
                mode: 'lines',
                name: 'Chronoamperogram'
            }];
            Plotly.relayout('plot-container', {
                'xaxis.title': 'Time (s)'
            });
            break;
    }
    
    Plotly.react('plot-container', traces);
}

// Show/hide parameter groups based on selected mode
function showParameterGroup(mode) {
    // Hide all parameter groups
    document.querySelectorAll('.parameter-group').forEach(group => {
        group.style.display = 'none';
    });
    
    // Show selected parameter group
    const groupId = `${mode.toLowerCase()}-params`;
    const group = document.getElementById(groupId);
    if (group) {
        group.style.display = 'block';
    }
}

// Get parameters for current mode
function getModeParameters() {
    const params = {
        mode: currentMode,
        currentRange: currentRange.value
    };
    
    switch(currentMode) {
        case 'CV':
            params.initial = parseFloat(document.getElementById('cv-initial').value);
            params.final = parseFloat(document.getElementById('cv-final').value);
            params.scanRate = parseFloat(document.getElementById('cv-scan-rate').value);
            params.step = parseFloat(document.getElementById('cv-step').value);
            params.cycles = parseInt(document.getElementById('cv-cycles').value);
            break;
            
        case 'DPV':
            params.initial = parseFloat(document.getElementById('dpv-initial').value);
            params.final = parseFloat(document.getElementById('dpv-final').value);
            params.amplitude = parseFloat(document.getElementById('dpv-amplitude').value);
            params.step = parseFloat(document.getElementById('dpv-step').value);
            params.pulseWidth = parseFloat(document.getElementById('dpv-pulse-width').value);
            params.pulsePeriod = parseFloat(document.getElementById('dpv-pulse-period').value);
            break;
            
        case 'SWV':
            // Basic SWV parameters
            params.initial = parseFloat(document.getElementById('swv-initial').value);
            params.final = parseFloat(document.getElementById('swv-final').value);
            params.amplitude = parseFloat(document.getElementById('swv-amplitude').value);
            params.step = parseFloat(document.getElementById('swv-step').value);
            params.frequency = parseFloat(document.getElementById('swv-frequency').value);
            
            // Enhanced SWV parameters (for CV service compatibility)
            params.begin = params.initial;  // Map initial -> begin
            params.end = params.final;      // Map final -> end
            params.step_potential = params.step;
            
            // Preconcentration parameters
            params.preconc_enabled = document.getElementById('swv-preconc-enabled').checked;
            params.preconc_potential = parseFloat(document.getElementById('swv-preconc-potential').value);
            params.preconc_time = parseFloat(document.getElementById('swv-preconc-time').value);
            params.equilibration_time = parseFloat(document.getElementById('swv-equilibration-time').value);
            
            console.log('🚨 SWV Frontend Params:', params);
            break;
            
        case 'CA':
            params.initial = parseFloat(document.getElementById('ca-initial').value);
            params.step = parseFloat(document.getElementById('ca-step').value);
            params.duration = parseFloat(document.getElementById('ca-duration').value);
            params.interval = parseFloat(document.getElementById('ca-interval').value);
            break;
    }
    
    return params;
}

// Update data table
function updateDataTable(data) {
    const tbody = document.getElementById('data-table-body');
    tbody.innerHTML = '';
    
    for (let i = 0; i < data.time.length; i++) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${data.time[i].toFixed(3)}</td>
            <td>${data.potential[i].toFixed(3)}</td>
            <td>${data.current[i].toExponential(3)}</td>
        `;
        tbody.appendChild(row);
    }
}

// Export data to CSV
function exportToCsv() {
    const data = dataPoints;
    if (data.time.length === 0) return;
    
    let csv = 'Time (s),Potential (V),Current (A)\n';
    for (let i = 0; i < data.time.length; i++) {
        csv += `${data.time[i]},${data.potential[i]},${data.current[i]}\n`;
    }
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('hidden', '');
    a.setAttribute('href', url);
    a.setAttribute('download', `${currentMode}_measurement_${new Date().toISOString()}.csv`);
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

// Copy data to clipboard
function copyDataToClipboard() {
    const data = dataPoints;
    if (data.time.length === 0) return;
    
    let text = 'Time (s)\tPotential (V)\tCurrent (A)\n';
    for (let i = 0; i < data.time.length; i++) {
        text += `${data.time[i]}\t${data.potential[i]}\t${data.current[i]}\n`;
    }
    
    navigator.clipboard.writeText(text).then(() => {
        alert('Data copied to clipboard!');
    });
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    initializePlot();
    
    // Mode selection
    modeSelect.addEventListener('change', (e) => {
        currentMode = e.target.value;
        showParameterGroup(currentMode);
    });
    
    // Note: Connection handling is managed by PortManager
    // measurement.js only listens to connection state changes via connectionState.addListener above
    
    // Start measurement
    startBtn.addEventListener('click', async () => {
        if (!isConnected) return;
        
        try {
            const params = getModeParameters();
            const setupResponse = await fetch('/api/measurement/universal/setup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    mode: currentMode,
                    parameters: params
                })
            });
            
            if (!setupResponse.ok) {
                throw new Error('Setup failed');
            }
            
            const response = await fetch('/api/measurement/universal/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    mode: currentMode
                })
            });
            
            const data = await response.json();
            if (data.success) {
                isMeasuring = true;
                startBtn.disabled = true;
                stopBtn.disabled = false;
                dataPoints = { time: [], potential: [], current: [] };
                startDataCollection();
            }
        } catch (error) {
            console.error('Start measurement error:', error);
            alert('Failed to start measurement');
        }
    });
    
    // Stop measurement
    stopBtn.addEventListener('click', async () => {
        if (!isMeasuring) return;
        
        try {
            const response = await fetch('/api/measurement/universal/stop', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    mode: currentMode
                })
            });
            const data = await response.json();
            if (data.success) {
                isMeasuring = false;
                startBtn.disabled = false;
                stopBtn.disabled = true;
            }
        } catch (error) {
            console.error('Stop measurement error:', error);
        }
    });
    
    // Export button
    document.getElementById('export-csv-btn').addEventListener('click', exportToCsv);
    
    // Copy button
    document.getElementById('copy-data-btn').addEventListener('click', copyDataToClipboard);
    
    // Zoom controls
    document.getElementById('zoom-in-btn').addEventListener('click', () => {
        Plotly.relayout('plot-container', {
            'xaxis.range': [
                Plotly.d3.select('#plot-container').layout.xaxis.range[0] * 0.8,
                Plotly.d3.select('#plot-container').layout.xaxis.range[1] * 0.8
            ]
        });
    });
    
    document.getElementById('zoom-out-btn').addEventListener('click', () => {
        Plotly.relayout('plot-container', {
            'xaxis.range': [
                Plotly.d3.select('#plot-container').layout.xaxis.range[0] * 1.2,
                Plotly.d3.select('#plot-container').layout.xaxis.range[1] * 1.2
            ]
        });
    });
    
    document.getElementById('reset-zoom-btn').addEventListener('click', () => {
        Plotly.relayout('plot-container', {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
    });
});

// Data collection with improved timeout handling and request deduplication
function startDataCollection() {
    let consecutiveFailures = 0;
    const maxConsecutiveFailures = 10; // 🔧 FIXED: Reduce to 10 (5 seconds with 500ms polling)  
    let dataReceived = false; // Track if we've received any data
    let requestInProgress = false; // 🔧 NEW: Prevent duplicate requests
    
    const dataCollector = setInterval(async () => {
        if (!isMeasuring) {
            clearInterval(dataCollector);
            return;
        }
        
        // 🔧 NEW: Skip if previous request still in progress
        if (requestInProgress) {
            console.log('⏳ Skipping request - previous still in progress');
            return;
        }
        
        requestInProgress = true;
        try {
            const response = await fetch('/api/measurement/universal/status', {
                timeout: 3000, // 🔧 NEW: 3 second timeout
                headers: {
                    'Cache-Control': 'no-cache' // 🔧 NEW: Prevent caching
                }
            });
            
            // Check if response is OK
            if (!response.ok) {
                consecutiveFailures++;
                console.warn(`Data fetch failed: ${response.status} ${response.statusText} (${consecutiveFailures}/${maxConsecutiveFailures})`);
                
                // Only timeout if we haven't received any data AND we've had many failures
                if (!dataReceived && consecutiveFailures >= maxConsecutiveFailures) {
                    console.error('Measurement timeout: No data received from STM32');
                    clearInterval(dataCollector);
                    isMeasuring = false;
                    startBtn.disabled = false;
                    stopBtn.disabled = true;
                    alert('Measurement timeout: No data received from STM32. Please check connection and try again.');
                }
                return;
            }
            
            const data = await response.json();
            
            // Reset failure counter on successful response
            consecutiveFailures = 0;
            
            // Check if measurement is completed
            if (!data.active && !data.is_measuring && data.data_points_count > 0) {
                console.log('📡 Measurement completed by device');
                clearInterval(dataCollector);
                isMeasuring = false;
                startBtn.disabled = false;
                stopBtn.disabled = true;
                return;
            }
            
            // Process SWV progress data first (if available)
            if (data.swv_progress) {
                updateSWVProgress(data.swv_progress);
            }
            
            // Process measurement data from universal API
            if (data.measurement_data && data.measurement_data.length > 0) {
                dataReceived = true; // Mark that we've received data
                
                // Clear existing data and set new data from universal API
                dataPoints.time = [];
                dataPoints.potential = [];
                dataPoints.current = [];
                
                // Universal API provides complete dataset
                data.measurement_data.forEach(point => {
                    if (point.time !== undefined) dataPoints.time.push(point.time);
                    if (point.potential !== undefined) dataPoints.potential.push(point.potential);
                    if (point.current !== undefined) dataPoints.current.push(point.current);
                });
                
                // Update plot and table
                updatePlot(dataPoints);
                updateDataTable(dataPoints);
                
                console.log(`📡 Universal API: ${data.data_points_count} total points for ${data.mode} mode`);
            } else {
                // No data in this poll, but don't immediately fail
                console.log('📡 No measurement data yet (waiting for device...)');
            }
            
        } catch (error) {
            consecutiveFailures++;
            console.error(`Data collection error (${consecutiveFailures}/${maxConsecutiveFailures}):`, error);
            
            // Only timeout after many consecutive failures AND no data received
            if (!dataReceived && consecutiveFailures >= maxConsecutiveFailures) {
                console.error('Measurement timeout: Network/communication error');
                clearInterval(dataCollector);
                isMeasuring = false;
                startBtn.disabled = false;
                stopBtn.disabled = true;
                alert('Measurement timeout: Communication error. Please check connection and try again.');
            }
        } finally {
            // 🔧 NEW: Always reset request flag
            requestInProgress = false;
        }
    }, 500); // 🔧 FIXED: Reduce from 100ms to 500ms to prevent server overload in DPV mode
}

// SWV Progress tracking
function updateSWVProgress(progressData) {
    if (!progressData) return;
    
    const progressContainer = document.getElementById('swv-progress-container');
    const progressBar = document.getElementById('swv-progress-bar');
    const progressText = document.getElementById('swv-progress-text');
    const progressDetail = document.getElementById('swv-progress-detail');
    
    if (!progressContainer) return;
    
    // Show progress container during SWV measurement
    if (currentMode === 'SWV' && isMeasuring) {
        progressContainer.style.display = 'block';
    }
    
    console.log('🚨 SWV Progress Update:', progressData);
    
    if (progressData.phase === 'PRECONCENTRATION') {
        const percent = Math.round((progressData.elapsed / progressData.total) * 100);
        progressBar.style.width = `${percent}%`;
        progressBar.className = 'progress-bar bg-warning'; // Orange for preconc
        
        progressText.textContent = `Preconcentration: ${percent}%`;
        progressDetail.innerHTML = `
            <small class="text-muted">
                ⚡ Potential: ${progressData.potential}V | 
                ⏱️ Time: ${progressData.elapsed}s / ${progressData.total}s
            </small>
        `;
        
    } else if (progressData.phase === 'EQUILIBRATION') {
        const percent = Math.round((progressData.elapsed / progressData.total) * 100);
        progressBar.style.width = `${percent}%`;
        progressBar.className = 'progress-bar bg-info'; // Blue for equilibration
        
        progressText.textContent = `Equilibration: ${percent}%`;
        progressDetail.innerHTML = `
            <small class="text-muted">
                ⚖️ Stabilizing at ${progressData.potential}V | 
                ⏱️ Time: ${progressData.elapsed}s / ${progressData.total}s
            </small>
        `;
        
    } else if (progressData.phase === 'SCANNING') {
        const percent = Math.round((progressData.current_point / progressData.total_points) * 100);
        progressBar.style.width = `${percent}%`;
        progressBar.className = 'progress-bar bg-success'; // Green for scanning
        
        progressText.textContent = `SWV Scanning: ${percent}%`;
        progressDetail.innerHTML = `
            <small class="text-muted">
                📊 Point ${progressData.current_point} / ${progressData.total_points} | 
                ⚡ Current: ${progressData.potential}V
            </small>
        `;
        
    } else if (progressData.phase === 'COMPLETE') {
        progressBar.style.width = '100%';
        progressBar.className = 'progress-bar bg-success';
        progressText.textContent = 'SWV Complete! ✅';
        progressDetail.innerHTML = '<small class="text-success">Measurement finished successfully</small>';
        
        // Hide progress after 3 seconds
        setTimeout(() => {
            if (progressContainer) {
                progressContainer.style.display = 'none';
            }
        }, 3000);
    }
}

// SWV Preconcentration settings toggle
document.addEventListener('DOMContentLoaded', function() {
    const preoncEnabledCheckbox = document.getElementById('swv-preconc-enabled');
    const preoncSettings = document.getElementById('swv-preconc-settings');
    
    if (preoncEnabledCheckbox && preoncSettings) {
        function togglePreoncSettings() {
            if (preoncEnabledCheckbox.checked) {
                preoncSettings.classList.remove('disabled');
                preoncSettings.style.opacity = '1';
                
                // Enable all input fields
                const inputs = preoncSettings.querySelectorAll('input');
                inputs.forEach(input => input.disabled = false);
            } else {
                preoncSettings.classList.add('disabled');
                preoncSettings.style.opacity = '0.5';
                
                // Disable all input fields
                const inputs = preoncSettings.querySelectorAll('input');
                inputs.forEach(input => input.disabled = true);
            }
        }
        
        // Initial state
        togglePreoncSettings();
        
        // Listen for changes
        preoncEnabledCheckbox.addEventListener('change', togglePreoncSettings);
        
        console.log('🚨 SWV Preconcentration toggle initialized');
    }
});

// Note: PortManager is initialized in port_manager.js
