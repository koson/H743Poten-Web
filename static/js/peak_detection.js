// Peak detection utilities
const detectionManager = {
    results: {},
    
    // Show details in new tab
    showDetails(method, results) {
        // Get current data
        const currentData = window.getCurrentData ? window.getCurrentData() : null;
        if (!currentData) {
            alert('No data available for analysis');
            return;
        }

        console.log('Creating analysis session for method:', method);
        console.log('Results:', results);
        console.log('Current data points:', currentData.voltage.length);

        // Send POST request to create analysis session
        fetch('/peak_detection/create_analysis_session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                peaks: results.peaks || [],
                data: {
                    ...results,
                    voltage: currentData.voltage,
                    current: currentData.current,
                    previewData: results.previewData || {
                        voltage: currentData.voltage,
                        current: currentData.current,
                        peaks: []
                    }
                },
                method: method,
                methodName: this.getMethodName(method)
            })
        })
        .then(response => {
            console.log('Session creation response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Session creation response:', data);
            if (data.session_id) {
                // Open new tab with session ID
                window.open(`/peak_detection/peak_analysis/${data.session_id}`, '_blank');
            } else {
                alert('Failed to create analysis session: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error creating analysis session:', error);
            alert('Failed to create analysis session: ' + error.message);
        });
    },
    
    // Start detection for a method
    startDetection(method) {
        console.log('Starting detection for method:', method);
        
        // Check if data is loaded
        const currentData = window.getCurrentData ? window.getCurrentData() : null;
        if (!currentData) {
            alert('Please load data first before starting peak detection.');
            return;
        }
        
        const gridId = this.getGridId(method);
        const grid = document.getElementById(gridId);
        
        if (!grid) {
            console.error('Grid not found for method:', method);
            return;
        }
        
        grid.style.display = 'block';
        this.performDetection(grid, method, currentData);
    },
    
    // Get grid ID for method
    getGridId(method) {
        return {
            'ml': 'ml-analysis',
            'prominence': 'traditional-analysis',
            'derivative': 'hybrid-analysis'
        }[method];
    },

    // Get method display name
    getMethodName(method) {
        return {
            'ml': 'DeepCV',
            'prominence': 'TraditionalCV',
            'derivative': 'HybridCV'
        }[method];
    },
    
    // Perform real detection process
    performDetection(grid, method, data) {
        const progressBar = grid.querySelector('.progress-bar');
        let progress = 0;
        
        // Show progress
        const interval = setInterval(() => {
            progress += 10;
            if (progressBar) {
                progressBar.style.width = `${progress}%`;
            }
            if (progress >= 100) {
                clearInterval(interval);
                this.executeDetection(method, data);
            }
        }, 100);
    },

    // Execute actual peak detection
    async executeDetection(method, data) {
        try {
            // Call backend peak detection API
            const response = await fetch(`/peak_detection/get-peaks/${method}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    voltage: data.voltage,
                    current: data.current
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.success) {
                this.completeDetection(method, result);
            } else {
                throw new Error(result.error || 'Detection failed');
            }
        } catch (error) {
            console.error('Detection error:', error);
            this.showDetectionError(method, error.message);
        }
    },

    // Show detection error
    showDetectionError(method, errorMessage) {
        const gridId = this.getGridId(method);
        const grid = document.getElementById(gridId);
        
        if (grid) {
            const progressBar = grid.querySelector('.progress-bar');
            if (progressBar) {
                progressBar.style.width = '100%';
                progressBar.classList.remove('bg-success');
                progressBar.classList.add('bg-danger');
            }
            
            // Show error message
            alert(`Peak detection failed: ${errorMessage}`);
        }
    },

    // Simulate detection process (kept for backward compatibility)
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
    completeDetection(method, apiResult = null) {
        let results;
        
        if (apiResult) {
            // Use real results from API
            results = {
                peaks: apiResult.peaks ? apiResult.peaks.length : 0,
                confidence: this.calculateAverageConfidence(apiResult.peaks || []),
                processingTime: 0.5,
                previewData: this.convertToPreviewData(apiResult)
            };
        } else {
            // Fall back to mock results
            results = {
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
        }
        
        // Get grid and update it
        const gridId = this.getGridId(method);
        const grid = document.getElementById(gridId);
        
        if (!grid) {
            console.error('Grid not found for method:', method);
            return;
        }

        // Store results for this method
        this.results[method] = apiResult || results;

        // Update the UI
        this.updateResultsUI(grid, results, method);
    },

    // Calculate average confidence from peaks
    calculateAverageConfidence(peaks) {
        if (!peaks || peaks.length === 0) return 0;
        
        const totalConfidence = peaks.reduce((sum, peak) => sum + (peak.confidence || 50), 0);
        return Math.round(totalConfidence / peaks.length);
    },

    // Convert API result to preview data format
    convertToPreviewData(apiResult) {
        const currentData = window.getCurrentData ? window.getCurrentData() : null;
        
        if (!currentData) {
            return {
                voltage: [-0.5, -0.3, -0.1, 0.1, 0.3, 0.5],
                current: [-2, 1, 3, 1, -1, -2],
                peaks: []
            };
        }

        // Use actual data for preview
        const previewData = {
            voltage: currentData.voltage,
            current: currentData.current,
            peaks: []
        };

        // Convert peaks to preview format
        if (apiResult.peaks) {
            previewData.peaks = apiResult.peaks.map(peak => ({
                x: peak.voltage,
                y: peak.current,
                type: peak.type
            }));
        }

        return previewData;
    },

    // Update results UI
    updateResultsUI(grid, results, method) {
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
