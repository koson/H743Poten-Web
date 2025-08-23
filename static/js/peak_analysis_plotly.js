// Plotly.js logic for Peak Analysis Details page
// This script replaces Chart.js logic in peak_analysis.html

// ===== BASELINE ANALYSIS FUNCTIONS (migrated from C# CVAnalyzer) =====

// Linear Regression Function
function linearRegression(points) {

    // console.log('[REGRESSION] linearRegression(points)', { points });
    if (!points || points.length < 2) {
        console.warn('[REGRESSION] Insufficient data points:', points?.length || 0);
        return { slope: 0, intercept: 0, rSquared: 0 };
    }

    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
    const n = points.length;

    for (const point of points) {
        if (!isFinite(point.voltage) || !isFinite(point.current)) {
            console.warn('[REGRESSION] Non-finite data point:', point);
            continue;
        }
        sumX += point.voltage;
        sumY += point.current;
        sumXY += point.voltage * point.current;
        sumX2 += point.voltage * point.voltage;
    }

    const denominator = n * sumX2 - sumX * sumX;
    
    if (Math.abs(denominator) < 1e-12) {
        console.warn('[REGRESSION] Near-zero denominator, voltage variance too small');
        return { slope: 0, intercept: sumY / n, rSquared: 0 };
    }

    const slope = (n * sumXY - sumX * sumY) / denominator;
    const intercept = (sumY - slope * sumX) / n;
    
    // Calculate R²
    const meanY = sumY / n;
    let ssRes = 0, ssTot = 0;
    
    for (const point of points) {
        if (!isFinite(point.voltage) || !isFinite(point.current)) continue;
        
        const predicted = slope * point.voltage + intercept;
        const residual = point.current - predicted;
        const deviation = point.current - meanY;
        
        ssRes += residual * residual;
        ssTot += deviation * deviation;
    }
    
    let rSquared = 0;
    if (ssTot > 1e-12) {
        rSquared = Math.max(0, 1 - (ssRes / ssTot));
    }
    
    // Validate results
    if (!isFinite(slope) || !isFinite(intercept) || !isFinite(rSquared)) {
        console.warn('[REGRESSION] Non-finite results:', { slope, intercept, rSquared });
        return { slope: 0, intercept: meanY, rSquared: 0 };
    }

    // console.log('[REGRESSION] linearRegression(points)', { points, slope, intercept, rSquared });

    return { slope, intercept, rSquared };
}

// Check if a region has linear current-voltage relationship
function isLinearRegion(region, tolerance = 1e-5) {
    if (region.length < 10) return false;

    try {
        const regression = linearRegression(region);
        const rSquared = regression.rSquared; // Use R² directly from regression
        
        // Calculate slope consistency
        const slopes = [];
        for (let i = 1; i < region.length; i++) {
            const voltDiff = region[i].voltage - region[i-1].voltage;
            const currDiff = region[i].current - region[i-1].current;
            if (Math.abs(voltDiff) > 1e-6) {
                const slope = currDiff / voltDiff;
                if (isFinite(slope)) slopes.push(slope);
            }
        }
        
        if (slopes.length < 5) return false;
        
        const meanSlope = slopes.reduce((sum, s) => sum + s, 0) / slopes.length;
        const slopeVariance = slopes.reduce((sum, s) => sum + Math.pow(s - meanSlope, 2), 0) / slopes.length;
        const slopeStdDev = Math.sqrt(slopeVariance);
        const slopeCV = Math.abs(meanSlope) > 1e-10 ? slopeStdDev / Math.abs(meanSlope) : Infinity;
        
        // Check current variability
        const currentRange = Math.max(...region.map(p => p.current)) - Math.min(...region.map(p => p.current));
        const meanAbsCurrent = region.reduce((sum, p) => sum + Math.abs(p.current), 0) / region.length;
        const currentVariability = meanAbsCurrent > 0 ? currentRange / meanAbsCurrent : 0;
        
        // Relaxed but reasonable criteria for real CV data
        const rSquaredThreshold = 0.85;       // More reasonable for real data
        const slopeCVThreshold = 0.5;         // Allow some slope variation
        const currentVariabilityThreshold = 1.0; // Allow reasonable current variation
        
        const hasGoodLinearity = rSquared > rSquaredThreshold;
        const hasReasonableSlope = slopeCV < slopeCVThreshold;
        const hasStableCurrent = currentVariability < currentVariabilityThreshold;
        
        const isLinear = hasGoodLinearity && hasReasonableSlope && hasStableCurrent;
        
        // Log all attempted regions for debugging
        console.log(`[LINEARITY] Testing region ${region[0].voltage.toFixed(3)} to ${region[region.length-1].voltage.toFixed(3)}:`, {
            size: region.length,
            rSquared: rSquared.toFixed(4),
            slopeCV: slopeCV.toFixed(4),
            currentVar: currentVariability.toFixed(4),
            criteria: {
                r2OK: hasGoodLinearity,
                slopeOK: hasReasonableSlope, 
                currentOK: hasStableCurrent
            },
            result: isLinear
        });
        
        return isLinear;
        
    } catch (error) {
        // console.warn('[BASELINE] Error in linearity check:', error.message);
        return false;
    }
}

