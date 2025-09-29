/**
 * Parameter Dashboard JavaScript
 * Manages measurement parameters and calibration data
 */

class ParameterDashboard {
    constructor() {
        this.measurements = [];
        this.filteredMeasurements = [];
        this.samples = [];
        this.selectedMeasurements = new Set(); // Track selected measurements
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadData();
    }

    bindEvents() {
        // Control panel events
        document.getElementById('refreshBtn').addEventListener('click', () => this.loadData());
        document.getElementById('exportBtn').addEventListener('click', () => this.exportData());
        
        // Filter events
        document.getElementById('sampleFilter').addEventListener('change', () => this.applyFilters());
        document.getElementById('instrumentFilter').addEventListener('change', () => this.applyFilters());
        document.getElementById('scanRateFilter').addEventListener('change', () => this.applyFilters());
        
        // Batch selection events
        document.getElementById('selectAllBtn')?.addEventListener('click', () => this.selectAll());
        document.getElementById('clearSelectionBtn')?.addEventListener('click', () => this.clearSelection());
        document.getElementById('processSelectedBtn')?.addEventListener('click', () => this.processSelected());
        document.getElementById('groupByScanRateBtn')?.addEventListener('click', () => this.groupByScanRate());
        document.getElementById('viewAveragedGraphBtn')?.addEventListener('click', () => this.viewAveragedGraph());
        document.getElementById('batchDeleteBtn')?.addEventListener('click', () => this.confirmBatchDelete());
        
        // Modal events
        document.getElementById('createCalibrationBtn').addEventListener('click', () => this.createCalibrationSession());
        document.getElementById('exportPeaksBtn').addEventListener('click', () => this.exportPeaks());
        document.getElementById('exportAveragedGraphBtn')?.addEventListener('click', () => this.exportAveragedGraph());
        document.getElementById('confirmDeleteBtn')?.addEventListener('click', () => this.executeDelete());
    }

    async loadData() {
        try {
            this.showLoading(true);
            
            // Load measurements
            const measurementsResponse = await fetch('/api/parameters/measurements');
            if (!measurementsResponse.ok) {
                throw new Error(`HTTP error! status: ${measurementsResponse.status}`);
            }
            
            const measurementsData = await measurementsResponse.json();
            
            // Handle both array response and object with success property
            if (Array.isArray(measurementsData)) {
                this.measurements = measurementsData;
            } else if (measurementsData.success && measurementsData.measurements) {
                this.measurements = measurementsData.measurements;
            } else {
                throw new Error(measurementsData.error || 'Failed to load measurements');
            }
            
            this.filteredMeasurements = [...this.measurements];
            this.updateStatistics();
            this.populateFilters();
            this.renderMeasurementsTable();
            
        } catch (error) {
            console.error('Error loading data:', error);
            this.showAlert('Error loading data: ' + error.message, 'danger');
        } finally {
            this.showLoading(false);
        }
    }

    updateStatistics() {
        const total = this.measurements.length;
        const reference = this.measurements.filter(m => m.instrument_type === 'palmsens').length;
        const target = this.measurements.filter(m => m.instrument_type === 'stm32').length;
        
        // Calculate potential calibration pairs
        const sampleGroups = {};
        this.measurements.forEach(m => {
            if (!sampleGroups[m.sample_id]) {
                sampleGroups[m.sample_id] = { palmsens: 0, stm32: 0 };
            }
            sampleGroups[m.sample_id][m.instrument_type]++;
        });
        
        const calibrationPairs = Object.values(sampleGroups)
            .reduce((acc, group) => acc + Math.min(group.palmsens, group.stm32), 0);

        document.getElementById('totalMeasurements').textContent = total;
        document.getElementById('referenceMeasurements').textContent = reference;
        document.getElementById('targetMeasurements').textContent = target;
        document.getElementById('calibrationPairs').textContent = calibrationPairs;
    }

    populateFilters() {
        // Get unique sample IDs
        const sampleIds = [...new Set(this.measurements.map(m => m.sample_id))].sort();
        
        const sampleFilter = document.getElementById('sampleFilter');
        sampleFilter.innerHTML = '<option value="">All Samples</option>';
        
        sampleIds.forEach(sampleId => {
            const option = document.createElement('option');
            option.value = sampleId;
            option.textContent = sampleId;
            sampleFilter.appendChild(option);
        });

        // Get unique scan rates
        const scanRates = [...new Set(this.measurements
            .map(m => m.scan_rate)
            .filter(sr => sr !== null && sr !== undefined))]
            .sort((a, b) => a - b);
        
        const scanRateFilter = document.getElementById('scanRateFilter');
        scanRateFilter.innerHTML = '<option value="">All Scan Rates</option>';
        
        scanRates.forEach(scanRate => {
            const option = document.createElement('option');
            option.value = scanRate;
            option.textContent = `${scanRate} mV/s`;
            scanRateFilter.appendChild(option);
        });
    }

    applyFilters() {
        const sampleFilter = document.getElementById('sampleFilter').value;
        const instrumentFilter = document.getElementById('instrumentFilter').value;
        const scanRateFilter = document.getElementById('scanRateFilter').value;
        
        this.filteredMeasurements = this.measurements.filter(measurement => {
            const sampleMatch = !sampleFilter || measurement.sample_id === sampleFilter;
            const instrumentMatch = !instrumentFilter || measurement.instrument_type === instrumentFilter;
            const scanRateMatch = !scanRateFilter || measurement.scan_rate == scanRateFilter;
            return sampleMatch && instrumentMatch && scanRateMatch;
        });
        
        this.renderMeasurementsTable();
    }

    renderMeasurementsTable() {
        const tbody = document.querySelector('#measurementsTable tbody');
        tbody.innerHTML = '';
        
        this.filteredMeasurements.forEach(measurement => {
            const row = this.createMeasurementRow(measurement);
            tbody.appendChild(row);
        });
    }

