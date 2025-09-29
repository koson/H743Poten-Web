// Utility functions for drawing preview graphs
const previewGraphUtils = {
    // Draw a preview graph
    drawGraph(canvas, data) {
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        
        const width = canvas.width;
        const height = canvas.height;
        const padding = 10;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = '#f8f9fa';
        ctx.fillRect(0, 0, width, height);
        
        // Get data ranges
        const xMin = Math.min(...data.voltage);
        const xMax = Math.max(...data.voltage);
        const yMin = Math.min(...data.current);
        const yMax = Math.max(...data.current);
        
        // Scale factors
        const xScale = (width - 2 * padding) / (xMax - xMin);
        const yScale = (height - 2 * padding) / (yMax - yMin);
        
        // Drawing functions
        const toCanvasX = x => padding + (x - xMin) * xScale;
        const toCanvasY = y => height - (padding + (y - yMin) * yScale);
        
        // Draw axes
        ctx.strokeStyle = '#dee2e6';
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, height - padding);
        ctx.lineTo(width - padding, height - padding);
        ctx.stroke();
        
        // Draw CV curve
        ctx.strokeStyle = '#0d6efd';
        ctx.beginPath();
        ctx.moveTo(toCanvasX(data.voltage[0]), toCanvasY(data.current[0]));
        for (let i = 1; i < data.voltage.length; i++) {
            ctx.lineTo(toCanvasX(data.voltage[i]), toCanvasY(data.current[i]));
        }
        ctx.stroke();
        
        // Draw peaks if available
        if (data.peaks && Array.isArray(data.peaks) && data.peaks.length > 0) {
            data.peaks.forEach(peak => {
                const x = peak.x || peak.voltage;
                const y = peak.y || peak.current;
                ctx.fillStyle = peak.type === 'oxidation' ? '#dc3545' : '#198754';
                ctx.beginPath();
                ctx.arc(toCanvasX(x), toCanvasY(y), 4, 0, 2 * Math.PI);
                ctx.fill();
            });
        }
        
        // Add labels
        ctx.font = '10px Arial';
        ctx.fillStyle = '#6c757d';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'top';
        ctx.fillText('V', width - padding, height - padding);
        
        ctx.textAlign = 'right';
        ctx.textBaseline = 'bottom';
        ctx.fillText('i', padding, padding);
    }
};

// Make available globally
window.previewGraphUtils = previewGraphUtils;
