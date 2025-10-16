# Integro Testing Guide

## Overview

The Integro test suite uses `pytest-recording` to cache API responses, preventing rate limiting and allowing offline testing.

## Test Files

- `test_simple.py` - Simple tests with delays and recording
- `test_offline.py` - Offline-only tests using cached responses
- `test_e2e.py` - Full end-to-end tests (may hit rate limits)

## Running Tests

### Using Make (Recommended)

```bash
# Run simple tests (uses cassettes after first run)
make test

# Run tests offline only (no API calls)
make test-offline

# Run tests in parallel
make test-fast

# Run with verbose output
make test-verbose

# Run full e2e tests (WARNING: may hit rate limits)
make test-e2e
```

### Direct pytest

```bash
# Run with recording (creates cassettes on first run)
pytest test_simple.py -v

# Run offline only (fails if cassettes missing)
pytest test_offline.py -v

# Force new recordings
pytest test_simple.py -v --record-mode=rewrite
```

## How Recording Works

1. **First Run**: Tests make real API calls and save responses to `cassettes/` directory
2. **Subsequent Runs**: Tests use cached responses from cassettes
3. **Offline Mode**: Tests with `record_mode="none"` will fail if they try to make real API calls

## Cassette Management

```bash
# View cassettes
ls -la cassettes/

# Clear cassettes to force new recordings
rm -rf cassettes/

# Copy cassettes for offline testing
cp -r cassettes/test_simple cassettes/test_offline
```

## Rate Limiting Protection

- Tests include 2-second delays between API calls
- Tool call limits set to prevent loops
- Cassettes eliminate API calls after first run

## Supported Groq Models

Only these models are configured for testing:
- `llama-3.1-8b-instant`
- `openai/gpt-oss-20b`
- `openai/gpt-oss-120b`
- `moonshotai/kimi-k2-instruct`

## Troubleshooting

### Tests hitting API despite cassettes
- Check cassette files exist in `cassettes/` directory
- Ensure test names match cassette filenames
- Verify `record_mode` is not set to `rewrite` or `new_episodes`

### Rate limit errors
- Use `make test` instead of `make test-e2e`
- Add longer delays in `test_simple.py` (increase `API_DELAY`)
- Use offline tests: `make test-offline`

### Cassette not found
- Run `make test` first to create cassettes
- Check cassette naming matches test function names

## CI/CD Integration

For CI environments, commit the `cassettes/` directory to ensure tests can run offline:

```yaml
# GitHub Actions example
- name: Run tests offline
  run: |
    source .venv/bin/activate
    make test-offline
```

This ensures tests run quickly and don't require API keys in CI.