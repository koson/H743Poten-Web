// Peak Canvas Manager - handles all canvas operations in the modal
const peakCanvasManager = {
    canvas: null,
    context: null,
    container: null,
    data: null,
    method: null,
    isInitialized: false,
    
    // Initialize the canvas manager
    initialize(canvasId, container) {
        console.log('Initializing peak canvas manager...');
        
        // Get and validate canvas
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error('Canvas element not found:', canvasId);
            return false;
        }
        
        // Get and validate context
        this.context = this.canvas.getContext('2d');
        if (!this.context) {
            console.error('Could not get canvas context');
            return false;
        }
        
        // Set container
        this.container = container;
        this.updateCanvasSize();
        
        // Set initialization flag
        this.isInitialized = true;
        console.log('Peak canvas manager initialized successfully');
        
        return true;
    },
    
    // Update canvas size based on container
    updateCanvasSize() {
        if (!this.canvas || !this.container) return;
        
        // Get container size
        const rect = this.container.getBoundingClientRect();
        const width = rect.width;
        const height = Math.min(400, rect.height);
        
        // Update canvas size
        this.canvas.width = width;
        this.canvas.height = height;
        
        // Redraw if we have data
        if (this.data) {
            this.drawPlot();
        }
    },
    
    // Update plot data
    updateData(data, method) {
        this.data = data;
        this.method = method;
    },
    
    // Draw the plot
    drawPlot() {
        if (!this.isInitialized) {
            console.error('Cannot draw plot: Canvas manager not initialized');
            return;
        }
        
        if (!this.data) {
            console.error('Cannot draw plot: No data available');
            return;
        }
        
        const width = this.canvas.width;
        const height = this.canvas.height;
        const padding = 40;
        
        // Clear canvas
        this.context.clearRect(0, 0, width, height);
        this.context.fillStyle = '#ffffff';
        this.context.fillRect(0, 0, width, height);
        
        // Get data ranges
        const xMin = Math.min(...this.data.voltage);
        const xMax = Math.max(...this.data.voltage);
        const yMin = Math.min(...this.data.current);
        const yMax = Math.max(...this.data.current);
        
        // Add padding to ranges
        const xPadding = (xMax - xMin) * 0.1;
        const yPadding = (yMax - yMin) * 0.1;
        
        // Scale factors
        const xScale = (width - 2 * padding) / ((xMax + xPadding) - (xMin - xPadding));
        const yScale = (height - 2 * padding) / ((yMax + yPadding) - (yMin - yPadding));
        
        // Drawing functions
        const toCanvasX = x => padding + (x - (xMin - xPadding)) * xScale;
        const toCanvasY = y => height - (padding + (y - (yMin - yPadding)) * yScale);
        
        // Draw grid
        this.context.strokeStyle = '#f0f0f0';
        this.context.lineWidth = 1;
        
        // Vertical grid lines
        for (let x = xMin; x <= xMax; x += (xMax - xMin) / 10) {
            this.context.beginPath();
            this.context.moveTo(toCanvasX(x), padding);
            this.context.lineTo(toCanvasX(x), height - padding);
            this.context.stroke();
        }
        
        // Horizontal grid lines
        for (let y = yMin; y <= yMax; y += (yMax - yMin) / 10) {
            this.context.beginPath();
            this.context.moveTo(padding, toCanvasY(y));
            this.context.lineTo(width - padding, toCanvasY(y));
            this.context.stroke();
        }
        
        // Draw axes
        this.context.strokeStyle = '#000000';
        this.context.lineWidth = 2;
        this.context.beginPath();
        this.context.moveTo(padding, padding);
        this.context.lineTo(padding, height - padding);
        this.context.lineTo(width - padding, height - padding);
        this.context.stroke();
        
        // Draw axis labels
        this.context.font = '14px Arial';
        this.context.fillStyle = '#000000';
        
        // X-axis label
        this.context.textAlign = 'center';
        this.context.textBaseline = 'top';
        this.context.fillText('Voltage (V)', width / 2, height - padding / 2);
        
        // Y-axis label
        this.context.save();
        this.context.translate(padding / 2, height / 2);
        this.context.rotate(-Math.PI / 2);
        this.context.textAlign = 'center';
        this.context.fillText('Current (µA)', 0, 0);
        this.context.restore();
        
        // Draw axis values
        this.context.font = '12px Arial';
        
        // X-axis values
        for (let x = xMin; x <= xMax; x += (xMax - xMin) / 5) {
            const xPos = toCanvasX(x);
            this.context.textAlign = 'center';
            this.context.textBaseline = 'top';
            this.context.fillText(x.toFixed(2), xPos, height - padding + 5);
        }
        
        // Y-axis values
        for (let y = yMin; y <= yMax; y += (yMax - yMin) / 5) {
            const yPos = toCanvasY(y);
            this.context.textAlign = 'right';
            this.context.textBaseline = 'middle';
            this.context.fillText(y.toFixed(2), padding - 5, yPos);
        }
        
        // Draw CV curve
        this.context.strokeStyle = '#0d6efd';
        this.context.lineWidth = 2;
        this.context.beginPath();
        this.context.moveTo(toCanvasX(this.data.voltage[0]), toCanvasY(this.data.current[0]));
        
        for (let i = 1; i < this.data.voltage.length; i++) {
            this.context.lineTo(toCanvasX(this.data.voltage[i]), toCanvasY(this.data.current[i]));
        }
        
        this.context.stroke();
        
        // Draw peaks
        this.data.peaks.forEach(peak => {
            // Draw peak point
            this.context.fillStyle = peak.type === 'oxidation' ? '#dc3545' : '#198754';
            this.context.beginPath();
            this.context.arc(toCanvasX(peak.x), toCanvasY(peak.y), 6, 0, 2 * Math.PI);
            this.context.fill();
            
            // Draw peak label
            this.context.font = '12px Arial';
            this.context.fillStyle = '#000000';
            this.context.textAlign = 'center';
            this.context.textBaseline = 'bottom';
            this.context.fillText(peak.type === 'oxidation' ? 'Ox' : 'Red', 
                                toCanvasX(peak.x), 
                                toCanvasY(peak.y) - 10);
        });
    }
};
