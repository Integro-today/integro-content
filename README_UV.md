# Using UV with Integro

[UV](https://github.com/astral-sh/uv) is a fast Python package installer and resolver, written in Rust. It's a drop-in replacement for pip and pip-tools, and is 10-100x faster.

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Run the automated setup script
./uv_setup.sh
```

This script will:
1. Install `uv` if not present
2. Create a virtual environment
3. Install all dependencies
4. Check for `.env` configuration
5. Run the test suite

### Option 2: Manual Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv --python 3.11

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Integro in development mode
uv pip install -e .

# Install test dependencies
uv pip install pytest pytest-asyncio

# Setup environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# Run tests
python -m pytest test_e2e.py -v
```

## UV Commands Reference

### Environment Management

```bash
# Create virtual environment with specific Python version
uv venv --python 3.11

# Create virtual environment with system Python
uv venv

# Remove virtual environment
rm -rf .venv
```

### Package Management

```bash
# Install package
uv pip install package_name

# Install from requirements.txt
uv pip install -r requirements.txt

# Install in editable/development mode
uv pip install -e .

# Install with optional dependencies
uv pip install -e ".[dev]"

# List installed packages
uv pip list

# Show package info
uv pip show integro

# Uninstall package
uv pip uninstall package_name
```

### Dependency Resolution

```bash
# Compile requirements (like pip-compile)
uv pip compile requirements.in -o requirements.txt

# Sync environment with requirements
uv pip sync requirements.txt

# Upgrade all packages
uv pip install --upgrade -r requirements.txt
```

## Running Tests with UV

After setting up the environment:

```bash
# Activate environment
source .venv/bin/activate

# Run all tests
python -m pytest test_e2e.py -v

# Run specific test
python -m pytest test_e2e.py::TestIntegroE2E::test_word_repetition_simple -v

# Run with coverage
uv pip install pytest-cov
python -m pytest test_e2e.py --cov=integro --cov-report=html

# Run in parallel (faster)
uv pip install pytest-xdist
python -m pytest test_e2e.py -n auto
```

## Development Workflow

```bash
# 1. Create/activate environment
uv venv && source .venv/bin/activate

# 2. Install in dev mode with all dependencies
uv pip install -e ".[dev]"

# 3. Run formatter
black integro/ test_e2e.py

# 4. Run linter
ruff check integro/

# 5. Run tests
pytest test_e2e.py -v

# 6. Deactivate when done
deactivate
```

## Advantages of UV

1. **Speed**: 10-100x faster than pip
2. **Reliability**: Better dependency resolution
3. **Compatibility**: Drop-in replacement for pip
4. **Memory Efficient**: Uses less memory than pip
5. **Better Caching**: Smarter package caching

## Troubleshooting

### UV not found
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Permission denied
```bash
chmod +x uv_setup.sh
./uv_setup.sh
```

### GROQ_API_KEY missing
```bash
cp .env.example .env
# Edit .env and add: GROQ_API_KEY=your_key_here
```

### Clear cache (if packages are corrupted)
```bash
uv cache clean
```

### Recreate environment from scratch
```bash
rm -rf .venv
uv venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[dev]"
```