/**
 * Peak Detection Visualization System
 * Interactive CV plot with peak detection visualization
 */

class PeakVisualizationManager {
    constructor() {
        this.plotData = {
            voltage: [],
            current: [],
            peaks: []  // Will store peak information: {voltage, current, type, confidence}
        };
        
        // Canvas and plot settings
        this.canvas = null;
        this.ctx = null;
        this.margin = 60;
        this.plotWidth = 0;
        this.plotHeight = 0;
        
        // Interaction state
        this.hoveredPeak = null;
        this.selectedPeak = null;
        this.isDragging = false;
        this.showGrid = true; // Grid visibility state
        this.originalScale = { // Store original scale for reset
            voltage: null,
            current: null
        };
        
        // Analysis results for each method
        this.analysisResults = {
            ml: { started: false, completed: false },
            prominence: { started: false, completed: false },
            derivative: { started: false, completed: false }
        };
        
        this.methodMappings = {
            'ml': { gridId: 'ml-analysis', name: 'DeepCV' },
            'prominence': { gridId: 'traditional-analysis', name: 'TraditionalCV' },
            'derivative': { gridId: 'hybrid-analysis', name: 'HybridCV' }
        };
        
        this.init();
    }

    init() {
        console.log('🚀 Peak Visualization Manager Initialized');
        this.setupCanvas();
        this.setupEventListeners();
        this.loadInitialData();
    }

    setupCanvas() {
        console.log('Setting up canvas...');
        this.canvas = document.getElementById('peakVisualizationChart');
        if (!this.canvas) {
            console.error('Canvas element not found');
            return;
        }
        console.log('Canvas found, dimensions:', {
            width: this.canvas.width,
            height: this.canvas.height,
            clientWidth: this.canvas.clientWidth,
            clientHeight: this.canvas.clientHeight
        });
        
        this.ctx = this.canvas.getContext('2d');
        if (!this.ctx) {
            console.error('Could not get canvas context');
            return;
        }
        
        // Set canvas dimensions
        this.updateCanvasDimensions();
        
        // Cleanup any existing resize listener
        if (this.resizeHandler) {
            window.removeEventListener('resize', this.resizeHandler);
        }
        
        // Setup debounced resize handler
        let resizeTimeout;
        this.resizeHandler = () => {
            if (resizeTimeout) {
                clearTimeout(resizeTimeout);
            }
            resizeTimeout = setTimeout(() => {
                console.log('Window resized, updating canvas dimensions...');
                this.updateCanvasDimensions();
            }, 250); // 250ms debounce
        };
        
        window.addEventListener('resize', this.resizeHandler);
        
        console.log('Canvas setup completed');
    }

    updateCanvasDimensions() {
        if (!this.canvas) return;
        
        const container = this.canvas.parentElement;
        if (!container) return;

        // Only update if dimensions actually changed
        const newWidth = container.clientWidth;
        const newHeight = container.clientHeight;
        
        if (this.canvas.width !== newWidth || this.canvas.height !== newHeight) {
            this.canvas.width = newWidth;
            this.canvas.height = newHeight;
            
            this.plotWidth = this.canvas.width - (2 * this.margin);
            this.plotHeight = this.canvas.height - (2 * this.margin);
            
            // Redraw if we have data
            if (this.plotData.voltage.length > 0) {
                requestAnimationFrame(() => this.drawPlot());
            }
        }
    }