// Find all linear segments in the data
function findAllLinearSegments(data, minSegmentSize = 10) {
    if (!data || data.length < minSegmentSize) return [];
    
    const segments = [];
    const sortedData = data.slice().sort((a, b) => a.voltage - b.voltage);
    
    console.log(`[SEGMENTS] Analyzing ${sortedData.length} points for linear segments with relaxed criteria`);
    
    // Try different segment sizes systematically
    for (let startIdx = 0; startIdx <= sortedData.length - minSegmentSize; startIdx += 3) { // Skip every 3 points for efficiency
        for (let size = minSegmentSize; size <= Math.min(40, sortedData.length - startIdx); size += 3) {
            const endIdx = startIdx + size - 1;
            const segment = sortedData.slice(startIdx, endIdx + 1);
            
            // Pre-filter: basic requirements
            const voltageSpan = segment[segment.length-1].voltage - segment[0].voltage;
            if (voltageSpan < 0.015) continue; // Must span at least 15mV
            
            // console.log(`[SEGMENTS] Testing segment ${startIdx} to ${endIdx} (${segment[0].voltage.toFixed(3)} to ${segment[segment.length-1].voltage.toFixed(3)}V)`);
            
            if (isLinearRegion(segment)) {
                // Check for significant overlap with existing segments
                const overlapThreshold = 0.6;
                const hasSignificantOverlap = segments.some(existingSegment => {
                    const overlapStart = Math.max(segment[0].voltage, existingSegment.data[0].voltage);
                    const overlapEnd = Math.min(segment[segment.length-1].voltage, existingSegment.data[existingSegment.data.length-1].voltage);
                    const overlapSize = Math.max(0, overlapEnd - overlapStart);
                    const segmentSize = segment[segment.length-1].voltage - segment[0].voltage;
                    const overlapRatio = overlapSize / segmentSize;
                    return overlapRatio > overlapThreshold;
                });
                
                if (!hasSignificantOverlap) {
                    // Calculate quality metrics
                    const regression = linearRegression(segment);
                    const meanCurrent = segment.reduce((sum, p) => sum + p.current, 0) / segment.length;
                    let ssRes = 0, ssTot = 0;
                    
                    for (const point of segment) {
                        const predicted = regression.slope * point.voltage + regression.intercept;
                        ssRes += Math.pow(point.current - predicted, 2);
                        ssTot += Math.pow(point.current - meanCurrent, 2);
                    }
                    
                    const rSquared = ssTot > 0 ? (1 - (ssRes / ssTot)) : 0;
                    const currentRange = Math.max(...segment.map(p => p.current)) - Math.min(...segment.map(p => p.current));
                    const currentVariability = Math.abs(meanCurrent) > 1e-10 ? currentRange / Math.abs(meanCurrent) : 0;
                    const absSlope = Math.abs(regression.slope);
                    
                    // Quality score emphasizing R² and voltage span
                    const sizeBonus = Math.log(segment.length / minSegmentSize + 1);
                    const spanBonus = Math.min(voltageSpan / 0.05, 2.0); // Bonus for spans >= 50mV
                    const stabilityBonus = 1.0 / (1.0 + currentVariability);
                    // Prefer flatter (baseline-like) segments: penalize larger slopes using a soft factor
                    const flatnessBonus = 1.0 / (1.0 + absSlope);
                    const quality = rSquared * sizeBonus * spanBonus * stabilityBonus * flatnessBonus;
                    
                    segments.push({
                        data: segment,
                        startVoltage: segment[0].voltage,
                        endVoltage: segment[segment.length-1].voltage,
                        size: segment.length,
                        rSquared,
                        regression,
                        absSlope,
                        voltageSpan,
                        currentRange,
                        currentVariability,
                        quality
                    });
                    
                    console.log(`[SEGMENTS] ✓ Added linear segment:`, {
                        startV: segment[0].voltage.toFixed(3),
                        endV: segment[segment.length-1].voltage.toFixed(3),
                        size: segment.length,
                        rSquared: rSquared.toFixed(4),
                        voltageSpan: voltageSpan.toFixed(3),
                        quality: quality.toFixed(4)
                    });
                }
            }
        }
    }
    
    // Sort segments by quality (best first)
    segments.sort((a, b) => b.quality - a.quality);
    
    console.log(`[SEGMENTS] Found ${segments.length} linear segments total`);
    
    // Show all segments for debugging
    segments.forEach((segment, index) => {
        console.log(`[SEGMENTS] Segment ${index + 1}:`, {
            startV: segment.startVoltage.toFixed(3),
            endV: segment.endVoltage.toFixed(3),
            size: segment.size,
            rSquared: segment.rSquared.toFixed(4),
            quality: segment.quality.toFixed(4)
        });
    });
    
    return segments;
}

// Select best baseline segment based on position relative to peaks
function selectBaselineSegment(segments, peakVoltage, direction = 'forward') {
    if (segments.length === 0) return null;
    
    console.log(`[BASELINE] Selecting ${direction} baseline from ${segments.length} segments, peak at ${peakVoltage.toFixed(3)}V`);
    
    let bestSegment = null;
    let bestScore = -1;
    
    for (const segment of segments) {
        let isValidPosition = false;
        let distanceFromPeak = 0;
        let positionScore = 0;
        // Hard filter: exclude segments with steep slope (baseline is expected to be near-flat)
        // Threshold chosen empirically in uA/V; adjust if needed per dataset scale.
        const steepSlope = Math.abs(segment.absSlope ?? segment.regression?.slope ?? 0) > 5; // >5 uA/V considered too steep for baseline
        if (steepSlope) {
            continue;
        }
        
        if (direction === 'forward') {
            // For forward baseline: segment should be before the oxidation peak
            const segmentEndVoltage = segment.endVoltage;
            distanceFromPeak = peakVoltage - segmentEndVoltage;
            
            if (distanceFromPeak > 0.02) { // allow >=20mV before peak
                isValidPosition = true;
                // Prefer ~80-120mV before peak, but be tolerant
                positionScore = 1.0 / (1.0 + Math.abs(distanceFromPeak - 0.10)); // Optimal ~100mV
            }
        } else {
            // For reverse baseline: segment should be after the reduction peak
            const segmentStartVoltage = segment.startVoltage;
            distanceFromPeak = segmentStartVoltage - peakVoltage;
            
            if (distanceFromPeak > 0.02) { // >=20mV after peak
                isValidPosition = true;
                positionScore = 1.0 / (1.0 + Math.abs(distanceFromPeak - 0.08)); // Optimal around 80mV after peak
            }
        }
        
        if (isValidPosition) {
            // Improved scoring with better balance
            const meanCurrent = Math.abs(segment.regression.intercept);
            const stabilityScore = meanCurrent > 1e-10 ? 
                1.0 / (1.0 + segment.currentRange / meanCurrent * 2) : 
                1.0 / (1.0 + segment.currentRange * 1000);
            
            // Add flatness score: the flatter the better (baseline should be straight/flat)
            const absSlope = Math.abs(segment.absSlope ?? segment.regression.slope);
            const flatnessScore = 1.0 / (1.0 + absSlope); // ~1 when slope ~0, decreases as slope increases
            
            // Weights: emphasize R² and flatness; keep some position and stability
            const rSquaredWeight = 0.45;
            const flatnessWeight = 0.35;
            const positionWeight = 0.15;
            const stabilityWeight = 0.05;
            
            const combinedScore = (segment.rSquared * rSquaredWeight) + 
                                (flatnessScore * flatnessWeight) +
                                (positionScore * positionWeight) + 
                                (stabilityScore * stabilityWeight);
            
            console.log(`[BASELINE] ${direction} segment candidate:`, {
                startV: segment.startVoltage.toFixed(3),
                endV: segment.endVoltage.toFixed(3),
                distFromPeak: distanceFromPeak.toFixed(3),
                rSquared: segment.rSquared.toFixed(4),
                positionScore: positionScore.toFixed(4),
                flatnessScore: flatnessScore.toFixed(4),
                absSlope: absSlope.toExponential(3),
                stabilityScore: stabilityScore.toFixed(4),
                combinedScore: combinedScore.toFixed(4)
            });
            
            if (combinedScore > bestScore) {
                bestScore = combinedScore;
                bestSegment = segment;
            }
        }
    }
    
    if (bestSegment) {
        console.log(`[BASELINE] Selected ${direction} baseline segment:`, {
            startV: bestSegment.startVoltage.toFixed(3),
            endV: bestSegment.endVoltage.toFixed(3),
            size: bestSegment.size,
            rSquared: bestSegment.rSquared.toFixed(4),
            score: bestScore.toFixed(4)
        });
    } else {
        console.warn(`[BASELINE] No suitable ${direction} baseline segment found`);
    }
    
    return bestSegment;
}

