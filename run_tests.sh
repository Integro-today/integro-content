#!/bin/bash

# Run Integro E2E Test Suite

echo "======================================"
echo "    INTEGRO E2E TEST RUNNER"
echo "======================================"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Copy .env.example to .env and add your GROQ_API_KEY"
    echo ""
fi

# Check for GROQ_API_KEY
if [ -z "$GROQ_API_KEY" ]; then
    # Try to load from .env
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
    fi
    
    if [ -z "$GROQ_API_KEY" ]; then
        echo "❌ Error: GROQ_API_KEY not found"
        echo "   Please set GROQ_API_KEY in your .env file or environment"
        exit 1
    fi
fi

echo "✓ GROQ_API_KEY found"
echo ""

# Install dependencies if needed
if ! python -c "import integro" 2>/dev/null; then
    echo "Installing Integro package..."
    pip install -e . > /dev/null 2>&1
    echo "✓ Integro installed"
    echo ""
fi

# Run tests
echo "Running E2E tests..."
echo "======================================"
echo ""

python test_e2e.py

echo ""
echo "======================================"
echo "Test run complete!"