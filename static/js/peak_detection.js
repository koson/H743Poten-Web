// Peak detection utilities
const detectionManager = {
    results: {},
    
    // Show details in new tab
    showDetails(method, results) {
        // Send POST request to create analysis session
        fetch('/create_analysis_session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                peaks: results.previewData.peaks,
                data: results.previewData,
                method: method
            })
        })
        .then(response => response.json())
        .then(data => {
            // Open new tab with session ID
            window.open(`/peak_analysis/${data.session_id}`, '_blank');
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to create analysis session');
        });
    },
    
    // Start detection for a method
    startDetection(method) {
        console.log('Starting detection for method:', method);
        const gridId = this.getGridId(method);
        const grid = document.getElementById(gridId);
        
        if (!grid) {
            console.error('Grid not found for method:', method);
            return;
        }
        
        grid.style.display = 'block';
        this.simulateDetection(grid, method);
    },
    
    // Get grid ID for method
    getGridId(method) {
        return {
            'ml': 'ml-analysis',
            'prominence': 'traditional-analysis',
            'derivative': 'hybrid-analysis'
        }[method];
    },
    
    // Simulate detection process
    simulateDetection(grid, method) {
        const progressBar = grid.querySelector('.progress-bar');
        let progress = 0;
        
        const interval = setInterval(() => {
            progress += 5;
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
            }
            if (progress >= 100) {
                clearInterval(interval);
                this.completeDetection(method);
            }
        }, 50);
    },
    
    // Complete detection process
    completeDetection(method) {
        // Get mock results
        const results = {
            peaks: 4,
            confidence: 89,
            processingTime: 0.5,
            previewData: {
                voltage: [-0.5, -0.3, -0.1, 0.1, 0.3, 0.5],
                current: [-2, 1, 3, 1, -1, -2],
                peaks: [
                    { x: -0.1, y: 3, type: 'oxidation' },
                    { x: 0.3, y: -1, type: 'reduction' }
                ]
            }
        };
        
        // Get grid and update it
        const gridId = this.getGridId(method);
        const grid = document.getElementById(gridId);
        
        if (!grid) {
            console.error('Grid not found for method:', method);
            return;
        }
        
        // Update grid statistics
        grid.querySelector('.peaks-count').textContent = results.peaks;
        grid.querySelector('.confidence-value').textContent = results.confidence + '%';
        grid.querySelector('.processing-time').textContent = results.processingTime + 's';
        
        // Update preview graph
        const previewCanvas = grid.querySelector('.preview-canvas');
        if (previewCanvas) {
            const container = previewCanvas.parentElement;
            if (container) {
                previewCanvas.width = container.clientWidth;
                previewCanvas.height = container.clientHeight;
                
                const ctx = previewCanvas.getContext('2d');
                if (ctx) {
                    previewGraphUtils.drawGraph(previewCanvas, results.previewData);
                }
            }
        }
        
        // Setup view details button
        const detailsBtn = grid.querySelector('.view-details-btn');
        if (detailsBtn) {
            detailsBtn.disabled = false;
            detailsBtn.onclick = () => {
                console.log('View Details clicked for method:', method);
                this.showDetails(method, results);
            };
        }
        
        // Log notification
        const notification = `Detected ${results.peaks} peaks with ${results.confidence}% confidence`;
        console.log(notification);
        
        // Store results for later use
        this.results[method] = results;
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize preview canvases
    document.querySelectorAll('.preview-canvas').forEach(canvas => {
        const container = canvas.parentElement;
        if (container) {
            canvas.width = container.clientWidth;
            canvas.height = container.clientHeight;
            
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#f8f9fa';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.font = '12px Arial';
            ctx.fillStyle = '#6c757d';
            ctx.textAlign = 'center';
            ctx.fillText('Waiting for detection...', canvas.width/2, canvas.height/2);
        }
    });
    
    // Expose global functions
    window.detectionManager = detectionManager;
    window.startDetection = (method) => detectionManager.startDetection(method);
});
