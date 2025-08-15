/**
 * Data Browser JavaScript for H743Poten Web Interface
 * Handles CV measurement data browsing and management
 */

// Global variables
let currentSessions = [];
let currentSessionId = null;

// DOM Elements
const autoSaveToggle = document.getElementById('auto-save-toggle');
const dataDirectoryInput = document.getElementById('data-directory');
const totalSessionsSpan = document.getElementById('total-sessions');
const totalSizeSpan = document.getElementById('total-size');
const refreshDataBtn = document.getElementById('refresh-data-btn');
const refreshSessionsBtn = document.getElementById('refresh-sessions-btn');
const saveCurrentBtn = document.getElementById('save-current-btn');
const loadingIndicator = document.getElementById('loading-indicator');
const noDataMessage = document.getElementById('no-data-message');
const sessionsContainer = document.getElementById('sessions-container');
const sessionsTableBody = document.getElementById('sessions-table-body');

// Modal elements
const sessionDetailModal = new bootstrap.Modal(document.getElementById('session-detail-modal'));
const deleteConfirmationModal = new bootstrap.Modal(document.getElementById('delete-confirmation-modal'));

// Initialize data browser
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Data Browser initializing...');
    
    // Load initial data
    await loadDataInfo();
    await loadAutoSaveStatus();
    await loadSessions();
    
    // Check if we can save current measurement
    await checkCurrentMeasurement();
    
    // Set up event listeners
    setupEventListeners();
    
    console.log('Data Browser initialized');
});

// Event listeners
function setupEventListeners() {
    // Auto-save toggle
    autoSaveToggle.addEventListener('change', async (e) => {
        await setAutoSave(e.target.checked);
    });
    
    // Refresh buttons
    refreshDataBtn.addEventListener('click', async () => {
        await loadDataInfo();
    });
    
    refreshSessionsBtn.addEventListener('click', async () => {
        await loadSessions();
    });
    
    // Save current measurement
    saveCurrentBtn.addEventListener('click', async () => {
        await saveCurrentMeasurement();
    });
    
    // Modal download buttons
    document.getElementById('download-csv-btn').addEventListener('click', () => {
        if (currentSessionId) {
            downloadSessionFile(currentSessionId, 'csv');
        }
    });
    
    document.getElementById('download-png-btn').addEventListener('click', () => {
        if (currentSessionId) {
            downloadSessionFile(currentSessionId, 'png');
        }
    });
    
    // Modal delete button
    document.getElementById('delete-session-btn').addEventListener('click', () => {
        if (currentSessionId) {
            showDeleteConfirmation(currentSessionId);
        }
    });
    
    // Confirm delete button
    document.getElementById('confirm-delete-btn').addEventListener('click', async () => {
        if (currentSessionId) {
            await deleteSession(currentSessionId);
            deleteConfirmationModal.hide();
            sessionDetailModal.hide();
            await loadSessions();
            await loadDataInfo();
        }
    });
}

// Load data directory info
async function loadDataInfo() {
    try {
        const response = await fetch('/api/data-logging/info');
        const data = await response.json();
        
        if (data.error) {
            console.error('Failed to load data info:', data.error);
            return;
        }
        
        dataDirectoryInput.value = data.data_directory || 'Not set';
        totalSessionsSpan.textContent = data.total_sessions || 0;
        totalSizeSpan.textContent = `${data.total_size_mb || 0} MB`;
        
    } catch (error) {
        console.error('Error loading data info:', error);
    }
}

// Load auto-save status
async function loadAutoSaveStatus() {
    try {
        const response = await fetch('/api/data-logging/auto-save');
        const data = await response.json();
        
        if (data.error) {
            console.error('Failed to load auto-save status:', data.error);
            return;
        }
        
        autoSaveToggle.checked = data.auto_save_enabled || false;
        
    } catch (error) {
        console.error('Error loading auto-save status:', error);
    }
}

// Set auto-save status
async function setAutoSave(enabled) {
    try {
        const response = await fetch('/api/data-logging/auto-save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`Auto-save ${enabled ? 'enabled' : 'disabled'}`, 'success');
        } else {
            console.error('Failed to set auto-save:', data.error);
            showToast(`Failed to ${enabled ? 'enable' : 'disable'} auto-save`, 'error');
            // Revert toggle state
            autoSaveToggle.checked = !enabled;
        }
        
    } catch (error) {
        console.error('Error setting auto-save:', error);
        showToast('Error updating auto-save setting', 'error');
        // Revert toggle state
        autoSaveToggle.checked = !enabled;
    }
}