// Find linear baseline region in scan data before peak
function findLinearBaselineRegion(scanData, peakVoltage, direction = 'forward') {
    if (!scanData || scanData.length < 10) {
        console.warn(`[BASELINE] Insufficient ${direction} scan data:`, scanData.length);
        return [];
    }

    console.log(`[BASELINE] New segment-based approach for ${direction} scan, peak at ${peakVoltage.toFixed(3)}V`);
    
    // Step 1: Find all linear segments in the data
    const allSegments = findAllLinearSegments(scanData, 10);
    
    if (allSegments.length === 0) {
        console.warn(`[BASELINE] No linear segments found in ${direction} scan`);
        // Fallback to simple approach
        const sortedData = scanData.slice().sort((a, b) => a.voltage - b.voltage);
        if (direction === 'forward') {
            return sortedData.slice(0, Math.floor(sortedData.length * 0.3));
        } else {
            return sortedData.slice(-Math.floor(sortedData.length * 0.3));
        }
    }
    
    // Step 2: Select the best segment for baseline
    const selectedSegment = selectBaselineSegment(allSegments, peakVoltage, direction);
    
    if (selectedSegment) {
        return selectedSegment.data;
    } else {
        // Fallback: use the highest quality segment that has reasonable position
        console.warn(`[BASELINE] Using fallback: highest quality segment for ${direction}`);
        const fallbackSegment = allSegments.find(segment => {
            if (direction === 'forward') {
                return peakVoltage - segment.endVoltage > 0.02; // At least 20mV before peak
            } else {
                return segment.startVoltage - peakVoltage > 0.01; // At least 10mV after peak
            }
        });
        
        return fallbackSegment ? fallbackSegment.data : [];
    }
}

// Calculate Separate Baselines (Forward/Reverse scan) - Improved Algorithm
function calculateSeparateBaselines(forwardData, reverseData, peaks) {
    console.log('[BASELINE] Starting improved baseline calculation:', {
        forwardPoints: forwardData.length,
        reversePoints: reverseData.length,
        peaks: peaks.length
    });

    // Find oxidation and reduction peaks
    const oxPeaks = peaks.filter(p => p.type === 'oxidation');
    const redPeaks = peaks.filter(p => p.type === 'reduction');
    
    let prePeakPoints = [];
    let postPeakPoints = [];
    
    // Find linear baseline region for forward scan (before oxidation peak)
    if (forwardData.length >= 10) {
        if (oxPeaks.length > 0) {
            // Use the first (most negative) oxidation peak as reference
            const targetPeak = oxPeaks.reduce((earliest, peak) => 
                (peak.x || peak.voltage) < (earliest.x || earliest.voltage) ? peak : earliest
            );
            prePeakPoints = findLinearBaselineRegion(forwardData, targetPeak.x || targetPeak.voltage, 'forward');
        } else {
            // No oxidation peak found, use first 20% of forward data
            const fallbackSize = Math.max(5, Math.floor(forwardData.length * 0.2));
            prePeakPoints = forwardData.slice().sort((a, b) => a.voltage - b.voltage).slice(0, fallbackSize);
        }
    }
    
    // Find linear baseline region for reverse scan (after reduction peak)  
    if (reverseData.length >= 10) {
        if (redPeaks.length > 0) {
            // Use the last (most positive) reduction peak as reference
            const targetPeak = redPeaks.reduce((latest, peak) => 
                (peak.x || peak.voltage) > (latest.x || latest.voltage) ? peak : latest
            );
            postPeakPoints = findLinearBaselineRegion(reverseData, targetPeak.x || targetPeak.voltage, 'reverse');
        } else {
            // No reduction peak found, use last 20% of reverse data
            const fallbackSize = Math.max(5, Math.floor(reverseData.length * 0.2));
            postPeakPoints = reverseData.slice().sort((a, b) => a.voltage - b.voltage).slice(-fallbackSize);
        }
    }

    console.log('[BASELINE] Baseline regions found:', {
        prePeakPoints: prePeakPoints.length,
        postPeakPoints: postPeakPoints.length,
        prePeakRange: prePeakPoints.length > 0 ? [prePeakPoints[0].voltage, prePeakPoints[prePeakPoints.length-1].voltage] : 'none',
        postPeakRange: postPeakPoints.length > 0 ? [postPeakPoints[0].voltage, postPeakPoints[postPeakPoints.length-1].voltage] : 'none'
    });

    // Check if we have enough data points for both baselines
    if (prePeakPoints.length < 2 && postPeakPoints.length < 2) {
        throw new Error(`Insufficient baseline data - Pre: ${prePeakPoints.length}, Post: ${postPeakPoints.length}`);
    }

    // Handle cases where only one baseline region is available
    if (prePeakPoints.length < 2) {
        console.warn('[BASELINE] Insufficient pre-peak data, using post-peak for both baselines');
        prePeakPoints = postPeakPoints;
    }
    
    if (postPeakPoints.length < 2) {
        console.warn('[BASELINE] Insufficient post-peak data, using pre-peak for both baselines');
        postPeakPoints = prePeakPoints;
    }

    const prePeakRegression = linearRegression(prePeakPoints);
    const postPeakRegression = linearRegression(postPeakPoints);

    // Generate baseline points for full voltage range
    const oxidationBaseline = forwardData.map(dp => ({
        voltage: dp.voltage,
        current: prePeakRegression.slope * dp.voltage + prePeakRegression.intercept
    }));

    const reductionBaseline = reverseData.map(dp => ({
        voltage: dp.voltage,
        current: postPeakRegression.slope * dp.voltage + postPeakRegression.intercept
    }));

    console.log('[BASELINE] Regression results:', {
        prePeak: { 
            slope: prePeakRegression.slope.toExponential(3), 
            intercept: prePeakRegression.intercept.toFixed(6),
            points: prePeakPoints.length
        },
        postPeak: { 
            slope: postPeakRegression.slope.toExponential(3), 
            intercept: postPeakRegression.intercept.toFixed(6),
            points: postPeakPoints.length
        }
    });

    return { 
        oxidationBaseline, 
        reductionBaseline,
        prePeakPoints,
        postPeakPoints,
        prePeakRegression,
        postPeakRegression
    };
}

