// AI Dashboard JavaScript

// Initialize various charts when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    initPeakChart();
    initConcentrationChart();
    initQualityGauge();
    
    // Add toast container for demo messages
    const toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container';
    document.body.appendChild(toastContainer);
});

// Show processing indicator when starting analysis
function startAnalysis() {
    document.getElementById('processingIndicator').style.display = 'flex';
    fetchAnalysisData();
}

// Fetch data from AI backend
async function fetchAnalysisData() {
    try {
        // Generate sample data
        const voltage = Array.from({length: 100}, (_, i) => -0.5 + i * 0.01);
        const current = voltage.map(v => 
            Math.sin(v * 10) * Math.exp(-Math.abs(v)) * 2 + 
            Math.sin(v * 5) * 0.5
        );

        console.log('Sending analyze request with data:', { voltage, current });

        // Make API calls in parallel for efficiency
        const [peakData, concentrationData, qualityData, insightsData] = await Promise.all([
            fetch('/ai/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ voltage, current })
            }),
            fetch('/ai/api/predict-concentration', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    peaks: [
                        { voltage: 0.85, current: 2.3, width: 0.15 }
                    ]
                })
            }),
            fetch('/ai/api/enhance-signal', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    signal: Array.from({length: 100}, (_, i) => Math.sin(i * 0.1))
                })
            }),
            fetch('/ai/api/status')
        ]);

        // Process results
        updateDashboard(
            await peakData.json(),
            await concentrationData.json(),
            await qualityData.json(),
            await insightsData.json()
        );
    } catch (error) {
        console.error('Error fetching analysis data:', error);
        showError('Failed to fetch analysis data');
    } finally {
        document.getElementById('processingIndicator').style.display = 'none';
    }
}

// Initialize Peak Analysis Chart
function initPeakChart() {
    const ctx = document.getElementById('peakChart').getContext('2d');
    window.peakChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [], // Will be populated with voltage values
            datasets: [{
                label: 'Current Response',
                data: [], // Will be populated with current values
                borderColor: '#007bff',
                fill: false,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                zoom: {
                    zoom: {
                        wheel: {
                            enabled: true
                        },
                        mode: 'xy'
                    },
                    pan: {
                        enabled: true,
                        mode: 'xy'
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Potential (V)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Current (μA)'
                    }
                }
            }
        }
    });
}

// Initialize Concentration Chart
function initConcentrationChart() {
    const ctx = document.getElementById('concentrationChart').getContext('2d');
    window.concentrationChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Calibration Points',
                data: [], // Will be populated with calibration data
                backgroundColor: '#007bff'
            }, {
                label: 'Unknown Sample',
                data: [], // Will be populated with sample data
                backgroundColor: '#dc3545'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Concentration (μM)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Peak Current (μA)'
                    }
                }
            }
        }
    });
}

