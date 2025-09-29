// Enhanced CV measurement polling for real-time updates
// Add this to browser console to improve real-time performance

console.log("🔧 Enhanced CV Real-time Polling Started");

// Function to continuously poll for CV data
function enhancedCVPolling() {
    const pollInterval = 500; // Poll every 0.5 seconds for real-time updates
    let pollCount = 0;
    
    const interval = setInterval(async () => {
        try {
            pollCount++;
            console.log(`🔄 CV Poll #${pollCount}`);
            
            // Get CV data
            const response = await fetch('/api/measurement/data/CV');
            const data = await response.json();
            
            if (data.success) {
                const points = data.data.points || [];
                const isCompleted = data.data.completed || false;
                const isMeasuring = data.data.status?.is_measuring || false;
                
                console.log(`📊 CV Data: ${points.length} points, measuring: ${isMeasuring}, completed: ${isCompleted}`);
                
                // Log data details for first few polls
                if (pollCount <= 5 && points.length > 0) {
                    console.log(`📊 Sample data:`, points.slice(0, 3));
                }
                
                // Stop polling if measurement completed and we have data
                if (isCompleted && points.length > 0) {
                    console.log(`✅ CV Measurement completed with ${points.length} points`);
                    clearInterval(interval);
                    return;
                }
                
                // Stop polling after 2 minutes to prevent infinite polling
                if (pollCount > 240) { // 240 * 0.5s = 2 minutes
                    console.log(`⏰ Polling timeout after 2 minutes`);
                    clearInterval(interval);
                    return;
                }
                
            } else {
                console.log(`❌ CV Poll error:`, data.error);
            }
            
        } catch (error) {
            console.error(`❌ CV Polling error:`, error);
        }
    }, pollInterval);
    
    console.log(`🚀 Enhanced CV polling started (every ${pollInterval}ms)`);
    return interval;
}

// Function to test SCPI commands directly
async function testCVCommands() {
    console.log("🧪 Testing CV SCPI Commands");
    
    const commands = [
        "POTEn:CV:STATUS?",
        "POTEn:CV:DATA?",
        "*IDN?"
    ];
    
    for (const command of commands) {
        try {
            const response = await fetch('/api/uart/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: command })
            });
            
            const result = await response.json();
            console.log(`📡 ${command} → ${result.response || result.error}`);
        } catch (error) {
            console.log(`❌ ${command} failed:`, error);
        }
    }
}

// Function to start CV measurement with debug
async function startCVWithDebug() {
    console.log("🚀 Starting CV measurement with debug");
    
    const params = {
        mode: 'CV',
        begin_voltage: -1.0,
        upper_voltage: 1.0,
        lower_voltage: -1.0,
        scan_rate: 0.05,
        cycles: 1,
        current_range: 2
    };
    
    try {
        // Setup measurement
        const setupResponse = await fetch('/api/measurement/setup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        
        const setupResult = await setupResponse.json();
        console.log("📋 Setup result:", setupResult);
        
        if (setupResult.success) {
            // Start measurement
            const startResponse = await fetch('/api/measurement/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: 'CV' })
            });
            
            const startResult = await startResponse.json();
            console.log("🚀 Start result:", startResult);
            
            if (startResult.success) {
                console.log("✅ CV measurement started - beginning enhanced polling");
                return enhancedCVPolling();
            }
        }
    } catch (error) {
        console.error("❌ Failed to start CV measurement:", error);
    }
}

console.log("🔧 Enhanced CV functions loaded:");
console.log("  - enhancedCVPolling() - Start real-time polling");
console.log("  - testCVCommands() - Test SCPI commands");
console.log("  - startCVWithDebug() - Start CV with debug output");