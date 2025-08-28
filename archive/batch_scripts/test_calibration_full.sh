#!/bin/bash
# Test Cross-Instrument Calibration API using curl

echo "🔬 Testing Cross-Instrument Calibration API"
echo ""

# Test 1: Get measurement pairs
echo "1. Testing measurement pairs..."
PAIRS_RESPONSE=$(curl -s "http://localhost:5000/api/calibration/measurement-pairs")

if [[ $? -eq 0 ]]; then
    echo "   ✅ API accessible"
    
    # Parse response to get IDs
    STM32_ID=$(echo "$PAIRS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success') and data.get('pairs'):
        print(data['pairs'][0]['stm32_measurement']['id'])
    else:
        print('0')
except:
    print('0')
")
    
    PALMSENS_ID=$(echo "$PAIRS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success') and data.get('pairs'):
        print(data['pairs'][0]['palmsens_measurement']['id'])
    else:
        print('0')
except:
    print('0')
")
    
    echo "   📊 STM32 ID: $STM32_ID, PalmSens ID: $PALMSENS_ID"
    
    if [[ "$STM32_ID" != "0" && "$PALMSENS_ID" != "0" ]]; then
        echo ""
        echo "2. Testing calibration..."
        
        # Test 2: Perform calibration
        CALIBRATION_RESPONSE=$(curl -s -X POST "http://localhost:5000/api/calibration/calibrate" \
            -H "Content-Type: application/json" \
            -d "{\"stm32_measurement_id\": $STM32_ID, \"palmsens_measurement_id\": $PALMSENS_ID}")
        
        if [[ $? -eq 0 ]]; then
            echo "   ✅ Calibration API responded"
            
            # Parse calibration results
            echo "$CALIBRATION_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        result = data['calibration_result']
        print(f'   📈 R² Value: {result[\"r_squared\"]:.4f}')
        print(f'   🔧 Current Slope: {result[\"current_slope\"]:.6f}')
        print(f'   ⚡ Current Offset: {result[\"current_offset\"]:.3e}')
        print(f'   📊 Data Points: {result[\"data_points\"]}')
        
        quality = 'excellent' if result['r_squared'] > 0.95 else 'good' if result['r_squared'] > 0.8 else 'fair'
        print(f'   🏆 Quality: {quality.upper()}')
    else:
        print(f'   ❌ Calibration failed: {data.get(\"error\")}')
except Exception as e:
    print(f'   ❌ Parse error: {e}')
    print('   Raw response:')
    print(sys.stdin.read()[:300])
"
            
            echo ""
            echo "3. Testing calibration models..."
            
            # Test 3: Get calibration models
            MODELS_RESPONSE=$(curl -s "http://localhost:5000/api/calibration/models")
            
            echo "$MODELS_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        models = data.get('models', {})
        print(f'   ✅ Models available: {len(models)}')
        for key, model in models.items():
            print(f'   📋 Model {key}: R²={model[\"r_squared\"]:.4f}, Quality={model[\"quality\"]}')
    else:
        print(f'   ❌ Models API failed: {data.get(\"error\")}')
except Exception as e:
    print(f'   ❌ Parse error: {e}')
"
        else
            echo "   ❌ Calibration API failed"
        fi
    else
        echo "   ⚠️  No valid measurement pairs found"
    fi
else
    echo "   ❌ Cannot connect to server"
fi

echo ""
echo "🎯 Calibration API Test Complete!"