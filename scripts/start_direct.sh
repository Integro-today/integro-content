#!/bin/bash
# Direct startup script without KB debug (faster deployment)

echo "=========================================="
echo "Starting Integro Therapeutic Workflow"
echo "Direct mode - KB debug disabled for fast startup"
echo "=========================================="

# Start the main application directly
exec uvicorn integro.web_server:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --log-level info