// Calculate Combined Baseline (Weighted Average)
function calculateCombinedBaseline(data, prePeakStart, prePeakEnd, postPeakStart, postPeakEnd) {
    const prePeakData = data.filter(p => p.voltage >= prePeakStart && p.voltage <= prePeakEnd);
    const postPeakData = data.filter(p => p.voltage >= postPeakStart && p.voltage <= postPeakEnd);

    if (prePeakData.length < 2 || postPeakData.length < 2) {
        throw new Error("Not enough data points in the specified ranges for baseline calculation.");
    }

    const prePeakRegression = linearRegression(prePeakData);
    const postPeakRegression = linearRegression(postPeakData);

    // Weighted average of slopes and intercepts
    const totalPoints = prePeakData.length + postPeakData.length;
    const prePeakWeight = prePeakData.length / totalPoints;
    const postPeakWeight = postPeakData.length / totalPoints;

    const combinedSlope = (prePeakWeight * prePeakRegression.slope) + (postPeakWeight * postPeakRegression.slope);
    const combinedIntercept = (prePeakWeight * prePeakRegression.intercept) + (postPeakWeight * postPeakRegression.intercept);

    // Generate baseline points using combined slope and intercept
    const combinedBaseline = data.map(dp => ({
        voltage: dp.voltage,
        current: combinedSlope * dp.voltage + combinedIntercept
    }));

    return combinedBaseline;
}

// Subtract Baseline from Data
function subtractBaseline(data, baseline) {
    if (data.length !== baseline.length) {
        throw new Error("Data and baseline must have the same number of points.");
    }

    const correctedData = [];
    for (let i = 0; i < data.length; i++) {
        // Check voltage values match (with small tolerance for floating-point)
        if (Math.abs(data[i].voltage - baseline[i].voltage) > 1e-9) {
            throw new Error(`Voltage mismatch at index ${i}: Data voltage = ${data[i].voltage}, Baseline voltage = ${baseline[i].voltage}`);
        }
        correctedData.push({
            voltage: data[i].voltage,
            current: data[i].current - baseline[i].current
        });
    }
    return correctedData;
}

// Calculate Peak Height relative to baseline
function calculatePeakHeight(peakVoltage, baseline, dataSet) {
    // Find closest baseline point to peak voltage
    const closestBaselinePoint = baseline.reduce((closest, point) => 
        Math.abs(point.voltage - peakVoltage) < Math.abs(closest.voltage - peakVoltage) ? point : closest
    );
    
    if (closestBaselinePoint) {
        const peakPoint = dataSet.find(p => Math.abs(p.voltage - peakVoltage) < 1e-6);
        if (peakPoint) {
            return peakPoint.current - closestBaselinePoint.current;
        }
    }
    return 0;
}

// Scan for all linear windows of given size, return array of {startIdx, endIdx, regression, rSquared, slope, intercept}
function scanLinearWindows(data, windowSize = 7, r2Threshold = 0.90, maxAbsSlope = 5) {
    if (!data || data.length < windowSize) return [];
    const results = [];
    for (let i = 0; i <= data.length - windowSize; i++) {
        const window = data.slice(i, i + windowSize);
        const reg = linearRegression(window);
        if (reg.rSquared >= r2Threshold && Math.abs(reg.slope) <= maxAbsSlope) {
            results.push({
                startIdx: i,
                endIdx: i + windowSize - 1,
                regression: reg,
                rSquared: reg.rSquared,
                slope: reg.slope,
                intercept: reg.intercept,
                voltageStart: window[0].voltage,
                voltageEnd: window[window.length-1].voltage
            });
        }
    }
    return results;
}

// Auto-detect baseline regions from peaks using linear window scan

// Calculate simple baseline for single scan data - Improved Algorithm
function calculateSimpleBaseline(data, peaks) {
    if (!data || data.length < 4) {
        console.warn('[BASELINE] Insufficient data for simple baseline');
        return null;
    }

    try {
        console.log('[BASELINE] Starting simple baseline calculation with improved algorithm');
        
        // Sort data by voltage for easier processing
        const sortedData = data.slice().sort((a, b) => a.voltage - b.voltage);
        
    // Try to find the best linear regions from the data
        let bestBaselinePoints = [];
    let bestScore = 0;
        
        const minRegionSize = Math.max(5, Math.floor(sortedData.length * 0.1));
        const maxRegionSize = Math.floor(sortedData.length * 0.4);
        
        // Search for linear regions avoiding peak areas
        const peakVoltages = peaks.map(p => p.x || p.voltage);
        
        // Try different combinations of regions
        for (let regionSize = maxRegionSize; regionSize >= minRegionSize; regionSize -= 5) {
            for (let startIdx = 0; startIdx <= sortedData.length - regionSize; startIdx++) {
                const region = sortedData.slice(startIdx, startIdx + regionSize);
                
                // Check if this region avoids peak areas
                const regionStart = region[0].voltage;
                const regionEnd = region[region.length - 1].voltage;
                const regionCenter = (regionStart + regionEnd) / 2;
                
                // Calculate distance from nearest peak
                const minDistFromPeak = peakVoltages.length > 0 ? 
                    Math.min(...peakVoltages.map(pv => Math.abs(regionCenter - pv))) : Infinity;
                
                // Check if this region is linear
                if (isLinearRegion(region)) {
                    const reg = linearRegression(region);
                    const absSlope = Math.abs(reg.slope);
                    // Exclude clearly non-flat segments (steep slope)
                    if (absSlope > 5) {
                        continue;
                    }
                    // Score based on linearity (strong), flatness (strong), size and distance from peaks
                    const linearityScore = Math.max(0, reg.rSquared - 0.85) / 0.15; // 0 at 0.85, ~1 near 1.0
                    const flatnessScore = 1.0 / (1.0 + absSlope);
                    const sizeScore = region.length / maxRegionSize; // 0..1
                    const distanceScore = Math.min(1, minDistFromPeak / (0.1)); // normalize ~0.1V
                    const score = (0.4 * linearityScore) + (0.4 * flatnessScore) + (0.1 * sizeScore) + (0.1 * distanceScore);
                    
                    if (score > bestScore) {
                        bestScore = score;
                        bestBaselinePoints = region;
                        console.log('[BASELINE] Found better baseline region:', {
                            size: region.length,
                            range: [regionStart.toFixed(3), regionEnd.toFixed(3)],
                            distFromPeak: minDistFromPeak.toFixed(3),
                            r2: reg.rSquared.toFixed(4),
                            absSlope: absSlope.toExponential(3),
                            score: score.toFixed(3)
                        });
                    }
                }
            }
        }

        // If no good linear region found, use multiple smaller regions
        if (bestBaselinePoints.length === 0) {
            console.warn('[BASELINE] No single linear region found, trying multiple regions');
            
            // Use first and last portions, avoiding peak areas
            const voltageRange = sortedData[sortedData.length - 1].voltage - sortedData[0].voltage;
            const safeMargin = voltageRange * 0.1;
            
            const startRegion = sortedData.filter(p => 
                p.voltage <= sortedData[0].voltage + safeMargin * 2
            );
            
            const endRegion = sortedData.filter(p => 
                p.voltage >= sortedData[sortedData.length - 1].voltage - safeMargin * 2
            );
            
            // Take best parts from start and end
            const startSize = Math.min(startRegion.length, Math.floor(sortedData.length * 0.15));
            const endSize = Math.min(endRegion.length, Math.floor(sortedData.length * 0.15));
            
            bestBaselinePoints = [
                ...startRegion.slice(0, startSize),
                ...endRegion.slice(-endSize)
            ];
        }

        if (bestBaselinePoints.length < 2) {
            // Final fallback: use first and last 10% of data
            const fallbackSize = Math.max(2, Math.floor(sortedData.length * 0.1));
            bestBaselinePoints = [
                ...sortedData.slice(0, fallbackSize),
                ...sortedData.slice(-fallbackSize)
            ];
        }

        const regression = linearRegression(bestBaselinePoints);
        
        // Generate baseline for entire voltage range
        const baseline = sortedData.map(dp => ({
            voltage: dp.voltage,
            current: regression.slope * dp.voltage + regression.intercept
        }));

        console.log('[BASELINE] Simple baseline completed:', {
            baselinePoints: bestBaselinePoints.length,
            regression: {
                slope: regression.slope.toExponential(3),
                intercept: regression.intercept.toFixed(6)
            }
        });

        return {
            baseline,
            baselinePoints: bestBaselinePoints,
            regression
        };

    } catch (error) {
        console.error('[BASELINE] Error in simple baseline calculation:', error.message);
        return null;
    }
}

