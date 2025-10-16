#!/bin/bash
# Modular Qdrant startup script for Railway
# Returns 0 if Qdrant starts successfully, 1 if fallback mode enabled

echo "=========================================="
echo "🔍 Qdrant Service Startup"
echo "=========================================="

# Exit immediately if not on Railway or using external Qdrant
if [ -z "$RAILWAY_ENVIRONMENT" ]; then
    echo "📍 Not on Railway - skipping Qdrant"
    exit 0
fi

if [ -n "$USE_EXTERNAL_QDRANT" ] || [ -n "$QDRANT_HOST" ]; then
    echo "📍 Using external Qdrant service - skipping local startup"
    exit 0
fi

# Configuration
DATA_PATH="${RAILWAY_VOLUME_MOUNT_PATH:-/app/data}"
QDRANT_LOG="$DATA_PATH/logs/qdrant.log"
QDRANT_CONFIG="$DATA_PATH/qdrant/config.yaml"

# Ensure directories exist
mkdir -p "$DATA_PATH/logs" "$DATA_PATH/qdrant/storage" "$DATA_PATH/qdrant/snapshots"

# Step 1: Test Qdrant binary
echo "🔍 Testing Qdrant binary..."
qdrant --version > /tmp/qdrant_test.log 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "❌ Qdrant binary failed (exit code: $EXIT_CODE)"
    echo "   Error output:"
    cat /tmp/qdrant_test.log | head -5 | sed 's/^/   | /'
    
    # Check if it's a WAL corruption issue
    if grep -q "Resource temporarily unavailable\|WAL error" /tmp/qdrant_test.log 2>/dev/null; then
        echo "🔧 Detected WAL corruption - clearing old data..."
        rm -rf "$DATA_PATH/qdrant/storage/collections"/*
        rm -rf "$DATA_PATH/qdrant/storage/raft_state.json"
        echo "✅ Cleared corrupted data"
    fi
    
    # Check specific error codes
    if [ $EXIT_CODE -eq 101 ] || [ $EXIT_CODE -eq 139 ]; then
        echo "   💡 This indicates binary incompatibility with Railway's environment"
    elif [ $EXIT_CODE -eq 127 ]; then
        echo "   💡 Qdrant binary not found in PATH"
    fi
    
    echo "⚠️ Enabling fallback mode (in-memory storage)"
    export DISABLE_QDRANT=true
    touch "$DATA_PATH/qdrant_disabled"
    exit 1
fi

echo "✅ Qdrant binary OK"

# Step 2: Create optimized config
echo "📝 Creating Qdrant configuration..."
cat > "$QDRANT_CONFIG" << EOF
log_level: INFO
storage:
  storage_path: $DATA_PATH/qdrant/storage
  snapshots_path: $DATA_PATH/qdrant/snapshots
  on_disk_payload: true
  wal:
    wal_capacity_mb: 4
  performance:
    max_optimization_threads: 1
  hnsw_index:
    on_disk: true
    m: 8
service:
  host: 127.0.0.1
  http_port: 6333
  grpc_port: 6334
  max_request_size_mb: 2
telemetry_disabled: true
EOF

# Step 3: Set memory limits
echo "🔧 Setting memory constraints..."
ulimit -v 524288  # 512MB virtual memory limit

# Step 4: Clean WAL if it exists (prevents corruption issues)
if [ -f "$DATA_PATH/qdrant/storage/raft_state.json" ]; then
    echo "🔧 Cleaning potential WAL corruption..."
    rm -f "$DATA_PATH/qdrant/storage/raft_state.json"
    rm -rf "$DATA_PATH/qdrant/storage/collections"/*/wal
    echo "✅ Cleaned WAL files"
fi

# Step 5: Start Qdrant with immediate error capture
echo "🚀 Starting Qdrant..."

# First, try a quick test start to catch immediate failures
timeout 3 qdrant --config-path "$QDRANT_CONFIG" > "$QDRANT_LOG" 2>&1
TEST_RESULT=$?

if [ $TEST_RESULT -ne 124 ]; then
    # It exited before timeout - check for WAL error
    if grep -q "Resource temporarily unavailable\|WAL error\|Can't init WAL" "$QDRANT_LOG" 2>/dev/null; then
        echo "⚠️ WAL corruption detected - clearing all data..."
        rm -rf "$DATA_PATH/qdrant/storage"
        mkdir -p "$DATA_PATH/qdrant/storage"
        echo "✅ Cleared all Qdrant data - will start fresh"
        
        # Try again with clean slate
        timeout 3 qdrant --config-path "$QDRANT_CONFIG" > "$QDRANT_LOG" 2>&1
        TEST_RESULT=$?
    fi
    
    if [ $TEST_RESULT -ne 124 ]; then
        echo "❌ Qdrant crashed immediately!"
        echo "   Last error lines:"
        tail -10 "$QDRANT_LOG" | sed 's/^/   | /'
        
        echo "⚠️ Enabling fallback mode"
        export DISABLE_QDRANT=true
        touch "$DATA_PATH/qdrant_disabled"
        exit 1
    fi
fi

# Now start for real
qdrant --config-path "$QDRANT_CONFIG" >> "$QDRANT_LOG" 2>&1 &
QDRANT_PID=$!
echo "   PID: $QDRANT_PID"

# Step 6: Wait for readiness
echo "⏳ Waiting for Qdrant to be ready..."
for i in {1..20}; do
    # Check if process is still alive
    if ! kill -0 $QDRANT_PID 2>/dev/null; then
        echo "❌ Qdrant process died!"
        echo "   Last log lines:"
        tail -10 "$QDRANT_LOG" | sed 's/^/   | /'
        
        echo "⚠️ Enabling fallback mode"
        export DISABLE_QDRANT=true
        touch "$DATA_PATH/qdrant_disabled"
        exit 1
    fi
    
    # Check if API is responding
    if curl -s http://localhost:6333/readyz > /dev/null 2>&1; then
        echo "✅ Qdrant is ready!"
        
        # Export PID for monitoring
        echo $QDRANT_PID > "$DATA_PATH/qdrant.pid"
        exit 0
    fi
    
    sleep 1
done

# Timeout reached
echo "⚠️ Qdrant did not become ready in time"
kill $QDRANT_PID 2>/dev/null || true

echo "⚠️ Enabling fallback mode"
export DISABLE_QDRANT=true
touch "$DATA_PATH/qdrant_disabled"
exit 1