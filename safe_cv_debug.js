// Fixed CV debugging with proper delays to avoid rate limiting
console.log("🔧 Rate-Limited Safe CV Debugging Tools");

// Helper function to wait
const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Safe SCPI command sender with rate limiting protection
async function safeSendCommand(command, waitTime = 1000) {
    try {
        console.log(`📡 Sending: ${command}`);
        
        const response = await fetch('/api/uart/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: command })
        });
        
        const result = await response.json();
        
        if (response.status === 429) {
            console.warn(`⚠️ Rate limited for ${command}, waiting longer...`);
            await wait(2000); // Wait 2 seconds for rate limit
            return await safeSendCommand(command, waitTime); // Retry
        }
        
        console.log(`📥 Response: ${result.response || result.error}`);
        await wait(waitTime); // Wait before next command
        
        return result;
        
    } catch (error) {
        console.error(`❌ Error sending ${command}:`, error);
        await wait(waitTime);
        return { error: error.message };
    }
}

// Safe CV debugging with proper timing
async function safeCVDebug() {
    console.log("🔍 === Safe CV Debugging (Rate-Limited Protected) ===");
    
    // Step 1: Check connection
    console.log("1️⃣ Testing Connection...");
    await safeSendCommand("*IDN?", 1500);
    
    // Step 2: Check initial status
    console.log("2️⃣ Initial Status...");
    await safeSendCommand("POTEn:CV:STATUS?", 1500);
    
    // Step 3: Start CV with safe parameters
    console.log("3️⃣ Starting CV Measurement...");
    const cvCommand = "POTEn:CV:Start:ALL -0.5,0.5,-0.5,0.1,1";
    const startResult = await safeSendCommand(cvCommand, 2000);
    
    if (!startResult.response || !startResult.response.includes("OK")) {
        console.error("❌ CV Start failed - STM32 did not respond with OK");
        return;
    }
    
    console.log("✅ CV Started successfully, monitoring...");
    
    // Step 4: Monitor status (slower polling)
    console.log("4️⃣ Monitoring Status (every 3 seconds)...");
    
    for (let i = 1; i <= 10; i++) {
        console.log(`📊 Status check ${i}/10...`);
        const statusResult = await safeSendCommand("POTEn:CV:STATUS?", 3000);
        
        if (statusResult.response?.includes("COMPLETE")) {
            console.log(`🏁 Measurement completed after ${i * 3} seconds`);
            break;
        } else if (statusResult.response?.includes("MEASURING")) {
            console.log(`⚡ Still measuring... (${i * 3}s elapsed)`);
        } else {
            console.log(`❓ Status: ${statusResult.response || "Unknown"}`);
        }
    }
    
    // Step 5: Get final data
    console.log("5️⃣ Getting Final Data...");
    await wait(2000); // Extra wait before data request
    const dataResult = await safeSendCommand("POTEn:CV:DATA?", 1000);
    
    if (dataResult.response) {
        analyzeCVData(dataResult.response);
    }
}

// Analyze CV data to determine if it's a real scan
function analyzeCVData(rawData) {
    console.log("📊 === CV Data Analysis ===");
    console.log(`Raw data length: ${rawData.length} characters`);
    
    const lines = rawData.split('\n').filter(line => line.trim().length > 0);
    console.log(`Total lines: ${lines.length}`);
    
    // Show first few lines
    console.log("First 5 lines:");
    lines.slice(0, 5).forEach((line, i) => {
        console.log(`  ${i+1}: ${line}`);
    });
    
    // Filter out header
    const dataLines = lines.filter(line => !line.startsWith('voltage,current'));
    console.log(`Data points: ${dataLines.length}`);
    
    if (dataLines.length <= 5) {
        console.error("🚨 PROBLEM CONFIRMED: Only 5 data points!");
        console.log("📝 This means:");
        console.log("  - STM32 received the command");
        console.log("  - STM32 responded with 'OK'");
        console.log("  - BUT STM32 is NOT performing a full CV scan");
        console.log("  - STM32 is only sending 5 test/sample points");
        
        console.log("🔧 Possible solutions:");
        console.log("  1. Check STM32 firmware CV implementation");
        console.log("  2. Verify working electrode connection");
        console.log("  3. Try different voltage ranges");
        console.log("  4. Check current range settings");
        
        // Show the 5 points we got
        console.log("📊 The 5 points received:");
        dataLines.forEach((line, i) => {
            const parts = line.split(',');
            if (parts.length >= 2) {
                console.log(`  Point ${i+1}: V=${parts[0]}, I=${parts[1]}`);
            }
        });
        
    } else if (dataLines.length < 20) {
        console.warn(`⚠️ Warning: Only ${dataLines.length} points (expected 40+)`);
        console.log("This suggests incomplete CV scan");
    } else {
        console.log(`✅ Good: ${dataLines.length} data points - proper CV scan`);
    }
}

// Quick status monitor without rate limiting issues
async function quickStatusCheck() {
    console.log("⚡ Quick Status Check (safe timing)");
    
    for (let i = 1; i <= 5; i++) {
        console.log(`Check ${i}/5...`);
        await safeSendCommand("POTEn:CV:STATUS?", 2000);
    }
}

// Test just the data command
async function testDataOnly() {
    console.log("📊 Testing Data Command Only");
    await wait(1000);
    const result = await safeSendCommand("POTEn:CV:DATA?", 1000);
    
    if (result.response) {
        analyzeCVData(result.response);
    }
}

console.log("🎯 Available safe debug functions:");
console.log("  - safeCVDebug() - Complete safe CV debug");
console.log("  - quickStatusCheck() - Just check status");
console.log("  - testDataOnly() - Just get current data");
console.log("  - analyzeCVData(data) - Analyze data manually");

console.log("⚠️  All commands have proper delays to avoid rate limiting");