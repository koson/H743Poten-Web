// Plotly.js logic for Peak Analysis Details page
// This script replaces Chart.js logic in peak_analysis.html

// ===== BASELINE ANALYSIS FUNCTIONS (migrated from C# CVAnalyzer) =====

// Linear Regression Function
function linearRegression(points) {
    if (!points || points.length < 2) {
        throw new Error("At least two data points are required for linear regression.");
    }

    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
    const n = points.length;

    for (const point of points) {
        sumX += point.voltage;
        sumY += point.current;
        sumXY += point.voltage * point.current;
        sumX2 += point.voltage * point.voltage;
    }

    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    return { slope, intercept };
}

// Check if a region has linear current-voltage relationship
function isLinearRegion(region, tolerance = 1e-5) {
    if (region.length < 10) return false; // Need at least 10 points for reliable analysis

    try {
        const regression = linearRegression(region);
        
        // Calculate R-squared to measure linearity
        const meanCurrent = region.reduce((sum, p) => sum + p.current, 0) / region.length;
        let ssRes = 0; // Sum of squares of residuals
        let ssTot = 0; // Total sum of squares
        
        for (const point of region) {
            const predicted = regression.slope * point.voltage + regression.intercept;
            ssRes += Math.pow(point.current - predicted, 2);
            ssTot += Math.pow(point.current - meanCurrent, 2);
        }
        
        const rSquared = ssTot > 0 ? (1 - (ssRes / ssTot)) : 0;
        
        // Calculate slope consistency - very strict for true baseline
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
        
        // Very strict curvature detection
        const secondDerivatives = [];
        for (let i = 1; i < slopes.length; i++) {
            const slopeChange = Math.abs(slopes[i] - slopes[i-1]);
            secondDerivatives.push(slopeChange);
        }
        
        const maxCurvature = secondDerivatives.length > 0 ? Math.max(...secondDerivatives) : 0;
        const avgCurvature = secondDerivatives.length > 0 ? 
            secondDerivatives.reduce((sum, d) => sum + d, 0) / secondDerivatives.length : 0;
        
        // Check for monotonic behavior (consistent trend direction)
        let positiveSlopes = 0, negativeSlopes = 0, zeroSlopes = 0;
        for (const slope of slopes) {
            if (Math.abs(slope) < 1e-8) zeroSlopes++;
            else if (slope > 0) positiveSlopes++;
            else negativeSlopes++;
        }
        
        const dominantDirection = Math.max(positiveSlopes, negativeSlopes, zeroSlopes);
        const consistency = dominantDirection / slopes.length;
        
        // Very strict criteria for baseline detection
        const rSquaredThreshold = 0.98;       // Very high R²
        const slopeCVThreshold = 0.15;        // Very low slope variation
        const maxCurvatureThreshold = 1e-8;   // Almost no curvature
        const avgCurvatureThreshold = 1e-9;   // Almost no average curvature
        const consistencyThreshold = 0.8;     // Most slopes should be in same direction
        
        const hasGoodLinearity = rSquared > rSquaredThreshold;
        const hasConsistentSlope = slopeCV < slopeCVThreshold;
        const hasLowCurvature = maxCurvature < maxCurvatureThreshold && avgCurvature < avgCurvatureThreshold;
        const hasConsistentDirection = consistency > consistencyThreshold;
        
        // Current should not vary much in a true baseline
        const currentRange = Math.max(...region.map(p => p.current)) - Math.min(...region.map(p => p.current));
        const meanAbsCurrent = region.reduce((sum, p) => sum + Math.abs(p.current), 0) / region.length;
        const currentVariability = meanAbsCurrent > 0 ? currentRange / meanAbsCurrent : 0;
        const hasLowVariability = currentVariability < 0.5; // Very strict current variability
        
        const isLinear = hasGoodLinearity && hasConsistentSlope && hasLowCurvature && 
                        hasConsistentDirection && hasLowVariability;
        
        console.log(`[BASELINE] Strict linearity analysis:`, {
            rSquared: rSquared.toFixed(6),
            slopeCV: slopeCV.toFixed(6),
            maxCurvature: maxCurvature.toExponential(3),
            avgCurvature: avgCurvature.toExponential(3),
            consistency: consistency.toFixed(3),
            currentVariability: currentVariability.toFixed(6),
            isLinear,
            voltageRange: [region[0].voltage.toFixed(3), region[region.length-1].voltage.toFixed(3)],
            criteria: {
                rSquaredOK: hasGoodLinearity,
                slopeCVOK: hasConsistentSlope,
                lowCurvatureOK: hasLowCurvature,
                consistentDirectionOK: hasConsistentDirection,
                lowVariabilityOK: hasLowVariability
            }
        });
        
        return isLinear;
        
    } catch (error) {
        console.warn('[BASELINE] Error in linearity check:', error.message);
        return false;
    }
}

