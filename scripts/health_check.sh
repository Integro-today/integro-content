#!/bin/bash
# Simple health check script for Railway

PORT=${PORT:-8000}
MAX_TRIES=10
WAIT_TIME=2

echo "Health check on port $PORT..."

for i in $(seq 1 $MAX_TRIES); do
    if curl -f -s http://localhost:$PORT/health > /dev/null 2>&1; then
        echo "✅ Health check passed!"
        exit 0
    fi
    
    echo "Attempt $i/$MAX_TRIES failed, waiting ${WAIT_TIME}s..."
    sleep $WAIT_TIME
done

echo "❌ Health check failed after $MAX_TRIES attempts"
exit 1