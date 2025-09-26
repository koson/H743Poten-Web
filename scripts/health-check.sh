#!/bin/bash

echo "🏥 H743 Potentiostat Health Check"
echo "================================="
echo "Time: $(date)"
echo ""

# Define targets
declare -A TARGETS=(
    ["Local"]="localhost:8080"
    ["Home Pi"]="192.168.1.100:8080"
    ["Office Pi"]="192.168.2.100:8080"
)

check_service() {
    local name="$1"
    local url="$2"
    
    printf "%-15s " "$name:"
    
    # Try health endpoint first, then main page
    if curl -s --max-time 5 "http://$url/health" > /dev/null 2>&1; then
        echo "✅ Online (Health OK)"
        return 0
    elif curl -s --max-time 5 "http://$url/" > /dev/null 2>&1; then
        echo "✅ Online (Web OK)"
        return 0
    else
        echo "❌ Offline"
        return 1
    fi
}

total_services=0
online_services=0

for name in "${!TARGETS[@]}"; do
    url="${TARGETS[$name]}"
    total_services=$((total_services + 1))
    
    if check_service "$name" "$url"; then
        online_services=$((online_services + 1))
    fi
done

echo ""
echo "Summary: $online_services/$total_services services online"

if [ $online_services -eq $total_services ]; then
    echo "🎉 All services are healthy!"
    exit 0
elif [ $online_services -gt 0 ]; then
    echo "⚠️  Some services are offline"
    exit 1
else
    echo "🚨 All services are offline!"
    exit 2
fi