// Wait for DOM and Plotly to be ready
function ensurePlotlyReady(callback) {
    console.log('[PLOTLY] ensurePlotlyReady called');
    if (window.Plotly) {
        console.log('[PLOTLY] Plotly already available');
        callback();
    } else {
        console.log('[PLOTLY] Loading Plotly...');
        var s = document.createElement('script');
        s.src = 'https://cdn.plot.ly/plotly-2.26.0.min.js';
        s.onload = function() {
            console.log('[PLOTLY] Plotly loaded successfully');
            callback();
        };
        s.onerror = function() {
            console.error('[PLOTLY] Failed to load Plotly');
        };
        document.head.appendChild(s);
    }
}

function renderPeakAnalysisPlot(chartData, peaksData, methodNameStr) {
    console.log('[RENDER] renderPeakAnalysisPlot called with:', {chartData, peaksData, methodNameStr});
    
    const plotDiv = document.getElementById('plotly-peak-graph');
    if (!plotDiv) {
        console.error('[RENDER] plotly-peak-graph element not found!');
        return;
    }
    
    console.log('[RENDER] plotDiv found:', plotDiv);

    // Defensive: ensure peaksData is always an array
    let peaksArr = [];
    console.log('[RENDER] Processing peaksData:', peaksData);
    console.log('[RENDER] peaksData type:', typeof peaksData);
    console.log('[RENDER] peaksData isArray:', Array.isArray(peaksData));
    
    if (Array.isArray(peaksData)) {
        peaksArr = peaksData;
        console.log('[RENDER] Using peaksData as array, length:', peaksArr.length);
    } else if (peaksData && typeof peaksData === 'object') {
        console.log('[RENDER] peaksData is object, processing...');
    } else {
        console.log('[RENDER] No peaks data or invalid format');
    }
    
    console.log('[RENDER] Final peaksArr:', peaksArr);
    console.log('[RENDER] Creating CV trace...');
    
    // Initialize baseline traces and info for now (simplified)
    let baselineTraces = [];
    let baselineInfo = null;
    
    console.log('[RENDER] Checking for baseline data in peaksData...');
    console.log('[RENDER] peaksData structure check:', peaksData);
    
    // Check if any peak has baseline data
    if (peaksArr.length > 0) {
        console.log('[RENDER] First peak object:', peaksArr[0]);
        console.log('[RENDER] First peak keys:', Object.keys(peaksArr[0]));
        
        if (peaksArr[0].baseline) {
            console.log('[RENDER] Found baseline data in first peak:', peaksArr[0].baseline);
            const baseline = peaksArr[0].baseline;
            
            if (baseline.forward && baseline.reverse) {
                // Create baseline traces
                const n = chartData.voltage.length;
                const mid = Math.floor(n / 2);
                
                baselineTraces.push({
                    x: chartData.voltage.slice(0, mid),
                    y: baseline.forward,
                    mode: 'lines',
                    name: 'Forward Baseline',
                    line: { color: '#ff6b6b', width: 2, dash: 'dash' },
                    hovertemplate: 'Forward Baseline<br>V: %{x:.3f}<br>I: %{y:.3f}<extra></extra>',
                });
                
                baselineTraces.push({
                    x: chartData.voltage.slice(mid),
                    y: baseline.reverse,
                    mode: 'lines',
                    name: 'Reverse Baseline',
                    line: { color: '#4ecdc4', width: 2, dash: 'dash' },
                    hovertemplate: 'Reverse Baseline<br>V: %{x:.3f}<br>I: %{y:.3f}<extra></extra>',
                });
                
                // Add baseline segment markers if available
                if (baseline.markers) {
                    if (baseline.markers.forward_segment && baseline.markers.forward_segment.start_idx !== null) {
                        const startIdx = baseline.markers.forward_segment.start_idx;
                        const endIdx = baseline.markers.forward_segment.end_idx;
                        const segmentVoltage = chartData.voltage.slice(startIdx, endIdx + 1);
                        const segmentCurrent = chartData.current.slice(startIdx, endIdx + 1);
                        
                        baselineTraces.push({
                            x: segmentVoltage,
                            y: segmentCurrent,
                            mode: 'markers',
                            name: `Forward Segment (R²=${baseline.markers.forward_segment.r2?.toFixed(3) || 'N/A'})`,
                            marker: { color: '#ff6b6b', size: 6, symbol: 'circle' },
                            hovertemplate: 'Forward Segment<br>V: %{x:.3f}<br>I: %{y:.3f}<br>R²: ' + (baseline.markers.forward_segment.r2?.toFixed(3) || 'N/A') + '<extra></extra>',
                        });
                    }
                    
                    if (baseline.markers.reverse_segment && baseline.markers.reverse_segment.start_idx !== null) {
                        const startIdx = baseline.markers.reverse_segment.start_idx;
                        const endIdx = baseline.markers.reverse_segment.end_idx;
                        const segmentVoltage = chartData.voltage.slice(startIdx, endIdx + 1);
                        const segmentCurrent = chartData.current.slice(startIdx, endIdx + 1);
                        
                        baselineTraces.push({
                            x: segmentVoltage,
                            y: segmentCurrent,
                            mode: 'markers',
                            name: `Reverse Segment (R²=${baseline.markers.reverse_segment.r2?.toFixed(3) || 'N/A'})`,
                            marker: { color: '#4ecdc4', size: 6, symbol: 'circle' },
                            hovertemplate: 'Reverse Segment<br>V: %{x:.3f}<br>I: %{y:.3f}<br>R²: ' + (baseline.markers.reverse_segment.r2?.toFixed(3) || 'N/A') + '<extra></extra>',
                        });
                    }
                }
                
                baselineInfo = {
                    forward: baseline.forward,
                    reverse: baseline.reverse,
                    isSimple: false
                };
                
                console.log('[RENDER] Created baseline traces:', baselineTraces.length);
            } else {
                console.log('[RENDER] Baseline object exists but missing forward/reverse data');
            }
        } else {
            console.log('[RENDER] No baseline property in first peak');
        }
    } else {
        console.log('[RENDER] No baseline data found in peaks');
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
            gridcolor: '#f0f0f0'
        },
        margin: { t: 50, l: 60, r: 30, b: 60 },
        legend: { orientation: 'h', y: -0.2 },
        hovermode: 'closest',
        height: 500
    };

    // Combine all traces: CV data, peaks, and baseline traces
    const allTraces = [cvTrace, peakTrace, ...baselineTraces];
    
    console.log('[RENDER] About to call Plotly.newPlot with', allTraces.length, 'traces');
    console.log('[RENDER] Traces:', allTraces);
    
    ensurePlotlyReady(function() {
        console.log('[RENDER] Plotly ready, creating plot...');
        Plotly.newPlot(plotDiv, allTraces, layout, {responsive: true});
        console.log('[RENDER] Plot created successfully');
    });

    // Store baseline info globally for export and further analysis
    window.currentBaselineInfo = baselineInfo;

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
} // End of renderPeakAnalysisPlot function

