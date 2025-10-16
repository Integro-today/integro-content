#!/bin/bash

# Setup and run Integro tests with uv

echo "======================================"
echo "    INTEGRO UV SETUP & TEST"
echo "======================================"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "✓ uv installed"
    echo ""
fi

# Create virtual environment with uv
echo "Creating virtual environment with uv..."
uv venv --python 3.11
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies with uv
echo "Installing dependencies..."
uv pip install -e .
uv pip install pytest pytest-asyncio
echo "✓ Dependencies installed"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Copy .env.example to .env and add your GROQ_API_KEY"
    echo ""
    read -p "Do you want to create .env from example? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp .env.example .env
        echo "✓ Created .env file. Please edit it to add your GROQ_API_KEY"
        echo "  Then run this script again."
        exit 0
    fi
fi

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check for GROQ_API_KEY
if [ -z "$GROQ_API_KEY" ]; then
    echo "❌ Error: GROQ_API_KEY not found"
    echo "   Please set GROQ_API_KEY in your .env file"
    exit 1
fi

echo "✓ GROQ_API_KEY found"
echo ""

# Run tests
echo "Running E2E tests with pytest..."
echo "======================================"
echo ""

python -m pytest test_e2e.py -v

echo ""
echo "======================================"
echo "Test run complete!"
echo ""
echo "To run tests again, use:"
echo "  source .venv/bin/activate"
echo "  python -m pytest test_e2e.py -v"