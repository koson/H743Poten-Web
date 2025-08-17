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
        this.canvas = document.getElementById('peakVisualizationChart');
        if (!this.canvas) {
            console.error('Canvas element not found');
            return;
        }
        this.ctx = this.canvas.getContext('2d');
        
        // Set canvas dimensions
        this.updateCanvasDimensions();
        
        // Handle window resize
        window.addEventListener('resize', () => this.updateCanvasDimensions());
    }

    updateCanvasDimensions() {
        if (!this.canvas) return;
        
        const container = this.canvas.parentElement;
        this.canvas.width = container.clientWidth;
        this.canvas.height = container.clientHeight;
        
        this.plotWidth = this.canvas.width - (2 * this.margin);
        this.plotHeight = this.canvas.height - (2 * this.margin);
        
        // Redraw if we have data
        if (this.plotData.voltage.length > 0) {
            this.drawPlot();
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
            // First load the graph data
            const response = await fetch('http://localhost:5000/api/workflow_api/get-graph-data');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            if (data.success && data.data) {
                this.plotData.voltage = data.data.voltage;
                this.plotData.current = data.data.current;
                
                // Then analyze with all methods in parallel
                const methods = ['prominence', 'derivative', 'ml'];
                const peakPromises = methods.map(method => 
                    fetch(`/api/peak_detection/get-peaks/${method}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            voltage: this.plotData.voltage,
                            current: this.plotData.current
                        })
                    }).then(res => res.json())
                );

                // Wait for all analyses to complete
                const results = await Promise.all(peakPromises);
                
                // Update stats for each method
                methods.forEach((method, i) => {
                    if (results[i].success) {
                        const peakCount = results[i].peaks.length;
                        document.getElementById(`${method}-peaks`).textContent = peakCount;
                    }
                });

                // Store method results
                this.methodResults = Object.fromEntries(
                    methods.map((method, i) => [method, results[i]])
                );

                // Initialize with first method
                if (results[0].success) {
                    this.plotData.peaks = results[0].peaks;
                    this.currentMethod = methods[0];
                }

                this.drawPlot();
                this.updateDataInfo(data.data);
            }
        } catch (error) {
            console.error('Error loading data:', error);
            this.showError('Failed to load data. Please try again.');
        }
    }

    drawPlot() {
        if (!this.ctx || !this.plotData.voltage.length) return;
        
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw background
        this.drawBackground();
        
        // Draw grid
        this.drawGrid();
        
        // Draw CV curve
        this.drawCVCurve();
        
        // Draw peaks if any
        if (this.plotData.peaks.length > 0) {
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

    async runDetection(method) {
        const startTime = performance.now();
        
        try {
            const result = await fetch(`/api/peak_detection/get-peaks/${method}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    voltage: this.plotData.voltage,
                    current: this.plotData.current
                })
            }).then(res => res.json());

            const endTime = performance.now();
            const processingTime = ((endTime - startTime) / 1000).toFixed(3);

            return {
                ...result,
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

    showAnalysisDetails(method) {
        const results = this.analysisResults[method].results;
        if (!results) return;

        // Update plot with results
        this.plotData.peaks = results.peaks;
        this.currentMethod = method;
        
        // Show analysis modal
        const modal = new bootstrap.Modal(document.getElementById('analysisModal'));
        modal.show();
        
        // Redraw plot
        this.drawPlot();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing Peak Visualization System...');
    window.peakVisualization = new PeakVisualizationManager();
});