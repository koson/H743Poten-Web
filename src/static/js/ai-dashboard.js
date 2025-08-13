// AI Dashboard JavaScript

// Initialize various charts when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    initPeakChart();
    initConcentrationChart();
    initQualityGauge();
});

// Show processing indicator when starting analysis
function startAnalysis() {
    document.getElementById('processingIndicator').style.display = 'flex';
    fetchAnalysisData();
}

// Fetch data from AI backend
async function fetchAnalysisData() {
    try {
        // Make API calls in parallel for efficiency
        const [peakData, concentrationData, qualityData, insightsData] = await Promise.all([
            fetch('/ai/api/analyze'),
            fetch('/ai/api/predict-concentration'),
            fetch('/ai/api/enhance-signal'),
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

    window.peakChart.data.labels = data.voltage || [];
    window.peakChart.data.datasets[0].data = data.current || [];
    window.peakChart.update();
}

// Update Concentration Chart
function updateConcentrationChart(data) {
    if (!data || !window.concentrationChart) return;

    window.concentrationChart.data.datasets[0].data = data.calibration || [];
    window.concentrationChart.data.datasets[1].data = data.sample || [];
    window.concentrationChart.update();
}

// Update Quality Gauge
function updateQualityGauge(data) {
    if (!data || !window.qualityGauge) return;

    const quality = data.quality || 0;
    window.qualityGauge.data.datasets[0].data = [quality, 100 - quality];
    window.qualityGauge.update();
}

// Update Insights
function updateInsights(data) {
    // Update insights cards with new data
}

// Update Metrics
function updateMetrics(peakData, concentrationData, qualityData) {
    // Update metric cards with new values
}

// Show error message
function showError(message) {
    // Implement error display logic
}

// Show demo for specific component
function showDemo(componentType) {
    // Implement demo functionality
}
