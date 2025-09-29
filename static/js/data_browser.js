/**
 * Data Browser JavaScript for H743Poten Web Interface
 * Handles universal measurement data browsing and management (CV, DPV, SWV, CA)
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
    
    // Start smart auto-refresh with much less frequent updates
    let refreshCounter = 0;
    setInterval(async () => {
        refreshCounter++;
        
        // Check measurement status less frequently (every 15 seconds)
        if (refreshCounter % 3 === 0) {
            await checkCurrentMeasurement();
        }
        
        // Check auto-save much less frequently - only when enabled (every 2 minutes)
        if (autoSaveToggle.checked && refreshCounter % 24 === 0) {
            await checkAutoSave();
        }
        
        // Refresh sessions list much less frequently to prevent image loading interruption (every 30 seconds)
        if (refreshCounter % 6 === 0) {
            await loadSessions();
        }
    }, 5000); // Base interval increased to 5 seconds
    
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
        
        // Auto-save enabled by default for data protection
        autoSaveToggle.checked = data.auto_save_enabled || true;
        
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
// Store previous sessions for comparison
let previousSessionsHash = null;

async function loadSessions() {
    try {
        const response = await fetch('/api/data-logging/sessions');
        const data = await response.json();
        
        if (data.error) {
            console.error('Failed to load sessions:', data.error);
            showError('Failed to load sessions');
            return;
        }
        
        const newSessions = data.sessions || [];
        
        // Create hash of sessions to check for changes
        const newSessionsHash = JSON.stringify(newSessions.map(s => ({
            id: s.session_id,
            timestamp: s.timestamp,
            count: s.data_points_count
        })));
        
        // Only update UI if sessions actually changed
        if (newSessionsHash !== previousSessionsHash) {
            showLoading(true);
            currentSessions = newSessions;
            renderSessions(currentSessions);
            previousSessionsHash = newSessionsHash;
            console.log(`📊 Sessions updated: ${newSessions.length} total`);
        }
        
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
    let paramsSummary = '';
    
    // Create universal parameter summary based on available parameters
    if (params.start_voltage !== undefined && params.end_voltage !== undefined) {
        paramsSummary = `${params.start_voltage}V to ${params.end_voltage}V`;
    } else if (params.lower !== undefined && params.upper !== undefined) {
        paramsSummary = `${params.lower}V to ${params.upper}V`;
    } else if (params.applied_voltage !== undefined) {
        paramsSummary = `Applied: ${params.applied_voltage}V`;
    } else {
        paramsSummary = 'Voltage: N/A';
    }
    
    // Add rate/frequency information
    if (params.scan_rate !== undefined) {
        paramsSummary += ` @ ${params.scan_rate}V/s`;
    } else if (params.rate !== undefined) {
        paramsSummary += ` @ ${params.rate}V/s`;
    } else if (params.frequency !== undefined) {
        paramsSummary += ` @ ${params.frequency}Hz`;
    } else if (params.duration !== undefined) {
        paramsSummary += ` for ${params.duration}s`;
    }
    
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
    
    // Parameters - Universal display
    const params = metadata.parameters || {};
    displayUniversalParameters(params, sessionData, metadata);
    document.getElementById('detail-cycles').textContent = 
        metadata.cycles || 1;
}

// Display parameters dynamically based on measurement mode
function displayUniversalParameters(params, sessionData, metadata) {
    const parametersDiv = document.getElementById('detail-parameters');
    let html = '<dl class="row">';
    
    // CV-specific parameters
    if (params.scan_rate !== undefined || params.rate !== undefined) {
        const scanRate = params.scan_rate || params.rate;
        html += `
            <dt class="col-sm-5">Scan Rate:</dt>
            <dd class="col-sm-7">${scanRate} V/s</dd>
        `;
    }
    
    // DPV/SWV-specific parameters
    if (params.step_size !== undefined) {
        html += `
            <dt class="col-sm-5">Step Size:</dt>
            <dd class="col-sm-7">${params.step_size} V</dd>
        `;
    }
    
    if (params.pulse_amplitude !== undefined) {
        html += `
            <dt class="col-sm-5">Pulse Amplitude:</dt>
            <dd class="col-sm-7">${params.pulse_amplitude} V</dd>
        `;
    }
    
    if (params.pulse_width !== undefined) {
        html += `
            <dt class="col-sm-5">Pulse Width:</dt>
            <dd class="col-sm-7">${params.pulse_width} ms</dd>
        `;
    }
    
    // SWV-specific parameters
    if (params.frequency !== undefined) {
        html += `
            <dt class="col-sm-5">Frequency:</dt>
            <dd class="col-sm-7">${params.frequency} Hz</dd>
        `;
    }
    
    // CA-specific parameters
    if (params.applied_voltage !== undefined) {
        html += `
            <dt class="col-sm-5">Applied Voltage:</dt>
            <dd class="col-sm-7">${params.applied_voltage} V</dd>
        `;
    }
    
    if (params.duration !== undefined) {
        html += `
            <dt class="col-sm-5">Duration:</dt>
            <dd class="col-sm-7">${params.duration} s</dd>
        `;
    }
    
    // Sampling parameters
    if (params.sample_interval !== undefined) {
        html += `
            <dt class="col-sm-5">Sample Interval:</dt>
            <dd class="col-sm-7">${params.sample_interval} ms</dd>
        `;
    }
    
    // If no specific parameters found, show default message
    if (html === '<dl class="row">') {
        html += '<dt class="col-sm-12"><em class="text-muted">No additional parameters available</em></dt>';
    }
    
    html += '</dl>';
    parametersDiv.innerHTML = html;
    
    // Load PNG image with simplified loader
    if (sessionData.png_exists) {
        const plotImg = document.getElementById('session-plot-img');
        const plotLoading = document.getElementById('plot-loading');
        
        // Reset loading state
        plotLoading.innerHTML = `
            <div class="d-flex flex-column align-items-center">
                <div class="spinner-border plot-loading-spinner" role="status"></div>
                <p class="mt-2 mb-0">Loading plot...</p>
                <small class="text-muted">Please wait</small>
            </div>
        `;
        
        // Use the simple image loader with improved fallback
        if (window.loadPlotImage && typeof window.loadPlotImage === 'function') {
            console.log('✅ Using external plot loader');
            window.loadPlotImage(metadata.session_id, plotImg, plotLoading);
        } else {
            console.log('🔄 Plot loader not available, using built-in fallback');
            // Built-in fallback image loading
            const imgUrl = `/api/data-logging/sessions/${metadata.session_id}/view/png?t=${Date.now()}`;
            console.log('📸 Loading image:', imgUrl);
            
            const timeout = setTimeout(() => {
                console.warn('⏰ Image load timeout');
                plotLoading.innerHTML = `
                    <div class="text-center text-muted py-3">
                        <i class="fas fa-clock fa-2x mb-2 text-warning"></i><br>
                        Loading timeout<br>
                        <small>Please try refreshing</small>
                    </div>
                `;
            }, 8000);
            
            plotImg.onload = () => {
                clearTimeout(timeout);
                console.log('✅ Image loaded successfully');
                plotLoading.style.display = 'none';
                plotImg.style.display = 'block';
            };
            
            plotImg.onerror = () => {
                clearTimeout(timeout);
                console.error('❌ Image failed to load');
                plotLoading.innerHTML = `
                    <div class="text-center text-muted py-3">
                        <i class="fas fa-times-circle fa-2x mb-2 text-danger"></i><br>
                        Image not available<br>
                        <small>Try again later</small>
                    </div>
                `;
            };
            
            // Start loading
            plotImg.src = imgUrl;
        }
        
    } else {
        console.log('No PNG file exists for this session');
        const plotLoading = document.getElementById('plot-loading');
        plotLoading.innerHTML = `
            <div class="text-center text-muted py-3">
                <i class="fas fa-image fa-2x mb-2"></i><br>
                No plot image available<br>
                <small>This session was saved without a plot</small>
            </div>
        `;
        plotLoading.style.display = 'block';
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
// Store previous button state to prevent unnecessary updates
let previousButtonState = null;

async function checkCurrentMeasurement() {
    try {
        // Check universal measurement status
        const response = await fetch('/api/measurement/status');
        const status = await response.json();
        
        let newButtonState;
        if (status.data_points_count && status.data_points_count > 0) {
            newButtonState = {
                disabled: false,
                title: `Save ${status.data_points_count} data points (${status.mode || 'Unknown'} mode)`
            };
        } else {
            newButtonState = {
                disabled: true,
                title: 'No current measurement data to save'
            };
        }
        
        // Only update button if state actually changed
        if (!previousButtonState || 
            previousButtonState.disabled !== newButtonState.disabled || 
            previousButtonState.title !== newButtonState.title) {
            
            saveCurrentBtn.disabled = newButtonState.disabled;
            saveCurrentBtn.title = newButtonState.title;
            previousButtonState = newButtonState;
        }
        
    } catch (error) {
        console.error('Error checking current measurement:', error);
        // Fallback to CV status for compatibility
        try {
            const cvResponse = await fetch('/api/cv/status');
            const cvStatus = await cvResponse.json();
            
            let fallbackButtonState;
            if (cvStatus.data_points_count && cvStatus.data_points_count > 0) {
                fallbackButtonState = {
                    disabled: false,
                    title: `Save ${cvStatus.data_points_count} data points (CV mode)`
                };
            } else {
                fallbackButtonState = {
                    disabled: true,
                    title: 'No current measurement data to save'
                };
            }
            
            // Only update button if state actually changed
            if (!previousButtonState || 
                previousButtonState.disabled !== fallbackButtonState.disabled || 
                previousButtonState.title !== fallbackButtonState.title) {
                
                saveCurrentBtn.disabled = fallbackButtonState.disabled;
                saveCurrentBtn.title = fallbackButtonState.title;
                previousButtonState = fallbackButtonState;
            }
            
        } catch (fallbackError) {
            console.error('Error checking CV fallback status:', fallbackError);
            if (!previousButtonState || !previousButtonState.disabled) {
                saveCurrentBtn.disabled = true;
                previousButtonState = { disabled: true, title: 'Error checking measurement status' };
            }
        }
    }
}

// Check for auto-save opportunities (ONLY when measurement completes)
async function checkAutoSave() {
    try {
        // Check if auto-save is enabled
        const autoSaveEnabled = autoSaveToggle.checked;
        if (!autoSaveEnabled) {
            return; // Auto-save is disabled
        }
        
        // Check universal measurement status
        const response = await fetch('/api/measurement/status');
        const status = await response.json();
        
        // Check if there's completed measurement data that hasn't been auto-saved
        if (status.success && 
            !status.active && 
            !status.is_measuring && 
            status.data_points_count > 0 &&
            status.mode) {
            
            // Check if this data was already auto-saved by looking at recent sessions
            const sessionsResponse = await fetch('/api/data-logging/sessions');
            const sessionsData = await sessionsResponse.json();
            
            if (sessionsData.sessions && sessionsData.sessions.length > 0) {
                // Check if the most recent session was created in the last 5 minutes to prevent duplicates
                const mostRecent = sessionsData.sessions[0];
                const recentTime = new Date(mostRecent.timestamp);
                const now = new Date();
                const timeDiff = (now - recentTime) / 1000; // seconds
                
                // If most recent session is very recent (within 5 minutes), check if it has same data points
                if (timeDiff < 300) { // 5 minutes
                    // If data points count matches, likely a duplicate - skip auto-save
                    if (mostRecent.metadata && 
                        mostRecent.metadata.data_points_count === status.data_points_count &&
                        mostRecent.metadata.mode === status.mode) {
                        console.log(`🚫 Skipping auto-save - recent ${status.mode} session with same data points exists`);
                        return;
                    }
                }
            }
            
            // Auto-save the measurement
            console.log(`🔄 Auto-saving ${status.mode} measurement with ${status.data_points_count} data points`);
            
            const sessionId = `${status.mode}_${new Date().toISOString().replace(/[:.]/g, '-')}`;
            
            const saveResponse = await fetch('/api/data-logging/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    session_id: sessionId,
                    auto_saved: true 
                })
            });
            
            const saveResult = await saveResponse.json();
            
            if (saveResult.success) {
                console.log(`✅ Auto-saved measurement: ${sessionId}`);
                showToast(`Auto-saved ${status.mode} measurement`, 'success');
                
                // Refresh sessions list to show the new auto-saved session
                await loadSessions();
            } else {
                console.error('Auto-save failed:', saveResult.error);
            }
        }
        
    } catch (error) {
        console.error('Error in auto-save check:', error);
    }
}

// Save current measurement
async function saveCurrentMeasurement() {
    try {
        // Determine current measurement mode
        let mode = 'UNKNOWN';
        try {
            const statusResponse = await fetch('/api/measurement/status');
            const statusData = await statusResponse.json();
            mode = statusData.mode || 'UNKNOWN';
        } catch (error) {
            // Fallback to CV if universal status not available
            mode = 'CV';
            console.warn('Using CV fallback for save operation');
        }
        
        // Generate session ID with mode prefix
        const sessionId = `${mode}_${new Date().toISOString().replace(/[:.]/g, '-')}`;
        
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
    // Only show loading for initial load or significant changes
    if (show && !previousSessionsHash) {
        loadingIndicator.style.display = 'block';
        loadingIndicator.style.opacity = '1';
        noDataMessage.style.display = 'none';
        sessionsContainer.style.opacity = '0.5';
    } else {
        loadingIndicator.style.opacity = '0';
        setTimeout(() => {
            if (loadingIndicator.style.opacity === '0') {
                loadingIndicator.style.display = 'none';
            }
        }, 200);
        sessionsContainer.style.opacity = '1';
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

// Auto-refresh is handled in the main initialization function above
// No need for duplicate interval
