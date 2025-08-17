// Function to load and plot real CV data
async function plotRealCVData() {
    try {
        // Load data from the CSV file
        const response = await fetch('/temp_data/preview_Palmsens_Palmsens_0.5mM_CV_100mVpS_E1_scan_05.csv');
        const csvText = await response.text();
        
        // Parse CSV
        const lines = csvText.split('\n');
        const voltage = [];
        const current = [];
        
        // Skip header (first 2 lines)
        for (let i = 2; i < lines.length; i++) {
            const line = lines[i].trim();
            if (line) {
                const [v, ua] = line.split(',').map(Number);
                voltage.push(v);
                current.push(ua);
            }
        }

        // Get canvas
        const canvas = document.getElementById('previewChart');
        if (!canvas) return;
        
        // Plot data
        const ctx = canvas.getContext('2d');
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Set margins and dimensions
        const margin = 60;
        const width = canvas.width;
        const height = canvas.height;
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
        
        // Draw grid lines
        for (let i = 0; i <= 10; i++) {
            const x = margin + (i * plotWidth / 10);
            const y = margin + (i * plotHeight / 10);
            
            // Vertical lines
            ctx.beginPath();
            ctx.moveTo(x, margin);
            ctx.lineTo(x, margin + plotHeight);
            ctx.stroke();
            
            // Horizontal lines
            ctx.beginPath();
            ctx.moveTo(margin, y);
            ctx.lineTo(margin + plotWidth, y);
            ctx.stroke();
        }
        
        // Calculate ranges
        const vMin = Math.min(...voltage);
        const vMax = Math.max(...voltage);
        const iMin = Math.min(...current);
        const iMax = Math.max(...current);
        
        // Plot CV curve
        ctx.strokeStyle = '#4169E1';
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        for (let i = 0; i < voltage.length; i++) {
            // Convert data points to canvas coordinates
            const x = margin + ((voltage[i] - vMin) / (vMax - vMin)) * plotWidth;
            const y = margin + plotHeight - ((current[i] - iMin) / (iMax - iMin)) * plotHeight;
            
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
        ctx.fillText(`${vMin.toFixed(2)}V`, margin, height - 20);
        ctx.fillText(`${((vMin + vMax) / 2).toFixed(2)}V`, margin + plotWidth/2, height - 20);
        ctx.fillText(`${vMax.toFixed(2)}V`, margin + plotWidth, height - 20);
        
        // Y-axis label
        ctx.save();
        ctx.translate(20, margin + plotHeight/2);
        ctx.rotate(-Math.PI/2);
        ctx.fillText('Current (μA)', 0, 0);
        ctx.restore();
        
        // Update graph info
        const graphInfo = document.querySelector('.graph-info');
        if (graphInfo) {
            graphInfo.innerHTML = `
                <h4>Data Source: Real CV measurement (uploaded file)</h4>
                <p>Voltage Range: ${vMin.toFixed(2)}V to ${vMax.toFixed(2)}V</p>
                <p>Current Range: ${iMin.toFixed(2)}μA to ${iMax.toFixed(2)}μA</p>
                <button class="btn btn-primary" id="exportDataBtn">
                    📥 Export Graph Data (CSV)
                </button>
            `;
        }
        
        // Store data for export
        window.cvData = {
            voltage: voltage,
            current: current
        };
        
    } catch (error) {
        console.error('Error plotting CV data:', error);
        alert('Failed to load and plot CV data. Please try again.');
    }
}

// Call this function when showing graph tab
document.addEventListener('DOMContentLoaded', function() {
    // Add graph tab click handler
    const graphsTab = document.querySelector('[onclick="showPreviewTab(\'graphs\')"]');
    if (graphsTab) {
        graphsTab.addEventListener('click', plotRealCVData);
    }
    
    // Add export button click handler
    document.body.addEventListener('click', function(e) {
        if (e.target && e.target.id === 'exportDataBtn') {
            // Use the exportGraphData function from export_utils.js
            if (typeof window.exportGraphData === 'function') {
                window.exportGraphData();
            } else {
                console.error('exportGraphData function not found');
            }
        }
    });
});