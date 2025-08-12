// Global variables
let isConnected = false;
let isMeasuring = false;
let currentMode = 'CV';
let plot = null;
let dataPoints = [];
let updateInterval = null;

// DOM Elements
const connectBtn = document.getElementById('connect-btn');
const connectionStatus = document.getElementById('connection-status');
const modeSelect = document.getElementById('mode-select');
const setupBtn = document.getElementById('setup-btn');
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const exportBtn = document.getElementById('export-btn');
const uartInput = document.getElementById('uart-input');
const uartSendBtn = document.getElementById('uart-send-btn');
const uartOutput = document.getElementById('uart-output');
const clearUartBtn = document.getElementById('clear-uart-btn');
const exportUartBtn = document.getElementById('export-uart-btn');
const plotContainer = document.getElementById('plot-container');
const fullscreenPlotBtn = document.getElementById('fullscreen-plot-btn');
const clearPlotBtn = document.getElementById('clear-plot-btn');

// Initialize Plotly plot
function initializePlot() {
    const layout = {
        title: 'Measurement Data',
        xaxis: { title: 'Voltage (V)' },
        yaxis: { title: 'Current (A)' },
        showlegend: true,
        legend: { x: 0, y: 1 }
    };
    
    plot = Plotly.newPlot('plot-container', [], layout, {
        responsive: true,
        scrollZoom: true,
        modeBarButtonsToRemove: ['autoScale2d']
    });
}

// Connection handling
async function toggleConnection() {
    try {
        if (!isConnected) {
            const response = await fetch('/api/connection/connect', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                isConnected = true;
                updateConnectionUI(true);
                startDataPolling();
            }
        } else {
            const response = await fetch('/api/connection/disconnect', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                isConnected = false;
                updateConnectionUI(false);
                stopDataPolling();
            }
        }
    } catch (error) {
        console.error('Connection error:', error);
        showNotification('Connection error: ' + error.message, 'error');
    }
}

function updateConnectionUI(connected) {
    isConnected = connected;
    connectBtn.innerHTML = connected ? 
        '<i class="fas fa-unlink"></i> Disconnect' : 
        '<i class="fas fa-link"></i> Connect';
    
    connectionStatus.innerHTML = connected ?
        '<i class="fas fa-plug status-connected"></i> Connected' :
        '<i class="fas fa-plug status-disconnected"></i> Disconnected';
    
    setupBtn.disabled = !connected;
    startBtn.disabled = !connected;
    stopBtn.disabled = !connected;
    uartInput.disabled = !connected;
    uartSendBtn.disabled = !connected;
}

// Measurement control
async function setupMeasurement() {
    const mode = modeSelect.value;
    const params = getModeParameters(mode);
    
    try {
        const response = await fetch('/api/measurement/setup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode, params })
        });
        
        const data = await response.json();
        if (data.success) {
            showNotification('Measurement setup complete', 'success');
            startBtn.disabled = false;
        } else {
            showNotification('Setup failed: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Setup error:', error);
        showNotification('Setup error: ' + error.message, 'error');
    }
}