// Export for global usage
window.renderPeakAnalysisPlot = renderPeakAnalysisPlot;

// Patch showPeakDetails to handle undefined regression/baselineInfo gracefully
const origShowPeakDetails = window.showPeakDetails;
window.showPeakDetails = function(peak) {
    const detailsDiv = document.querySelector('.peak-details');
    if (!detailsDiv || !peak) return;
    const v = (peak.x !== undefined ? peak.x : peak.voltage);
    const i = (peak.y !== undefined ? peak.y : peak.current);
    let peakHeight = '';
    if (peak.height !== undefined) {
        peakHeight = `<div class="mb-2"><span class='value-label'>Peak Height:</span> <span class='value'>${peak.height.toFixed(3)} µA</span></div>`;
    }
    // Baseline information
    let baselineInfo = '';
    if (window.currentBaselineInfo) {
        if (window.currentBaselineInfo.isSimple) {
            // Simple baseline info
            const regression = window.currentBaselineInfo.regression;
            if (regression && typeof regression.slope === 'number' && typeof regression.intercept === 'number') {
                const baselineAtPeak = regression.slope * v + regression.intercept;
                baselineInfo = `
                    <hr class="my-3">
                    <h6 class="mb-2">Baseline Analysis</h6>
                    <div class="mb-2"><span class='value-label'>Type:</span> <span class='value'>Simple baseline</span></div>
                    <div class="mb-2"><span class='value-label'>Baseline at Peak:</span> <span class='value'>${baselineAtPeak.toFixed(3)} µA</span></div>
                    <div class="mb-2"><span class='value-label'>Slope:</span> <span class='value'>${regression.slope.toExponential(3)} µA/V</span></div>
                    <div class="mb-2"><span class='value-label'>Intercept:</span> <span class='value'>${regression.intercept.toFixed(3)} µA</span></div>
                `;
            } else {
                baselineInfo = `<div class='text-danger'>No valid regression for baseline.</div>`;
            }
        } else {
            // Separate baseline info
            const isOxidation = peak.type === 'oxidation';
            const regression = isOxidation ? 
                window.currentBaselineInfo.prePeakRegression : 
                window.currentBaselineInfo.postPeakRegression;
            if (regression && typeof regression.slope === 'number' && typeof regression.intercept === 'number') {
                const baselineAtPeak = regression.slope * v + regression.intercept;
                const baselineRegion = isOxidation ? 'Pre-peak region' : 'Post-peak region';
                baselineInfo = `
                    <hr class="my-3">
                    <h6 class="mb-2">Baseline Analysis</h6>
                    <div class="mb-2"><span class='value-label'>Region:</span> <span class='value'>${baselineRegion}</span></div>
                    <div class="mb-2"><span class='value-label'>Baseline at Peak:</span> <span class='value'>${baselineAtPeak.toFixed(3)} µA</span></div>
                    <div class="mb-2"><span class='value-label'>Slope:</span> <span class='value'>${regression.slope.toExponential(3)} µA/V</span></div>
                    <div class="mb-2"><span class='value-label'>Intercept:</span> <span class='value'>${regression.intercept.toFixed(3)} µA</span></div>
                `;
            } else {
                baselineInfo = `<div class='text-danger'>No valid regression for baseline.</div>`;
            }
        }
    } else {
        baselineInfo = `<div class='text-danger'>No baseline information available.</div>`;
    }
    detailsDiv.innerHTML = `
        <h6 class="mb-3">Peak Details</h6>
        <div class="mb-2"><span class='value-label'>Type:</span> <span class='value badge ${peak.type === 'oxidation' ? 'bg-danger' : 'bg-success'}'>${peak.type}</span></div>
        <div class="mb-2"><span class='value-label'>Voltage:</span> <span class='value'>${v.toFixed(3)} V</span></div>
        <div class="mb-2"><span class='value-label'>Current:</span> <span class='value'>${i.toFixed(3)} µA</span></div>
        ${peakHeight}
        ${baselineInfo}
    `;
};


