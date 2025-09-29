// Advanced CV debugging script for browser console
console.log("🔧 Advanced CV Debugging Tools Loaded");

// Function to test CV command step by step
async function debugCVFlow() {
    console.log("🔍 === CV Flow Debug Started ===");
    
    // Step 1: Test connection
    console.log("1️⃣ Testing STM32 Connection...");
    try {
        const idResponse = await fetch('/api/uart/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: "*IDN?" })
        });
        const idResult = await idResponse.json();
        console.log(`📡 *IDN? → ${idResult.response || idResult.error}`);
    } catch (e) {
        console.error("❌ Connection test failed:", e);
        return;
    }
    
    // Step 2: Check initial status
    console.log("2️⃣ Checking Initial Status...");
    try {
        const statusResponse = await fetch('/api/uart/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: "POTEn:CV:STATUS?" })
        });
        const statusResult = await statusResponse.json();
        console.log(`📊 Initial Status → ${statusResult.response || statusResult.error}`);
    } catch (e) {
        console.error("❌ Status check failed:", e);
    }
    
    // Step 3: Send CV command with detailed parameters
    console.log("3️⃣ Sending CV Start Command...");
    const cvCommand = "POTEn:CV:Start:ALL -0.5,0.5,-0.5,0.1,1";
    console.log(`📡 Command: ${cvCommand}`);
    
    try {
        const startResponse = await fetch('/api/uart/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: cvCommand })
        });
        const startResult = await startResponse.json();
        console.log(`🚀 Start Response → ${startResult.response || startResult.error}`);
        
        if (!startResult.response || startResult.response.trim() !== "OK") {
            console.error("❌ STM32 did not respond with OK - measurement may not have started");
            return;
        }
    } catch (e) {
        console.error("❌ Start command failed:", e);
        return;
    }
    
    // Step 4: Monitor status changes
    console.log("4️⃣ Monitoring Status Changes...");
    let statusChecks = 0;
    const maxChecks = 20;
    
    const statusInterval = setInterval(async () => {
        statusChecks++;
        try {
            const response = await fetch('/api/uart/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: "POTEn:CV:STATUS?" })
            });
            const result = await response.json();
            const status = result.response?.trim() || "ERROR";
            
            console.log(`📊 Status Check #${statusChecks}: ${status}`);
            
            if (status === "COMPLETE" || statusChecks >= maxChecks) {
                clearInterval(statusInterval);
                console.log("5️⃣ Getting Final Data...");
                await getFinalData();
            }
        } catch (e) {
            console.error(`❌ Status check #${statusChecks} failed:`, e);
        }
    }, 1000); // Check every 1 second
}

// Function to get and analyze final data
async function getFinalData() {
    try {
        const dataResponse = await fetch('/api/uart/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: "POTEn:CV:DATA?" })
        });
        const dataResult = await dataResponse.json();
        const rawData = dataResult.response || "";
        
        console.log(`📊 Raw Data Length: ${rawData.length} characters`);
        console.log(`📊 Raw Data Preview: ${rawData.substring(0, 200)}...`);
        
        if (rawData.length > 0) {
            const lines = rawData.split('\n').filter(line => line.trim().length > 0);
            console.log(`📊 Data Lines: ${lines.length}`);
            
            // Analyze data structure
            if (lines.length > 1) {
                console.log(`📊 Header: ${lines[0]}`);
                console.log(`📊 First Data: ${lines[1]}`);
                if (lines.length > 2) {
                    console.log(`📊 Second Data: ${lines[2]}`);
                }
                if (lines.length > 5) {
                    console.log(`📊 Last Data: ${lines[lines.length - 1]}`);
                }
            }
            
            // Check if data looks like proper CV scan
            const dataLines = lines.filter(line => !line.startsWith('voltage,current'));
            if (dataLines.length < 20) {
                console.warn(`⚠️ Warning: Only ${dataLines.length} data points - expected 40+ for proper CV scan`);
                console.log("🔍 This suggests STM32 is not performing a full CV scan");
            } else {
                console.log(`✅ Good: ${dataLines.length} data points received`);
            }
            
        } else {
            console.error("❌ No data received from STM32");
        }
        
    } catch (e) {
        console.error("❌ Failed to get final data:", e);
    }
}

// Function to test different CV parameters
async function testDifferentParameters() {
    const testParams = [
        "POTEn:CV:Start:ALL -0.5,0.5,-0.5,0.05,1",  // Slow scan
        "POTEn:CV:Start:ALL -0.2,0.2,-0.2,0.1,1",   // Small range
        "POTEn:CV:Start:ALL -1.0,1.0,-1.0,0.1,1"    // Large range
    ];
    
    for (let i = 0; i < testParams.length; i++) {
        console.log(`🧪 Test ${i+1}: ${testParams[i]}`);
        
        try {
            const response = await fetch('/api/uart/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: testParams[i] })
            });
            const result = await response.json();
            console.log(`  Response: ${result.response || result.error}`);
            
            // Wait a bit between tests
            await new Promise(resolve => setTimeout(resolve, 2000));
            
        } catch (e) {
            console.error(`  Error: ${e}`);
        }
    }
}

// Function to check if STM32 is actually scanning
async function checkIfScanningActive() {
    console.log("🔍 Checking if STM32 is actively scanning...");
    
    // Send start command
    const startResponse = await fetch('/api/uart/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: "POTEn:CV:Start:ALL -0.5,0.5,-0.5,0.1,1" })
    });
    const startResult = await startResponse.json();
    console.log(`🚀 Start: ${startResult.response}`);
    
    // Check status immediately and after delays
    const delays = [1000, 3000, 5000, 10000]; // 1s, 3s, 5s, 10s
    
    for (const delay of delays) {
        await new Promise(resolve => setTimeout(resolve, delay));
        
        const statusResponse = await fetch('/api/uart/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: "POTEn:CV:STATUS?" })
        });
        const statusResult = await statusResponse.json();
        console.log(`📊 Status at +${delay/1000}s: ${statusResult.response}`);
        
        if (statusResult.response?.trim() === "COMPLETE") {
            console.log(`⚡ Measurement completed in ${delay/1000} seconds`);
            break;
        }
    }
}

console.log("🎯 Available debug functions:");
console.log("  - debugCVFlow() - Complete CV debugging flow");
console.log("  - testDifferentParameters() - Test various CV parameters");
console.log("  - checkIfScanningActive() - Check if STM32 is actually scanning");
console.log("  - getFinalData() - Get and analyze CV data");

// Auto-start debugging
console.log("🚀 Starting automatic CV flow debug...");
debugCVFlow();