async function startMeasurement() {
    try {
        const response = await fetch('/api/measurement/start', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            isMeasuring = true;
            updateMeasurementUI(true);
            clearPlot();
        } else {
            showNotification('Start failed: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Start error:', error);
        showNotification('Start error: ' + error.message, 'error');
    }
}

async function stopMeasurement() {
    try {
        const response = await fetch('/api/measurement/stop', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            isMeasuring = false;
            updateMeasurementUI(false);
        } else {
            showNotification('Stop failed: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Stop error:', error);
        showNotification('Stop error: ' + error.message, 'error');
    }
}

function updateMeasurementUI(measuring) {
    isMeasuring = measuring;
    setupBtn.disabled = measuring;
    startBtn.disabled = measuring;
    stopBtn.disabled = !measuring;
    modeSelect.disabled = measuring;
}

// Data handling
function startDataPolling() {
    if (updateInterval) return;
    updateInterval = setInterval(updateData, 100);  // Poll every 100ms
}

function stopDataPolling() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
}

async function updateData() {
    if (!isConnected || !isMeasuring) return;
    
    try {
        const response = await fetch('/api/data/current');
        const data = await response.json();
        
        if (data.points && data.points.length > 0) {
            updatePlot(data.points);
        }
    } catch (error) {
        console.error('Data update error:', error);
    }
}

function updatePlot(points) {
    if (!plot) return;
    
    const xData = points.map(p => p.voltage);
    const yData = points.map(p => p.current);
    
    const trace = {
        x: xData,
        y: yData,
        mode: 'lines',
        name: currentMode
    };
    
    Plotly.update('plot-container', { x: [xData], y: [yData] });
}

function clearPlot() {
    dataPoints = [];
    Plotly.newPlot('plot-container', [], plot.layout);
}

// UART Console
async function sendUartCommand() {
    const command = uartInput.value.trim();
    if (!command) return;
    
    try {
        const response = await fetch('/api/uart/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command })
        });
        
        const data = await response.json();
        appendToUartOutput(command, data);
        uartInput.value = '';
        
    } catch (error) {
        console.error('UART error:', error);
        showNotification('UART error: ' + error.message, 'error');
    }
}

function appendToUartOutput(command, result) {
    const timestamp = new Date().toLocaleTimeString();
    const html = `
        <div class="mb-1">
            <span class="timestamp">[${timestamp}]</span>
            <span class="command">> ${command}</span>
            ${result.success ? 
                `<br><span class="response">${result.response}</span>` :
                `<br><span class="error">${result.error}</span>`}
        </div>
    `;
    uartOutput.innerHTML += html;
    uartOutput.scrollTop = uartOutput.scrollHeight;
}

function clearUartOutput() {
    uartOutput.innerHTML = '<div class="text-muted">UART communication log will appear here...</div>';
}

// Parameter handling
function getModeParameters(mode) {
    switch (mode) {
        case 'CV':
            return {
                start_voltage: parseFloat(document.getElementById('cv-start-voltage').value),
                end_voltage: parseFloat(document.getElementById('cv-end-voltage').value),
                scan_rate: parseFloat(document.getElementById('cv-scan-rate').value),
                step_size: parseFloat(document.getElementById('cv-step-size').value)
            };
        // Add other modes as needed
        default:
            return {};
    }
}

// Utility functions
function showNotification(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast show bg-${type === 'error' ? 'danger' : 'success'} text-white`;
    toast.innerHTML = `
        <div class="toast-body">
            ${message}
            <button type="button" class="btn-close btn-close-white float-end" data-bs-dismiss="toast"></button>
        </div>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// Event listeners
connectBtn.addEventListener('click', toggleConnection);
setupBtn.addEventListener('click', setupMeasurement);
startBtn.addEventListener('click', startMeasurement);
stopBtn.addEventListener('click', stopMeasurement);
clearPlotBtn.addEventListener('click', clearPlot);
uartSendBtn.addEventListener('click', sendUartCommand);
clearUartBtn.addEventListener('click', clearUartOutput);

uartInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendUartCommand();
});

fullscreenPlotBtn.addEventListener('click', () => {
    plotContainer.classList.toggle('fullscreen');
    fullscreenPlotBtn.innerHTML = plotContainer.classList.contains('fullscreen') ?
        '<i class="fas fa-compress"></i>' :
        '<i class="fas fa-expand"></i>';
});

modeSelect.addEventListener('change', (e) => {
    currentMode = e.target.value;
    // TODO: Show/hide parameter inputs based on mode
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializePlot();
    
    // Check initial connection status
    fetch('/api/connection/status')
        .then(response => response.json())
        .then(data => updateConnectionUI(data.connected))
        .catch(error => console.error('Status check error:', error));
});