// Find linear baseline region in scan data before peak
function findLinearBaselineRegion(scanData, peakVoltage, direction = 'forward') {
    if (!scanData || scanData.length < 10) {
        console.warn(`[BASELINE] Insufficient ${direction} scan data:`, scanData.length);
        return [];
    }

    // Sort data by voltage for easier processing
    const sortedData = scanData.slice().sort((a, b) => a.voltage - b.voltage);
    
    console.log(`[BASELINE] ${direction} scan voltage range:`, {
        minVoltage: sortedData[0].voltage.toFixed(3),
        maxVoltage: sortedData[sortedData.length-1].voltage.toFixed(3),
        totalPoints: sortedData.length,
        peakVoltage: peakVoltage.toFixed(3)
    });

    // Find peak position in sorted data
    let peakIndex = sortedData.findIndex(p => Math.abs(p.voltage - peakVoltage) < 0.01);
    if (peakIndex === -1) {
        // If exact peak not found, find nearest point
        peakIndex = sortedData.reduce((closest, point, index) => 
            Math.abs(point.voltage - peakVoltage) < Math.abs(sortedData[closest].voltage - peakVoltage) ? index : closest
        , 0);
    }

    if (direction === 'forward') {
        // For forward scan: Progressive growing from near peak backwards
        const minDistanceFromPeak = 0.08; // At least 80mV from peak
        let startSearchIndex = peakIndex;
        
        // Find starting point with minimum distance from peak
        for (let i = peakIndex - 1; i >= 0; i--) {
            if (peakVoltage - sortedData[i].voltage >= minDistanceFromPeak) {
                startSearchIndex = i;
                break;
            }
        }
        
        console.log(`[BASELINE] Progressive forward search starting from index ${startSearchIndex}, voltage ${sortedData[startSearchIndex]?.voltage.toFixed(3)}`);
        
        // Progressive growing: start small and expand until linearity breaks
        const startingSize = 10;
        let bestRegion = null;
        let bestScore = -1;
        
        // Try different starting positions near the reference point
        for (let centerIdx = startSearchIndex; centerIdx >= startingSize; centerIdx -= 2) {
            
            // Progressive expansion from this center point
            let lastValidRegion = null;
            let lastValidScore = -1;
            
            for (let halfSize = Math.floor(startingSize / 2); halfSize <= 25; halfSize += 1) { // Smaller increments
                const startIdx = Math.max(0, centerIdx - halfSize);
                const endIdx = Math.min(centerIdx + halfSize, sortedData.length - 1);
                const region = sortedData.slice(startIdx, endIdx + 1);
                
                if (region.length >= 10) {
                    // Check distance from peak
                    const regionEndVoltage = region[region.length - 1].voltage;
                    const distanceFromPeak = peakVoltage - regionEndVoltage;
                    
                    if (distanceFromPeak >= minDistanceFromPeak) {
                        // Test if this region is truly linear
                        if (isLinearRegion(region)) {
                            // Calculate quality score
                            const regression = linearRegression(region);
                            const meanCurrent = region.reduce((sum, p) => sum + p.current, 0) / region.length;
                            let ssRes = 0, ssTot = 0;
                            
                            for (const point of region) {
                                const predicted = regression.slope * point.voltage + regression.intercept;
                                ssRes += Math.pow(point.current - predicted, 2);
                                ssTot += Math.pow(point.current - meanCurrent, 2);
                            }
                            
                            const rSquared = ssTot > 0 ? (1 - (ssRes / ssTot)) : 0;
                            
                            // Additional curvature check near peak end
                            let hasIncreasingCurvature = false;
                            if (region.length > 15) {
                                const nearPeakSegment = region.slice(-8); // Last 8 points (closest to peak)
                                const slopes = [];
                                for (let i = 1; i < nearPeakSegment.length; i++) {
                                    const voltDiff = nearPeakSegment[i].voltage - nearPeakSegment[i-1].voltage;
                                    const currDiff = nearPeakSegment[i].current - nearPeakSegment[i-1].current;
                                    if (Math.abs(voltDiff) > 1e-6) {
                                        slopes.push(currDiff / voltDiff);
                                    }
                                }
                                
                                // Check if slopes are accelerating (indicating approach to peak)
                                if (slopes.length > 2) {
                                    const slopeChanges = [];
                                    for (let i = 1; i < slopes.length; i++) {
                                        slopeChanges.push(Math.abs(slopes[i] - slopes[i-1]));
                                    }
                                    const avgSlopeChange = slopeChanges.reduce((sum, c) => sum + c, 0) / slopeChanges.length;
                                    hasIncreasingCurvature = avgSlopeChange > 1e-6; // Threshold for detecting curvature increase
                                }
                            }
                            
                            if (!hasIncreasingCurvature) {
                                // This region is still good, save it
                                const proximityBonus = 1.0 / (1.0 + distanceFromPeak);
                                const sizeBonus = Math.log(region.length / 10 + 1);
                                const score = rSquared * (1 + proximityBonus) * (1 + sizeBonus);
                                
                                lastValidRegion = region;
                                lastValidScore = score;
                                
                                console.log(`[BASELINE] Forward progressive valid:`, {
                                    startV: region[0].voltage.toFixed(3),
                                    endV: region[region.length-1].voltage.toFixed(3),
                                    size: region.length,
                                    rSquared: rSquared.toFixed(6),
                                    score: score.toFixed(4),
                                    distFromPeak: distanceFromPeak.toFixed(3),
                                    curvatureOK: !hasIncreasingCurvature
                                });
                            } else {
                                console.log(`[BASELINE] Stopping expansion due to increasing curvature near peak at size ${region.length}`);
                                break; // Stop expanding this center point
                            }
                        } else {
                            // If linearity breaks, don't expand further from this center
                            console.log(`[BASELINE] Linearity broken at size ${region.length} for center ${sortedData[centerIdx].voltage.toFixed(3)}`);
                            break;
                        }
                    }
                }
            }
            
            // Update best region if this center produced a good result
            if (lastValidRegion && lastValidScore > bestScore) {
                bestScore = lastValidScore;
                bestRegion = lastValidRegion;
            }
        }
        
        if (bestRegion) {
            console.log(`[BASELINE] Selected progressive forward region:`, {
                startVoltage: bestRegion[0].voltage.toFixed(3),
                endVoltage: bestRegion[bestRegion.length-1].voltage.toFixed(3),
                size: bestRegion.length,
                score: bestScore.toFixed(4),
                voltageSpan: (bestRegion[bestRegion.length-1].voltage - bestRegion[0].voltage).toFixed(3)
            });
            return bestRegion;
        }
        
    } else {
        // For reverse scan: Progressive growing from near peak forwards
        const minDistanceFromPeak = 0.05; // At least 50mV from peak
        let startSearchIndex = peakIndex;
        
        // Find starting point with minimum distance from peak
        for (let i = peakIndex + 1; i < sortedData.length; i++) {
            if (sortedData[i].voltage - peakVoltage >= minDistanceFromPeak) {
                startSearchIndex = i;
                break;
            }
        }
        
        console.log(`[BASELINE] Progressive reverse search starting from index ${startSearchIndex}, voltage ${sortedData[startSearchIndex]?.voltage.toFixed(3)}`);
        
        const startingSize = 10;
        let bestRegion = null;
        let bestScore = -1;
        
        // Try different starting positions near the reference point
        for (let centerIdx = startSearchIndex; centerIdx < sortedData.length - startingSize; centerIdx += 2) {
            
            // Progressive expansion from this center point
            let lastValidRegion = null;
            let lastValidScore = -1;
            
            for (let halfSize = Math.floor(startingSize / 2); halfSize <= 25; halfSize += 1) { // Smaller increments
                const startIdx = Math.max(centerIdx - halfSize, 0);
                const endIdx = Math.min(centerIdx + halfSize, sortedData.length - 1);
                const region = sortedData.slice(startIdx, endIdx + 1);
                
                if (region.length >= 10) {
                    const regionStartVoltage = region[0].voltage;
                    const distanceFromPeak = regionStartVoltage - peakVoltage;
                    
                    if (distanceFromPeak >= minDistanceFromPeak) {
                        if (isLinearRegion(region)) {
                            const regression = linearRegression(region);
                            const meanCurrent = region.reduce((sum, p) => sum + p.current, 0) / region.length;
                            let ssRes = 0, ssTot = 0;
                            
                            for (const point of region) {
                                const predicted = regression.slope * point.voltage + regression.intercept;
                                ssRes += Math.pow(point.current - predicted, 2);
                                ssTot += Math.pow(point.current - meanCurrent, 2);
                            }
                            
                            const rSquared = ssTot > 0 ? (1 - (ssRes / ssTot)) : 0;
                            
                            // Additional curvature check near peak start
                            let hasIncreasingCurvature = false;
                            if (region.length > 15) {
                                const nearPeakSegment = region.slice(0, 8); // First 8 points (closest to peak)
                                const slopes = [];
                                for (let i = 1; i < nearPeakSegment.length; i++) {
                                    const voltDiff = nearPeakSegment[i].voltage - nearPeakSegment[i-1].voltage;
                                    const currDiff = nearPeakSegment[i].current - nearPeakSegment[i-1].current;
                                    if (Math.abs(voltDiff) > 1e-6) {
                                        slopes.push(currDiff / voltDiff);
                                    }
                                }
                                
                                // Check if slopes are accelerating (indicating approach from peak)
                                if (slopes.length > 2) {
                                    const slopeChanges = [];
                                    for (let i = 1; i < slopes.length; i++) {
                                        slopeChanges.push(Math.abs(slopes[i] - slopes[i-1]));
                                    }
                                    const avgSlopeChange = slopeChanges.reduce((sum, c) => sum + c, 0) / slopeChanges.length;
                                    hasIncreasingCurvature = avgSlopeChange > 1e-6;
                                }
                            }
                            
                            if (!hasIncreasingCurvature) {
                                const proximityBonus = 1.0 / (1.0 + distanceFromPeak);
                                const sizeBonus = Math.log(region.length / 10 + 1);
                                const score = rSquared * (1 + proximityBonus) * (1 + sizeBonus);
                                
                                lastValidRegion = region;
                                lastValidScore = score;
                                
                                console.log(`[BASELINE] Reverse progressive valid:`, {
                                    startV: region[0].voltage.toFixed(3),
                                    endV: region[region.length-1].voltage.toFixed(3),
                                    size: region.length,
                                    rSquared: rSquared.toFixed(6),
                                    score: score.toFixed(4),
                                    distFromPeak: distanceFromPeak.toFixed(3),
                                    curvatureOK: !hasIncreasingCurvature
                                });
                            } else {
                                console.log(`[BASELINE] Stopping reverse expansion due to increasing curvature near peak at size ${region.length}`);
                                break;
                            }
                        } else {
                            console.log(`[BASELINE] Linearity broken at size ${region.length} for center ${sortedData[centerIdx].voltage.toFixed(3)}`);
                            break;
                        }
                    }
                }
            }
            
            // Update best region if this center produced a good result
            if (lastValidRegion && lastValidScore > bestScore) {
                bestScore = lastValidScore;
                bestRegion = lastValidRegion;
            }
        }
        
        if (bestRegion) {
            console.log(`[BASELINE] Selected progressive reverse region:`, {
                startVoltage: bestRegion[0].voltage.toFixed(3),
                endVoltage: bestRegion[bestRegion.length-1].voltage.toFixed(3),
                size: bestRegion.length,
                score: bestScore.toFixed(4),
                voltageSpan: (bestRegion[bestRegion.length-1].voltage - bestRegion[0].voltage).toFixed(3)
            });
            return bestRegion;
        }
    }

    // Fallback: use conservative approach if adaptive method fails
    console.warn(`[BASELINE] Adaptive method failed for ${direction} scan, using conservative fallback`);
    
    if (direction === 'forward') {
        // Use middle portion of forward scan, avoiding both extremes
        const startIdx = Math.floor(sortedData.length * 0.2);
        const endIdx = Math.floor(sortedData.length * 0.5);
        const fallbackRegion = sortedData.slice(startIdx, endIdx);
        console.log(`[BASELINE] Forward fallback region:`, {
            startVoltage: fallbackRegion[0].voltage.toFixed(3),
            endVoltage: fallbackRegion[fallbackRegion.length-1].voltage.toFixed(3),
            size: fallbackRegion.length
        });
        return fallbackRegion;
    } else {
        // Use middle-to-end portion of reverse scan
        const startIdx = Math.floor(sortedData.length * 0.5);
        const endIdx = Math.floor(sortedData.length * 0.8);
        const fallbackRegion = sortedData.slice(startIdx, endIdx);
        console.log(`[BASELINE] Reverse fallback region:`, {
            startVoltage: fallbackRegion[0].voltage.toFixed(3),
            endVoltage: fallbackRegion[fallbackRegion.length-1].voltage.toFixed(3),
            size: fallbackRegion.length
        });
        return fallbackRegion;
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

// Auto-detect baseline regions from peaks
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

    if (!peaks || peaks.length === 0) {
        // If no peaks, use first and last 30% of data
        const margin = range * 0.3;
        
        return {
            prePeakStart: minV,
            prePeakEnd: minV + margin,
            postPeakStart: maxV - margin,
            postPeakEnd: maxV
        };
    }

    // Find oxidation and reduction peaks
    const oxPeaks = peaks.filter(p => p.type === 'oxidation');
    const redPeaks = peaks.filter(p => p.type === 'reduction');
    
    // Start with default regions (30% from each end)
    let prePeakStart = minV;
    let prePeakEnd = minV + range * 0.3;
    let postPeakStart = maxV - range * 0.3;
    let postPeakEnd = maxV;
    
    // Adjust based on peak positions
    if (oxPeaks.length > 0) {
        const firstOxPeak = Math.min(...oxPeaks.map(p => p.x || p.voltage));
        // Ensure pre-peak region ends before the first oxidation peak
        prePeakEnd = Math.min(prePeakEnd, firstOxPeak - range * 0.05);
        
        // Ensure we have a meaningful pre-peak region
        if (prePeakEnd - prePeakStart < range * 0.1) {
            prePeakEnd = prePeakStart + range * 0.1;
        }
    }
    
    if (redPeaks.length > 0) {
        const lastRedPeak = Math.max(...redPeaks.map(p => p.x || p.voltage));
        // Ensure post-peak region starts after the last reduction peak
        postPeakStart = Math.max(postPeakStart, lastRedPeak + range * 0.05);
        
        // Ensure we have a meaningful post-peak region
        if (postPeakEnd - postPeakStart < range * 0.1) {
            postPeakStart = postPeakEnd - range * 0.1;
        }
    }
    
    const regions = { prePeakStart, prePeakEnd, postPeakStart, postPeakEnd };
    console.log('[BASELINE] Detected regions:', regions);
    
    return regions;
}

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
                    // Score based on linearity, size, and distance from peaks
                    const score = region.length * minDistFromPeak;
                    
                    if (score > bestScore) {
                        bestScore = score;
                        bestBaselinePoints = region;
                        console.log('[BASELINE] Found better baseline region:', {
                            size: region.length,
                            range: [regionStart.toFixed(3), regionEnd.toFixed(3)],
                            distFromPeak: minDistFromPeak.toFixed(3),
                            score: score.toFixed(2)
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

    // Convert data to consistent format
    const dataPoints = chartData.voltage.map((v, i) => ({
        voltage: v,
        current: chartData.current[i]
    }));

    console.log('[BASELINE] Input data analysis:', {
        totalPoints: dataPoints.length,
        voltageRange: [Math.min(...chartData.voltage), Math.max(...chartData.voltage)],
        currentRange: [Math.min(...chartData.current), Math.max(...chartData.current)],
        peaksFound: peaksArr.length,
        hasDirection: !!(chartData.direction && chartData.direction.length),
        sampleData: dataPoints.slice(0, 3)
    });

    let baselineTraces = [];
    let baselineInfo = null;
    
    try {
        // Auto-detect baseline regions based on peaks
        const regions = autoDetectBaselineRegions(dataPoints, peaksArr);
        
        if (!regions) {
            console.warn('[BASELINE] Could not detect suitable baseline regions');
        } else {
            console.log('[BASELINE] Auto-detected regions:', regions);
            
            // Separate data into forward and reverse scans if direction info is available
            let forwardData = [], reverseData = [];
            
            if (chartData.direction && chartData.direction.length === dataPoints.length) {
                dataPoints.forEach((point, i) => {
                    if (chartData.direction[i] === 'forward') {
                        forwardData.push(point);
                    } else if (chartData.direction[i] === 'reverse') {
                        reverseData.push(point);
                    }
                });
            } else {
                // Infer direction from voltage pattern - improved algorithm
                const voltages = dataPoints.map(p => p.voltage);
                let maxVoltage = Math.max(...voltages);
                let maxIndex = voltages.indexOf(maxVoltage);
                
                // More sophisticated direction inference
                // Look for turning point where voltage changes direction significantly
                const voltageDiffs = [];
                for (let i = 1; i < voltages.length; i++) {
                    voltageDiffs.push(voltages[i] - voltages[i-1]);
                }
                
                // Find the point where voltage direction changes most significantly
                let turningPoint = maxIndex;
                let maxChange = 0;
                
                for (let i = Math.floor(voltages.length * 0.2); i < Math.floor(voltages.length * 0.8); i++) {
                    const beforeAvg = voltageDiffs.slice(Math.max(0, i-5), i).reduce((a, b) => a + b, 0) / 5;
                    const afterAvg = voltageDiffs.slice(i, Math.min(voltageDiffs.length, i+5)).reduce((a, b) => a + b, 0) / 5;
                    const change = Math.abs(beforeAvg - afterAvg);
                    
                    if (change > maxChange) {
                        maxChange = change;
                        turningPoint = i;
                    }
                }
                
                console.log('[BASELINE] Voltage direction analysis:', {
                    maxVoltage,
                    maxIndex,
                    detectedTurningPoint: turningPoint,
                    turningVoltage: voltages[turningPoint],
                    maxDirectionChange: maxChange.toFixed(6)
                });
                
                dataPoints.forEach((point, i) => {
                    if (i <= turningPoint) {
                        forwardData.push(point);
                    } else {
                        reverseData.push(point);
                    }
                });
            }
            
            console.log('[BASELINE] Data separation (improved):', {
                forward: forwardData.length, 
                reverse: reverseData.length,
                total: dataPoints.length,
                forwardVoltageRange: forwardData.length > 0 ? [
                    Math.min(...forwardData.map(p => p.voltage)).toFixed(3),
                    Math.max(...forwardData.map(p => p.voltage)).toFixed(3)
                ] : 'none',
                reverseVoltageRange: reverseData.length > 0 ? [
                    Math.min(...reverseData.map(p => p.voltage)).toFixed(3),
                    Math.max(...reverseData.map(p => p.voltage)).toFixed(3)
                ] : 'none'
            });
            
            // Check if we have sufficient data for baseline calculation
            const minDataPoints = 5; // Minimum points needed for meaningful baseline
            
            if (forwardData.length >= minDataPoints && reverseData.length >= minDataPoints) {
                try {
                    baselineInfo = calculateSeparateBaselines(
                        forwardData, reverseData, peaksArr
                    );
                    
                    // Create baseline traces for visualization
                    baselineTraces.push({
                        x: baselineInfo.oxidationBaseline.map(p => p.voltage),
                        y: baselineInfo.oxidationBaseline.map(p => p.current),
                        mode: 'lines',
                        name: 'Forward Baseline',
                        line: { color: '#ff6b6b', width: 2, dash: 'dash' },
                        hovertemplate: 'Forward Baseline<br>V: %{x:.3f}<br>I: %{y:.3f}<extra></extra>',
                    });
                    
                    baselineTraces.push({
                        x: baselineInfo.reductionBaseline.map(p => p.voltage),
                        y: baselineInfo.reductionBaseline.map(p => p.current),
                        mode: 'lines',
                        name: 'Reverse Baseline',
                        line: { color: '#4ecdc4', width: 2, dash: 'dash' },
                        hovertemplate: 'Reverse Baseline<br>V: %{x:.3f}<br>I: %{y:.3f}<extra></extra>',
                    });
                    
                    // Add baseline calculation points
                    baselineTraces.push({
                        x: baselineInfo.prePeakPoints.map(p => p.voltage),
                        y: baselineInfo.prePeakPoints.map(p => p.current),
                        mode: 'markers',
                        name: 'Pre-Peak Points',
                        marker: { color: '#ff6b6b', size: 6, symbol: 'circle-open' },
                        hovertemplate: 'Pre-Peak Point<br>V: %{x:.3f}<br>I: %{y:.3f}<extra></extra>',
                    });
                    
                    baselineTraces.push({
                        x: baselineInfo.postPeakPoints.map(p => p.voltage),
                        y: baselineInfo.postPeakPoints.map(p => p.current),
                        mode: 'markers',
                        name: 'Post-Peak Points',
                        marker: { color: '#4ecdc4', size: 6, symbol: 'circle-open' },
                        hovertemplate: 'Post-Peak Point<br>V: %{x:.3f}<br>I: %{y:.3f}<extra></extra>',
                    });
                    
                    // Calculate peak heights relative to baseline
                    peaksArr.forEach(peak => {
                        const peakVoltage = peak.x !== undefined ? peak.x : peak.voltage;
                        const baseline = peak.type === 'oxidation' ? baselineInfo.oxidationBaseline : baselineInfo.reductionBaseline;
                        peak.height = calculatePeakHeight(peakVoltage, baseline, dataPoints);
                        
                        // Add vertical line showing peak height
                        const baselineCurrent = baseline.find(p => Math.abs(p.voltage - peakVoltage) < 0.001)?.current || 0;
                        const peakCurrent = peak.y !== undefined ? peak.y : peak.current;
                        
                        baselineTraces.push({
                            x: [peakVoltage, peakVoltage],
                            y: [baselineCurrent, peakCurrent],
                            mode: 'lines',
                            name: `${peak.type} height`,
                            line: { color: peak.type === 'oxidation' ? '#dc3545' : '#198754', width: 2, dash: 'dot' },
                            showlegend: false,
                            hovertemplate: `Peak Height: ${peak.height.toFixed(3)} µA<extra></extra>`,
                        });
                    });
                    
                    console.log('[BASELINE] Baseline analysis completed successfully');
                    
                } catch (baselineError) {
                    console.error('[BASELINE] Error in baseline calculation:', baselineError.message);
                    
                    // Fallback: try simple baseline calculation
                    console.log('[BASELINE] Attempting simple baseline fallback...');
                    const simpleBaseline = calculateSimpleBaseline(dataPoints, peaksArr);
                    
                    if (simpleBaseline) {
                        console.log('[BASELINE] Simple baseline fallback successful');
                        
                        // Add simple baseline trace
                        baselineTraces.push({
                            x: simpleBaseline.baseline.map(p => p.voltage),
                            y: simpleBaseline.baseline.map(p => p.current),
                            mode: 'lines',
                            name: 'Simple Baseline',
                            line: { color: '#6c757d', width: 2, dash: 'dash' },
                            hovertemplate: 'Simple Baseline<br>V: %{x:.3f}<br>I: %{y:.3f}<extra></extra>',
                        });
                        
                        // Add baseline points
                        baselineTraces.push({
                            x: simpleBaseline.baselinePoints.map(p => p.voltage),
                            y: simpleBaseline.baselinePoints.map(p => p.current),
                            mode: 'markers',
                            name: 'Baseline Points',
                            marker: { color: '#6c757d', size: 6, symbol: 'circle-open' },
                            hovertemplate: 'Baseline Point<br>V: %{x:.3f}<br>I: %{y:.3f}<extra></extra>',
                        });
                        
                        // Calculate peak heights with simple baseline
                        peaksArr.forEach(peak => {
                            const peakVoltage = peak.x !== undefined ? peak.x : peak.voltage;
                            peak.height = calculatePeakHeight(peakVoltage, simpleBaseline.baseline, dataPoints);
                            
                            if (peak.height !== 0) {
                                const baselineCurrent = simpleBaseline.baseline.find(p => Math.abs(p.voltage - peakVoltage) < 0.001)?.current || 0;
                                const peakCurrent = peak.y !== undefined ? peak.y : peak.current;
                                
                                baselineTraces.push({
                                    x: [peakVoltage, peakVoltage],
                                    y: [baselineCurrent, peakCurrent],
                                    mode: 'lines',
                                    name: `${peak.type} height`,
                                    line: { color: peak.type === 'oxidation' ? '#dc3545' : '#198754', width: 2, dash: 'dot' },
                                    showlegend: false,
                                    hovertemplate: `Peak Height: ${peak.height.toFixed(3)} µA<extra></extra>`,
                                });
                            }
                        });
                        
                        // Store simple baseline info
                        baselineInfo = {
                            simpleBaseline: simpleBaseline.baseline,
                            baselinePoints: simpleBaseline.baselinePoints,
                            regression: simpleBaseline.regression,
                            isSimple: true
                        };
                    } else {
                        console.warn('[BASELINE] Simple baseline fallback also failed');
                    }
                }
            } else {
                console.warn('[BASELINE] Insufficient data points for baseline calculation:', {
                    forward: forwardData.length,
                    reverse: reverseData.length,
                    required: minDataPoints
                });
            }
        }
        
    } catch (error) {
        console.error('[BASELINE] Error in baseline analysis:', error.message);
        // Continue plotting without baseline analysis
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
}

// Show peak details in .peak-details panel
function showPeakDetails(peak) {
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
            // Separate baseline info
            const isOxidation = peak.type === 'oxidation';
            const regression = isOxidation ? 
                window.currentBaselineInfo.prePeakRegression : 
                window.currentBaselineInfo.postPeakRegression;
            
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
        }
    }
    
    detailsDiv.innerHTML = `
        <h6 class="mb-3">Peak Details</h6>
        <div class="mb-2"><span class='value-label'>Type:</span> <span class='value badge ${peak.type === 'oxidation' ? 'bg-danger' : 'bg-success'}'>${peak.type}</span></div>
        <div class="mb-2"><span class='value-label'>Voltage:</span> <span class='value'>${v.toFixed(3)} V</span></div>
        <div class="mb-2"><span class='value-label'>Current:</span> <span class='value'>${i.toFixed(3)} µA</span></div>
        ${peakHeight}
        ${baselineInfo}
    `;
}

// Expose for HTML
window.renderPeakAnalysisPlot = renderPeakAnalysisPlot;
window.ensurePlotlyReady = ensurePlotlyReady;

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