// ===== BASELINE PARAMETER CONTROL UI =====
// Add parameter controls to the DOM if not present
function addBaselineParamControls() {
    if (document.getElementById('baselineParamControls')) return;
    const container = document.createElement('div');
    container.id = 'baselineParamControls';
    container.style.margin = '10px 0 20px 0';
    container.innerHTML = `
        <div style="display:flex;gap:1.5em;align-items:center;flex-wrap:wrap;">
            <label>r² threshold: <input id="r2ThresholdInput" type="number" min="0.5" max="1" step="0.01" value="0.85" style="width:4em;"></label>
            <label>max |slope|: <input id="maxAbsSlopeInput" type="number" min="0" max="100" step="0.1" value="10" style="width:4em;"></label>
            <label>window size: <input id="windowSizeInput" type="number" min="3" max="50" step="1" value="9" style="width:4em;"></label>
            <button id="recalcBaselineParamsBtn" class="btn btn-sm btn-primary">Recalculate</button>
        </div>
    `;
    // Insert above the plot
    const plotDiv = document.getElementById('plotly-peak-graph');
    if (plotDiv && plotDiv.parentNode) {
        plotDiv.parentNode.insertBefore(container, plotDiv);
    } else {
        document.body.insertBefore(container, document.body.firstChild);
    }
}

// Store baseline params globally
window.baselineParams = {
    r2Threshold: 0.85,
    maxAbsSlope: 10,
    windowSize: 9
};

// Patch scanLinearWindows to use global params
function scanLinearWindows(data, windowSize, r2Threshold, maxAbsSlope) {
    windowSize = windowSize || window.baselineParams.windowSize;
    r2Threshold = r2Threshold || window.baselineParams.r2Threshold;
    maxAbsSlope = maxAbsSlope || window.baselineParams.maxAbsSlope;
    if (!data || data.length < windowSize) return [];
    const results = [];
    console.log('[SCAN] scanLinearWindows(data, windowSize, r2Threshold, maxAbsSlope)', { data, windowSize, r2Threshold, maxAbsSlope });
    
    for (let i = 0; i <= data.length - windowSize; i++) {

        const windowArr = data.slice(i, i + windowSize);
        // console.log(`[SCAN] Window ${i}-${i+windowSize-1}`, windowArr);
        const reg = linearRegression(windowArr);
        // console.log('const reg = linearRegression(windowArr)', reg);
        
        // Debug log for each window
        // console.log(`[SCAN] Window ${i}-${i+windowSize-1}: r2=${reg.rSquared.toFixed(4)}, slope=${reg.slope.toExponential(3)}`);
        if (reg.rSquared >= r2Threshold && Math.abs(reg.slope) <= maxAbsSlope) {
            results.push({
                startIdx: i,
                endIdx: i + windowSize - 1,
                regression: reg,
                rSquared: reg.rSquared,
                slope: reg.slope,
                intercept: reg.intercept,
                voltageStart: windowArr[0].voltage,
                voltageEnd: windowArr[windowArr.length-1].voltage
            });
        }
    }
    console.log('[SCAN] scanLinearWindows results:', results);
    return results;
}

// Patch autoDetectBaselineRegions to use global params
function autoDetectBaselineRegions(data, peaks) {
    if (!data || data.length < 4) {
        console.warn('[BASELINE] Insufficient data for baseline detection');
        return null;
    }

    const voltages = data.map(p => p.voltage).sort((a, b) => a - b);
    const minV = voltages[0];
    const maxV = voltages[voltages.length - 1];
    const range = maxV - minV;
    
    console.log('[BASELINE] Voltage range:', { minV, maxV, range });
    
    if (range < 0.1) {
        console.warn('[BASELINE] Voltage range too small for meaningful baseline detection');
        return null;
    }


    console.log('[BASELINE] รอบแรก: scan linear windows');

    // รอบแรก: scan linear windows
    const windowSize = window.baselineParams.windowSize;
    const r2Threshold = window.baselineParams.r2Threshold;
    const maxAbsSlope = window.baselineParams.maxAbsSlope;

    console.log('[BASELINE] scanLinearWindows(data, windowSize, r2Threshold, maxAbsSlope)', { data, windowSize, r2Threshold, maxAbsSlope });
    const linearWindows = scanLinearWindows(data, windowSize, r2Threshold, maxAbsSlope);
    if (linearWindows.length === 0) {
        console.warn('[BASELINE] No linear windows found, fallback to old margin method');
        // fallback: ใช้ขอบ 30% เหมือนเดิม
        const margin = range * 0.3;
        return {
            prePeakStart: minV,
            prePeakEnd: minV + margin,
            postPeakStart: maxV - margin,
            postPeakEnd: maxV
        };
    }

    console.log('[BASELINE] รอบสอง: เลือก window ที่เหมาะสมเป็น baseline');
    // รอบสอง: เลือก window ที่เหมาะสมเป็น baseline
    // ถ้ามี peak ให้เลือก window ที่อยู่ห่าง peak มากที่สุด (ก่อน/หลัง peak)
    let prePeakWindow = null, postPeakWindow = null;
    if (peaks && peaks.length > 0) {
        const oxPeaks = peaks.filter(p => p.type === 'oxidation');
        const redPeaks = peaks.filter(p => p.type === 'reduction');
        let oxV = oxPeaks.length > 0 ? Math.min(...oxPeaks.map(p => p.x || p.voltage)) : null;
        let redV = redPeaks.length > 0 ? Math.max(...redPeaks.map(p => p.x || p.voltage)) : null;

        // prePeak: window ที่อยู่ก่อน oxidation peak และห่าง peak มากที่สุด
        if (oxV !== null) {
            prePeakWindow = linearWindows
                .filter(w => w.voltageEnd < oxV - range * 0.02)
                .sort((a, b) => b.voltageEnd - a.voltageEnd)[0];
        }
        // postPeak: window ที่อยู่หลัง reduction peak และห่าง peak มากที่สุด
        if (redV !== null) {
            postPeakWindow = linearWindows
                .filter(w => w.voltageStart > redV + range * 0.02)
                .sort((a, b) => a.voltageStart - b.voltageStart)[0];
        }
    }
    // fallback: ถ้าไม่มี peak หรือหาไม่ได้ ให้ใช้ window ที่ซ้ายสุด/ขวาสุด
    if (!prePeakWindow) prePeakWindow = linearWindows[0];
    if (!postPeakWindow) postPeakWindow = linearWindows[linearWindows.length-1];

    // Defensive: check window existence before returning
    if (!prePeakWindow || !postPeakWindow) {
        console.warn('[BASELINE] Could not find suitable pre/post peak window', { prePeakWindow, postPeakWindow, linearWindows });
        return null;
    }

    console.log('[BASELINE] คืนค่าเป็นช่วง voltage');
    // คืนค่าเป็นช่วง voltage
    return {
        prePeakStart: prePeakWindow.voltageStart,
        prePeakEnd: prePeakWindow.voltageEnd,
        postPeakStart: postPeakWindow.voltageStart,
        postPeakEnd: postPeakWindow.voltageEnd,
        linearWindows // debug: ส่งออก windows ทั้งหมดด้วย
    };
}

