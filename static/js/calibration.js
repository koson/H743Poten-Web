// Calibration utilities
const calibrationManager = {
    selectedModel: 'random_forest',
    canvas: null,
    ctx: null,

    initialize() {
        this.canvas = document.getElementById('calibrationPlot');
        if (this.canvas) {
            this.ctx = this.canvas.getContext('2d');
            this.resizeCanvas();
            window.addEventListener('resize', () => this.resizeCanvas());
        }
    },

    resizeCanvas() {
        if (!this.canvas) return;
        const container = this.canvas.parentElement;
        this.canvas.width = container.clientWidth;
        this.canvas.height = 300;
        this.clearPlot();
    },

    clearPlot() {
        if (!this.ctx) return;
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.fillStyle = '#f8f9fa';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw waiting message
        this.ctx.font = '14px Arial';
        this.ctx.fillStyle = '#6c757d';
        this.ctx.textAlign = 'center';
        this.ctx.fillText('Select a model and start calibration', this.canvas.width/2, this.canvas.height/2);
    },

    drawCalibrationPlot(data) {
        if (!this.ctx) return;
        
        const width = this.canvas.width;
        const height = this.canvas.height;
        const padding = 40;
        
        // Clear canvas
        this.ctx.clearRect(0, 0, width, height);
        this.ctx.fillStyle = '#ffffff';
        this.ctx.fillRect(0, 0, width, height);
        
        const xMin = Math.min(...data.actual);
        const xMax = Math.max(...data.actual);
        const yMin = Math.min(...data.predicted);
        const yMax = Math.max(...data.predicted);
        
        // Add padding
        const xPadding = (xMax - xMin) * 0.1;
        const yPadding = (yMax - yMin) * 0.1;
        
        // Scale factors
        const xScale = (width - 2 * padding) / ((xMax + xPadding) - (xMin - xPadding));
        const yScale = (height - 2 * padding) / ((yMax + yPadding) - (yMin - yPadding));
        
        // Drawing functions
        const toCanvasX = x => padding + (x - (xMin - xPadding)) * xScale;
        const toCanvasY = y => height - (padding + (y - (yMin - yPadding)) * yScale);
        
        // Draw grid
        this.ctx.strokeStyle = '#f0f0f0';
        this.ctx.lineWidth = 1;
        
        // Vertical grid lines
        for (let x = Math.floor(xMin); x <= Math.ceil(xMax); x += (xMax - xMin) / 10) {
            this.ctx.beginPath();
            this.ctx.moveTo(toCanvasX(x), padding);
            this.ctx.lineTo(toCanvasX(x), height - padding);
            this.ctx.stroke();
        }
        
        // Horizontal grid lines
        for (let y = Math.floor(yMin); y <= Math.ceil(yMax); y += (yMax - yMin) / 10) {
            this.ctx.beginPath();
            this.ctx.moveTo(padding, toCanvasY(y));
            this.ctx.lineTo(width - padding, toCanvasY(y));
            this.ctx.stroke();
        }
        
        // Draw points
        this.ctx.fillStyle = 'rgba(40, 167, 69, 0.6)';
        data.actual.forEach((x, i) => {
            this.ctx.beginPath();
            this.ctx.arc(toCanvasX(x), toCanvasY(data.predicted[i]), 4, 0, 2 * Math.PI);
            this.ctx.fill();
        });
        
        // Draw perfect fit line
        this.ctx.strokeStyle = '#dc3545';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.moveTo(toCanvasX(xMin), toCanvasY(xMin));
        this.ctx.lineTo(toCanvasX(xMax), toCanvasY(xMax));
        this.ctx.stroke();
        
        // Draw axes
        this.ctx.strokeStyle = '#000000';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.moveTo(padding, height - padding);
        this.ctx.lineTo(width - padding, height - padding);
        this.ctx.moveTo(padding, height - padding);
        this.ctx.lineTo(padding, padding);
        this.ctx.stroke();
        
        // Draw labels
        this.ctx.font = '12px Arial';
        this.ctx.fillStyle = '#000000';
        this.ctx.textAlign = 'center';
        
        // X-axis label
        this.ctx.fillText('Actual Values', width/2, height - 10);
        
        // Y-axis label (rotated)
        this.ctx.save();
        this.ctx.translate(15, height/2);
        this.ctx.rotate(-Math.PI/2);
        this.ctx.fillText('Predicted Values', 0, 0);
        this.ctx.restore();
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    calibrationManager.initialize();
});

// Global functions
window.selectModel = (model) => {
    // Update selection in UI
    document.querySelectorAll('.list-group-item').forEach(item => {
        item.classList.remove('active');
        if (item.textContent.toLowerCase().includes(model)) {
            item.classList.add('active');
        }
    });
    calibrationManager.selectedModel = model;
};

window.startCalibration = () => {
    // Get selected model
    const model = calibrationManager.selectedModel;
    
    // Mock data for demonstration
    const mockData = {
        actual: Array.from({length: 50}, () => Math.random() * 10),
        predicted: Array.from({length: 50}, () => Math.random() * 10)
    };
    
    // Update plot
    calibrationManager.drawCalibrationPlot(mockData);
    
    // Update metrics
    document.getElementById('calibrationAccuracy').textContent = '95%';
    document.getElementById('calibrationError').textContent = '0.15';
    document.getElementById('calibrationTime').textContent = '2.3s';
};