// Initialize Quality Gauge Chart
function initQualityGauge() {
    const ctx = document.getElementById('qualityGauge').getContext('2d');
    window.qualityGauge = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Quality Score'],
            datasets: [{
                data: [92, 8], // Quality score and remaining
                backgroundColor: ['#28a745', '#e9ecef']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            circumference: 180,
            rotation: 270,
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// Update dashboard with new data
function updateDashboard(peakData, concentrationData, qualityData, insightsData) {
    updatePeakChart(peakData);
    updateConcentrationChart(concentrationData);
    updateQualityGauge(qualityData);
    updateInsights(insightsData);
    updateMetrics(peakData, concentrationData, qualityData);
}

// Update Peak Analysis Chart
function updatePeakChart(data) {
    if (!data || !window.peakChart) return;

    // Convert voltage and current arrays into xy points
    const points = data.voltage.map((v, i) => ({
        x: v,
        y: data.current[i]
    }));

    // Update voltammogram data
    window.peakChart.data.datasets = [{
        label: 'Current Response',
        data: points,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4
    }];

    // Add peak markers if data.peak_analysis exists and has peak_data
    const peakPoints = data.peak_analysis?.peak_data || [];
    if (peakPoints.length > 0) {
        window.peakChart.data.datasets.push({
            label: 'Detected Peaks',
            data: peakPoints.map(peak => ({
                x: peak.voltage,
                y: peak.current
            })),
            backgroundColor: '#dc3545',
            borderColor: '#dc3545',
            pointRadius: 6,
            pointHoverRadius: 8,
            type: 'scatter'
        });
    }

    window.peakChart.update();
}

// Update Concentration Chart
function updateConcentrationChart(data) {
    if (!data || !window.concentrationChart) return;

    const { predicted_concentration, calibration_points, r_squared } = data;

    // Update calibration points
    if (calibration_points && Array.isArray(calibration_points)) {
        // Convert calibration points if needed
        const points = calibration_points.map(p => ({
            x: typeof p[0] === 'number' ? p[0] : p.x,
            y: typeof p[1] === 'number' ? p[1] : p.y
        }));
        
        window.concentrationChart.data.datasets[0].data = points;

        // Generate fit line
        const minConc = Math.min(...points.map(p => p.x));
        const maxConc = Math.max(...points.map(p => p.x));
        
        // Linear fit
        const fitLine = [
            { x: minConc, y: minConc * points[0].y / points[0].x },
            { x: maxConc, y: maxConc * points[0].y / points[0].x }
        ];
        window.concentrationChart.data.datasets[1].data = fitLine;

        // Add predicted point
        if (predicted_concentration) {
            const predictedY = predicted_concentration * points[0].y / points[0].x;
            window.concentrationChart.data.datasets[2].data = [{
                x: predicted_concentration,
                y: predictedY
            }];
        }
    }

    window.concentrationChart.update();
}

// Update Quality Gauge
function updateQualityGauge(data) {
    if (!data || !window.qualityGauge) return;

    const quality = data.quality?.quality_score || 0;
    const qualityPercent = Math.round(quality * 100);
    
    window.qualityGauge.data.datasets[0].data = [qualityPercent, 100 - qualityPercent];
    window.qualityGauge.update();

    // Update quality metrics display
    const metricsContainer = document.querySelector('#quality .metrics-grid');
    if (metricsContainer) {
        metricsContainer.innerHTML = `
            <div class="metric-card">
                <div class="metric-value">${qualityPercent}%</div>
                <div class="metric-label">Overall Quality</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${data.quality?.snr_db?.toFixed(1) || 'N/A'} dB</div>
                <div class="metric-label">Signal-to-Noise</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${(data.quality?.baseline_drift * 100).toFixed(3) || 'N/A'}%</div>
                <div class="metric-label">Drift</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${quality > 0.8 ? 'Excellent' : quality > 0.6 ? 'Good' : 'Poor'}</div>
                <div class="metric-label">Baseline Stability</div>
            </div>
        `;
    }
}

// Update Insights
function updateInsights(data) {
    if (!data || !data.insights) return;

    const insightsContainer = document.querySelector('#insights .insights-container');
    if (!insightsContainer) return;

    // Clear existing insights
    insightsContainer.innerHTML = '';

    // Add new insights
    if (Array.isArray(data.insights)) {
        data.insights.forEach(insight => {
            const insightCard = document.createElement('div');
            insightCard.className = 'insight-card';
            insightCard.innerHTML = `
                <div class="insight-title">${insight.title}</div>
                <div>${insight.description}</div>
                ${insight.recommendations ? 
                    `<div class="insight-recommendations">
                        ${insight.recommendations.map(r => `<div>• ${r}</div>`).join('')}
                    </div>` : 
                    ''}
            `;
            insightsContainer.appendChild(insightCard);
        });
    }
}

// Update Metrics
function updateMetrics(peakData, concentrationData, qualityData) {
    // Update all metric cards with data from analysis results
    const metrics = {
        'peaks-detected': peakData?.peak_analysis?.peaks_detected || 0,
        'classification-accuracy': ((peakData?.peak_analysis?.classification_confidence || 0) * 100).toFixed(1) + '%',
        'processing-time': ((peakData?.processing_time || 0) * 1000).toFixed(1) + ' ms',
        'primary-peak': (peakData?.peak_analysis?.peak_data?.[0]?.voltage || 0).toFixed(2) + ' V',
        
        'predicted-concentration': concentrationData?.predicted_concentration ? 
            (concentrationData.predicted_concentration * 1e6).toFixed(1) + ' μM' : 'N/A',
        'confidence-interval': concentrationData?.confidence_interval ? 
            '±' + ((concentrationData.confidence_interval[1] - concentrationData.confidence_interval[0]) * 1e6 / 2).toFixed(1) + ' μM' : 'N/A',
        'r-squared': concentrationData?.r_squared?.toFixed(3) || 'N/A',
        
        'quality-score': (qualityData?.quality?.quality_score * 100).toFixed(0) + '%',
        'snr': qualityData?.quality?.snr_db?.toFixed(1) + ' dB',
        'baseline-drift': (qualityData?.quality?.baseline_drift * 100).toFixed(3) + '%'
    };

    // Update each metric display
    Object.entries(metrics).forEach(([id, value]) => {
        updateMetricValue(id, value);
    });
}

// Helper to update metric value
function updateMetricValue(id, value) {
    const element = document.querySelector(`[data-metric="${id}"]`);
    if (element) {
        element.textContent = value;
    }
}

// Show error message
function showError(message) {
    const toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) return;

    const errorToast = document.createElement('div');
    errorToast.className = 'error-toast';
    errorToast.innerHTML = `
        <div class="error-toast-content">
            <i class="fas fa-exclamation-circle"></i>
            <span>${message}</span>
        </div>
    `;
    
    toastContainer.appendChild(errorToast);
    
    // Remove after animation
    setTimeout(() => {
        errorToast.remove();
    }, 5000);
}

// Show demo for specific component
function showDemo(componentType) {
    const messages = {
        peak: "Peak Classifier activated! Real-time neural network analysis ready.",
        concentration: "Concentration Predictor loaded! Multi-model pipeline initialized.",
        signal: "Signal Processor active! Advanced filtering algorithms ready.",
        ai: "AI Intelligence system online! Expert knowledge database accessible."
    };
    
    const message = messages[componentType] || "Component activated!";
    const toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = 'demo-toast';
    toast.innerHTML = `
        <div class="demo-toast-content">
            <i class="fas fa-check-circle"></i>
            <span>${message}</span>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Remove after animation
    setTimeout(() => {
        toast.remove();
    }, 3000);
}
