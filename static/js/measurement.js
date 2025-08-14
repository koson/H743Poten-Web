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
            params.scanRate = parseFloat(document.getElementById('dpv-scan-rate').value);
            break;
            
        case 'SWV':
            params.initial = parseFloat(document.getElementById('swv-initial').value);
            params.final = parseFloat(document.getElementById('swv-final').value);
            params.amplitude = parseFloat(document.getElementById('swv-amplitude').value);
            params.step = parseFloat(document.getElementById('swv-step').value);
            params.frequency = parseFloat(document.getElementById('swv-frequency').value);
            break;
            
        case 'CA':
            params.initial = parseFloat(document.getElementById('ca-initial').value);
            params.step = parseFloat(document.getElementById('ca-step').value);
            params.time = parseFloat(document.getElementById('ca-time').value);
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
            const response = await fetch('/api/measurement/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params)
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
            const response = await fetch('/api/measurement/stop', { method: 'POST' });
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

// Data collection
function startDataCollection() {
    const dataCollector = setInterval(async () => {
        if (!isMeasuring) {
            clearInterval(dataCollector);
            return;
        }
        
        try {
            const response = await fetch('/api/measurement/data');
            const data = await response.json();
            
            if (data.completed) {
                clearInterval(dataCollector);
                isMeasuring = false;
                startBtn.disabled = false;
                stopBtn.disabled = true;
            }
            
            if (data.points) {
                // Append new data points
                dataPoints.time.push(...data.points.time);
                dataPoints.potential.push(...data.points.potential);
                dataPoints.current.push(...data.points.current);
                
                // Update plot and table
                updatePlot(dataPoints);
                updateDataTable(dataPoints);
            }
        } catch (error) {
            console.error('Data collection error:', error);
            clearInterval(dataCollector);
        }
    }, 100); // Poll every 100ms
}

// Note: PortManager is initialized in port_manager.js