    createMeasurementRow(measurement) {
        const row = document.createElement('tr');
        
        // Format timestamp
        const timestamp = new Date(measurement.timestamp).toLocaleString();
        
        // Format voltage range
        const voltageRange = measurement.voltage_start !== null && measurement.voltage_end !== null
            ? `${measurement.voltage_start.toFixed(2)}V to ${measurement.voltage_end.toFixed(2)}V`
            : 'N/A';
        
        // Format scan rate
        const scanRate = measurement.scan_rate !== null 
            ? `${measurement.scan_rate} mV/s` 
            : 'N/A';
        
        // Format data points - show 0 if it's 0, show actual number if > 0
        const dataPoints = measurement.data_points !== null && measurement.data_points !== undefined
            ? measurement.data_points.toString()
            : 'Analysis Only';
        
        // Instrument badge
        const instrumentBadge = measurement.instrument_type === 'palmsens' 
            ? '<span class="badge bg-success">Palmsens</span>'
            : '<span class="badge bg-info">STM32</span>';
        
        row.innerHTML = `
            <td>
                <input type="checkbox" class="form-check-input measurement-checkbox" 
                       data-measurement-id="${measurement.id}" 
                       data-scan-rate="${measurement.scan_rate}"
                       data-sample-id="${measurement.sample_id}"
                       onchange="parameterDashboard.onSelectionChange(${measurement.id}, this.checked)">
            </td>
            <td>${measurement.id}</td>
            <td><strong>${measurement.sample_id}</strong></td>
            <td>${instrumentBadge}</td>
            <td>${timestamp}</td>
            <td>${scanRate}</td>
            <td>${voltageRange}</td>
            <td>${dataPoints}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="parameterDashboard.viewPeaks(${measurement.id})">
                    <i class="fas fa-chart-line"></i> View Peaks
                </button>
            </td>
            <td>
                <div class="btn-group" role="group">
                    <button class="btn btn-sm btn-outline-info" onclick="parameterDashboard.exportMeasurement(${measurement.id})" title="Export">
                        <i class="fas fa-download"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-warning" onclick="parameterDashboard.createCalibration('${measurement.sample_id}')" title="Calibrate">
                        <i class="fas fa-link"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="parameterDashboard.confirmDeleteMeasurement(${measurement.id})" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        
        return row;
    }

    async viewPeaks(measurementId) {
        try {
            const response = await fetch(`/api/parameters/measurements/${measurementId}/peaks`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Handle both array response and object with success property
            let peaks;
            if (Array.isArray(data)) {
                peaks = data;
            } else if (data.success && data.peaks) {
                peaks = data.peaks;
            } else {
                throw new Error(data.error || 'Failed to load peaks');
            }
            
            this.displayPeaksModal(peaks, measurementId);
            
        } catch (error) {
            console.error('Error loading peaks:', error);
            this.showAlert('Error loading peaks: ' + error.message, 'danger');
        }
    }

    displayPeaksModal(peaks, measurementId) {
        const modal = new bootstrap.Modal(document.getElementById('peakDetailsModal'));
        const content = document.getElementById('peakDetailsContent');
        
        if (peaks.length === 0) {
            content.innerHTML = '<p class="text-muted">No peaks found for this measurement.</p>';
        } else {
            let html = `
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Index</th>
                                <th>Type</th>
                                <th>Voltage (V)</th>
                                <th>Current (µA)</th>
                                <th>Height (µA)</th>
                                <th>Baseline</th>
                                <th>Enabled</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            peaks.forEach(peak => {
                const enabledBadge = peak.enabled 
                    ? '<span class="badge bg-success">Yes</span>'
                    : '<span class="badge bg-secondary">No</span>';
                
                const typeBadge = peak.peak_type === 'oxidation'
                    ? '<span class="badge bg-warning">Oxidation</span>'
                    : '<span class="badge bg-primary">Reduction</span>';
                
                const baselineInfo = peak.baseline_current !== null
                    ? `${peak.baseline_current.toFixed(2)} µA (R² = ${(peak.baseline_r2 || 0).toFixed(3)})`
                    : 'N/A';
                
                html += `
                    <tr>
                        <td>${peak.peak_index}</td>
                        <td>${typeBadge}</td>
                        <td>${(peak.peak_voltage || 0).toFixed(3)}</td>
                        <td>${(peak.peak_current || 0).toFixed(2)}</td>
                        <td>${(peak.peak_height || 0).toFixed(2)}</td>
                        <td>${baselineInfo}</td>
                        <td>${enabledBadge}</td>
                    </tr>
                `;
            });
            
            html += '</tbody></table></div>';
            content.innerHTML = html;
        }
        