// Load sessions list
async function loadSessions() {
    try {
        showLoading(true);
        
        const response = await fetch('/api/data-logging/sessions');
        const data = await response.json();
        
        if (data.error) {
            console.error('Failed to load sessions:', data.error);
            showError('Failed to load sessions');
            return;
        }
        
        currentSessions = data.sessions || [];
        renderSessions(currentSessions);
        
    } catch (error) {
        console.error('Error loading sessions:', error);
        showError('Error loading sessions');
    } finally {
        showLoading(false);
    }
}

// Render sessions in table
function renderSessions(sessions) {
    if (sessions.length === 0) {
        showNoData();
        return;
    }
    
    showSessions();
    
    sessionsTableBody.innerHTML = '';
    
    sessions.forEach(session => {
        const row = createSessionRow(session);
        sessionsTableBody.appendChild(row);
    });
}

// Create session table row
function createSessionRow(session) {
    const row = document.createElement('tr');
    row.className = 'session-row';
    row.style.cursor = 'pointer';
    
    // Format timestamp
    const timestamp = new Date(session.timestamp).toLocaleString();
    
    // Parameters summary
    const params = session.parameters || {};
    const paramsSummary = `${params.lower || 'N/A'}V to ${params.upper || 'N/A'}V @ ${params.rate || 'N/A'}V/s`;
    
    // File status
    const files = session.files_exist || {};
    const csvIcon = files.csv ? '✅' : '❌';
    const pngIcon = files.png ? '✅' : '❌';
    
    row.innerHTML = `
        <td>
            <code>${session.session_id}</code>
        </td>
        <td>${timestamp}</td>
        <td>
            <small>${paramsSummary}</small><br>
            <small class="text-muted">${session.cycles || 1} cycle(s)</small>
        </td>
        <td>
            <span class="badge bg-info">${session.data_points_count || 0}</span>
        </td>
        <td>
            <span title="CSV file">📊 ${csvIcon}</span>
            <span title="PNG plot">📈 ${pngIcon}</span>
        </td>
        <td>
            <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-primary view-btn" title="View Details">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn btn-outline-success csv-btn" title="Download CSV" ${!files.csv ? 'disabled' : ''}>
                    <i class="fas fa-file-csv"></i>
                </button>
                <button class="btn btn-outline-secondary png-btn" title="Download PNG" ${!files.png ? 'disabled' : ''}>
                    <i class="fas fa-file-image"></i>
                </button>
                <button class="btn btn-outline-danger delete-btn" title="Delete Session">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </td>
    `;
    
    // Add event listeners
    const viewBtn = row.querySelector('.view-btn');
    const csvBtn = row.querySelector('.csv-btn');
    const pngBtn = row.querySelector('.png-btn');
    const deleteBtn = row.querySelector('.delete-btn');
    
    viewBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        showSessionDetails(session.session_id);
    });
    
    if (files.csv) {
        csvBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            downloadSessionFile(session.session_id, 'csv');
        });
    }
    
    if (files.png) {
        pngBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            downloadSessionFile(session.session_id, 'png');
        });
    }
    
    deleteBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        showDeleteConfirmation(session.session_id);
    });
    
    // Click on row to view details
    row.addEventListener('click', () => {
        showSessionDetails(session.session_id);
    });
    
    return row;
}

// Show session details in modal
async function showSessionDetails(sessionId) {
    try {
        currentSessionId = sessionId;
        
        // Show modal
        sessionDetailModal.show();
        
        // Set session ID in modal
        document.getElementById('modal-session-id').textContent = sessionId;
        document.getElementById('detail-session-id').textContent = sessionId;
        
        // Show loading for plot
        document.getElementById('plot-loading').style.display = 'block';
        document.getElementById('session-plot-img').style.display = 'none';
        
        // Load session details
        const response = await fetch(`/api/data-logging/sessions/${sessionId}`);
        const data = await response.json();
        
        if (data.error) {
            console.error('Failed to load session details:', data.error);
            showToast('Failed to load session details', 'error');
            return;
        }
        
        // Update modal with session details
        updateSessionDetailModal(data);
        
    } catch (error) {
        console.error('Error showing session details:', error);
        showToast('Error loading session details', 'error');
    }
}