// Add parameter controls on DOMContentLoaded
document.addEventListener('DOMContentLoaded', addBaselineParamControls);

// Patch recalculateBaseline to use new params
const origRecalculateBaseline = window.recalculateBaseline;
window.recalculateBaseline = function() {
    // Read params from UI
    const r2Input = document.getElementById('r2ThresholdInput');
    const slopeInput = document.getElementById('maxAbsSlopeInput');
    const winInput = document.getElementById('windowSizeInput');
    if (r2Input && slopeInput && winInput) {
        window.baselineParams.r2Threshold = parseFloat(r2Input.value);
        window.baselineParams.maxAbsSlope = parseFloat(slopeInput.value);
        window.baselineParams.windowSize = parseInt(winInput.value);
    }
    if (typeof origRecalculateBaseline === 'function') origRecalculateBaseline();
};

// Also hook recalc button
document.addEventListener('DOMContentLoaded', function() {
    const btn = document.getElementById('recalcBaselineParamsBtn');
    if (btn) btn.onclick = window.recalculateBaseline;
});

// ===== BASELINE CONTROL FUNCTIONS =====

// Toggle baseline visibility
function toggleBaselineVisibility() {
    const plotDiv = document.getElementById('plotly-peak-graph');
    if (!plotDiv || !plotDiv.data) return;
    
    let baselineVisible = true;
    const update = {};
    
    plotDiv.data.forEach((trace, i) => {
        if (trace.name && (trace.name.includes('Baseline') || trace.name.includes('Peak Points') || trace.name.includes('height'))) {
            if (i === 2) { // Check first baseline trace for current visibility
                baselineVisible = trace.visible !== false;
            }
            update[`visible[${i}]`] = !baselineVisible;
        }
    });
    
    Plotly.restyle(plotDiv, update);
    
    const toggleBtn = document.getElementById('toggleBaselineBtn');
    if (toggleBtn) {
        toggleBtn.innerHTML = baselineVisible ? 
            '<i class="bi bi-graph-up"></i> Show Baseline' : 
            '<i class="bi bi-graph-down"></i> Hide Baseline';
    }
}

// Recalculate baseline with current data
function recalculateBaseline() {
    // Get current selected trace
    const traceSelect = document.getElementById('traceSelect');
    const currentIdx = parseInt(traceSelect.value) || 0;
    
    // Re-render the plot with fresh baseline calculation
    if (typeof renderSingleTrace === 'function') {
        renderSingleTrace(currentIdx);
    } else {
        console.warn('renderSingleTrace function not available');
    }
    
    // Show feedback
    const recalculateBtn = document.getElementById('recalculateBaselineBtn');
    if (recalculateBtn) {
        recalculateBtn.innerHTML = '<i class="bi bi-check"></i> Recalculated';
        setTimeout(() => {
            recalculateBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Recalculate Baseline';
        }, 2000);
    }
}

// Export baseline data as CSV
function exportBaselineData() {
    if (!window.currentBaselineInfo) {
        alert('No baseline data available to export');
        return;
    }
    
    const baselineInfo = window.currentBaselineInfo;
    let csvContent = 'Baseline Analysis Data\n\n';
    
    if (baselineInfo.isSimple) {
        // Simple baseline export
        csvContent += 'Simple Baseline Data\n';
        csvContent += 'Voltage (V),Baseline Current (µA)\n';
        baselineInfo.simpleBaseline.forEach(point => {
            csvContent += `${point.voltage.toFixed(6)},${point.current.toFixed(6)}\n`;
        });
        
        csvContent += '\nBaseline Points Used\n';
        csvContent += 'Voltage (V),Current (µA)\n';
        baselineInfo.baselinePoints.forEach(point => {
            csvContent += `${point.voltage.toFixed(6)},${point.current.toFixed(6)}\n`;
        });
        
        csvContent += '\nRegression Parameters\n';
        csvContent += 'Slope (µA/V),Intercept (µA),Points Used\n';
        csvContent += `${baselineInfo.regression.slope.toExponential(6)},${baselineInfo.regression.intercept.toFixed(6)},${baselineInfo.baselinePoints.length}\n`;
        
    } else {
        // Separate baselines export
        csvContent += 'Forward (Oxidation) Baseline\n';
        csvContent += 'Voltage (V),Baseline Current (µA)\n';
        baselineInfo.oxidationBaseline.forEach(point => {
            csvContent += `${point.voltage.toFixed(6)},${point.current.toFixed(6)}\n`;
        });
        
        csvContent += '\nReverse (Reduction) Baseline\n';
        csvContent += 'Voltage (V),Baseline Current (µA)\n';
        baselineInfo.reductionBaseline.forEach(point => {
            csvContent += `${point.voltage.toFixed(6)},${point.current.toFixed(6)}\n`;
        });
        
        csvContent += '\nRegression Parameters\n';
        csvContent += 'Type,Slope (µA/V),Intercept (µA),Points Used\n';
        csvContent += `Forward,${baselineInfo.prePeakRegression.slope.toExponential(6)},${baselineInfo.prePeakRegression.intercept.toFixed(6)},${baselineInfo.prePeakPoints.length}\n`;
        csvContent += `Reverse,${baselineInfo.postPeakRegression.slope.toExponential(6)},${baselineInfo.postPeakRegression.intercept.toFixed(6)},${baselineInfo.postPeakPoints.length}\n`;
    }
    
    // Download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `baseline_analysis_${new Date().toISOString().slice(0,10)}.csv`;
    link.click();
}

// Setup baseline control event listeners
function setupBaselineControls() {
    const toggleBtn = document.getElementById('toggleBaselineBtn');
    const recalculateBtn = document.getElementById('recalculateBaselineBtn');
    const exportBaselineBtn = document.getElementById('exportBaselineBtn');
    
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleBaselineVisibility);
    }
    
    if (recalculateBtn) {
        recalculateBtn.addEventListener('click', recalculateBaseline);
    }
    
    if (exportBaselineBtn) {
        exportBaselineBtn.addEventListener('click', exportBaselineData);
    }
}

// Expose baseline control functions
window.toggleBaselineVisibility = toggleBaselineVisibility;
window.recalculateBaseline = recalculateBaseline;
window.exportBaselineData = exportBaselineData;
window.setupBaselineControls = setupBaselineControls;
window.ensurePlotlyReady = ensurePlotlyReady;

// End of file
