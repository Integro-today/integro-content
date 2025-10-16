#!/bin/bash
# Main startup script that coordinates all services

echo "=========================================="
echo "Starting Integro Services"
echo "=========================================="

# Only run debugging and Qdrant on Railway
if [ -n "$RAILWAY_ENVIRONMENT" ]; then
    echo "🚂 Railway environment detected"
    
    # Run debug script if it exists (non-blocking)
    if [ -f /app/scripts/debug_qdrant_full.sh ]; then
        echo "📊 Running diagnostics..."
        /app/scripts/debug_qdrant_full.sh > ${RAILWAY_VOLUME_MOUNT_PATH:-/app/data}/logs/debug_full.log 2>&1 &
        echo "   (Debug output saved to logs/debug_full.log)"
    fi
    
    # Check if using external Qdrant
    if [ -n "$USE_EXTERNAL_QDRANT" ] || [ -n "$QDRANT_HOST" ]; then
        echo ""
        echo "📡 Using external Qdrant service"
        # Clean up any corrupted embedded Qdrant data
        if [ -f /app/scripts/clean_qdrant_wal.sh ]; then
            /app/scripts/clean_qdrant_wal.sh
        fi
    else
        # Start embedded Qdrant service
        echo ""
        /app/scripts/qdrant_startup.sh
        QDRANT_RESULT=$?
        
        if [ $QDRANT_RESULT -eq 0 ]; then
            echo "✅ Embedded Qdrant service started successfully"
        else
            echo "⚠️ Running without Qdrant (using in-memory storage)"
            export DISABLE_QDRANT=true
        fi
    fi
else
    echo "📍 Local environment - skipping Qdrant"
fi

# Start any other services here
# ...

echo ""
echo "🌐 Starting web server..."
echo "=========================================="

# Start the main application
echo "Starting on port: ${PORT:-8000}"
exec uvicorn integro.web_server:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --log-level info