    setupEventListeners() {
        if (!this.canvas) return;
        
        // Mouse move for peak hovering
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        
        // Click for peak selection
        this.canvas.addEventListener('click', (e) => this.handleClick(e));
        
        // Setup export button listener
        const exportBtn = document.getElementById('exportPeakDataBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportPeakData());
        }

        // Setup detection start buttons
        document.querySelectorAll('.start-detection').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const method = e.target.dataset.method;
                const gridId = this.methodMappings[method].gridId;
                
                // Show analysis grid
                document.getElementById(gridId).style.display = 'block';
                
                // Update UI state
                this.analysisResults[method].started = true;
                this.updateAnalysisProgress(method, 0);
                
                // Simulate progress
                let progress = 0;
                const interval = setInterval(() => {
                    progress += 10;
                    this.updateAnalysisProgress(method, progress);
                    if (progress >= 100) {
                        clearInterval(interval);
                        this.completeAnalysis(method);
                    }
                }, 200);
                
                // Start actual analysis
                try {
                    const result = await this.runDetection(method);
                    this.updateAnalysisResults(method, result);
                } catch (error) {
                    console.error('Analysis failed:', error);
                    this.showError(`Analysis failed for ${this.methodMappings[method].name}`);
                }
            });
        });

        // Setup view details buttons
        document.querySelectorAll('.view-details-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const methodCard = e.target.closest('.method-card');
                const method = methodCard.querySelector('.start-detection').dataset.method;
                this.showAnalysisDetails(method);
            });
        });

        // Setup Toggle Grid button
        const toggleGridBtn = document.getElementById('toggleGridBtn');
        if (toggleGridBtn) {
            toggleGridBtn.addEventListener('click', () => {
                this.showGrid = !this.showGrid;
                toggleGridBtn.textContent = this.showGrid ? 'Hide Grid' : 'Show Grid';
                this.drawPlot();
            });
        }

        // Setup Reset View button
        const resetViewBtn = document.getElementById('resetViewBtn');
        if (resetViewBtn) {
            resetViewBtn.addEventListener('click', () => this.resetView());
        }
    }

    switchMethod(method) {
        if (this.methodResults && this.methodResults[method]) {
            this.currentMethod = method;
            this.plotData.peaks = this.methodResults[method].peaks;
            this.hoveredPeak = null;
            this.selectedPeak = null;
            this.drawPlot();
            
            // Update modal title with method
            const modalTitle = document.querySelector('.modal-title');
            if (modalTitle) {
                const methodNames = {
                    'prominence': 'Prominence Method Analysis',
                    'derivative': 'Derivative Method Analysis',
                    'ml': 'ML-Enhanced Analysis'
                };
                modalTitle.textContent = methodNames[method] || 'Peak Analysis';
            }

            // Update settings panel with method parameters
            this.updateMethodSettings(this.methodResults[method].params);
        }
    }

    updateMethodSettings(params) {
        const detailsPanel = document.querySelector('.data-info');
        if (detailsPanel && params) {
            const paramHtml = Object.entries(params)
                .map(([key, value]) => `
                    <div class="mb-2">
                        <label class="text-muted">${key}:</label>
                        <span class="ms-2">${Array.isArray(value) ? value.join(', ') : value}</span>
                    </div>
                `).join('');

            detailsPanel.innerHTML = `
                <h4>Method Parameters</h4>
                ${paramHtml}
            `;
        }
    }

    async loadInitialData() {
        try {
            // Load sample data for testing
            const data = {
                success: true,
                data: {
                    voltage: [-0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5],
                    current: [-1.2, -0.8, -0.3, 0.2, 0.8, 1.0, 0.8, 0.2, -0.3, -0.8, -1.2],
                    fileName: 'sample_cv.csv'
                }
            };
            
            if (data.success && data.data) {
                this.plotData.voltage = data.data.voltage;
                this.plotData.current = data.data.current;
                
                // Store original scale for reset functionality
                this.originalScale.voltage = [...data.data.voltage];
                this.originalScale.current = [...data.data.current];
                
                // Generate mock results for testing
                const mockResults = {
                    prominence: {
                        success: true,
                        peaks: [
                            { voltage: -0.3, current: -0.3, type: 'reduction', confidence: 85 },
                            { voltage: 0.0, current: 1.0, type: 'oxidation', confidence: 95 },
                            { voltage: 0.3, current: -0.3, type: 'reduction', confidence: 88 }
                        ],
                        params: { prominence: 0.1, width: 5 }
                    },
                    derivative: {
                        success: true,
                        peaks: [
                            { voltage: -0.35, current: -0.35, type: 'reduction', confidence: 82 },
                            { voltage: 0.0, current: 1.0, type: 'oxidation', confidence: 92 },
                            { voltage: 0.35, current: -0.35, type: 'reduction', confidence: 86 }
                        ],
                        params: { smoothing: 'savgol_filter', window: 5 }
                    },
                    ml: {
                        success: true,
                        peaks: [
                            { voltage: -0.32, current: -0.32, type: 'reduction', confidence: 89, width: 0.2, area: 0.15 },
                            { voltage: 0.0, current: 1.0, type: 'oxidation', confidence: 98, width: 0.25, area: 0.22 },
                            { voltage: 0.32, current: -0.32, type: 'reduction', confidence: 91, width: 0.2, area: 0.14 }
                        ],
                        params: { feature_extraction: ['width', 'area'], confidence_boost: 1.1 }
                    }
                };
                
                const methods = ['prominence', 'derivative', 'ml'];
                const results = methods.map(method => mockResults[method]);
                
                // Store method results
                this.methodResults = Object.fromEntries(
                    methods.map((method, i) => [method, results[i]])
                );

                // Initialize with first method
                if (results[0].success) {
                    this.plotData.peaks = results[0].peaks;
                    this.currentMethod = methods[0];
                }

                // Draw the plot and update info
                this.drawPlot();
                this.updateDataInfo(data.data);
                this.updatePeakList();
            }
        } catch (error) {
            console.error('Error loading data:', error);
            this.showError('Failed to load data. Please try again.');
        }
    }

    drawPlot() {
        console.log('Drawing plot...', {
            context: !!this.ctx,
            canvasWidth: this.canvas?.width,
            canvasHeight: this.canvas?.height,
            dataPoints: this.plotData.voltage.length,
            peaks: this.plotData.peaks.length
        });
        
        if (!this.ctx || !this.plotData.voltage.length) {
            console.warn('Cannot draw plot: missing context or data');
            return;
        }
        
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw background
        this.drawBackground();
        
        // Draw grid
        this.drawGrid();
        
        // Draw CV curve
        this.drawCVCurve();
        console.log('Drew CV curve');
        
        // Draw peaks if any
        if (this.plotData.peaks.length > 0) {
            console.log('Drawing peaks:', this.plotData.peaks);
            this.drawPeaks();
        }
        
        // Draw axes and labels
        this.drawAxesAndLabels();
        
        // Draw hover effects if applicable
        if (this.hoveredPeak !== null) {
            this.drawPeakHover(this.hoveredPeak);
        }
        
        // Draw selection if applicable
        if (this.selectedPeak !== null) {
            this.drawPeakSelection(this.selectedPeak);
        }
        
        console.log('Plot drawing completed');
    }

    drawBackground() {
        this.ctx.fillStyle = '#f8f9fa';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.ctx.fillStyle = 'white';
        this.ctx.fillRect(
            this.margin, 
            this.margin, 
            this.plotWidth, 
            this.plotHeight
        );
    }

    drawGrid() {
        if (!this.showGrid) return;
        
        this.ctx.strokeStyle = '#e0e0e0';
        this.ctx.lineWidth = 1;
        
        // Vertical grid lines
        for (let i = 0; i <= 10; i++) {
            const x = this.margin + (i * this.plotWidth / 10);
            this.ctx.beginPath();
            this.ctx.moveTo(x, this.margin);
            this.ctx.lineTo(x, this.margin + this.plotHeight);
            this.ctx.stroke();
        }
        
        // Horizontal grid lines
        for (let i = 0; i <= 8; i++) {
            const y = this.margin + (i * this.plotHeight / 8);
            this.ctx.beginPath();
            this.ctx.moveTo(this.margin, y);
            this.ctx.lineTo(this.margin + this.plotWidth, y);
            this.ctx.stroke();
        }
    }

    drawCVCurve() {
        const { voltage, current } = this.plotData;
        if (!voltage.length || !current.length) return;
        
        // Find data ranges
        const vMin = Math.min(...voltage);
        const vMax = Math.max(...voltage);
        const iMin = Math.min(...current);
        const iMax = Math.max(...current);
        
        // Draw curve
        this.ctx.strokeStyle = '#4169E1';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        
        for (let i = 0; i < voltage.length; i++) {
            // Convert to canvas coordinates
            const x = this.margin + ((voltage[i] - vMin) / (vMax - vMin)) * this.plotWidth;
            const y = this.margin + this.plotHeight - ((current[i] - iMin) / (iMax - iMin)) * this.plotHeight;
            
            if (i === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        }
        
        this.ctx.stroke();
    }

    drawPeaks() {
        // First draw confidence rings for all peaks
        this.plotData.peaks.forEach(peak => {
            if (peak.confidence) {
                const x = this.voltage2x(peak.voltage);
                const y = this.current2y(peak.current);
                this.drawConfidenceRing(x, y, peak.confidence);
            }
        });

        // Then draw peak markers and labels
        this.plotData.peaks.forEach((peak, index) => {
            const x = this.voltage2x(peak.voltage);
            const y = this.current2y(peak.current);
            
            // Draw method-specific peak marker style
            this.drawMethodPeakMarker(x, y, peak, this.currentMethod);
            
            // Draw peak label if not hovered
            if (index !== this.hoveredPeak) {
                this.drawPeakLabel(peak, index);
            }
        });
    }

    drawConfidenceRing(x, y, confidence) {
        // Calculate ring size based on confidence
        const maxRadius = 12;
        const radius = (confidence / 100) * maxRadius;
        
        // Draw confidence ring
        this.ctx.beginPath();
        this.ctx.arc(x, y, radius, 0, 2 * Math.PI);
        this.ctx.strokeStyle = `rgba(255, 255, 255, 0.5)`;
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
    }

    drawMethodPeakMarker(x, y, peak, method) {
        const styles = {
            prominence: {
                radius: 5,
                fillStyle: peak.type === 'oxidation' ? '#4CAF50' : '#f44336',
                strokeStyle: 'white'
            },
            derivative: {
                radius: 6,
                fillStyle: peak.type === 'oxidation' ? '#2196F3' : '#FF9800',
                strokeStyle: '#333'
            },
            ml: {
                radius: 7,
                fillStyle: peak.type === 'oxidation' ? '#9C27B0' : '#E91E63',
                strokeStyle: '#FFF'
            }
        };

        const style = styles[method] || styles.prominence;
        
        // Draw marker circle with method-specific style
        this.ctx.beginPath();
        this.ctx.arc(x, y, style.radius, 0, 2 * Math.PI);
        this.ctx.fillStyle = style.fillStyle;
        this.ctx.fill();
        this.ctx.strokeStyle = style.strokeStyle;
        this.ctx.lineWidth = 1.5;
        this.ctx.stroke();

        // Add method-specific decoration
        if (method === 'ml' && peak.width) {
            // Draw width indicator for ML method
            const halfWidth = peak.width / 2;
            const x1 = this.voltage2x(peak.voltage - halfWidth);
            const x2 = this.voltage2x(peak.voltage + halfWidth);
            
            this.ctx.beginPath();
            this.ctx.moveTo(x1, y);
            this.ctx.lineTo(x2, y);
            this.ctx.strokeStyle = style.fillStyle;
            this.ctx.lineWidth = 1;
            this.ctx.setLineDash([2, 2]);
            this.ctx.stroke();
            this.ctx.setLineDash([]);
        }
    }

    drawPeakMarker(peak, index) {
        // Convert peak coordinates to canvas coordinates
        const x = this.voltage2x(peak.voltage);
        const y = this.current2y(peak.current);
        
        // Draw marker circle
        this.ctx.beginPath();
        this.ctx.arc(x, y, 5, 0, 2 * Math.PI);
        this.ctx.fillStyle = peak.type === 'oxidation' ? '#4CAF50' : '#f44336';
        this.ctx.fill();
        
        // Draw confidence indicator if available
        if (peak.confidence) {
            this.drawConfidenceRing(x, y, peak.confidence);
        }
    }

    drawPeakLabel(peak, index) {
        const x = this.voltage2x(peak.voltage);
        const y = this.current2y(peak.current);
        
        this.ctx.font = '12px Arial';
        this.ctx.fillStyle = '#333';
        this.ctx.textAlign = 'center';
        this.ctx.fillText(`Peak ${index + 1}`, x, y - 15);
    }

    drawPeakHover(index) {
        const peak = this.plotData.peaks[index];
        if (!peak) return;
        
        const x = this.voltage2x(peak.voltage);
        const y = this.current2y(peak.current);
        
        // Draw highlight circle
        this.ctx.beginPath();
        this.ctx.arc(x, y, 8, 0, 2 * Math.PI);
        this.ctx.strokeStyle = '#FFC107';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
        
        // Draw tooltip
        this.drawPeakTooltip(peak, x, y);
    }

    drawPeakTooltip(peak, x, y) {
        const tooltip = this.createTooltipContent(peak);
        
        // Draw tooltip background
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
        this.ctx.roundRect(x + 10, y - 70, 150, 60, 5);
        this.ctx.fill();
        
        // Draw tooltip text
        this.ctx.font = '12px Arial';
        this.ctx.fillStyle = 'white';
        this.ctx.textAlign = 'left';
        this.ctx.fillText(tooltip.voltage, x + 20, y - 50);
        this.ctx.fillText(tooltip.current, x + 20, y - 35);
        this.ctx.fillText(tooltip.type, x + 20, y - 20);
    }

    createTooltipContent(peak) {
        return {
            voltage: `Voltage: ${peak.voltage.toFixed(3)} V`,
            current: `Current: ${peak.current.toFixed(3)} μA`,
            type: `Type: ${peak.type}`,
            confidence: peak.confidence ? `Confidence: ${peak.confidence}%` : ''
        };
    }

    drawAxesAndLabels() {
        // Draw axes
        this.ctx.strokeStyle = '#333';
        this.ctx.lineWidth = 2;
        
        // X-axis
        this.ctx.beginPath();
        this.ctx.moveTo(this.margin, this.margin + this.plotHeight);
        this.ctx.lineTo(this.margin + this.plotWidth, this.margin + this.plotHeight);
        this.ctx.stroke();
        
        // Y-axis
        this.ctx.beginPath();
        this.ctx.moveTo(this.margin, this.margin);
        this.ctx.lineTo(this.margin, this.margin + this.plotHeight);
        this.ctx.stroke();
        
        // Add labels
        this.drawAxisLabels();
    }

    drawAxisLabels() {
        const { voltage, current } = this.plotData;
        if (!voltage.length || !current.length) return;
        
        const vMin = Math.min(...voltage);
        const vMax = Math.max(...voltage);
        const iMin = Math.min(...current);
        const iMax = Math.max(...current);
        
        this.ctx.font = '12px Arial';
        this.ctx.fillStyle = '#333';
        this.ctx.textAlign = 'center';
        
        // X-axis labels
        this.ctx.fillText(`${vMin.toFixed(2)}V`, this.margin, this.canvas.height - 5);
        this.ctx.fillText(`${((vMin + vMax) / 2).toFixed(2)}V`, 
            this.margin + this.plotWidth/2, this.canvas.height - 5);
        this.ctx.fillText(`${vMax.toFixed(2)}V`, 
            this.margin + this.plotWidth, this.canvas.height - 5);
        
        // Y-axis label
        this.ctx.save();
        this.ctx.translate(15, this.margin + this.plotHeight/2);
        this.ctx.rotate(-Math.PI/2);
        this.ctx.fillText('Current (μA)', 0, 0);
        this.ctx.restore();
    }

    handleMouseMove(event) {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        // Check if mouse is over any peak
        const hoveredIndex = this.findPeakAtPosition(x, y);
        
        if (hoveredIndex !== this.hoveredPeak) {
            this.hoveredPeak = hoveredIndex;
            this.drawPlot();  // Redraw with new hover state
        }
    }

    handleClick(event) {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        // Check if clicked on a peak
        const clickedIndex = this.findPeakAtPosition(x, y);
        
        if (clickedIndex !== null) {
            this.selectedPeak = this.selectedPeak === clickedIndex ? null : clickedIndex;
            this.drawPlot();  // Redraw with new selection state
            
            // Update peak details panel if exists
            if (this.selectedPeak !== null) {
                this.updatePeakDetails(this.plotData.peaks[this.selectedPeak]);
            }
        }
    }

    findPeakAtPosition(x, y) {
        for (let i = 0; i < this.plotData.peaks.length; i++) {
            const peak = this.plotData.peaks[i];
            const peakX = this.voltage2x(peak.voltage);
            const peakY = this.current2y(peak.current);
            
            // Check if within peak marker radius
            const distance = Math.sqrt(Math.pow(x - peakX, 2) + Math.pow(y - peakY, 2));
            if (distance <= 8) {  // 8px hit radius
                return i;
            }
        }
        return null;
    }

    voltage2x(voltage) {
        const vMin = Math.min(...this.plotData.voltage);
        const vMax = Math.max(...this.plotData.voltage);
        return this.margin + ((voltage - vMin) / (vMax - vMin)) * this.plotWidth;
    }

    current2y(current) {
        const iMin = Math.min(...this.plotData.current);
        const iMax = Math.max(...this.plotData.current);
        return this.margin + this.plotHeight - 
               ((current - iMin) / (iMax - iMin)) * this.plotHeight;
    }

    updateDataInfo(data) {
        const dataInfo = document.querySelector('.data-info');
        if (dataInfo) {
            dataInfo.innerHTML = `
                <h4>CV Data Information</h4>
                <p>File: ${data.fileName || 'Unknown'}</p>
                <p>Points: ${data.voltage.length}</p>
                <p>Voltage Range: ${Math.min(...data.voltage).toFixed(2)}V to ${Math.max(...data.voltage).toFixed(2)}V</p>
                <p>Current Range: ${Math.min(...data.current).toFixed(2)}μA to ${Math.max(...data.current).toFixed(2)}μA</p>
            `;
        }
    }

    updatePeakDetails(peak) {
        const detailsPanel = document.querySelector('.peak-details');
        if (detailsPanel) {
            detailsPanel.innerHTML = `
                <h4>Peak Details</h4>
                <p>Voltage: ${peak.voltage.toFixed(3)} V</p>
                <p>Current: ${peak.current.toFixed(3)} μA</p>
                <p>Type: ${peak.type}</p>
                ${peak.confidence ? `<p>Confidence: ${peak.confidence}%</p>` : ''}
                <button class="btn btn-sm btn-primary" onclick="copyPeakData(${JSON.stringify(peak)})">
                    📋 Copy Data
                </button>
            `;
        }
    }

    async exportPeakData() {
        try {
            // Create CSV content
            let csvContent = "Peak Number,Voltage (V),Current (μA),Type,Confidence (%)\n";
            
            this.plotData.peaks.forEach((peak, index) => {
                csvContent += `${index + 1},${peak.voltage.toFixed(3)},${peak.current.toFixed(3)},${peak.type},${peak.confidence || ''}\n`;
            });
            
            // Create and trigger download
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.setAttribute('href', url);
            link.setAttribute('download', `peak_data_${new Date().toISOString().slice(0,19)}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
        } catch (error) {
            console.error('Error exporting peak data:', error);
            this.showError('Failed to export peak data');
        }
    }

    showError(message) {
        // Show error in a toast or alert
        alert(message);
    }

    resetView() {
        console.log('Resetting view...');
        // Reset to original data ranges if stored
        if (this.originalScale.voltage && this.originalScale.current) {
            this.plotData.voltage = [...this.originalScale.voltage];
            this.plotData.current = [...this.originalScale.current];
        }
        // Reset zoom/pan state if implemented
        this.zoomLevel = 1;
        this.panOffset = { x: 0, y: 0 };
        // Redraw with reset state
        this.drawPlot();
        console.log('View reset completed');
    }

    async runDetection(method) {
        const startTime = performance.now();
        
        try {
            // Simulate peak detection for testing
            await new Promise(resolve => setTimeout(resolve, 500)); // Simulate API delay
            
            // Return stored mock results for the method
            const mockResult = this.methodResults[method];

            const endTime = performance.now();
            const processingTime = ((endTime - startTime) / 1000).toFixed(3);

            return {
                ...mockResult,
                processingTime
            };
        } catch (error) {
            console.error('Detection failed:', error);
            throw error;
        }
    }

    updateAnalysisProgress(method, progress) {
        const gridId = this.methodMappings[method].gridId;
        const grid = document.getElementById(gridId);
        if (!grid) return;

        // Update progress bar
        const progressBar = grid.querySelector('.progress-bar');
        progressBar.style.width = `${progress}%`;
        
        if (progress >= 100) {
            progressBar.classList.add('bg-success');
        }
    }

    updateAnalysisResults(method, result) {
        const gridId = this.methodMappings[method].gridId;
        const grid = document.getElementById(gridId);
        if (!grid) return;

        // Update stats
        grid.querySelector('.peaks-count').textContent = result.peaks.length;
        grid.querySelector('.confidence-value').textContent = 
            `${Math.round(result.peaks.reduce((acc, p) => acc + p.confidence, 0) / result.peaks.length)}%`;
        grid.querySelector('.processing-time').textContent = `${result.processingTime}s`;

        // Store results
        this.analysisResults[method] = {
            ...this.analysisResults[method],
            completed: true,
            results: result
        };
    }

    completeAnalysis(method) {
        // Enable view details button
        const gridId = this.methodMappings[method].gridId;
        const grid = document.getElementById(gridId);
        if (!grid) return;

        const detailsBtn = grid.querySelector('.view-details-btn');
        detailsBtn.disabled = false;
    }

    updatePeakList() {
        const peakList = document.querySelector('.peak-list');
        if (!peakList || !this.plotData.peaks.length) return;

        // Update method badge
        const methodBadge = document.querySelector('.peak-info .badge');
        if (methodBadge) {
            methodBadge.textContent = this.currentMethod || 'No Method';
        }

        // Create table for peaks
        const tableHtml = `
            <div class="peak-list">
                ${this.plotData.peaks.map((peak, index) => `
                    <div class="peak-item${this.selectedPeak === index ? ' selected' : ''}" data-peak-index="${index}">
                        <div class="peak-type">
                            <span class="type-badge ${peak.type.toLowerCase()}">${peak.type}</span>
                        </div>
                        <div class="peak-values">
                            <span class="value-label">V:</span>
                            <span class="value">${peak.voltage.toFixed(3)} V</span>
                            <span class="value-label ms-3">I:</span>
                            <span class="value">${peak.current.toFixed(3)} μA</span>
                        </div>
                        <div class="peak-confidence">
                            <span class="badge bg-success">${peak.confidence}%</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        peakList.innerHTML = tableHtml;

        peakList.innerHTML = peaksHtml;

        // Add click listeners to peak items
        peakList.querySelectorAll('.peak-item').forEach(item => {
            item.addEventListener('click', () => {
                const index = parseInt(item.dataset.peakIndex);
                this.selectedPeak = this.selectedPeak === index ? null : index;
                this.drawPlot();
                this.updatePeakList(); // Refresh selection state
                if (this.selectedPeak !== null) {
                    this.updatePeakDetails(this.plotData.peaks[this.selectedPeak]);
                }
            });
        });
    }

    showAnalysisDetails(method) {
        const results = this.analysisResults[method].results;
        if (!results) return;

        // Update plot with results
        this.plotData.peaks = results.peaks;
        this.currentMethod = method;
        
        // Show analysis modal
        const modalElement = document.getElementById('analysisModal');
        if (!modalElement) return;

        // Remove aria-hidden and add proper focus management
        modalElement.removeAttribute('aria-hidden');
        
        // Store reference to the trigger button to restore focus later
        this.lastFocusedElement = document.activeElement;
        
        const modal = new bootstrap.Modal(modalElement, {
            backdrop: true,
            keyboard: true,
            focus: true
        });
        
        // Handle modal events
        const onShown = () => {
            console.log('Modal shown, initializing canvas...');
            this.setupCanvas();
            this.updateCanvasDimensions();
            this.drawPlot();
            
            // Focus the first focusable element in the modal
            const firstFocusable = modalElement.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (firstFocusable) {
                firstFocusable.focus();
            }
        };
        
        const onHidden = () => {
            // Restore focus to the trigger button when modal closes
            if (this.lastFocusedElement) {
                this.lastFocusedElement.focus();
            }
            // Clean up event listeners
            modalElement.removeEventListener('shown.bs.modal', onShown);
            modalElement.removeEventListener('hidden.bs.modal', onHidden);
        };
        
        modalElement.addEventListener('shown.bs.modal', onShown);
        modalElement.addEventListener('hidden.bs.modal', onHidden);
        
        modal.show();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing Peak Visualization System...');
    window.peakVisualization = new PeakVisualizationManager();
});