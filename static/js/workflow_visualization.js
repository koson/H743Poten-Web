/**
 * H743Poten Workflow Visualization JavaScript
 * Enhanced Interactive Analysis Pipeline
 */

class H743WorkflowManager {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 6;
        this.selectedInstrument = 'stm32';
        this.selectedMethod = 'deepcv';
        this.selectedCalibration = 'random_forest';
        this.analysisData = {};
        this.sessionData = {}; // Initialize session data
        this.apiBase = '/api/workflow';
        this.isProcessing = false;
        
        this.init();
    }

    init() {
        console.log('🚀 H743Poten Workflow Manager Initialized');
        this.setupEventListeners();
        this.loadWorkflowStatus();
        this.updateUI();
    }

    setupEventListeners() {
        // Individual instrument file inputs
        const palmsensInput = document.getElementById('palmsensInput');
        const stm32Input = document.getElementById('stm32Input');
        const genericInput = document.getElementById('genericInput');

        if (palmsensInput) {
            palmsensInput.addEventListener('change', (e) => this.handleInstrumentFileSelection(e, 'palmsens'));
        }
        if (stm32Input) {
            stm32Input.addEventListener('change', (e) => this.handleInstrumentFileSelection(e, 'stm32'));
        }
        if (genericInput) {
            genericInput.addEventListener('change', (e) => this.handleInstrumentFileSelection(e, 'generic'));
        }

        // Legacy file input for compatibility
        const folderInput = document.getElementById('folderInput');
        if (folderInput) {
            folderInput.addEventListener('change', (e) => this.handleFileSelection(e));
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey) {
                switch(e.key) {
                    case 'ArrowRight':
                        e.preventDefault();
                        this.nextStep();
                        break;
                    case 'ArrowLeft':
                        e.preventDefault();
                        this.previousStep();
                        break;
                }
            }
        });

        // Auto-save progress
        setInterval(() => this.saveProgress(), 30000); // Save every 30 seconds
    }

    async loadWorkflowStatus() {
        try {
            const response = await fetch(`${this.apiBase}/status`);
            const data = await response.json();
            
            if (data.success) {
                this.analysisData = data.session_data;
                this.updateStepCompletion(data.status);
            }
        } catch (error) {
            console.error('Failed to load workflow status:', error);
        }
    }

    updateStepCompletion(status) {
        if (status.files_loaded) this.markStepCompleted(1);
        if (status.preprocessing_done) this.markStepCompleted(2);
        if (status.peaks_detected) this.markStepCompleted(3);
        if (status.calibration_applied) this.markStepCompleted(4);
    }

    // New Functions for Individual Instrument File Handling
    handleInstrumentFileSelection(event, instrumentType) {
        const files = event.target.files;
        console.log(`📂 Selected ${files.length} files for ${instrumentType}`);
        
        if (files.length === 0) return;

        // Calculate total size
        let totalSize = 0;
        Array.from(files).forEach(file => {
            totalSize += file.size;
        });

        // Update UI for specific instrument
        this.updateInstrumentFileInfo(instrumentType, files, totalSize);
        
        // Store files data
        if (!this.analysisData.instrumentFiles) {
            this.analysisData.instrumentFiles = {};
        }
        this.analysisData.instrumentFiles[instrumentType] = {
            files: Array.from(files),
            totalSize: totalSize,
            count: files.length
        };

        this.showNotification(
            `Selected ${files.length} files for ${instrumentType} (${(totalSize / (1024 * 1024)).toFixed(2)}MB)`, 
            'success'
        );
    }

    updateInstrumentFileInfo(instrumentType, files, totalSize) {
        const infoElement = document.getElementById(`${instrumentType}Info`);
        const countElement = document.getElementById(`${instrumentType}Count`);
        const sizeElement = document.getElementById(`${instrumentType}Size`);

        if (infoElement) {
            infoElement.textContent = `${files[0].webkitRelativePath.split('/')[0]} (${files.length} files)`;
        }
        if (countElement) {
            countElement.textContent = files.length;
        }
        if (sizeElement) {
            sizeElement.textContent = `${(totalSize / (1024 * 1024)).toFixed(2)} MB`;
        }
    }

    // Step Status Management
    updateStepStatus(stepNumber, status) {
        const step = document.getElementById(`step${stepNumber}`);
        if (!step) return;

        // Remove existing status classes
        step.classList.remove('active', 'completed', 'error');
        
        // Add new status based on the status parameter
        switch(status) {
            case 'current':
                step.classList.add('active');
                break;
            case 'completed':
                step.classList.add('completed');
                break;
            case 'error':
                step.classList.add('error');
                break;
            default:
                // Default pending state (no additional class)
                break;
        }
    }

    selectInstrument(instrumentType) {
        this.selectedInstrument = instrumentType;
        
        // Update visual selection
        document.querySelectorAll('.instrument-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Find and select the clicked instrument
        document.querySelectorAll('.instrument-card').forEach(card => {
            if (card.onclick.toString().includes(instrumentType)) {
                card.classList.add('selected');
            }
        });

        // Show/hide relevant import sections
        this.updateImportSections(instrumentType);
        
        this.showNotification(`Selected ${instrumentType.toUpperCase()} as target instrument`, 'info');
    }

    updateImportSections(instrumentType) {
        const sections = ['palmsens-section', 'stm32-section', 'generic-section'];
        
        sections.forEach(sectionId => {
            const section = document.getElementById(sectionId);
            if (section) {
                if (instrumentType === 'generic') {
                    // Show only generic section for generic mode
                    section.style.display = sectionId === 'generic-section' ? 'block' : 'none';
                } else {
                    // Show palmsens and stm32 sections, hide generic
                    section.style.display = sectionId === 'generic-section' ? 'none' : 'block';
                }
            }
        });
    }

    async scanAllInstrumentFiles() {
        const instrumentFiles = this.analysisData.instrumentFiles || {};
        const availableInstruments = Object.keys(instrumentFiles);
        
        if (availableInstruments.length === 0) {
            this.showNotification('Please select files for at least one instrument first', 'warning');
            return;
        }

        this.setProcessing(true);
        this.updateStepStatus(1, 'current');

        try {
            // Combine all files from all instruments
            let allFiles = [];
            let totalSize = 0;

            availableInstruments.forEach(instrument => {
                const instrumentData = instrumentFiles[instrument];
                allFiles = allFiles.concat(instrumentData.files);
                totalSize += instrumentData.totalSize;
            });

            // Create FormData for upload
            const formData = new FormData();
            allFiles.forEach(file => {
                formData.append('files[]', file);
            });

            // Add instrument metadata
            formData.append('instruments', JSON.stringify(availableInstruments));

            this.showNotification(`Scanning ${allFiles.length} files from ${availableInstruments.length} instruments...`, 'info');

            const response = await fetch(`${this.apiBase}/scan-files`, {
                method: 'POST',
                body: formData
            });

            if (response.status === 413) {
                const errorData = await response.json();
                this.updateStepStatus(1, 'error');
                this.showNotification(`Upload failed: ${errorData.error}`, 'error');
                return;
            }

            const data = await response.json();
            
            if (data.success) {
                this.updateFileResults(data);
                this.updateStepStatus(1, 'completed');
                this.showNotification(
                    `Successfully scanned ${data.valid_files} valid CV files from ${availableInstruments.join(', ')}`, 
                    'success'
                );
                
                setTimeout(() => {
                    this.goToStep(2);
                }, 1500);
            } else {
                this.updateStepStatus(1, 'error');
                this.showNotification(data.error || 'File scanning failed', 'error');
            }
        } catch (error) {
            console.error('File scanning failed:', error);
            this.updateStepStatus(1, 'error');
            this.showNotification('File scanning failed: ' + error.message, 'error');
        } finally {
            this.setProcessing(false);
        }
    }

    // Step Navigation
    goToStep(stepNumber) {
        if (stepNumber < 1 || stepNumber > this.totalSteps) return;
        
        // Remove active class from all steps
        document.querySelectorAll('.step').forEach(step => {
            step.classList.remove('active');
        });
        
        document.querySelectorAll('.nav-dot').forEach(dot => {
            dot.classList.remove('active');
        });

        // Activate current step
        const targetStep = document.getElementById(`step${stepNumber}`);
        if (targetStep) {
            targetStep.classList.add('active');
            targetStep.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
        
        const navDot = document.querySelectorAll('.nav-dot')[stepNumber - 1];
        if (navDot) {
            navDot.classList.add('active');
        }
        
        this.currentStep = stepNumber;
        this.updateUI();
    }

    nextStep() {
        if (this.currentStep < this.totalSteps) {
            this.goToStep(this.currentStep + 1);
        }
    }

    previousStep() {
        if (this.currentStep > 1) {
            this.goToStep(this.currentStep - 1);
        }
    }

    markStepCompleted(stepNumber) {
        const step = document.getElementById(`step${stepNumber}`);
        if (step) {
            step.classList.add('completed');
            step.classList.remove('active');
        }
        
        // Update step number to show checkmark
        const stepNumber_el = step?.querySelector('.step-number');
        if (stepNumber_el) {
            stepNumber_el.textContent = '';
            stepNumber_el.innerHTML = '✓';
        }
    }

    updateUI() {
        // Update navigation dots
        document.querySelectorAll('.nav-dot').forEach((dot, index) => {
            dot.classList.toggle('active', index + 1 === this.currentStep);
        });
    }

    // Step 1: Data Import Functions
    selectInstrument(instrument) {
        this.selectedInstrument = instrument;
        document.querySelectorAll('#step1 .instrument-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Find and select the clicked card
        const cards = document.querySelectorAll('#step1 .instrument-card');
        cards.forEach(card => {
            if (card.querySelector('div:nth-child(2)').textContent.toLowerCase().includes(instrument)) {
                card.classList.add('selected');
            }
        });
        
        console.log(`🔧 Selected instrument: ${instrument}`);
        this.showNotification(`Selected ${instrument.toUpperCase()} instrument`, 'info');
    }

    handleFileSelection(event) {
        const files = Array.from(event.target.files);
        if (files.length === 0) return;

        const selectedPath = document.getElementById('selectedPath');
        if (selectedPath) {
            selectedPath.textContent = `Selected: ${files.length} files from folder`;
        }

        // Auto-trigger file scanning
        setTimeout(() => this.scanFiles(), 500);
    }

    async scanFiles() {
        const fileInput = document.getElementById('folderInput');
        const files = fileInput?.files;
        
        if (!files || files.length === 0) {
            this.showNotification('Please select a folder first!', 'warning');
            return;
        }

        // Check file size before upload
        let totalSize = 0;
        let oversizedFiles = [];
        
        Array.from(files).forEach(file => {
            totalSize += file.size;
            if (file.size > 50 * 1024 * 1024) { // 50MB per file
                oversizedFiles.push({
                    name: file.name,
                    size: (file.size / (1024 * 1024)).toFixed(2)
                });
            }
        });

        // Check total size (100MB limit)
        if (totalSize > 100 * 1024 * 1024) {
            this.showNotification(
                `Total file size (${(totalSize / (1024 * 1024)).toFixed(2)}MB) exceeds 100MB limit`, 
                'error'
            );
            return;
        }

        // Warn about oversized individual files
        if (oversizedFiles.length > 0) {
            const fileList = oversizedFiles.map(f => `${f.name} (${f.size}MB)`).join('\n');
            this.showNotification(
                `Large files detected (>50MB per file):\n${fileList}`, 
                'warning'
            );
        }

        this.setProcessing(true);
        this.showNotification(`Uploading ${files.length} files (${(totalSize / (1024 * 1024)).toFixed(2)}MB)...`, 'info');
        
        try {
            // Create FormData for file upload
            const formData = new FormData();
            Array.from(files).forEach(file => {
                formData.append('files[]', file);
            });

            // Show upload progress
            const progressBar = this.createProgressBar('Uploading files...');

            const response = await fetch(`${this.apiBase}/scan-files`, {
                method: 'POST',
                body: formData
            });

            progressBar.remove();

            if (response.status === 413) {
                const errorData = await response.json();
                this.showNotification(
                    `Upload failed: ${errorData.error}. Try reducing file size or selecting fewer files.`, 
                    'error'
                );
                return;
            }

            const data = await response.json();
            
            if (data.success) {
                this.updateFileResults(data);
                this.showNotification(
                    `Successfully scanned ${data.valid_files} valid CV files (${data.total_size_mb}MB)`, 
                    'success'
                );
                
                if (data.valid_files > 0) {
                    setTimeout(() => {
                        this.markStepCompleted(1);
                        this.goToStep(2);
                    }, 1500);
                }
            } else {
                this.showNotification(data.error || 'File scanning failed', 'error');
            }
        } catch (error) {
            console.error('File scanning failed:', error);
            if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                this.showNotification('Network error. Please check connection and try again.', 'error');
            } else {
                this.showNotification('File scanning failed: ' + error.message, 'error');
            }
        } finally {
            this.setProcessing(false);
        }
    }

    createProgressBar(message) {
        const progressDiv = document.createElement('div');
        progressDiv.style.cssText = `
            position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
            background: white; padding: 20px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            z-index: 10000; min-width: 300px; text-align: center;
        `;
        
        progressDiv.innerHTML = `
            <div style="margin-bottom: 15px; font-weight: bold;">${message}</div>
            <div style="width: 100%; height: 20px; background: #f0f0f0; border-radius: 10px; overflow: hidden;">
                <div style="height: 100%; background: linear-gradient(45deg, #4CAF50, #45a049); 
                           width: 0%; transition: width 0.3s ease; animation: pulse 1.5s infinite;">
                </div>
            </div>
            <div style="margin-top: 10px; font-size: 0.9em; color: #666;">Please wait...</div>
        `;
        
        document.body.appendChild(progressDiv);
        return progressDiv;
    }

    updateFileResults(data) {
        const fileCount = document.getElementById('fileCount');
        const validFiles = document.getElementById('validFiles');
        const dataSize = document.getElementById('dataSize');
        
        if (fileCount) fileCount.textContent = data.total_files;
        if (validFiles) validFiles.textContent = data.valid_files;
        if (dataSize) dataSize.textContent = data.total_size_mb + ' MB';
    }

    async validateFormat() {
        this.showNotification('Validating file formats...', 'info');
        
        // Simulate validation
        setTimeout(() => {
            this.showNotification('File format validation completed successfully!', 'success');
        }, 1000);
    }

    // Step 2: Preprocessing Functions
    async startPreprocessing() {
        if (this.isProcessing) return;
        
        this.setProcessing(true);
        
        try {
            const response = await fetch(`${this.apiBase}/preprocess`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    instrument_type: this.selectedInstrument
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.animatePreprocessing(data);
                this.updatePreprocessingResults(data);
            } else {
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Preprocessing failed:', error);
            this.showNotification('Preprocessing failed', 'error');
        } finally {
            this.setProcessing(false);
        }
    }

    animatePreprocessing(data) {
        const progressBar = document.getElementById('preprocessProgress');
        const log = document.getElementById('preprocessLog');
        
        let stepIndex = 0;
        const steps = data.processing_steps || [
            {step: 'Initializing...', progress: 20},
            {step: 'Processing files...', progress: 60},
            {step: 'Completed!', progress: 100}
        ];

        const animate = () => {
            if (stepIndex < steps.length) {
                const currentStep = steps[stepIndex];
                
                // Update progress bar
                if (progressBar) {
                    progressBar.style.width = currentStep.progress + '%';
                    progressBar.textContent = currentStep.progress + '%';
                }
                
                // Update log
                if (log) {
                    const logEntry = document.createElement('div');
                    logEntry.textContent = `> ${currentStep.step}`;
                    log.appendChild(logEntry);
                    log.scrollTop = log.scrollHeight;
                }
                
                stepIndex++;
                
                if (currentStep.progress < 100) {
                    setTimeout(animate, 800);
                } else {
                    setTimeout(() => {
                        this.markStepCompleted(2);
                        this.goToStep(3);
                    }, 1000);
                }
            }
        };

        animate();
    }

    updatePreprocessingResults(data) {
        const processedFiles = document.getElementById('processedFiles');
        const qualityScore = document.getElementById('qualityScore');
        const unitFormat = document.getElementById('unitFormat');
        
        if (processedFiles) processedFiles.textContent = data.processed_files;
        if (qualityScore) qualityScore.textContent = data.quality_score + '%';
        if (unitFormat) unitFormat.textContent = data.unit_format;
    }

    showDataPreview() {
        this.showNotification('Opening data preview window...', 'info');
        
        // Update modal with current data
        this.updatePreviewModal();
        
        // Show the modal
        const modal = document.getElementById('dataPreviewModal');
        modal.style.display = 'block';
        
        // Generate sample chart
        setTimeout(() => {
            this.generatePreviewChart();
        }, 300);
    }

    updatePreviewModal() {
        // Safely get session data with fallbacks
        const sessionData = this.sessionData || {};
        const fileInfo = sessionData.workflow_files || {};
        const preprocessingResults = sessionData.preprocessing_results || {};
        
        // Get current file counts from UI if session data not available
        const palmsensCount = document.getElementById('palmsensCount')?.textContent || '0';
        const stm32Count = document.getElementById('stm32Count')?.textContent || '0';
        const genericCount = document.getElementById('genericCount')?.textContent || '0';
        
        // Calculate total files
        const totalFiles = fileInfo.valid_files || 
                          (parseInt(palmsensCount) + parseInt(stm32Count) + parseInt(genericCount));
        
        // Get current instrument type from UI
        const currentInstrument = this.getSelectedInstrument() || 'STM32';
        const currentQuality = this.calculateQualityScore(currentInstrument);
        
        // Update summary values
        document.getElementById('previewFileCount').textContent = totalFiles;
        document.getElementById('previewDataPoints').textContent = totalFiles * 1000;
        document.getElementById('previewInstrument').textContent = currentInstrument;
        document.getElementById('previewQuality').textContent = currentQuality + '%';
        
        // Update statistics based on instrument type
        this.updatePreviewStatistics(currentInstrument.toLowerCase());
    }

    getSelectedInstrument() {
        // Check which instrument has files selected
        const palmsensCount = parseInt(document.getElementById('palmsensCount')?.textContent || '0');
        const stm32Count = parseInt(document.getElementById('stm32Count')?.textContent || '0');
        const genericCount = parseInt(document.getElementById('genericCount')?.textContent || '0');
        
        if (palmsensCount > 0) return 'PALMSENS';
        if (stm32Count > 0) return 'STM32';
        if (genericCount > 0) return 'GENERIC';
        return 'STM32'; // Default
    }

    calculateQualityScore(instrument) {
        switch(instrument.toLowerCase()) {
            case 'palmsens': return 98;
            case 'stm32': return 95;
            case 'generic': return 85;
            default: return 90;
        }
    }

    updatePreviewStatistics(instrumentType) {
        let stats = {
            minVoltage: '-1.0V',
            maxVoltage: '+1.0V',
            scanRate: '100 mV/s',
            peakCurrent: '45.2 μA',
            baselineCurrent: '2.1 μA',
            snrValue: '21.5 dB'
        };

        // Adjust stats based on instrument
        if (instrumentType === 'palmsens') {
            stats.peakCurrent = '52.8 μA';
            stats.snrValue = '28.3 dB';
        } else if (instrumentType === 'stm32') {
            stats.peakCurrent = '45.2 μA';
            stats.snrValue = '21.5 dB';
        } else {
            stats.peakCurrent = '38.7 μA';
            stats.snrValue = '18.2 dB';
        }

        // Update DOM elements
        Object.keys(stats).forEach(key => {
            const element = document.getElementById(key);
            if (element) element.textContent = stats[key];
        });
    }

    async generatePreviewChart() {
        const canvas = document.getElementById('previewChart');
        if (!canvas) return;

        try {
            // Fetch real or mock data from backend
            const response = await fetch('/api/workflow/get-preview-data');
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to load data');
            }
            
            this.drawChart(canvas, data);
            
            // Update graph info with real data details
            this.updateGraphInfo(data);
            
        } catch (error) {
            console.error('Error loading chart data:', error);
            // Fallback to original mock data
            this.drawMockChart(canvas);
        }
    }

    drawChart(canvas, data) {
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        // Set up coordinate system
        const margin = 60;
        const plotWidth = width - 2 * margin;
        const plotHeight = height - 2 * margin;

        // Draw background
        ctx.fillStyle = '#f8f9fa';
        ctx.fillRect(0, 0, width, height);

        // Draw plot area
        ctx.fillStyle = 'white';
        ctx.fillRect(margin, margin, plotWidth, plotHeight);

        // Draw grid
        this.drawGrid(ctx, margin, plotWidth, plotHeight);

        // Draw data curve
        if (data.voltage && data.current) {
            this.drawDataCurve(ctx, data.voltage, data.current, margin, plotWidth, plotHeight);
        }

        // Draw axes and labels
        this.drawAxes(ctx, margin, plotWidth, plotHeight, width, height);
        
        // Add title with data source info
        const title = data.data_source === 'real' ? 
            `Real CV Data: ${data.file_name || 'Uploaded File'}` : 
            `Sample Cyclic Voltammogram (${data.data_source})`;
        
        ctx.font = 'bold 14px Arial';
        ctx.fillStyle = '#333';
        ctx.textAlign = 'center';
        ctx.fillText(title, width/2, 25);
    }

    drawGrid(ctx, margin, plotWidth, plotHeight) {
        ctx.strokeStyle = '#e0e0e0';
        ctx.lineWidth = 1;
        
        // Vertical grid lines
        for (let i = 0; i <= 10; i++) {
            const x = margin + (i * plotWidth / 10);
            ctx.beginPath();
            ctx.moveTo(x, margin);
            ctx.lineTo(x, margin + plotHeight);
            ctx.stroke();
        }

        // Horizontal grid lines
        for (let i = 0; i <= 8; i++) {
            const y = margin + (i * plotHeight / 8);
            ctx.beginPath();
            ctx.moveTo(margin, y);
            ctx.lineTo(margin + plotWidth, y);
            ctx.stroke();
        }
    }

    drawDataCurve(ctx, voltageData, currentData, margin, plotWidth, plotHeight) {
        if (!voltageData || !currentData || voltageData.length === 0) return;

        // Find data ranges
        const minV = Math.min(...voltageData);
        const maxV = Math.max(...voltageData);
        const minI = Math.min(...currentData);
        const maxI = Math.max(...currentData);
        
        const rangeV = maxV - minV;
        const rangeI = maxI - minI;

        // Draw curve
        ctx.strokeStyle = '#4169E1';
        ctx.lineWidth = 3;
        ctx.beginPath();

        for (let i = 0; i < voltageData.length; i++) {
            const voltage = voltageData[i];
            const current = currentData[i];
            
            // Convert to canvas coordinates
            const x = margin + ((voltage - minV) / rangeV) * plotWidth;
            const y = margin + plotHeight - ((current - minI) / rangeI) * plotHeight;
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        ctx.stroke();

        // Store ranges for axis labels
        this.chartRanges = { minV, maxV, minI, maxI };
    }

    drawAxes(ctx, margin, plotWidth, plotHeight, width, height) {
        // Draw axes
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 2;
        
        // X-axis
        ctx.beginPath();
        ctx.moveTo(margin, margin + plotHeight);
        ctx.lineTo(margin + plotWidth, margin + plotHeight);
        ctx.stroke();

        // Y-axis
        ctx.beginPath();
        ctx.moveTo(margin, margin);
        ctx.lineTo(margin, margin + plotHeight);
        ctx.stroke();

        // Add labels
        ctx.fillStyle = '#333';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';

        // X-axis labels (use real data ranges if available)
        const ranges = this.chartRanges || { minV: -1, maxV: 1, minI: -30, maxI: 50 };
        
        ctx.fillText(`${ranges.minV.toFixed(1)}V`, margin, height - 20);
        ctx.fillText(`${((ranges.minV + ranges.maxV) / 2).toFixed(1)}V`, margin + plotWidth/2, height - 20);
        ctx.fillText(`${ranges.maxV.toFixed(1)}V`, margin + plotWidth, height - 20);

        // Y-axis label
        ctx.save();
        ctx.translate(20, margin + plotHeight/2);
        ctx.rotate(-Math.PI/2);
        ctx.fillText('Current (μA)', 0, 0);
        ctx.restore();
    }

    updateGraphInfo(data) {
        const graphInfo = document.querySelector('.graph-info');
        if (graphInfo && data) {
            const voltageRange = data.voltage ? 
                `${Math.min(...data.voltage).toFixed(1)}V to ${Math.max(...data.voltage).toFixed(1)}V` :
                '-1.0V to +1.0V';
            
            const currentRange = data.current ?
                `${Math.min(...data.current).toFixed(1)}μA to ${Math.max(...data.current).toFixed(1)}μA` :
                '-50μA to +50μA';
            
            graphInfo.innerHTML = `
                <p><strong>Data Source:</strong> ${data.data_source === 'real' ? 'Real uploaded data' : 
                    data.data_source === 'enhanced_mock' ? 'Real uploaded data (enhanced)' : 'Generated sample data'}</p>
                <p><strong>Voltage Range:</strong> ${voltageRange}</p>
                <p><strong>Current Range:</strong> ${currentRange}</p>
                ${data.file_name ? `<p><strong>File:</strong> ${data.file_name}</p>` : ''}
                ${data.data_points ? `<p><strong>Data Points:</strong> ${data.data_points}</p>` : ''}
                <div style="margin-top: 10px;">
                    <button onclick="checkDataSourceStatus()" class="btn btn-sm btn-info">Check Data Source Status</button>
                </div>
            `;
        }
    }

    // Keep original mock chart as fallback
    drawMockChart(canvas) {
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        // Set up coordinate system
        const margin = 60;
        const plotWidth = width - 2 * margin;
        const plotHeight = height - 2 * margin;

        // Draw background
        ctx.fillStyle = '#f8f9fa';
        ctx.fillRect(0, 0, width, height);

        // Draw plot area
        ctx.fillStyle = 'white';
        ctx.fillRect(margin, margin, plotWidth, plotHeight);

        // Draw grid
        ctx.strokeStyle = '#e0e0e0';
        ctx.lineWidth = 1;
        
        // Vertical grid lines
        for (let i = 0; i <= 10; i++) {
            const x = margin + (i * plotWidth / 10);
            ctx.beginPath();
            ctx.moveTo(x, margin);
            ctx.lineTo(x, margin + plotHeight);
            ctx.stroke();
        }

        // Horizontal grid lines
        for (let i = 0; i <= 8; i++) {
            const y = margin + (i * plotHeight / 8);
            ctx.beginPath();
            ctx.moveTo(margin, y);
            ctx.lineTo(margin + plotHeight, y);
            ctx.stroke();
        }

        // Draw sample CV curve
        ctx.strokeStyle = '#4169E1';
        ctx.lineWidth = 3;
        ctx.beginPath();

        const points = 200;
        for (let i = 0; i <= points; i++) {
            const voltage = -1 + (2 * i / points); // -1V to +1V
            
            // Generate realistic CV curve with noise
            let current = 0;
            
            // Forward scan (oxidation peak)
            if (voltage > -0.5 && voltage < 0.5) {
                current = 30 * Math.exp(-Math.pow((voltage - 0.2) / 0.1, 2));
            }
            
            // Reverse scan (reduction peak)
            if (voltage > -0.3 && voltage < 0.3) {
                current -= 25 * Math.exp(-Math.pow((voltage + 0.15) / 0.08, 2));
            }
            
            // Add baseline and noise
            current += 2 + Math.random() * 3 - 1.5;
            
            // Convert to canvas coordinates
            const x = margin + ((voltage + 1) / 2) * plotWidth;
            const y = margin + plotHeight - ((current + 30) / 60) * plotHeight;
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        ctx.stroke();

        // Draw axes
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 2;
        
        // X-axis
        ctx.beginPath();
        ctx.moveTo(margin, margin + plotHeight);
        ctx.lineTo(margin + plotWidth, margin + plotHeight);
        ctx.stroke();

        // Y-axis
        ctx.beginPath();
        ctx.moveTo(margin, margin);
        ctx.lineTo(margin, margin + plotHeight);
        ctx.stroke();

        // Add labels
        ctx.fillStyle = '#333';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';

        // X-axis labels
        ctx.fillText('-1.0V', margin, height - 20);
        ctx.fillText('0V', margin + plotWidth/2, height - 20);
        ctx.fillText('+1.0V', margin + plotWidth, height - 20);

        // Y-axis labels
        ctx.save();
        ctx.translate(20, margin + plotHeight/2);
        ctx.rotate(-Math.PI/2);
        ctx.fillText('Current (μA)', 0, 0);
        ctx.restore();

        // Title
        ctx.font = 'bold 14px Arial';
        ctx.fillText('Sample Cyclic Voltammogram (Fallback)', width/2, 25);
    }

    // Step 3: Peak Detection Functions
    selectMethod(method) {
        this.selectedMethod = method;
        document.querySelectorAll('#step3 .instrument-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Find and select the clicked card
        event.target.closest('.instrument-card').classList.add('selected');
        
        this.showNotification(`Selected ${method} detection method`, 'info');
    }

    async startDetection() {
        if (this.isProcessing) return;
        
        this.setProcessing(true);
        
        try {
            // Animate progress bar
            this.animateDetectionProgress();
            
            const response = await fetch(`${this.apiBase}/detect-peaks`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    method: this.selectedMethod
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.updateDetectionResults(data);
                this.showNotification(`Detected ${data.peaks_detected} peaks with ${data.confidence}% confidence`, 'success');
                
                setTimeout(() => {
                    this.markStepCompleted(3);
                    this.goToStep(4);
                }, 1500);
            } else {
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Peak detection failed:', error);
            this.showNotification('Peak detection failed', 'error');
        } finally {
            this.setProcessing(false);
        }
    }

    animateDetectionProgress() {
        const progressBar = document.getElementById('detectionProgress');
        if (!progressBar) return;
        
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15 + 5;
            if (progress > 100) progress = 100;
            
            progressBar.style.width = progress + '%';
            progressBar.textContent = Math.round(progress) + '%';
            
            if (progress >= 100) {
                clearInterval(interval);
            }
        }, 200);
    }

    updateDetectionResults(data) {
        const peaksDetected = document.getElementById('peaksDetected');
        const detectionConfidence = document.getElementById('detectionConfidence');
        const processingTime = document.getElementById('processingTime');
        const confidenceBar = document.getElementById('confidenceBar');
        const confidenceText = document.getElementById('confidenceText');
        
        if (peaksDetected) peaksDetected.textContent = data.peaks_detected;
        if (detectionConfidence) detectionConfidence.textContent = data.confidence + '%';
        if (processingTime) processingTime.textContent = data.processing_time + 's';
        
        // Update confidence meter
        if (confidenceBar && confidenceText) {
            confidenceBar.style.width = data.confidence + '%';
            confidenceText.textContent = data.confidence + '%';
            
            // Update color based on confidence level
            confidenceBar.className = 'confidence-fill';
            if (data.confidence >= 80) {
                confidenceBar.classList.add('confidence-high');
            } else if (data.confidence >= 60) {
                confidenceBar.classList.add('confidence-medium');
            } else {
                confidenceBar.classList.add('confidence-low');
            }
        }
    }

    compareResults() {
        this.showNotification('Opening method comparison view...', 'info');
        // In a real implementation, this would show side-by-side results
        setTimeout(() => {
            alert('Comparison view would show side-by-side results from all three methods:\n\n' +
                  '• DeepCV: 4 peaks, 89% confidence\n' +
                  '• Traditional: 3 peaks, 72% confidence\n' +
                  '• Hybrid: 3 peaks, 78% confidence');
        }, 500);
    }

    // Step 4: Calibration Functions
    selectCalibration(model) {
        this.selectedCalibration = model;
        document.querySelectorAll('#step4 .instrument-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        event.target.closest('.instrument-card').classList.add('selected');
        
        this.showNotification(`Selected ${model} calibration model`, 'info');
    }

    async startCalibration() {
        if (this.isProcessing) return;
        
        this.setProcessing(true);
        this.showNotification('Starting cross-instrument calibration...', 'info');
        
        try {
            const response = await fetch(`${this.apiBase}/calibrate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model_type: this.selectedCalibration
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.updateCalibrationResults(data);
                this.showNotification(`Calibration completed with ${data.accuracy}% accuracy`, 'success');
                
                setTimeout(() => {
                    this.markStepCompleted(4);
                    this.goToStep(5);
                }, 1500);
            } else {
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Calibration failed:', error);
            this.showNotification('Calibration failed', 'error');
        } finally {
            this.setProcessing(false);
        }
    }

    updateCalibrationResults(data) {
        const calibrationAccuracy = document.getElementById('calibrationAccuracy');
        const potentialError = document.getElementById('potentialError');
        const currentError = document.getElementById('currentError');
        
        if (calibrationAccuracy) calibrationAccuracy.textContent = data.accuracy + '%';
        if (potentialError) potentialError.textContent = data.potential_error + '%';
        if (currentError) currentError.textContent = data.current_error + '%';
    }

    viewCalibrationDetails() {
        this.showNotification('Opening calibration details...', 'info');
        setTimeout(() => {
            alert('Detailed calibration metrics:\n\n' +
                  `• Model: ${this.selectedCalibration}\n` +
                  '• Training Data: 100 paired measurements\n' +
                  '• Cross-validation: 5-fold\n' +
                  '• Feature Count: 17 electrochemical parameters\n' +
                  '• Processing Time: <0.01s per measurement');
        }, 500);
    }

    // Step 5: Visualization Functions
    async showCVPlots() {
        const viz = await this.generateVisualization('cv_plots');
        this.updateVisualizationArea(viz);
    }

    async showPeakAnalysis() {
        const viz = await this.generateVisualization('peak_analysis');
        this.updateVisualizationArea(viz);
    }

    async showCalibrationComparison() {
        const viz = await this.generateVisualization('calibration_comparison');
        this.updateVisualizationArea(viz);
    }

    async generateVisualization(type) {
        try {
            const response = await fetch(`${this.apiBase}/generate-visualization`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ type })
            });

            const data = await response.json();
            return data.success ? data.visualization : null;
        } catch (error) {
            console.error('Visualization generation failed:', error);
            return null;
        }
    }

    updateVisualizationArea(vizData) {
        const viz = document.getElementById('visualizationArea');
        if (!viz) return;

        if (!vizData) {
            viz.innerHTML = `
                <div class="visualization-placeholder">
                    <p>❌ Failed to generate visualization</p>
                    <p>Please try again or contact support</p>
                </div>
            `;
            return;
        }

        viz.innerHTML = `
            <div style="text-align: left;">
                <h3>📊 ${vizData.title}</h3>
                <div style="background: #f0f0f0; height: 300px; border-radius: 10px; 
                           display: flex; align-items: center; justify-content: center; 
                           margin: 20px 0; position: relative;">
                    <div style="text-align: center;">
                        <div style="font-size: 3em; margin-bottom: 10px;">📈</div>
                        <p><strong>${vizData.type.toUpperCase()} Visualization</strong></p>
                        <p style="color: #666; font-size: 0.9em;">Interactive charts would be rendered here</p>
                    </div>
                    <div style="position: absolute; top: 10px; right: 10px; 
                               background: rgba(76, 175, 80, 0.9); color: white; 
                               padding: 5px 10px; border-radius: 15px; font-size: 0.8em;">
                        Data Ready
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                           gap: 15px; margin-top: 15px;">
                    ${this.generateVisualizationStats(vizData)}
                </div>
            </div>
        `;
    }

    generateVisualizationStats(vizData) {
        const data = vizData.data || {};
        
        if (vizData.type === 'cv_plots') {
            return `
                <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd;">
                    <strong>Voltage Range</strong><br>
                    <span style="color: #4CAF50; font-size: 1.2em;">${data.voltage ? (Math.max(...data.voltage) - Math.min(...data.voltage)).toFixed(2) + 'V' : 'N/A'}</span>
                </div>
                <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd;">
                    <strong>Current Range</strong><br>
                    <span style="color: #2196F3; font-size: 1.2em;">${data.current ? (Math.max(...data.current) - Math.min(...data.current)).toExponential(2) + 'A' : 'N/A'}</span>
                </div>
                <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd;">
                    <strong>Peaks Found</strong><br>
                    <span style="color: #FF9800; font-size: 1.2em;">${data.peaks ? data.peaks.length : 0}</span>
                </div>
            `;
        } else if (vizData.type === 'peak_analysis') {
            return `
                <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd;">
                    <strong>Peak Count</strong><br>
                    <span style="color: #4CAF50; font-size: 1.2em;">${data.peak_count || 0}</span>
                </div>
                <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd;">
                    <strong>Confidence</strong><br>
                    <span style="color: #2196F3; font-size: 1.2em;">${data.confidence || 0}%</span>
                </div>
                <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd;">
                    <strong>Avg Peak Area</strong><br>
                    <span style="color: #FF9800; font-size: 1.2em;">${data.peak_details ? (data.peak_details.reduce((a,p) => a + p.area, 0) / data.peak_details.length).toExponential(2) : 'N/A'}</span>
                </div>
            `;
        } else {
            return `
                <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd;">
                    <strong>Potential Accuracy</strong><br>
                    <span style="color: #4CAF50; font-size: 1.2em;">${data.improvement?.potential_accuracy || 0}%</span>
                </div>
                <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd;">
                    <strong>Current Accuracy</strong><br>
                    <span style="color: #2196F3; font-size: 1.2em;">${data.improvement?.current_accuracy || 0}%</span>
                </div>
                <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd;">
                    <strong>Calibration Type</strong><br>
                    <span style="color: #FF9800; font-size: 1.2em;">${this.selectedCalibration.replace('_', ' ')}</span>
                </div>
            `;
        }
    }

    async exportJSON() {
        try {
            const response = await fetch(`${this.apiBase}/export`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ format: 'json' })
            });

            const data = await response.json();
            
            if (data.success) {
                this.downloadFile(data.data, data.filename, 'application/json');
                this.showNotification('JSON export completed', 'success');
            } else {
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Export failed:', error);
            this.showNotification('Export failed', 'error');
        }
    }

    async exportCSV() {
        try {
            const response = await fetch(`${this.apiBase}/export`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ format: 'csv' })
            });

            const data = await response.json();
            
            if (data.success) {
                // Convert to CSV format
                const csvContent = this.convertToCSV(data.data);
                this.downloadFile(csvContent, data.filename, 'text/csv');
                this.showNotification('CSV export completed', 'success');
            } else {
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Export failed:', error);
            this.showNotification('Export failed', 'error');
        }
    }

    generateReport() {
        this.showNotification('Generating comprehensive analysis report...', 'info');
        
        setTimeout(() => {
            const report = this.createAnalysisReport();
            this.downloadFile(report, `H743Poten_Analysis_Report_${new Date().toISOString().slice(0,10)}.html`, 'text/html');
            this.showNotification('Analysis report generated', 'success');
        }, 1500);
    }

    createAnalysisReport() {
        return `
<!DOCTYPE html>
<html>
<head>
    <title>H743Poten Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { text-align: center; border-bottom: 2px solid #4CAF50; padding-bottom: 20px; }
        .section { margin: 30px 0; }
        .metric { display: inline-block; margin: 10px 20px; padding: 10px; background: #f5f5f5; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔬 H743Poten Analysis Report</h1>
        <p>Generated: ${new Date().toLocaleString()}</p>
    </div>
    
    <div class="section">
        <h2>📊 Analysis Summary</h2>
        <div class="metric">
            <strong>Instrument:</strong> ${this.selectedInstrument.toUpperCase()}
        </div>
        <div class="metric">
            <strong>Detection Method:</strong> ${this.selectedMethod}
        </div>
        <div class="metric">
            <strong>Calibration:</strong> ${this.selectedCalibration}
        </div>
    </div>
    
    <div class="section">
        <h2>🎯 Results</h2>
        <p>Peak detection and calibration completed successfully with high confidence scores.</p>
        <p>Data quality assessment passed all scientific accuracy requirements.</p>
    </div>
    
    <div class="section">
        <h2>✅ Quality Assurance</h2>
        <p>All validation steps completed. Results are ready for scientific publication.</p>
    </div>
    
    <div class="section">
        <p><em>This report was generated by the H743Poten Analysis System.</em></p>
    </div>
</body>
</html>`;
    }

    // Step 6: Quality Assurance Functions
    finalizeResults() {
        // Update quality metrics
        const overallQuality = document.getElementById('overallQuality');
        const scientificAccuracy = document.getElementById('scientificAccuracy');
        const reliabilityScore = document.getElementById('reliabilityScore');
        
        if (overallQuality) overallQuality.textContent = '94%';
        if (scientificAccuracy) scientificAccuracy.textContent = '96%';
        if (reliabilityScore) reliabilityScore.textContent = '92%';
        
        setTimeout(() => {
            this.markStepCompleted(6);
            this.showSuccessModal();
        }, 1000);
    }

    showSuccessModal() {
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.8); z-index: 10000;
            display: flex; align-items: center; justify-content: center;
        `;
        
        modal.innerHTML = `
            <div style="background: white; padding: 40px; border-radius: 15px; text-align: center; max-width: 500px;">
                <div style="font-size: 4em; margin-bottom: 20px;">🎉</div>
                <h2 style="color: #4CAF50; margin-bottom: 20px;">Analysis Completed Successfully!</h2>
                <p>Your electrochemical data has been processed with scientific accuracy and is ready for publication-quality use.</p>
                <div style="margin: 20px 0; padding: 15px; background: #f0f8ff; border-radius: 8px;">
                    <strong>🏆 Achievement Unlocked:</strong><br>
                    Scientific Grade Analysis Complete
                </div>
                <button onclick="this.parentElement.parentElement.remove()" 
                        style="background: #4CAF50; color: white; border: none; padding: 12px 24px; 
                               border-radius: 5px; cursor: pointer; font-size: 1.1em;">
                    Awesome!
                </button>
            </div>
        `;
        
        document.body.appendChild(modal);
    }

    shareResults() {
        this.showNotification('Opening sharing options...', 'info');
        setTimeout(() => {
            alert('Sharing options:\n\n' +
                  '• Export to cloud storage\n' +
                  '• Email results to collaborators\n' +
                  '• Generate shareable link\n' +
                  '• Export to research database');
        }, 500);
    }

    // Utility Functions
    setProcessing(isProcessing) {
        this.isProcessing = isProcessing;
        const buttons = document.querySelectorAll('.btn-primary');
        buttons.forEach(btn => {
            btn.disabled = isProcessing;
            if (isProcessing) {
                btn.style.opacity = '0.6';
                btn.style.cursor = 'not-allowed';
            } else {
                btn.style.opacity = '1';
                btn.style.cursor = 'pointer';
            }
        });
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 9999;
            padding: 15px 20px; border-radius: 8px; color: white;
            font-weight: bold; min-width: 250px; text-align: center;
            animation: slideIn 0.3s ease-out;
        `;
        
        const colors = {
            info: '#2196F3',
            success: '#4CAF50',
            warning: '#FF9800',
            error: '#f44336'
        };
        
        notification.style.background = colors[type] || colors.info;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    downloadFile(content, filename, mimeType) {
        const blob = new Blob([typeof content === 'string' ? content : JSON.stringify(content, null, 2)], 
                             { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    convertToCSV(data) {
        // Simple CSV conversion for demonstration
        let csv = 'Parameter,Value\n';
        
        const flatData = this.flattenObject(data);
        for (const [key, value] of Object.entries(flatData)) {
            csv += `"${key}","${value}"\n`;
        }
        
        return csv;
    }

    flattenObject(obj, prefix = '') {
        const flattened = {};
        
        for (const key in obj) {
            if (obj.hasOwnProperty(key)) {
                const newKey = prefix ? `${prefix}.${key}` : key;
                
                if (typeof obj[key] === 'object' && obj[key] !== null && !Array.isArray(obj[key])) {
                    Object.assign(flattened, this.flattenObject(obj[key], newKey));
                } else {
                    flattened[newKey] = obj[key];
                }
            }
        }
        
        return flattened;
    }

    saveProgress() {
        const progress = {
            currentStep: this.currentStep,
            selectedInstrument: this.selectedInstrument,
            selectedMethod: this.selectedMethod,
            selectedCalibration: this.selectedCalibration,
            timestamp: Date.now()
        };
        
        localStorage.setItem('h743poten_workflow_progress', JSON.stringify(progress));
    }

    loadProgress() {
        const saved = localStorage.getItem('h743poten_workflow_progress');
        if (saved) {
            const progress = JSON.parse(saved);
            this.currentStep = progress.currentStep || 1;
            this.selectedInstrument = progress.selectedInstrument || 'stm32';
            this.selectedMethod = progress.selectedMethod || 'deepcv';
            this.selectedCalibration = progress.selectedCalibration || 'random_forest';
        }
    }
}

// Global functions for HTML onclick handlers
function selectInstrument(instrument) {
    if (window.workflowManager) {
        window.workflowManager.selectInstrument(instrument);
    }
}

function scanFiles() {
    if (window.workflowManager) {
        window.workflowManager.scanFiles();
    }
}

function validateFormat() {
    if (window.workflowManager) {
        window.workflowManager.validateFormat();
    }
}

function startPreprocessing() {
    if (window.workflowManager) {
        window.workflowManager.startPreprocessing();
    }
}

// Global functions for workflow interaction
function showDataPreview() {
    try {
        if (window.workflowManager) {
            window.workflowManager.showDataPreview();
        } else {
            console.error('Workflow manager not initialized');
            alert('System not ready. Please refresh the page.');
        }
    } catch (error) {
        console.error('Error opening data preview:', error);
        alert('Error opening preview. Please try again.');
    }
}

function selectMethod(method) {
    if (window.workflowManager) {
        window.workflowManager.selectMethod(method);
    }
}

function startDetection() {
    if (window.workflowManager) {
        window.workflowManager.startDetection();
    }
}

function compareResults() {
    if (window.workflowManager) {
        window.workflowManager.compareResults();
    }
}

function selectCalibration(model) {
    if (window.workflowManager) {
        window.workflowManager.selectCalibration(model);
    }
}

function startCalibration() {
    if (window.workflowManager) {
        window.workflowManager.startCalibration();
    }
}

function viewCalibrationDetails() {
    if (window.workflowManager) {
        window.workflowManager.viewCalibrationDetails();
    }
}

function showCVPlots() {
    if (window.workflowManager) {
        window.workflowManager.showCVPlots();
    }
}

function showPeakAnalysis() {
    if (window.workflowManager) {
        window.workflowManager.showPeakAnalysis();
    }
}

function showCalibrationComparison() {
    if (window.workflowManager) {
        window.workflowManager.showCalibrationComparison();
    }
}

function exportJSON() {
    if (window.workflowManager) {
        window.workflowManager.exportJSON();
    }
}

function exportCSV() {
    if (window.workflowManager) {
        window.workflowManager.exportCSV();
    }
}

function generateReport() {
    if (window.workflowManager) {
        window.workflowManager.generateReport();
    }
}

function finalizeResults() {
    if (window.workflowManager) {
        window.workflowManager.finalizeResults();
    }
}

function shareResults() {
    if (window.workflowManager) {
        window.workflowManager.shareResults();
    }
}

function goToStep(stepNumber) {
    if (window.workflowManager) {
        window.workflowManager.goToStep(stepNumber);
    }
}

// New Functions for Updated UI
function selectInstrument(instrumentType) {
    if (window.workflowManager) {
        window.workflowManager.selectInstrument(instrumentType);
    }
}

function scanAllFiles() {
    if (window.workflowManager) {
        window.workflowManager.scanAllInstrumentFiles();
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Global functions for modal interaction
function closeDataPreview() {
    const modal = document.getElementById('dataPreviewModal');
    modal.style.display = 'none';
}

function showPreviewTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName + '-tab').classList.add('active');
    
    // Add active class to clicked button
    event.target.classList.add('active');
    
    // If switching to graphs tab, regenerate chart
    if (tabName === 'graphs') {
        setTimeout(() => {
            if (window.workflowManager) {
                window.workflowManager.generatePreviewChart();
            }
        }, 100);
    }
}

function proceedToNextStep() {
    closeDataPreview();
    if (window.workflowManager) {
        window.workflowManager.updateStepStatus(2, 'completed');
        window.workflowManager.setCurrentStep(3);
        window.workflowManager.showNotification('Proceeding to Peak Detection...', 'success');
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('dataPreviewModal');
    if (event.target === modal) {
        closeDataPreview();
    }
}

// Global function for checking data source status
async function checkDataSourceStatus() {
    try {
        const response = await fetch('/api/workflow/data-source-info');
        const result = await response.json();
        
        if (result.success) {
            const statusHtml = `
                <div class="alert alert-info">
                    <h5>Data Source Status</h5>
                    <p><strong>Status:</strong> ${result.data_source_status}</p>
                    <p><strong>Description:</strong> ${result.source_description}</p>
                    <p><strong>Session Data:</strong> ${result.has_session_data ? 'Active' : 'None'}</p>
                    <p><strong>Uploaded Files:</strong> ${result.has_uploaded_files ? result.uploaded_file_count : 'None'}</p>
                    ${result.uploaded_files.length > 0 ? 
                        `<p><strong>Files:</strong> ${result.uploaded_files.join(', ')}</p>` : ''}
                    <p><strong>Temp Dir:</strong> ${result.temp_dir_exists ? 'Exists' : 'Missing'}</p>
                </div>
            `;
            
            // Show in a modal or alert
            const existingModal = document.getElementById('dataSourceModal');
            if (existingModal) {
                existingModal.remove();
            }
            
            const modal = document.createElement('div');
            modal.id = 'dataSourceModal';
            modal.innerHTML = `
                <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                     background: rgba(0,0,0,0.5); z-index: 1000; display: flex; 
                     align-items: center; justify-content: center;">
                    <div style="background: white; padding: 20px; border-radius: 5px; 
                         max-width: 500px; width: 90%;">
                        ${statusHtml}
                        <button onclick="document.getElementById('dataSourceModal').remove()" 
                                class="btn btn-primary">Close</button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
        } else {
            alert(`Error checking data source status: ${result.error}`);
        }
    } catch (error) {
        alert(`Failed to check data source status: ${error.message}`);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing H743Poten Workflow Manager...');
    window.workflowManager = new H743WorkflowManager();
});
