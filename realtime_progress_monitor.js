// Real-time CV progress monitor with 1-2 second updates
// Paste this in browser console for better user experience

console.log("🔄 Real-time CV Progress Monitor Started");

let progressMonitor = null;
let updateCount = 0;

// Enhanced progress monitoring with visual feedback
function startProgressMonitor() {
    if (progressMonitor) {
        clearInterval(progressMonitor);
    }
    
    updateCount = 0;
    
    progressMonitor = setInterval(async () => {
        updateCount++;
        
        try {
            // Get CV measurement data
            const response = await fetch('/api/measurement/data/CV');
            const data = await response.json();
            
            if (data.success) {
                const points = data.data.points || [];
                const status = data.data.status || {};
                const isCompleted = data.data.completed || false;
                const isMeasuring = status.is_measuring || false;
                const progress = status.progress || {};
                
                // Enhanced console output
                console.clear();
                console.log("🔬 === CV Real-time Monitor ===");
                console.log(`⏱️  Update #${updateCount} (${new Date().toLocaleTimeString()})`);
                console.log(`📊 Points: ${points.length}`);
                console.log(`⚡ Status: ${isMeasuring ? '🟢 MEASURING' : (isCompleted ? '✅ COMPLETED' : '⏸️  IDLE')}`);
                
                // Progress information
                if (progress.phase) {
                    console.log(`📈 Progress: ${progress.percentage || 0}% - ${progress.message || 'Unknown'}`);
                    if (progress.elapsed_time) {
                        console.log(`⏰ Elapsed: ${progress.elapsed_time.toFixed(1)}s`);
                    }
                    if (progress.estimated_total) {
                        console.log(`🎯 Estimated: ${progress.estimated_total.toFixed(1)}s total`);
                    }
                }
                
                // Data quality check
                if (points.length > 0) {
                    const voltages = points.map(p => p.potential);
                    const currents = points.map(p => p.current);
                    const vRange = `${Math.min(...voltages).toFixed(3)}V to ${Math.max(...voltages).toFixed(3)}V`;
                    const iRange = `${Math.min(...currents).toFixed(2)} to ${Math.max(...currents).toFixed(2)} µA`;
                    
                    console.log(`🔋 Voltage Range: ${vRange}`);
                    console.log(`⚡ Current Range: ${iRange}`);
                    
                    // Critical: 5-point detection
                    if (points.length <= 5 && !isMeasuring) {
                        console.warn("🚨 WARNING: Only 5 points - STM32 firmware issue detected!");
                        console.log("💡 This is NOT a web interface problem");
                        console.log("💡 STM32 is not performing full CV scan");
                    } else if (points.length >= 20) {
                        console.log("✅ Good: Proper CV scan detected");
                    }
                }
                
                // Visual progress bar in console
                if (progress.percentage) {
                    const barLength = 20;
                    const filled = Math.round((progress.percentage / 100) * barLength);
                    const bar = '█'.repeat(filled) + '░'.repeat(barLength - filled);
                    console.log(`📊 [${bar}] ${progress.percentage.toFixed(1)}%`);
                }
                
                console.log("─".repeat(50));
                
                // Stop monitoring when completed
                if (isCompleted) {
                    console.log(`🎉 Measurement completed with ${points.length} points!`);
                    clearInterval(progressMonitor);
                    progressMonitor = null;
                    
                    // Final summary
                    if (points.length <= 5) {
                        console.error("🚨 FINAL DIAGNOSIS: STM32 firmware CV implementation incomplete");
                        console.log("📋 Recommendations:");
                        console.log("  1. Check STM32 CV scan loop implementation");
                        console.log("  2. Verify ADC sampling during scan");
                        console.log("  3. Confirm voltage stepping logic");
                        console.log("  4. Test with different electrode setup");
                    } else {
                        console.log("✅ SUCCESS: Full CV scan completed properly");
                    }
                }
                
                // Safety timeout after 5 minutes
                if (updateCount > 300) { // 300 * 1s = 5 minutes
                    console.log("⏰ Monitor timeout after 5 minutes");
                    clearInterval(progressMonitor);
                    progressMonitor = null;
                }
                
            } else {
                console.error(`❌ API Error: ${data.error}`);
            }
            
        } catch (error) {
            console.error(`❌ Monitor Error: ${error.message}`);
        }
        
    }, 1500); // Update every 1.5 seconds - good balance for real-time feel
    
    console.log("🚀 Progress monitor started (1.5s updates)");
    console.log("💡 Console will clear and update automatically");
    console.log("💡 Run stopProgressMonitor() to stop");
}

// Stop monitoring function
function stopProgressMonitor() {
    if (progressMonitor) {
        clearInterval(progressMonitor);
        progressMonitor = null;
        console.log("⏹️ Progress monitor stopped");
    }
}

// Auto-start monitoring
console.log("🎯 Functions available:");
console.log("  - startProgressMonitor() - Start real-time monitoring");
console.log("  - stopProgressMonitor() - Stop monitoring");
console.log("");
console.log("🚀 Auto-starting progress monitor...");
startProgressMonitor();