        // Store current measurement ID for export
        this.currentMeasurementId = measurementId;
        modal.show();
    }

    async createCalibration(sampleId) {
        try {
            // Load calibration pairs for this sample
            const response = await fetch(`/api/parameters/calibration_pairs/${sampleId}`);
            const data = await response.json();
            
            if (data.success && data.pairs.length > 0) {
                this.displayCalibrationModal(data.pairs, sampleId);
            } else {
                this.showAlert(`No calibration pairs found for sample ${sampleId}. Need both Palmsens and STM32 measurements.`, 'warning');
            }
        } catch (error) {
            console.error('Error loading calibration pairs:', error);
            this.showAlert('Error loading calibration pairs: ' + error.message, 'danger');
        }
    }

    displayCalibrationModal(pairs, sampleId) {
        const modal = new bootstrap.Modal(document.getElementById('calibrationModal'));
        
        // Set default session name
        document.getElementById('sessionName').value = `${sampleId}_Calibration_${new Date().toISOString().split('T')[0]}`;
        
        // Populate reference measurements (Palmsens)
        const refSelect = document.getElementById('referenceMeasurement');
        refSelect.innerHTML = '';
        pairs.forEach(pair => {
            const option = document.createElement('option');
            option.value = pair.reference_id;
            option.textContent = `ID ${pair.reference_id} - ${new Date(pair.reference_timestamp).toLocaleString()}`;
            refSelect.appendChild(option);
        });
        
        // Populate target measurements (STM32)
        const targetSelect = document.getElementById('targetMeasurement');
        targetSelect.innerHTML = '';
        pairs.forEach(pair => {
            const option = document.createElement('option');
            option.value = pair.target_id;
            option.textContent = `ID ${pair.target_id} - ${new Date(pair.target_timestamp).toLocaleString()}`;
            targetSelect.appendChild(option);
        });
        
        modal.show();
    }

    async createCalibrationSession() {
        try {
            const formData = {
                session_name: document.getElementById('sessionName').value,
                reference_measurement_id: parseInt(document.getElementById('referenceMeasurement').value),
                target_measurement_id: parseInt(document.getElementById('targetMeasurement').value),
                calibration_method: document.getElementById('calibrationMethod').value,
                notes: document.getElementById('calibrationNotes').value
            };
            
            const response = await fetch('/api/parameters/create_calibration_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert(`Calibration session created: ${data.session_id}`, 'success');
                bootstrap.Modal.getInstance(document.getElementById('calibrationModal')).hide();
            } else {
                throw new Error(data.error || 'Failed to create calibration session');
            }
        } catch (error) {
            console.error('Error creating calibration session:', error);
            this.showAlert('Error creating calibration session: ' + error.message, 'danger');
        }
    }

    async exportMeasurement(measurementId) {
        try {
            const response = await fetch(`/api/parameters/export/${measurementId}?format=json`);
            const data = await response.json();
            
            if (data.success) {
                this.downloadJSON(data.data, `measurement_${measurementId}.json`);
            } else {
                throw new Error(data.error || 'Failed to export measurement');
            }
        } catch (error) {
            console.error('Error exporting measurement:', error);
            this.showAlert('Error exporting measurement: ' + error.message, 'danger');
        }
    }

    async exportPeaks() {
        if (!this.currentMeasurementId) return;
        
        try {
            const response = await fetch(`/api/parameters/measurements/${this.currentMeasurementId}/peaks`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Handle both array response and object with success property
            let exportData;
            if (Array.isArray(data)) {
                exportData = { peaks: data, success: true };
            } else if (data.success) {
                exportData = data;
            } else {
                throw new Error(data.error || 'Failed to export peaks');
            }
            
            this.downloadJSON(exportData, `peaks_${this.currentMeasurementId}.json`);
            
        } catch (error) {
            console.error('Error exporting peaks:', error);
            this.showAlert('Error exporting peaks: ' + error.message, 'danger');
        }
    }

    exportData() {
        // Export all filtered measurements
        const exportData = {
            measurements: this.filteredMeasurements,
            export_timestamp: new Date().toISOString(),
            total_count: this.filteredMeasurements.length
        };
        
        this.downloadJSON(exportData, `parameter_export_${new Date().toISOString().split('T')[0]}.json`);
    }

    downloadJSON(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    showLoading(show) {
        const spinner = document.getElementById('loadingSpinner');
        if (show) {
            spinner.classList.remove('d-none');
        } else {
            spinner.classList.add('d-none');
        }
    }

    showAlert(message, type = 'info') {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Insert at top of container
        const container = document.querySelector('.parameter-dashboard .container-fluid');
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // ===== BATCH PROCESSING METHODS =====
    
    onSelectionChange(measurementId, checked) {
        if (checked) {
            this.selectedMeasurements.add(measurementId);
        } else {
            this.selectedMeasurements.delete(measurementId);
        }
        this.updateSelectionInfo();
    }

    selectAll() {
        this.selectedMeasurements.clear();
        this.filteredMeasurements.forEach(m => this.selectedMeasurements.add(m.id));
        
        // Update checkboxes
        document.querySelectorAll('.measurement-checkbox').forEach(checkbox => {
            checkbox.checked = true;
        });
        
        this.updateSelectionInfo();
    }

    toggleSelectAll(checked) {
        if (checked) {
            this.selectAll();
        } else {
            this.clearSelection();
        }
        
        // Update main checkbox
        const selectAllCheckbox = document.getElementById('selectAllCheckbox');
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = checked;
        }
    }

    clearSelection() {
        this.selectedMeasurements.clear();
        
        // Update checkboxes
        document.querySelectorAll('.measurement-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        this.updateSelectionInfo();
    }

    updateSelectionInfo() {
        const count = this.selectedMeasurements.size;
        const selectedInfoElement = document.getElementById('selectedInfo');
        if (selectedInfoElement) {
            selectedInfoElement.textContent = `${count} measurement(s) selected`;
        }

        // Group by scan rate for display
        const groups = this.groupSelectedByScanRate();
        const groupInfoElement = document.getElementById('groupInfo');
        if (groupInfoElement && count > 0) {
            const groupTexts = Object.entries(groups).map(([scanRate, measurements]) => 
                `${scanRate}: ${measurements.length} measurements`
            );
            groupInfoElement.innerHTML = `<small>Groups: ${groupTexts.join(', ')}</small>`;
        } else if (groupInfoElement) {
            groupInfoElement.innerHTML = '';
        }
    }
    
    getSelectedMeasurementIds() {
        return Array.from(this.selectedMeasurements);
    }

    groupSelectedByScanRate() {
        const selected = this.measurements.filter(m => this.selectedMeasurements.has(m.id));
        console.log('\n=== GROUP SELECTED BY SCAN RATE DEBUG ===');
        console.log('Selected measurement IDs:', Array.from(this.selectedMeasurements));
        console.log('Filtered selected measurements:', selected.map(m => ({ id: m.id, scan_rate: m.scan_rate })));
        
        const groups = {};
        
        selected.forEach(measurement => {
            const scanRate = measurement.scan_rate !== null ? `${measurement.scan_rate} mV/s` : 'Unknown';
            console.log(`Measurement ${measurement.id}: scan_rate = ${measurement.scan_rate} -> group key = "${scanRate}"`);
            
            if (!groups[scanRate]) {
                groups[scanRate] = [];
            }
            groups[scanRate].push(measurement);
        });
        
        console.log('Final groups:', Object.entries(groups).map(([key, measurements]) => ({
            scanRate: key,
            count: measurements.length,
            measurementIds: measurements.map(m => m.id)
        })));
        console.log('=== END GROUP DEBUG ===\n');
        
        return groups;
    }

    groupByScanRate() {
        const groups = this.groupSelectedByScanRate();
        
        if (Object.keys(groups).length === 0) {
            this.showAlert('No measurements selected', 'warning');
            return;
        }

        // Auto-select measurements with same scan rate if only one group
        if (Object.keys(groups).length === 1) {
            const scanRate = Object.keys(groups)[0];
            this.showAlert(`Selected measurements already have the same scan rate: ${scanRate}`, 'info');
            return;
        }

        // Show group selection modal
        this.showScanRateGroupModal(groups);
    }

    showScanRateGroupModal(groups) {
        let modalHTML = `
            <div class="modal fade" id="scanRateGroupModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Group by Scan Rate</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>Selected measurements are grouped by scan rate:</p>
                            <div class="table-responsive">
                                <table class="table table-sm">
                                    <thead>
                                        <tr>
                                            <th>Scan Rate</th>
                                            <th>Count</th>
                                            <th>Sample IDs</th>
                                            <th>Action</th>
                                        </tr>
                                    </thead>
                                    <tbody>
        `;

        Object.entries(groups).forEach(([scanRate, measurements]) => {
            const sampleIds = [...new Set(measurements.map(m => m.sample_id))].join(', ');
            modalHTML += `
                <tr>
                    <td><strong>${scanRate}</strong></td>
                    <td>${measurements.length}</td>
                    <td>${sampleIds}</td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="parameterDashboard.processGroup('${scanRate}')">
                            Process Group
                        </button>
                    </td>
                </tr>
            `;
        });

        modalHTML += `
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" onclick="parameterDashboard.processAllGroups()">
                                Process All Groups
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if any
        const existingModal = document.getElementById('scanRateGroupModal');
        if (existingModal) existingModal.remove();

        // Add to body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('scanRateGroupModal'));
        modal.show();
    }

    async processSelected() {
        if (this.selectedMeasurements.size === 0) {
            this.showAlert('No measurements selected', 'warning');
            return;
        }

        const selected = this.measurements.filter(m => this.selectedMeasurements.has(m.id));
        
        try {
            // Group by scan rate for statistical analysis
            const groups = this.groupSelectedByScanRate();
            
            let results = {};
            for (const [scanRate, measurements] of Object.entries(groups)) {
                results[scanRate] = await this.calculateStatistics(measurements);
            }

            this.showStatisticsModal(results);
            
        } catch (error) {
            console.error('Error processing selected measurements:', error);
            this.showAlert('Error processing measurements: ' + error.message, 'danger');
        }
    }

    async processGroup(scanRate) {
        const groups = this.groupSelectedByScanRate();
        const measurements = groups[scanRate];
        
        if (!measurements || measurements.length === 0) {
            this.showAlert('No measurements found for this scan rate', 'warning');
            return;
        }

        try {
            const results = await this.calculateStatistics(measurements);
            this.showStatisticsModal({ [scanRate]: results });
        } catch (error) {
            console.error('Error processing group:', error);
            this.showAlert('Error processing group: ' + error.message, 'danger');
        }
    }

    async processAllGroups() {
        try {
            const groups = this.groupSelectedByScanRate();
            let results = {};
            
            for (const [scanRate, measurements] of Object.entries(groups)) {
                results[scanRate] = await this.calculateStatistics(measurements);
            }

            this.showStatisticsModal(results);
            
            // Close group modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('scanRateGroupModal'));
            if (modal) modal.hide();
            
        } catch (error) {
            console.error('Error processing all groups:', error);
            this.showAlert('Error processing groups: ' + error.message, 'danger');
        }
    }

    async calculateStatistics(measurements) {
        const peakData = [];
        
        // Collect all peaks from measurements
        for (const measurement of measurements) {
            try {
                const response = await fetch(`/api/parameters/measurements/${measurement.id}/peaks`);
                if (response.ok) {
                    const data = await response.json();
                    const peaks = Array.isArray(data) ? data : (data.peaks || []);
                    
                    peaks.forEach(peak => {
                        peakData.push({
                            measurementId: measurement.id,
                            sampleId: measurement.sample_id,
                            ...peak
                        });
                    });
                }
            } catch (error) {
                console.warn(`Failed to load peaks for measurement ${measurement.id}:`, error);
            }
        }

        // Group peaks by type
        const oxidationPeaks = peakData.filter(p => p.peak_type === 'oxidation');
        const reductionPeaks = peakData.filter(p => p.peak_type === 'reduction');

        // Calculate statistics
        return {
            measurements: measurements.length,
            totalPeaks: peakData.length,
            oxidationStats: this.calculatePeakStatistics(oxidationPeaks),
            reductionStats: this.calculatePeakStatistics(reductionPeaks),
            rawData: peakData
        };
    }

    calculatePeakStatistics(peaks) {
        if (peaks.length === 0) {
            return { count: 0, mean: null, std: null, min: null, max: null };
        }

        const heights = peaks.map(p => p.peak_height).filter(h => h !== null);
        const currents = peaks.map(p => p.peak_current).filter(c => c !== null);
        const voltages = peaks.map(p => p.peak_voltage).filter(v => v !== null);

        return {
            count: peaks.length,
            height: this.calculateStats(heights),
            current: this.calculateStats(currents),
            voltage: this.calculateStats(voltages)
        };
    }

    calculateStats(values) {
        if (values.length === 0) return { mean: null, std: null, min: null, max: null };

        const mean = values.reduce((a, b) => a + b, 0) / values.length;
        const variance = values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / values.length;
        const std = Math.sqrt(variance);

        return {
            mean: mean,
            std: std,
            min: Math.min(...values),
            max: Math.max(...values),
            sem: std / Math.sqrt(values.length) // Standard error of mean
        };
    }

    showStatisticsModal(results) {
        let modalHTML = `
            <div class="modal fade" id="statisticsModal" tabindex="-1">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Peak Statistics & Error Analysis</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
        `;

        Object.entries(results).forEach(([scanRate, stats]) => {
            modalHTML += `
                <div class="mb-4">
                    <h6 class="text-primary">Scan Rate: ${scanRate}</h6>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header bg-warning text-dark">
                                    <h6 class="mb-0">Oxidation Peaks (${stats.oxidationStats.count})</h6>
                                </div>
                                <div class="card-body">
                                    ${this.formatStatsTable(stats.oxidationStats)}
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card">
                                <div class="card-header bg-primary text-white">
                                    <h6 class="mb-0">Reduction Peaks (${stats.reductionStats.count})</h6>
                                </div>
                                <div class="card-body">
                                    ${this.formatStatsTable(stats.reductionStats)}
                                </div>
                            </div>
                        </div>
                    </div>
                    <p class="small text-muted mt-2">
                        Based on ${stats.measurements} measurements, ${stats.totalPeaks} total peaks
                    </p>
                </div>
            `;
        });

        modalHTML += `
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" onclick="parameterDashboard.exportStatistics()">
                                Export Results
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if any
        const existingModal = document.getElementById('statisticsModal');
        if (existingModal) existingModal.remove();

        // Add to body and show
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        const modal = new bootstrap.Modal(document.getElementById('statisticsModal'));
        modal.show();

        // Store results for export
        this.lastStatistics = results;
    }

    formatStatsTable(stats) {
        if (stats.count === 0) {
            return '<p class="text-muted">No peaks found</p>';
        }

        return `
            <table class="table table-sm">
                <tr>
                    <th>Parameter</th>
                    <th>Mean ± SEM</th>
                    <th>Std Dev</th>
                    <th>Range</th>
                </tr>
                <tr>
                    <td>Height (μA)</td>
                    <td>${stats.height?.mean?.toFixed(3) || 'N/A'} ± ${stats.height?.sem?.toFixed(3) || 'N/A'}</td>
                    <td>${stats.height?.std?.toFixed(3) || 'N/A'}</td>
                    <td>${stats.height?.min?.toFixed(3) || 'N/A'} to ${stats.height?.max?.toFixed(3) || 'N/A'}</td>
                </tr>
                <tr>
                    <td>Current (μA)</td>
                    <td>${stats.current?.mean?.toFixed(3) || 'N/A'} ± ${stats.current?.sem?.toFixed(3) || 'N/A'}</td>
                    <td>${stats.current?.std?.toFixed(3) || 'N/A'}</td>
                    <td>${stats.current?.min?.toFixed(3) || 'N/A'} to ${stats.current?.max?.toFixed(3) || 'N/A'}</td>
                </tr>
                <tr>
                    <td>Voltage (V)</td>
                    <td>${stats.voltage?.mean?.toFixed(4) || 'N/A'} ± ${stats.voltage?.sem?.toFixed(4) || 'N/A'}</td>
                    <td>${stats.voltage?.std?.toFixed(4) || 'N/A'}</td>
                    <td>${stats.voltage?.min?.toFixed(4) || 'N/A'} to ${stats.voltage?.max?.toFixed(4) || 'N/A'}</td>
                </tr>
            </table>
        `;
    }

    exportStatistics() {
        if (!this.lastStatistics) {
            this.showAlert('No statistics to export', 'warning');
            return;
        }

        const data = {
            timestamp: new Date().toISOString(),
            analysis_type: 'Peak Statistics with Error Bars',
            results: this.lastStatistics
        };

        this.downloadJSON(data, `peak_statistics_${new Date().toISOString().slice(0,10)}.json`);
    }

    async viewAveragedGraph() {
        if (this.selectedMeasurements.size === 0) {
            this.showAlert('Please select measurements to view averaged graph', 'warning');
            return;
        }

        // Wait for Plotly to be available
        if (typeof Plotly === 'undefined') {
            console.log('Waiting for Plotly to load...');
            await new Promise((resolve) => {
                const checkPlotly = () => {
                    if (typeof Plotly !== 'undefined') {
                        resolve();
                    } else {
                        setTimeout(checkPlotly, 100);
                    }
                };
                checkPlotly();
            });
        }

        const selected = this.measurements.filter(m => this.selectedMeasurements.has(m.id));
        
        try {
            // Group by scan rate
            const groups = this.groupSelectedByScanRate();
            
            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('averagedGraphModal'));
            modal.show();
            
            // Update modal info
            const groupCount = Object.keys(groups).length;
            const totalMeasurements = selected.length;
            
            // Check if any group has multiple measurements for proper averaging
            const groupsWithMultipleMeasurements = Object.entries(groups).filter(([rate, meas]) => meas.length > 1);
            const hasProperAveraging = groupsWithMultipleMeasurements.length > 0;
            
            let infoHtml = `
                <strong>Averaged Graph Analysis</strong><br>
                Selected measurements: ${totalMeasurements}<br>
                Scan rate groups: ${groupCount}<br>
                ${Object.entries(groups).map(([rate, meas]) => {
                    const filesList = meas.map(m => `ID:${m.id} (${m.filename || 'No filename'})`).join(', ');
                    return `<strong>${rate}:</strong> ${meas.length} measurements<br><small class="text-muted">Files: ${filesList}</small>`;
                }).join('<br>')}
            `;
            
            if (!hasProperAveraging) {
                infoHtml += `<br><br><div class="alert alert-warning mt-2">
                    <strong>Note:</strong> Each scan rate group has only 1 measurement. 
                    To see averaging with error bars, select multiple measurements with the same scan rate.
                </div>`;
            } else {
                infoHtml += `<br><br><div class="alert alert-info mt-2">
                    <strong>Averaging:</strong> ${groupsWithMultipleMeasurements.length} groups will show averaged curves with error bars.
                </div>`;
            }
            
            document.getElementById('averagedGraphInfo').innerHTML = infoHtml;
            
            // Plot averaged graph for each group
            await this.plotAveragedGraph(groups);
            
        } catch (error) {
            console.error('Error creating averaged graph:', error);
            this.showAlert('Error creating averaged graph: ' + error.message, 'danger');
        }
    }

    async plotAveragedGraph(groups) {
        // Check if Plotly is available
        if (typeof Plotly === 'undefined') {
            console.error('Plotly.js is not loaded');
            document.getElementById('averagedGraph').innerHTML = 
                '<div class="alert alert-danger">Plotly.js library is not loaded. Please refresh the page.</div>';
            return;
        }
        
        const plotData = [];
        const colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'];
        let colorIndex = 0;
        
        for (const [scanRate, measurements] of Object.entries(groups)) {
            try {
                // Get CV data for all measurements in this group
                const cvDataArray = await Promise.all(
                    measurements.map(async (measurement) => {
                        try {
                            console.log(`\n=== FETCHING DATA FOR MEASUREMENT ${measurement.id} ===`);
                            console.log(`Measurement details:`, {
                                id: measurement.id,
                                filename: measurement.filename,
                                scan_rate: measurement.scan_rate,
                                timestamp: measurement.timestamp
                            });
                            
                            const response = await fetch(`/api/parameters/measurements/${measurement.id}/peaks`);
                            if (!response.ok) {
                                console.warn(`❌ API request failed for measurement ${measurement.id}:`, response.status);
                                console.warn(`Using sample data as fallback`);
                                return await this.loadSampleData(); // Use real sample data as fallback
                            }
                            const data = await response.json();
                            console.log(`\n=== API DATA DEBUG FOR MEASUREMENT ${measurement.id} ===`);
                            console.log('Raw API response keys:', Object.keys(data));
                            console.log('CV data available:', !!data.cv_data);
                            console.log('CV data length:', data.cv_data ? data.cv_data.length : 'N/A');
                            
                            if (data.cv_data && data.cv_data.length > 0) {
                                const firstPoint = data.cv_data[0];
                                const midPoint = data.cv_data[Math.floor(data.cv_data.length/2)];
                                const lastPoint = data.cv_data[data.cv_data.length-1];
                                
                                console.log('Raw CV data structure:');
                                console.log('  First point keys:', Object.keys(firstPoint));
                                console.log('  First point values:', firstPoint);
                                console.log('  Mid point values:', midPoint);
                                console.log('  Last point values:', lastPoint);
                                
                                console.log('Sample data points:');
                                console.log(`  First: V=${firstPoint.voltage}, I=${firstPoint.current}`);
                                console.log(`  Mid:   V=${midPoint.voltage}, I=${midPoint.current}`);
                                console.log(`  Last:  V=${lastPoint.voltage}, I=${lastPoint.current}`);
                                
                                const currents = data.cv_data.map(p => p.current);
                                const voltages = data.cv_data.map(p => p.voltage);
                                const minCurrent = Math.min(...currents);
                                const maxCurrent = Math.max(...currents);
                                const minVoltage = Math.min(...voltages);
                                const maxVoltage = Math.max(...voltages);
                                
                                console.log('Data ranges:');
                                console.log(`  Voltage: ${minVoltage.toFixed(6)} to ${maxVoltage.toFixed(6)} V`);
                                console.log(`  Current: ${minCurrent.toFixed(6)} to ${maxCurrent.toFixed(6)} (units unknown)`);
                                console.log(`Peak magnitude estimate: ${Math.max(Math.abs(minCurrent), Math.abs(maxCurrent)).toFixed(6)}`);
                                
                                // Check if this looks like sample data pattern (be more specific)
                                const isSampleDataPattern = (
                                    Math.abs(minCurrent + 34.88) < 0.1 && 
                                    Math.abs(maxCurrent - 4.97) < 0.1 &&
                                    Math.abs(minVoltage + 0.4) < 0.001 &&
                                    Math.abs(maxVoltage - 0.7) < 0.001 &&
                                    data.cv_data.length === 220
                                );
                                
                                if (isSampleDataPattern) {
                                    console.warn('⚠️  WARNING: This data matches SAMPLE DATA pattern!');
                                    console.warn('   Expected real data should have much larger current values (μA range: -70000 to +100000)');
                                    console.warn('   This might indicate API is returning wrong data or using wrong CSV files');
                                } else {
                                    console.log('✅ Data pattern does NOT match known sample data');
                                }
                                
                                // Log measurement details for debugging
                                console.log(`📊 Measurement ${measurement.id} details:`, {
                                    id: measurement.id,
                                    scan_rate: measurement.scan_rate,
                                    filename: measurement.filename,
                                    timestamp: measurement.timestamp
                                });
                            }
                            console.log('=== END API DATA DEBUG ===\n');
                            
                            console.log(`CV data for measurement ${measurement.id}:`, data.cv_data ? data.cv_data.length : 'no data');
                            
                            // If no CV data, use sample data
                            if (!data.cv_data || data.cv_data.length === 0) {
                                console.warn(`❌ No CV data found for measurement ${measurement.id}`);
                                console.warn(`Using sample data as fallback`);
                                const sampleData = await this.loadSampleData();
                                // Mark as sample data
                                sampleData._isSampleData = true;
                                sampleData._originalMeasurementId = measurement.id;
                                sampleData._originalFilename = measurement.filename;
                                return sampleData;
                            }
                            
                            // Transform data structure if needed
                            let cvData = data.cv_data;
                            
                            // Check if data structure needs transformation (object format to array format)
                            if (cvData.length > 0 && cvData[0] && typeof cvData[0] === 'object') {
                                const firstPoint = cvData[0];
                                
                                // If data points are objects with numeric string keys (e.g., {'0': voltage, '1': current})
                                if ('0' in firstPoint && '1' in firstPoint && !('voltage' in firstPoint)) {
                                    console.log('🔄 Converting data format from object indices to voltage/current properties');
                                    cvData = cvData.map((point, index) => ({
                                        voltage: parseFloat(point['0']),
                                        current: parseFloat(point['1'])
                                    }));
                                    console.log(`✅ Converted ${cvData.length} data points`);
                                    
                                    // Verify conversion
                                    if (cvData.length > 0) {
                                        const first = cvData[0];
                                        const mid = cvData[Math.floor(cvData.length/2)];
                                        const last = cvData[cvData.length-1];
                                        console.log('Converted data verification:');
                                        console.log(`  First: V=${first.voltage.toFixed(3)}, I=${first.current.toFixed(3)}`);
                                        console.log(`  Mid:   V=${mid.voltage.toFixed(3)}, I=${mid.current.toFixed(3)}`);
                                        console.log(`  Last:  V=${last.voltage.toFixed(3)}, I=${last.current.toFixed(3)}`);
                                    }
                                }
                            }
                            
                            // Mark as real data
                            cvData._isRealData = true;
                            cvData._measurementId = measurement.id;
                            cvData._filename = measurement.filename;
                            console.log(`✅ Using REAL data for measurement ${measurement.id} (${measurement.filename})`);
                            
                            return cvData;
                        } catch (error) {
                            console.error(`Error fetching peaks for measurement ${measurement.id}:`, error);
                            return await this.loadSampleData(); // Use real sample data as fallback
                        }
                    })
                );
                
                if (cvDataArray.length === 0 || cvDataArray.every(data => data.length === 0)) {
                    console.warn(`No CV data found for scan rate ${scanRate}`);
                    continue;
                }
                
                console.log(`\n=== PROCESSING SCAN RATE: ${scanRate} mV/s ===`);
                console.log(`Measurements being averaged:`, measurements.map(m => `ID ${m.id} (${new Date(m.timestamp).toLocaleString()})`));
                console.log(`CV datasets collected: ${cvDataArray.length}`);
                
                // Check data sources
                const realDataCount = cvDataArray.filter(data => data._isRealData).length;
                const sampleDataCount = cvDataArray.filter(data => data._isSampleData).length;
                
                console.log(`📊 DATA SOURCE SUMMARY:`);
                console.log(`  - Real API data: ${realDataCount}/${cvDataArray.length}`);
                console.log(`  - Sample fallback data: ${sampleDataCount}/${cvDataArray.length}`);
                
                if (sampleDataCount > 0) {
                    console.warn(`⚠️  WARNING: ${sampleDataCount} measurements using sample data instead of real data!`);
                    cvDataArray.forEach((data, idx) => {
                        if (data._isSampleData) {
                            console.warn(`    - Measurement ${data._originalMeasurementId} (${data._originalFilename}): No CV data available`);
                        }
                    });
                }
                
                // Debug the raw CV data before averaging
                cvDataArray.forEach((data, idx) => {
                    const firstPoint = data[0];
                    const midPoint = data[Math.floor(data.length/2)];
                    const lastPoint = data[data.length-1];
                    console.log(`  Dataset ${idx+1}: ${data.length} points`);
                    console.log(`    First: V=${firstPoint.voltage.toFixed(3)}, I=${firstPoint.current.toFixed(3)}`);
                    console.log(`    Mid:   V=${midPoint.voltage.toFixed(3)}, I=${midPoint.current.toFixed(3)}`);
                    console.log(`    Last:  V=${lastPoint.voltage.toFixed(3)}, I=${lastPoint.current.toFixed(3)}`);
                });
                
                // Calculate averaged CV curve with error bars
                const averagedData = this.calculateAveragedCVData(cvDataArray);
                
                if (averagedData.voltage.length === 0) {
                    console.warn(`No averaged data generated for scan rate ${scanRate}`);
                    continue;
                }
                
                console.log(`Generated averaged data with ${averagedData.voltage.length} points for scan rate ${scanRate}`);
                
                // Export CSV data to console for manual inspection
                console.log(`\n=== CSV DATA EXPORT FOR ${scanRate} mV/s ===`);
                console.log('Copy the following to Excel/CSV:');
                console.log('Voltage(V),Current_Mean(µA),Current_SEM(µA)');
                for (let i = 0; i < Math.min(20, averagedData.voltage.length); i++) {
                    console.log(`${averagedData.voltage[i].toFixed(6)},${averagedData.currentMean[i].toFixed(6)},${averagedData.currentSem[i].toFixed(6)}`);
                }
                if (averagedData.voltage.length > 20) {
                    console.log(`... and ${averagedData.voltage.length - 20} more rows`);
                }
                console.log('=== END CSV EXPORT ===\n');
                
                const color = colors[colorIndex % colors.length];
                const baseColorIndex = colorIndex; // Store base color index for this group
                
                // Add individual measurement traces (with lighter opacity)
                cvDataArray.forEach((data, idx) => {
                    const measurement = measurements[idx]; // Get measurement from the measurements array
                    const lighterColor = this.adjustColorOpacity(color, 0.4); // Make individual traces lighter
                    
                    plotData.push({
                        x: data.map(point => point.voltage),
                        y: data.map(point => point.current),
                        mode: 'lines',
                        name: `ID ${measurement.id} (${scanRate} mV/s)`,
                        line: { 
                            color: lighterColor, 
                            width: 1.5,
                            dash: idx === 0 ? 'solid' : 'dash' // First solid, second dashed
                        },
                        type: 'scatter',
                        showlegend: true,
                        hovertemplate: `<b>ID ${measurement.id}</b><br>` +
                                     `Voltage: %{x:.3f} V<br>` +
                                     `Current: %{y:.2f} µA<br>` +
                                     `<extra></extra>`
                    });
                });
                
                // Add averaged trace with error bars (prominent)
                plotData.push({
                    x: averagedData.voltage,
                    y: averagedData.currentMean,
                    error_y: {
                        type: 'data',
                        array: averagedData.currentSem,
                        visible: true,
                        color: color,
                        thickness: 2,
                        width: 6
                    },
                    mode: 'lines',
                    name: `${scanRate} mV/s (Average ± SEM)`,
                    line: { color: color, width: 4 },
                    type: 'scatter',
                    showlegend: true,
                    hovertemplate: `<b>Average</b><br>` +
                                 `Voltage: %{x:.3f} V<br>` +
                                 `Current: %{y:.2f} ± %{error_y.array:.2f} µA<br>` +
                                 `<extra></extra>`
                });
                
                colorIndex++;
                
            } catch (error) {
                console.error(`Error processing group ${scanRate}:`, error);
            }
        }
        
        console.log('Final plot data:', plotData);
        
        // Debug plot data structure
        console.log('\n=== PLOT DATA DEBUG ===');
        console.log(`Number of traces to plot: ${plotData.length}`);
        plotData.forEach((trace, idx) => {
            console.log(`  Trace ${idx+1}: ${trace.name}`);
            console.log(`    X data points: ${trace.x ? trace.x.length : 'none'}`);
            console.log(`    Y data points: ${trace.y ? trace.y.length : 'none'}`);
            console.log(`    Error bars: ${trace.error_y ? 'yes' : 'no'}`);
            if (trace.x && trace.x.length > 0) {
                console.log(`    X range: ${Math.min(...trace.x).toFixed(3)} to ${Math.max(...trace.x).toFixed(3)}`);
                console.log(`    Y range: ${Math.min(...trace.y).toFixed(3)} to ${Math.max(...trace.y).toFixed(3)}`);
                console.log(`    Sample X values: [${trace.x.slice(0,3).map(v => v.toFixed(3)).join(', ')}]`);
                console.log(`    Sample Y values: [${trace.y.slice(0,3).map(v => v.toFixed(3)).join(', ')}]`);
            }
        });
        console.log('=== END PLOT DATA DEBUG ===\n');
        
        if (plotData.length === 0) {
            document.getElementById('averagedGraph').innerHTML = 
                '<div class="alert alert-warning">No CV data available for selected measurements</div>';
            return;
        }
        
        const layout = {
            title: 'Individual CV Curves vs Averaged Data with Error Bars',
            xaxis: { 
                title: 'Voltage (V)',
                showgrid: true,
                gridcolor: '#f0f0f0'
            },
            yaxis: { 
                title: 'Current (μA)',
                showgrid: true,
                gridcolor: '#f0f0f0'
            },
            hovermode: 'closest',
            showlegend: true,
            legend: {
                x: 0.02,
                y: 0.98,
                bgcolor: 'rgba(255,255,255,0.9)',
                bordercolor: '#ccc',
                borderwidth: 1,
                font: { size: 11 }
            },
            margin: { l: 60, r: 20, t: 80, b: 50 },
            annotations: [{
                text: 'Solid/dashed lines: Individual measurements<br>Thick lines with error bars: Averaged data ± SEM',
                showarrow: false,
                xref: 'paper',
                yref: 'paper',
                x: 0.02,
                y: -0.15,
                xanchor: 'left',
                yanchor: 'top',
                font: { size: 10, color: '#666' }
            }]
        };
        
        Plotly.newPlot('averagedGraph', plotData, layout, {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
        });
        
        console.log('✅ Plotly graph created successfully with', plotData.length, 'traces');
        console.log('📊 Graph element ID:', document.getElementById('averagedGraph') ? 'Found' : 'NOT FOUND');
        
        // Check the actual graph element content
        const graphElement = document.getElementById('averagedGraph');
        if (graphElement) {
            console.log('📋 Graph element HTML length:', graphElement.innerHTML.length);
            console.log('📋 Graph element classes:', graphElement.className);
            console.log('📋 Graph element children count:', graphElement.children.length);
            console.log('📋 Graph element first 200 chars:', graphElement.innerHTML.substring(0, 200));
        }
        
        // Force a small delay and then redraw to ensure modal is fully rendered
        setTimeout(() => {
            console.log('🔄 Forcing Plotly redraw...');
            Plotly.redraw('averagedGraph');
            console.log('🎯 Redraw completed at:', new Date().toLocaleTimeString());
            
            // Check content again after redraw
            const graphElementAfter = document.getElementById('averagedGraph');
            if (graphElementAfter) {
                console.log('📋 After redraw - HTML length:', graphElementAfter.innerHTML.length);
                console.log('📋 After redraw - first 200 chars:', graphElementAfter.innerHTML.substring(0, 200));
            }
        }, 100);
    }

    calculateAveragedCVData(cvDataArray) {
        if (cvDataArray.length === 0) return { voltage: [], currentMean: [], currentSem: [] };
        
        console.log('\n=== CV AVERAGING CALCULATION DEBUG ===');
        console.log(`Input: ${cvDataArray.length} CV datasets to average`);
        
        // Log details about each dataset
        cvDataArray.forEach((data, idx) => {
            console.log(`Dataset ${idx + 1}:`);
            console.log(`  - Points: ${data.length}`);
            console.log(`  - Voltage range: ${Math.min(...data.map(p => p.voltage)).toFixed(3)}V to ${Math.max(...data.map(p => p.voltage)).toFixed(3)}V`);
            console.log(`  - Current range: ${Math.min(...data.map(p => p.current)).toFixed(6)}µA to ${Math.max(...data.map(p => p.current)).toFixed(6)}µA`);
            console.log(`  - Sample points (first 3):`, data.slice(0, 3).map(p => `V=${p.voltage.toFixed(3)}, I=${p.current.toFixed(3)}`));
        });
        
        // For CV data, keep the complete CV cycle (forward + reverse) intact
        // Don't average across forward/reverse scans, only across different measurements
        
        if (cvDataArray.length === 1) {
            // Single measurement - return as is
            const data = cvDataArray[0];
            console.log('\n⚠️  SINGLE MEASUREMENT DETECTED - NO AVERAGING POSSIBLE ⚠️');
            console.log('This will show the original CV curve without error bars.');
            console.log('To see averaged curves with error bars, select multiple measurements with the same scan rate.');
            
            return {
                voltage: data.map(p => p.voltage),
                currentMean: data.map(p => p.current),
                currentSem: data.map(p => 0) // No error for single measurement
            };
        }
        
        // Multiple measurements - average corresponding points from different CV cycles
        console.log('\nMultiple measurements detected - averaging corresponding CV points');
        
        // Find the dataset with the most points to use as reference
        let referenceData = cvDataArray[0];
        for (const data of cvDataArray) {
            if (data.length > referenceData.length) {
                referenceData = data;
            }
        }
        
        console.log(`Reference dataset selected: ${referenceData.length} points`);
        console.log(`Reference voltage range: ${Math.min(...referenceData.map(p => p.voltage)).toFixed(3)}V to ${Math.max(...referenceData.map(p => p.voltage)).toFixed(3)}V`);
        
        // For each point in reference data, find corresponding points in other datasets
        const voltageGrid = [];
        const currentMean = [];
        const currentSem = [];
        
        let matchedPoints = 0;
        let totalPoints = 0;
        
        for (let refIdx = 0; refIdx < referenceData.length; refIdx++) {
            const refPoint = referenceData[refIdx];
            const refVoltage = refPoint.voltage;
            const currents = [refPoint.current];
            totalPoints++;
            
            // Find corresponding points in other datasets by index position 
            // (more reliable for CV data than voltage matching)
            for (let i = 1; i < cvDataArray.length; i++) {
                const dataset = cvDataArray[i];
                
                // Try to match by index first (for similar CV cycles)
                if (refIdx < dataset.length) {
                    const correspondingPoint = dataset[refIdx];
                    
                    // Verify voltage is reasonably close (within 0.02V tolerance for CV)
                    const voltageDiff = Math.abs(correspondingPoint.voltage - refVoltage);
                    if (voltageDiff < 0.02) {
                        currents.push(correspondingPoint.current);
                        matchedPoints++;
                    } else {
                        // Fallback: find nearest voltage point
                        let closestPoint = dataset[0];
                        let minDistance = Math.abs(dataset[0].voltage - refVoltage);
                        
                        for (const point of dataset) {
                            const distance = Math.abs(point.voltage - refVoltage);
                            if (distance < minDistance) {
                                minDistance = distance;
                                closestPoint = point;
                            }
                        }
                        
                        // Only include if voltage is reasonably close
                        if (minDistance < 0.02) {
                            currents.push(closestPoint.current);
                            matchedPoints++;
                        }
                    }
                }
            }
            
            // Calculate statistics for this point
            if (currents.length > 0) {
                const mean = currents.reduce((a, b) => a + b, 0) / currents.length;
                const variance = currents.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / currents.length;
                const sem = Math.sqrt(variance) / Math.sqrt(currents.length);
                
                // Debug extreme SEM values
                if (sem > 5.0) {
                    console.warn(`High SEM detected at V=${refVoltage.toFixed(3)}: SEM=${sem.toFixed(3)}, currents=[${currents.map(c => c.toFixed(2)).join(', ')}]`);
                }
                
                voltageGrid.push(refVoltage);
                currentMean.push(mean);
                currentSem.push(sem);
            }
        }
        
        console.log(`\nAveraging results:`);
        console.log(`  - Total reference points processed: ${totalPoints}`);
        console.log(`  - Matched points across datasets: ${matchedPoints}`);
        console.log(`  - Final averaged data points: ${voltageGrid.length}`);
        console.log(`  - Average voltage range: ${Math.min(...voltageGrid).toFixed(3)}V to ${Math.max(...voltageGrid).toFixed(3)}V`);
        console.log(`  - Average current range: ${Math.min(...currentMean).toFixed(6)}µA to ${Math.max(...currentMean).toFixed(6)}µA`);
        console.log(`  - Sample averaged points (first 5):`);
        for (let i = 0; i < Math.min(5, voltageGrid.length); i++) {
            console.log(`    [${i}] V=${voltageGrid[i].toFixed(3)}, I_mean=${currentMean[i].toFixed(3)}, I_sem=${currentSem[i].toFixed(3)}`);
        }
        console.log('=== END CV AVERAGING DEBUG ===\n');
        
        return {
            voltage: voltageGrid,
            currentMean: currentMean,
            currentSem: currentSem
        };
    }

    generateDemoData() {
        // Generate realistic CV data based on actual CV characteristics
        const demoData = [];
        const vStart = -0.4, vEnd = 0.7;
        const steps = 110;
        
        // Add some variation for different measurements
        const variation = () => (Math.random() - 0.5) * 0.02;
        const baseNoise = () => (Math.random() - 0.5) * 0.5;
        
        console.log('Generating synthetic CV data with proper voltage progression');
        
        // Forward scan (-0.4V to 0.7V)
        for (let i = 0; i <= steps; i++) {
            const voltage = vStart + (vEnd - vStart) * i / steps;
            let current = 0;
            
            // Background current (capacitive + residual)
            current += -3 + voltage * 1.5;
            
            // Oxidation peak around 0.15V
            if (voltage > -0.1 && voltage < 0.5) {
                const oxPeak = 0.15 + variation();
                const oxHeight = 75 + Math.random() * 15;
                const oxWidth = 0.07;
                current += oxHeight * Math.exp(-Math.pow(voltage - oxPeak, 2) / (2 * oxWidth * oxWidth));
            }
            
            // Add noise
            current += baseNoise();
            
            demoData.push({
                voltage: Math.round(voltage * 1000) / 1000,
                current: Math.round(current * 100) / 100
            });
        }
        
        // Reverse scan (0.7V to -0.4V) - continue from where forward scan ended
        for (let i = steps - 1; i >= 0; i--) {
            const voltage = vStart + (vEnd - vStart) * i / steps;
            let current = 0;
            
            // Background current (more negative due to charging effects)
            current += -6 + voltage * 1.2;
            
            // Reduction peak around -0.05V (different position than oxidation)
            if (voltage > -0.3 && voltage < 0.2) {
                const redPeak = -0.05 + variation();
                const redHeight = -55 - Math.random() * 10;
                const redWidth = 0.08;
                current += redHeight * Math.exp(-Math.pow(voltage - redPeak, 2) / (2 * redWidth * redWidth));
            }
            
            // Add noise
            current += baseNoise();
            
            demoData.push({
                voltage: Math.round(voltage * 1000) / 1000,
                current: Math.round(current * 100) / 100
            });
        }
        
        console.log(`Generated synthetic CV data: ${demoData.length} points`);
        console.log(`Voltage range: ${Math.min(...demoData.map(p => p.voltage))}V to ${Math.max(...demoData.map(p => p.voltage))}V`);
        console.log(`Current range: ${Math.min(...demoData.map(p => p.current))}µA to ${Math.max(...demoData.map(p => p.current))}µA`);
        
        return demoData;
    }

    async loadSampleData() {
        // Load real CV data from sample files - try multiple files
        const sampleFiles = [
            'sample_data/Palmsens_0.5mM_CV_20mVpS_E3_scan_08.csv',
            'sample_data/cv_sample.csv',
            'sample_data/Pipot_Ferro_0_5mM_50mVpS_E4_scan_05.csv'
        ];
        
        console.log('=== CV DATA LOADING DETAILED DEBUG ===');
        console.log('Attempting to load sample data from files:', sampleFiles);
        
        for (const filePath of sampleFiles) {
            try {
                console.log(`\n--- Trying file: ${filePath} ---`);
                const response = await fetch(filePath);
                if (!response.ok) {
                    console.log(`✗ HTTP ${response.status}: ${response.statusText}`);
                    continue;
                }
                
                const csvText = await response.text();
                console.log(`✓ File loaded successfully`);
                console.log(`  - File size: ${csvText.length} characters`);
                console.log(`  - First 300 characters:`);
                console.log(csvText.substring(0, 300));
                
                const lines = csvText.split('\n').filter(line => line.trim());
                console.log(`  - Total lines: ${lines.length}`);
                
                // Skip first line if it's a comment or filename
                let startLine = 0;
                if (lines[0].includes('FileName:') || lines[0].includes('#')) {
                    startLine = 1;
                    console.log(`  - Skipping comment line: "${lines[0]}"`);
                }
                
                // Parse header
                const headers = lines[startLine].split(',').map(h => h.trim());
                console.log(`  - Headers found:`, headers);
                
                let voltageIndex = -1;
                let currentIndex = -1;
                
                // Look for voltage column (V)
                for (let i = 0; i < headers.length; i++) {
                    const header = headers[i].toLowerCase();
                    if (header === 'v' || header.includes('voltage')) {
                        voltageIndex = i;
                        console.log(`  - Voltage column found at index ${i}: "${headers[i]}"`);
                        break;
                    }
                }
                
                // Look for current column (uA, µA, current)
                for (let i = 0; i < headers.length; i++) {
                    const header = headers[i].toLowerCase();
                    if (header === 'ua' || header === 'µa' || header.includes('current')) {
                        currentIndex = i;
                        console.log(`  - Current column found at index ${i}: "${headers[i]}"`);
                        break;
                    }
                }
                
                if (voltageIndex === -1 || currentIndex === -1) {
                    console.log(`✗ Could not find voltage/current columns`);
                    console.log(`    Voltage index: ${voltageIndex}, Current index: ${currentIndex}`);
                    console.log(`    Headers were:`, headers);
                    continue;
                }
                
                const cvData = [];
                let validRows = 0;
                let invalidRows = 0;
                
                console.log(`  - Parsing data from line ${startLine + 1} to ${lines.length - 1}...`);
                
                for (let i = startLine + 1; i < lines.length; i++) {
                    const values = lines[i].split(',');
                    if (values.length >= Math.max(voltageIndex, currentIndex) + 1) {
                        const voltage = parseFloat(values[voltageIndex]);
                        const current = parseFloat(values[currentIndex]);
                        
                        if (!isNaN(voltage) && !isNaN(current)) {
                            cvData.push({ voltage, current });
                            validRows++;
                            
                            // Log first few data points for verification
                            if (validRows <= 5) {
                                console.log(`    Data point ${validRows}: V=${voltage.toFixed(6)}, I=${current.toFixed(6)}`);
                            }
                        } else {
                            invalidRows++;
                            if (invalidRows <= 3) {
                                console.log(`    Invalid row ${i}: voltage="${values[voltageIndex]}", current="${values[currentIndex]}"`);
                            }
                        }
                    } else {
                        invalidRows++;
                        if (invalidRows <= 3) {
                            console.log(`    Short row ${i}: ${values.length} columns, expected >= ${Math.max(voltageIndex, currentIndex) + 1}`);
                        }
                    }
                }
                
                console.log(`  - Data parsing results:`);
                console.log(`    Valid rows: ${validRows}`);
                console.log(`    Invalid rows: ${invalidRows}`);
                console.log(`    Total data points: ${cvData.length}`);
                
                if (cvData.length > 10) { // Lower threshold for testing
                    console.log(`✓ SUCCESS: Using data from ${filePath}`);
                    console.log(`  - Voltage range: ${Math.min(...cvData.map(p => p.voltage)).toFixed(6)}V to ${Math.max(...cvData.map(p => p.voltage)).toFixed(6)}V`);
                    console.log(`  - Current range: ${Math.min(...cvData.map(p => p.current)).toFixed(6)}µA to ${Math.max(...cvData.map(p => p.current)).toFixed(6)}µA`);
                    console.log(`  - Final sample data points (first 5):`);
                    cvData.slice(0, 5).forEach((point, idx) => {
                        console.log(`    [${idx}] V=${point.voltage.toFixed(6)}, I=${point.current.toFixed(6)}`);
                    });
                    
                    // Return actual data without artificial variation for now
                    console.log(`  - Returning real CV data without artificial variation`);
                    console.log('=== SELECTED FILE FOR AVERAGING ===');
                    return cvData;
                } else {
                    console.log(`✗ Insufficient data points: ${cvData.length} (need >10)`);
                }
                
            } catch (error) {
                console.log(`✗ Error loading ${filePath}:`, error);
                continue;
            }
        }
        
        // If all real files failed, use demo data
        console.log('\n⚠ FALLBACK TO DEMO DATA ⚠');
        console.log('Could not load any sample data files, using synthetic demo data');
        return this.generateDemoData();
    }

    exportAveragedGraph() {
        if (!document.getElementById('averagedGraph').children.length) {
            this.showAlert('No averaged graph to export', 'warning');
            return;
        }

        // Export as PNG
        Plotly.downloadImage('averagedGraph', {
            format: 'png',
            width: 1200,
            height: 800,
            filename: `averaged_cv_graph_${new Date().toISOString().slice(0,10)}`
        });
    }
    
    // Helper function to adjust color opacity
    adjustColorOpacity(color, opacity) {
        // Convert named colors or hex to rgba
        if (color.startsWith('#')) {
            // Hex color
            const r = parseInt(color.slice(1, 3), 16);
            const g = parseInt(color.slice(3, 5), 16);
            const b = parseInt(color.slice(5, 7), 16);
            return `rgba(${r}, ${g}, ${b}, ${opacity})`;
        } else if (color.startsWith('rgb(')) {
            // RGB color - convert to rgba
            const values = color.match(/\d+/g);
            return `rgba(${values[0]}, ${values[1]}, ${values[2]}, ${opacity})`;
        } else if (color.startsWith('rgba(')) {
            // Already rgba - replace alpha
            return color.replace(/,\s*[\d.]+\)/, `, ${opacity})`);
        } else {
            // Named color - convert to rgba (basic mapping)
            const colorMap = {
                'red': 'rgba(255, 0, 0, ',
                'blue': 'rgba(0, 0, 255, ',
                'green': 'rgba(0, 128, 0, ',
                'orange': 'rgba(255, 165, 0, ',
                'purple': 'rgba(128, 0, 128, ',
                'brown': 'rgba(165, 42, 42, ',
                'pink': 'rgba(255, 192, 203, ',
                'gray': 'rgba(128, 128, 128, ',
                'black': 'rgba(0, 0, 0, '
            };
            const baseColor = colorMap[color.toLowerCase()] || 'rgba(0, 0, 0, ';
            return baseColor + opacity + ')';
        }
    }
    
    // === DELETE FUNCTIONS ===
    
    confirmDeleteMeasurement(measurementId) {
        const measurement = this.measurements.find(m => m.id === measurementId);
        if (!measurement) {
            alert('Measurement not found!');
            return;
        }
        
        // Store for deletion
        this.deleteTarget = { type: 'single', id: measurementId };
        
        // Set modal content
        document.getElementById('deleteMessage').textContent = 'Are you sure you want to delete this measurement?';
        document.getElementById('deleteDetails').innerHTML = `
            <strong>Measurement Details:</strong><br>
            ID: ${measurement.id}<br>
            Sample: ${measurement.sample_id}<br>
            Instrument: ${measurement.instrument_type}<br>
            Timestamp: ${new Date(measurement.timestamp).toLocaleString()}<br>
            Scan Rate: ${measurement.scan_rate || 'N/A'} mV/s
        `;
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
        modal.show();
    }
    
    confirmBatchDelete() {
        const selectedIds = this.getSelectedMeasurementIds();
        if (selectedIds.length === 0) {
            alert('Please select measurements to delete.');
            return;
        }
        
        // Store for deletion
        this.deleteTarget = { type: 'batch', ids: selectedIds };
        
        // Set modal content
        document.getElementById('deleteMessage').textContent = 
            `Are you sure you want to delete ${selectedIds.length} selected measurement(s)?`;
        
        const selectedMeasurements = this.measurements.filter(m => selectedIds.includes(m.id));
        const detailsHtml = selectedMeasurements.map(m => 
            `ID ${m.id}: ${m.sample_id} (${m.instrument_type}) - ${new Date(m.timestamp).toLocaleString()}`
        ).join('<br>');
        
        document.getElementById('deleteDetails').innerHTML = `
            <strong>Selected Measurements:</strong><br>
            ${detailsHtml}
        `;
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
        modal.show();
    }
    
    async executeDelete() {
        if (!this.deleteTarget) return;
        
        try {
            // Hide modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('deleteConfirmModal'));
            modal.hide();
            
            // Show loading
            this.showLoading(true);
            
            let response;
            if (this.deleteTarget.type === 'single') {
                // Single delete
                response = await fetch(`/api/parameters/measurements/${this.deleteTarget.id}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
            } else {
                // Batch delete
                response = await fetch('/api/parameters/measurements/batch-delete', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        measurement_ids: this.deleteTarget.ids
                    })
                });
            }
            
            const result = await response.json();
            
            if (result.success) {
                // Show success message
                const deletedCount = this.deleteTarget.type === 'single' ? 1 : result.deleted_count;
                alert(`Successfully deleted ${deletedCount} measurement(s)!`);
                
                // Clear selection and reload data
                this.clearSelection();
                await this.loadData();
            } else {
                alert(`Error: ${result.error || 'Delete operation failed'}`);
            }
            
        } catch (error) {
            console.error('Delete error:', error);
            alert('Error deleting measurement(s). Please try again.');
        } finally {
            this.showLoading(false);
            this.deleteTarget = null;
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.parameterDashboard = new ParameterDashboard();
});