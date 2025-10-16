#!/bin/bash
# Startup script with knowledge base debugging for Railway

echo "=========================================="
echo "Starting Integro Therapeutic Workflow"
echo "=========================================="

# Run KB debug script with timeout (max 3 seconds)
echo "Running knowledge base debug check (max 3 seconds)..."
timeout 3 python /app/scripts/debug_kb_on_startup.py || echo "KB debug check timed out or failed - continuing..."

echo ""
echo "Starting main application..."
echo "=========================================="

# Start the main application
exec uvicorn integro.web_server:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --log-level info