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
            // แยก peaks ตามไฟล์: ถ้าแต่ละ peak มี fileIdx หรือ filename ให้ filter, ถ้าไม่มีก็ map เป็น []
            if (Array.isArray(results.peaks) && results.peaks.length > 0) {
                // ถ้าแต่ละ peak มี fileIdx หรือ filename ให้แยกตามนั้น
                if (results.peaks[0].fileIdx !== undefined) {
                    peaksToSend = window.currentDataFiles.map((f, i) => results.peaks.filter(p => p.fileIdx === i));
                } else if (results.peaks[0].filename) {
                    peaksToSend = window.currentDataFiles.map((f, i) => results.peaks.filter(p => p.filename === (f.filename || f.name || `Trace ${i+1}`)));
                } else {
                    // fallback: ถ้าแยกไม่ได้ ให้ map เป็น [] ยกเว้นไฟล์แรก
                    peaksToSend = window.currentDataFiles.map((f, i) => i === 0 ? (results.peaks || []) : []);
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
            // Multi-file: ถ้ามี currentDataFiles หลายไฟล์ ให้ส่ง dataFiles array ไป backend
            let payload;
            if (window.currentDataFiles && Array.isArray(window.currentDataFiles) && window.currentDataFiles.length > 0) {
                payload = {
                    dataFiles: window.currentDataFiles.map(f => ({
                        voltage: f.voltage,
                        current: f.current,
                        filename: f.filename || f.name || ''
                    }))
                };
            } else {
                payload = {
                    voltage: data.voltage,
                    current: data.current
                };
            }
            // Call backend peak detection API
            const response = await fetch(`/peak_detection/get-peaks/${method}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
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
            // Multi-file: peaks เป็น array of array (แต่ละไฟล์)
            let peaksArr = Array.isArray(apiResult.peaks) ? apiResult.peaks : [];
            // ถ้าเป็น single-file (array of object) ให้ wrap เป็น array of array
            if (peaksArr.length > 0 && !Array.isArray(peaksArr[0])) {
                peaksArr = [peaksArr];
            }
            // Confidence: เฉลี่ยทุกไฟล์
            let allPeaks = peaksArr.flat();
            let confidence = this.calculateAverageConfidence(allPeaks);
            // Processing time: ประเมินจากจำนวนไฟล์ (mockup: 0.1s/ไฟล์)
            let processingTime = Math.max(0.5, 0.1 * peaksArr.length);
            // Preview: ใช้ไฟล์แรก (หรือไฟล์ที่เลือก)
            let previewData = this.convertToPreviewData({
                peaks: peaksArr[0] || [],
                ...apiResult
            });
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
        // Show only one file for preview (last file selected)
        let voltage = [], current = [], previewPeaks = [];
        if (window.currentDataFiles && window.currentDataFiles.length > 0) {
            const lastIdx = window.currentDataFiles.length - 1;
            voltage = window.currentDataFiles[lastIdx].voltage;
            current = window.currentDataFiles[lastIdx].current;
            // Filter peaks for this file only (if possible)
            if (apiResult && Array.isArray(apiResult.peaks)) {
                // สมมุติว่าแต่ละ peak มี fileIdx ถ้า backend ส่งมา (ถ้าไม่มีจะโชว์ทุก peak)
                previewPeaks = apiResult.peaks.filter(p => (p.fileIdx === undefined || p.fileIdx === lastIdx))
                    .map(peak => ({ x: peak.voltage, y: peak.current, type: peak.type }));
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
                peaksToSend = Array.isArray(results.peaks) ? results.peaks : [];
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
