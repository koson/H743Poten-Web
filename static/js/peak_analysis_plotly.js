// Plotly.js logic for Peak Analysis Details page
// This script replaces Chart.js logic in peak_analysis.html

// Wait for DOM and Plotly to be ready
function ensurePlotlyReady(callback) {
    if (window.Plotly) {
        callback();
    } else {
        var s = document.createElement('script');
        s.src = 'https://cdn.plot.ly/plotly-2.26.0.min.js';
        s.onload = callback;
        document.head.appendChild(s);
    }
}

function renderPeakAnalysisPlot(chartData, peaksData, methodNameStr) {
    const plotDiv = document.getElementById('plotly-peak-graph');
    if (!plotDiv) return;

    // Defensive: ensure peaksData is always an array
    let peaksArr = [];
    if (Array.isArray(peaksData)) {
        peaksArr = peaksData;
    } else if (peaksData && typeof peaksData === 'object') {
        // Sometimes Flask may render as object if no peaks
        peaksArr = Object.values(peaksData);
    }

    // Main CV trace
    const cvTrace = {
        x: chartData.voltage,
        y: chartData.current,
        mode: 'lines',
        name: 'CV Data',
        line: { color: '#0d6efd', width: 2 },
        hoverinfo: 'x+y',
    };

    // Peak markers
    const peakTrace = {
        x: peaksArr.map(p => p.x !== undefined ? p.x : p.voltage),
        y: peaksArr.map(p => p.y !== undefined ? p.y : p.current),
        mode: 'markers+text',
        name: 'Peaks',
        marker: {
            size: 12,
            color: peaksArr.map(p => p.type === 'oxidation' ? '#dc3545' : '#198754'),
            line: { width: 2, color: '#fff' }
        },
        text: peaksArr.map(p => p.type === 'oxidation' ? 'Ox' : 'Red'),
        textposition: 'top center',
        hovertemplate: '%{text} peak<br>V: %{x:.3f} V<br>i: %{y:.3f} µA<extra></extra>',
    };

    // Add baseline traces using the utility function from cv_measurement.js
        // Baseline traces (forward/reverse) + vertical lines to peaks
        let baselineTraces = [];
        if (typeof getBaselineTraces === 'function') {
            baselineTraces = getBaselineTraces(chartData.voltage, chartData.current, chartData.direction, peaksArr, 0.1);
        }

    // Layout
    const layout = {
        title: methodNameStr ? `Peak Analysis: ${methodNameStr}` : 'Peak Analysis',
        xaxis: {
            title: 'Voltage (V)',
            tickformat: '.3f',
            zeroline: false,
            showgrid: true,
            gridcolor: '#f0f0f0',
        },
        yaxis: {
            title: 'Current (µA)',
            tickformat: '.3f',
            zeroline: false,
            showgrid: true,
            gridcolor: '#f0f0f0',
        },
        margin: { t: 50, l: 60, r: 30, b: 60 },
        legend: { orientation: 'h', y: -0.2 },
        hovermode: 'closest',
        height: 500,
    };

    // Combine all traces: CV data, peaks, and baseline traces
        const allTraces = [cvTrace, peakTrace, ...baselineTraces];
    
    Plotly.newPlot(plotDiv, allTraces, layout, {responsive: true});

    // Helper function to infer scan direction from voltage pattern (for CV)
    function inferDirectionFromVoltage(voltage) {
        if (!voltage || voltage.length < 3) return [];
        
        const direction = [];
        let isIncreasing = true;
        
        for (let i = 0; i < voltage.length; i++) {
            if (i > 0) {
                const diff = voltage[i] - voltage[i-1];
                if (Math.abs(diff) > 0.001) { // Threshold to ignore noise
                    if (diff > 0 && !isIncreasing) {
                        isIncreasing = true; // Switch to forward
                    } else if (diff < 0 && isIncreasing) {
                        isIncreasing = false; // Switch to reverse
                    }
                }
            }
            direction.push(isIncreasing ? 'forward' : 'reverse');
        }
        
        return direction;
    }
    
    // Helper function to add baseline to existing plot
    function addBaselineToExistingPlot() {
        const plotDiv = document.getElementById('plotly-peak-graph');
        if (!plotDiv || !plotDiv.data) return;
        
        let directionData = chartData.direction;
        if (!directionData && chartData.voltage && chartData.voltage.length > 2) {
            directionData = inferDirectionFromVoltage(chartData.voltage);
        }
        
        if (directionData && typeof getBaselineTraces === 'function') {
            const baselineTraces = getBaselineTraces(chartData.voltage, chartData.current, directionData);
            if (baselineTraces.length > 0) {
                console.log('[BASELINE] Adding baseline traces to existing plot:', baselineTraces.length);
                Plotly.addTraces(plotDiv, baselineTraces);
            }
        }
    }

    // Add click event for peak selection
    plotDiv.on('plotly_click', function(eventData) {
        if (!eventData || !eventData.points || eventData.points.length === 0) return;
        const pt = eventData.points[0];
        // Only respond to peak marker clicks (trace 1)
        if (pt.curveNumber === 1) {
            // Find peak index
            const peakIndex = pt.pointIndex;
            const peak = peaksArr[peakIndex];
            showPeakDetails(peak);
        }
    });
}

// Show peak details in .peak-details panel
function showPeakDetails(peak) {
    const detailsDiv = document.querySelector('.peak-details');
    if (!detailsDiv || !peak) return;
    const v = (peak.x !== undefined ? peak.x : peak.voltage);
    const i = (peak.y !== undefined ? peak.y : peak.current);
    let peakHeight = '';
    if (peak.height !== undefined) {
        peakHeight = `<div><span class='value-label'>Peak Height:</span> <span class='value'>${peak.height.toFixed(3)} µA</span></div>`;
    }
    detailsDiv.innerHTML = `
        <h6>Peak Details</h6>
        <div><span class='value-label'>Type:</span> <span class='value'>${peak.type}</span></div>
        <div><span class='value-label'>Voltage:</span> <span class='value'>${v.toFixed(3)} V</span></div>
        <div><span class='value-label'>Current:</span> <span class='value'>${i.toFixed(3)} µA</span></div>
        ${peakHeight}
    `;
}

// Expose for HTML
window.renderPeakAnalysisPlot = renderPeakAnalysisPlot;
window.ensurePlotlyReady = ensurePlotlyReady;