// Update session detail modal with data
function updateSessionDetailModal(sessionData) {
    const metadata = sessionData.metadata;
    
    // Update info fields
    document.getElementById('detail-timestamp').textContent = 
        new Date(metadata.timestamp).toLocaleString();
    document.getElementById('detail-data-points').textContent = 
        metadata.data_points_count || 0;
    
    // Voltage range
    const voltageRange = metadata.voltage_range;
    if (voltageRange) {
        document.getElementById('detail-voltage-range').textContent = 
            `${voltageRange.min.toFixed(3)}V to ${voltageRange.max.toFixed(3)}V`;
    }
    
    // Current range
    const currentRange = metadata.current_range;
    if (currentRange) {
        document.getElementById('detail-current-range').textContent = 
            `${currentRange.min.toExponential(2)}A to ${currentRange.max.toExponential(2)}A`;
    }
    
    // Parameters
    const params = metadata.parameters || {};
    document.getElementById('detail-scan-rate').textContent = 
        `${params.rate || 'N/A'} V/s`;
    document.getElementById('detail-cycles').textContent = 
        metadata.cycles || 1;
    
    // Load PNG image
    if (sessionData.png_exists) {
        const plotImg = document.getElementById('session-plot-img');
        const imgUrl = `/api/data-logging/sessions/${metadata.session_id}/view/png?t=${Date.now()}`;
        console.log('Loading PNG image from:', imgUrl);
        
        plotImg.src = imgUrl;
        plotImg.onload = () => {
            console.log('PNG image loaded successfully');
            document.getElementById('plot-loading').style.display = 'none';
            plotImg.style.display = 'block';
        };
        plotImg.onerror = (error) => {
            console.error('Failed to load PNG image:', error);
            console.error('Image URL:', imgUrl);
            document.getElementById('plot-loading').style.display = 'none';
            plotImg.style.display = 'none';
            showToast('Failed to load plot image', 'error');
        };
    } else {
        console.log('No PNG file exists for this session');
        document.getElementById('plot-loading').style.display = 'none';
        document.getElementById('session-plot-img').style.display = 'none';
    }
}

// Download session file
function downloadSessionFile(sessionId, fileType) {
    const url = `/api/data-logging/sessions/${sessionId}/download/${fileType}`;
    
    // Create temporary download link
    const link = document.createElement('a');
    link.href = url;
    link.download = `${sessionId}.${fileType}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showToast(`${fileType.toUpperCase()} file downloaded`, 'success');
}

// Show delete confirmation
function showDeleteConfirmation(sessionId) {
    currentSessionId = sessionId;
    document.getElementById('delete-session-name').textContent = sessionId;
    deleteConfirmationModal.show();
}

// Delete session
async function deleteSession(sessionId) {
    try {
        const response = await fetch(`/api/data-logging/sessions/${sessionId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`Session ${sessionId} deleted`, 'success');
        } else {
            console.error('Failed to delete session:', data.error);
            showToast('Failed to delete session', 'error');
        }
        
    } catch (error) {
        console.error('Error deleting session:', error);
        showToast('Error deleting session', 'error');
    }
}

// Check if current measurement can be saved
async function checkCurrentMeasurement() {
    try {
        // Check CV measurement status
        const response = await fetch('/api/cv/status');
        const status = await response.json();
        
        if (status.data_points_count && status.data_points_count > 0) {
            saveCurrentBtn.disabled = false;
            saveCurrentBtn.title = `Save ${status.data_points_count} data points`;
        } else {
            saveCurrentBtn.disabled = true;
            saveCurrentBtn.title = 'No current measurement data to save';
        }
        
    } catch (error) {
        console.error('Error checking current measurement:', error);
        saveCurrentBtn.disabled = true;
    }
}

// Save current measurement
async function saveCurrentMeasurement() {
    try {
        // Generate session ID
        const sessionId = `CV_${new Date().toISOString().replace(/[:.]/g, '-')}`;
        
        const response = await fetch('/api/data-logging/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`Measurement saved as ${data.session_id}`, 'success');
            await loadSessions();
            await loadDataInfo();
            await checkCurrentMeasurement();
        } else {
            console.error('Failed to save measurement:', data.error);
            showToast('Failed to save measurement', 'error');
        }
        
    } catch (error) {
        console.error('Error saving measurement:', error);
        showToast('Error saving measurement', 'error');
    }
}

// UI state management
function showLoading(show) {
    loadingIndicator.style.display = show ? 'block' : 'none';
    if (show) {
        noDataMessage.style.display = 'none';
        sessionsContainer.style.display = 'none';
    }
}

function showNoData() {
    loadingIndicator.style.display = 'none';
    noDataMessage.style.display = 'block';
    sessionsContainer.style.display = 'none';
}

function showSessions() {
    loadingIndicator.style.display = 'none';
    noDataMessage.style.display = 'none';
    sessionsContainer.style.display = 'block';
}

function showError(message) {
    showNoData();
    // You could show a more specific error message here
    console.error(message);
}

// Toast notification (simple implementation)
function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <span>${message}</span>
            <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 5000);
}

// Auto-refresh sessions every 30 seconds
setInterval(async () => {
    await checkCurrentMeasurement();
}, 30000);
