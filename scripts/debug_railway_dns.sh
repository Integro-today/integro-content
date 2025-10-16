#!/bin/bash
# Debug script for Railway internal DNS issues

echo "=========================================="
echo "🔍 Railway DNS Debugging"
echo "=========================================="

# Check environment
echo ""
echo "1️⃣ Environment Check:"
echo "   RAILWAY_ENVIRONMENT: ${RAILWAY_ENVIRONMENT:-not set}"
echo "   QDRANT_HOST: ${QDRANT_HOST:-not set}"
echo "   QDRANT_PORT: ${QDRANT_PORT:-not set}"

# Try DNS resolution
echo ""
echo "2️⃣ DNS Resolution Tests:"

# Function to test DNS
test_dns() {
    local hostname=$1
    echo -n "   Testing $hostname: "
    
    # Try nslookup
    if command -v nslookup >/dev/null 2>&1; then
        if nslookup "$hostname" >/dev/null 2>&1; then
            echo "✅ Resolved"
            nslookup "$hostname" 2>/dev/null | grep -A1 "Name:" | tail -1
        else
            echo "❌ Failed"
        fi
    # Try getent
    elif command -v getent >/dev/null 2>&1; then
        if getent hosts "$hostname" >/dev/null 2>&1; then
            echo "✅ Resolved"
            getent hosts "$hostname"
        else
            echo "❌ Failed"
        fi
    # Try ping
    elif ping -c 1 "$hostname" >/dev/null 2>&1; then
        echo "✅ Reachable"
    else
        echo "❌ Not found"
    fi
}

# Test various possible names
test_dns "qdrant.railway.internal"
test_dns "qdrant-staging.railway.internal"
test_dns "${QDRANT_HOST}"

# Try to discover services (if railway CLI available)
echo ""
echo "3️⃣ Service Discovery:"
if command -v railway >/dev/null 2>&1; then
    echo "   Railway CLI found - attempting service list..."
    railway status 2>/dev/null || echo "   ⚠️ Railway CLI not authenticated"
else
    echo "   ⚠️ Railway CLI not available"
fi

# Test connectivity with curl
echo ""
echo "4️⃣ Connection Tests:"
if [ -n "$QDRANT_HOST" ]; then
    echo -n "   Testing http://${QDRANT_HOST}:${QDRANT_PORT:-6333}/health: "
    if curl -s --max-time 5 "http://${QDRANT_HOST}:${QDRANT_PORT:-6333}/health" >/dev/null 2>&1; then
        echo "✅ Connected"
    else
        echo "❌ Failed ($(curl -s --max-time 5 "http://${QDRANT_HOST}:${QDRANT_PORT:-6333}/health" 2>&1 | head -1))"
    fi
fi

echo ""
echo "=========================================="
echo "💡 Debugging Tips:"
echo "   1. Check exact service name in Railway dashboard"
echo "   2. Ensure both services are in same environment"
echo "   3. Try using public URL if internal DNS fails"
echo "   4. Verify Qdrant service is running and healthy"
echo "=========================================="