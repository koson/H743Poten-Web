// Peak detection utilities
const detectionManager = {
    results: {},
    
    // Show details in new tab
    showDetails(method, results) {
        // Multi-file support: if window.currentDataFiles exists, send array of objects with filename
        let dataToSend, peaksToSend;
        if (window.currentDataFiles && Array.isArray(window.currentDataFiles) && window.currentDataFiles.length > 0) {
            dataToSend = window.currentDataFiles.map((file, idx) => ({
                voltage: file.voltage,
                current: file.current,
                filename: file.filename || file.name || `Trace ${idx+1}`
            }));
            // ถ้า results.peaks เป็น array of array (multi-file) ให้ใช้ตรง ๆ
            if (Array.isArray(results.peaks) && Array.isArray(results.peaks[0])) {
                peaksToSend = results.peaks;
            } else if (Array.isArray(results.peaks)) {
                // ถ้าเป็น array of object (single-file) ให้ wrap เป็น array of array
                peaksToSend = [results.peaks];
                // ถ้ามีไฟล์หลายตัว แต่ peaks เป็น array เดียว ให้กระจายไปไฟล์แรก
                if (window.currentDataFiles.length > 1) {
                    peaksToSend = [results.peaks, ...new Array(window.currentDataFiles.length - 1).fill([])];
                }
            } else {
                peaksToSend = window.currentDataFiles.map(() => []);
            }
        } else {
            // Single file fallback
            const currentData = window.getCurrentData ? window.getCurrentData() : null;
            if (!currentData) {
                alert('No data available for analysis');
                return;
            }
            dataToSend = {
                ...results,
                voltage: currentData.voltage,
                current: currentData.current,
                filename: currentData.filename || currentData.name || 'Trace 1',
                previewData: results.previewData || {
                    voltage: currentData.voltage,
                    current: currentData.current,
                    peaks: []
                }
            };
            peaksToSend = results.peaks || [];
        }

        console.log('Creating analysis session for method:', method);
        console.log('Results:', results);
        console.log('Data to send:', dataToSend);
        console.log('Peaks to send:', peaksToSend);

        fetch('/peak_detection/create_analysis_session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                peaks: peaksToSend,
                data: dataToSend,
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
        // ใช้ข้อมูลไฟล์ preview (ล่าสุด) เท่านั้น
        let previewData = null;
        if (window.currentDataFiles && window.currentDataFiles.length > 0) {
            const lastIdx = window.currentDataFiles.length - 1;
            previewData = {
                voltage: window.currentDataFiles[lastIdx].voltage,
                current: window.currentDataFiles[lastIdx].current
            };
        } else if (window.getCurrentData) {
            previewData = window.getCurrentData();
        }
        console.log('previewData for detection:', previewData);
        if (!previewData || !previewData.voltage || !previewData.current) {
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
        this.performDetection(grid, method, previewData);
    },
    
    // Get grid ID for method
    getGridId(method) {
        return {
            'ml': 'ml-analysis',
            'prominence': 'traditional-analysis',
            'derivative': 'hybrid-analysis'
        }[method];
    }, // Added comma here

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
        const startTime = performance.now(); // Track actual time
        try {
            console.log(`[${method}] Starting API call...`);
            // Multi-file: ถ้ามี currentDataFiles หลายไฟล์ ให้ส่ง dataFiles array ไป backend
            let payload;
            if (window.currentDataFiles && Array.isArray(window.currentDataFiles) && window.currentDataFiles.length > 0) {
                // Process all files - baseline detection is now fast with progress tracking
                const filesToProcess = window.currentDataFiles;
                payload = {
                    dataFiles: filesToProcess.map(f => ({
                        voltage: f.voltage,
                        current: f.current,
                        filename: f.filename || f.name || ''
                    }))
                };
                console.log(`[${method}] Sending multi-file payload with ${payload.dataFiles.length} files (limited from ${window.currentDataFiles.length})`);
            } else {
                payload = {
                    voltage: data.voltage,
                    current: data.current
                };
                console.log(`[${method}] Sending single-file payload`);
            }
            // Call backend peak detection API
            console.log(`[${method}] Making API call to /peak_detection/get-peaks/${method}`);
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minute timeout for large datasets
            
            const response = await fetch(`/peak_detection/get-peaks/${method}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);

            console.log(`[${method}] API response status:`, response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`[${method}] API error response:`, errorText);
                throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
            }

            const result = await response.json();
            console.log(`[${method}] API result:`, result);
            
            // Calculate actual processing time
            const endTime = performance.now();
            const actualProcessingTime = ((endTime - startTime) / 1000).toFixed(1); // Convert to seconds
            console.log(`[${method}] Actual processing time: ${actualProcessingTime}s`);
            
            if (result.success) {
                // Add actual processing time to result
                result.actualProcessingTime = parseFloat(actualProcessingTime);
                this.completeDetection(method, result);
            } else {
                throw new Error(result.error || 'Detection failed');
            }
        } catch (error) {
            console.error(`[${method}] Detection error:`, error);
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
        console.log(`🔍 [DEBUG] CompleteDetection called for ${method}`);
        console.log(`🔍 [DEBUG] API Result:`, apiResult);
        
        let results;
        if (apiResult) {
            console.log(`🔍 [DEBUG] Processing API result for ${method}`);
            console.log(`🔍 [DEBUG] API Result keys:`, Object.keys(apiResult));
            console.log(`🔍 [DEBUG] API Result full object:`, apiResult);
            
            // Debug baseline information
            if (apiResult.baseline) {
                console.log(`📊 [DEBUG] Baseline data in API result:`, {
                    full_length: apiResult.baseline.full?.length,
                    forward_length: apiResult.baseline.forward?.length,
                    reverse_length: apiResult.baseline.reverse?.length,
                    segment_info: apiResult.baseline.segment_info
                });
            } else {
                console.log(`❌ [DEBUG] No baseline data found in API result`);
            }
            
            // Multi-file: peaks เป็น array of array (แต่ละไฟล์)
            let peaksArr = Array.isArray(apiResult.peaks) ? apiResult.peaks : [];
            // ถ้าเป็น single-file (array of object) ให้ wrap เป็น array of array
            if (peaksArr.length > 0 && !Array.isArray(peaksArr[0])) {
                peaksArr = [peaksArr];
            }
            // Confidence: เฉลี่ยทุกไฟล์
            let allPeaks = peaksArr.flat();
            let confidence = this.calculateAverageConfidence(allPeaks);
            // Processing time: ใช้เวลาจริงจาก API call
            let processingTime = apiResult.actualProcessingTime || 0.5;
            // Preview: ใช้ไฟล์แรก (หรือไฟล์ที่เลือก)
            // Flatten peaks array เพื่อให้ convertToPreviewData ใช้ได้
            const flatPeaks = peaksArr.flat();
            
            let previewData = this.convertToPreviewData({
                ...apiResult,
                peaks: flatPeaks  // ใส่ peaks หลัง ...apiResult เพื่อ override
            });
            
            console.log(`📊 [DEBUG] Preview data for ${method}:`, previewData);
            
            results = {
                peaks: peaksArr,
                confidence,
                processingTime,
                previewData
            };
        } else {
            // Fall back to mock results
            results = {
                peaks: [
                    [
                        { x: -0.1, y: 3, type: 'oxidation' },
                        { x: 0.3, y: -1, type: 'reduction' }
                    ]
                ],
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
        console.log('[convertToPreviewData] Input apiResult:', apiResult);
        
        // Show only one file for preview (first file selected)
        let voltage = [], current = [], previewPeaks = [];
        if (window.currentDataFiles && window.currentDataFiles.length > 0) {
            const firstIdx = 0; // Show first file instead of last
            voltage = window.currentDataFiles[firstIdx].voltage;
            current = window.currentDataFiles[firstIdx].current;
            console.log('[convertToPreviewData] Using currentDataFiles[0], voltage length:', voltage?.length, 'current length:', current?.length);
            
            // Handle multi-file peak results (peaks is array of arrays)
            if (apiResult && apiResult.peaks) {
                let peaksToProcess = [];
                
                if (Array.isArray(apiResult.peaks)) {
                    // If peaks is array of arrays (multi-file), take first file
                    if (apiResult.peaks.length > 0 && Array.isArray(apiResult.peaks[0])) {
                        peaksToProcess = apiResult.peaks[0] || []; // First file's peaks
                        console.log('[convertToPreviewData] Multi-file detected, using first file peaks:', peaksToProcess.length);
                    } 
                    // If peaks is flat array (single file or flattened), filter by fileIdx
                    else {
                        peaksToProcess = apiResult.peaks.filter(p => (p.fileIdx === undefined || p.fileIdx === firstIdx));
                        console.log('[convertToPreviewData] Flat array detected, filtered peaks:', peaksToProcess.length);
                    }
                }
                
                // Map peaks to preview format
                previewPeaks = peaksToProcess.map(peak => ({ 
                    x: peak.voltage || peak.x || peak.potential || peak.E, 
                    y: peak.current || peak.y || peak.I || peak.i, 
                    type: peak.type || peak.peak_type || 'unknown'
                }));
                console.log('[convertToPreviewData] Mapped peaks:', previewPeaks);
            }
        } else if (window.currentData && window.currentData.voltage && window.currentData.current) {
            voltage = window.currentData.voltage;
            current = window.currentData.current;
            if (apiResult && Array.isArray(apiResult.peaks)) {
                previewPeaks = apiResult.peaks.map(peak => ({ x: peak.voltage, y: peak.current, type: peak.type }));
            }
        } else {
            voltage = [-0.5, -0.3, -0.1, 0.1, 0.3, 0.5];
            current = [-2, 1, 3, 1, -1, -2];
        }
        
        return {
            voltage,
            current,
            peaks: previewPeaks
        };
    },

    // Update results UI
    updateResultsUI(grid, results, method) {
        // Use previewData for this card only (not global results)
        const previewData = results.previewData;
        // Peak count = จำนวน peak ใน previewData เท่านั้น
        grid.querySelector('.peaks-count').textContent = previewData.peaks ? previewData.peaks.length : 0;
        // Confidence = เฉลี่ย confidence ของ peak ใน previewData (หรือ 0)
        let conf = 0;
        if (previewData.peaks && previewData.peaks.length > 0) {
            conf = Math.round(previewData.peaks.reduce((sum, p) => sum + (p.confidence || 50), 0) / previewData.peaks.length);
        }
        grid.querySelector('.confidence-value').textContent = conf + '%';
        // Processing time: ใช้ results.processingTime เดิม
        grid.querySelector('.processing-time').textContent = results.processingTime + 's';
        // Update preview graph
        const previewCanvas = grid.querySelector('.preview-canvas');
        if (previewCanvas) {
            console.log(`[${method}] Found preview canvas, data:`, previewData);
            const container = previewCanvas.parentElement;
            if (container) {
                previewCanvas.width = container.clientWidth;
                previewCanvas.height = container.clientHeight;
                console.log(`[${method}] Canvas dimensions: ${previewCanvas.width}x${previewCanvas.height}`);
                const ctx = previewCanvas.getContext('2d');
                if (ctx) {
                    if (window.previewGraphUtils) {
                        console.log(`[${method}] Drawing graph with data:`, {
                            voltage_length: previewData.voltage?.length,
                            current_length: previewData.current?.length,
                            peaks_count: previewData.peaks?.length
                        });
                        window.previewGraphUtils.drawGraph(previewCanvas, previewData);
                        console.log(`[${method}] Graph drawing completed`);
                    } else {
                        console.error(`[${method}] previewGraphUtils not available`);
                    }
                } else {
                    console.error(`[${method}] Canvas context not available`);
                }
            } else {
                console.error(`[${method}] Canvas container not found`);
            }
        } else {
            console.error(`[${method}] Preview canvas not found in grid`);
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
        const notification = `Detected ${previewData.peaks ? previewData.peaks.length : 0} peaks with ${conf}% confidence`;
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
