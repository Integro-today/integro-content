# Requirements Generation Guide

## Overview

This project uses `uv` to manage dependencies and generate `requirements.txt` from `pyproject.toml`.

## Why This Approach?

1. **Single Source of Truth**: `pyproject.toml` is the canonical source for dependencies
2. **Version Pinning**: `uv` automatically pins all transitive dependencies for reproducibility
3. **Optional Dependencies**: Voice features are optional extras, not required for basic functionality
4. **Docker Compatibility**: Both Dockerfile and Dockerfile.voice need `requirements.txt`

## Dependency Structure

### Main Dependencies (`pyproject.toml`)

All core dependencies are in `[project.dependencies]`:
- Agno framework
- FastAPI + Uvicorn
- Database drivers (PostgreSQL, SQLite, Qdrant)
- Document processing (pypdf, python-docx, etc.)
- ML/NLP (sentence-transformers, torch)
- Monitoring (prometheus, sentry)

### Optional Dependencies

#### `[project.optional-dependencies.dev]`
Development tools (not included in Docker builds):
- pytest, black, ruff, mypy
- ipython, watchdog
- httpie, locust

#### `[project.optional-dependencies.voice]`
LiveKit voice agent support (included in Docker builds):
- livekit>=0.1.0
- livekit-agents>=0.6.0
- livekit-plugins-assemblyai>=0.1.0
- livekit-plugins-cartesia>=0.1.0

## Generating requirements.txt

### For Production (with voice support)

```bash
uv pip compile pyproject.toml --extra voice -o requirements.txt
```

This generates a fully pinned requirements.txt with:
- All main dependencies
- Voice agent dependencies
- All transitive dependencies (586+ packages)

### For Testing (base only)

```bash
uv pip compile pyproject.toml -o requirements-base.txt
```

This generates requirements without voice support.

## File Comparison

### Old requirements.txt (integro-agents-wip)
- 107 lines
- Unpinned versions (e.g., `agno>=2.0.0`)
- Comments and grouping
- Voice dependencies inline

### New requirements.txt (integro-content)
- 641 lines
- Fully pinned versions (e.g., `agno==2.1.5`)
- All transitive dependencies
- Generated from pyproject.toml

## Docker Integration

### Automatic Generation During Build

Both Dockerfiles now use **multi-stage builds** to automatically generate `requirements.txt` from `pyproject.toml`:

#### Stage 1: Generate requirements.txt
```dockerfile
FROM python:3.11-slim AS requirements-builder
WORKDIR /build
RUN pip install --no-cache-dir uv
COPY pyproject.toml .
RUN uv pip compile pyproject.toml --extra voice -o requirements.txt
```

#### Stage 2: Build application
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY --from=requirements-builder /build/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

### Benefits

1. **Always Fresh**: requirements.txt is generated during every build
2. **Single Source of Truth**: pyproject.toml is the only dependency file to maintain
3. **No Drift**: Impossible for requirements.txt to be out of sync
4. **Cached Layers**: Docker caches the requirements generation step
5. **No Manual Updates**: Just edit pyproject.toml and rebuild

### Build Process

```bash
# Docker automatically:
# 1. Creates requirements-builder stage
# 2. Installs uv
# 3. Generates requirements.txt from pyproject.toml
# 4. Copies requirements.txt to main stage
# 5. Installs all dependencies
docker-compose build backend
docker-compose build voice-agent
```

Both Dockerfiles use the same multi-stage approach with voice extras included.

## Key Packages Added

### LiveKit Voice Support
- `livekit==1.0.16` - Core LiveKit SDK
- `livekit-agents==1.2.15` - Agent framework
- `livekit-api==1.0.7` - API client
- `livekit-plugins-assemblyai==1.2.15` - AssemblyAI integration
- `livekit-plugins-cartesia==1.2.15` - Cartesia voice synthesis

### Additional Dependencies (from voice extras)
- `av==15.1.0` - Audio/video processing
- `sounddevice==0.5.2` - Audio device access
- `colorama==0.4.6` - Terminal colors
- `nest-asyncio==1.6.0` - Nested event loop support
- `pyjwt==2.10.1` - JWT token handling
- OpenTelemetry packages for monitoring

## Maintenance

### When to Update

Update dependencies when:
1. Adding/removing dependencies in `pyproject.toml`
2. Updating version constraints
3. Security updates require new pins
4. Docker build fails due to missing dependencies

### Update Process

#### Using Makefile (Recommended)

```bash
# 1. Edit pyproject.toml
vim pyproject.toml

# 2. Update lock file and regenerate requirements.txt
make lock
make requirements

# 3. Test locally (optional, Docker auto-generates)
make install

# 4. Test Docker build
make docker-build

# 5. Commit changes
git add pyproject.toml uv.lock requirements.txt
git commit -m "Update dependencies"
```

#### Manual Process

```bash
# 1. Edit pyproject.toml
vim pyproject.toml

# 2. Update uv.lock file (includes all extras by default)
uv lock

# 3. Regenerate requirements.txt
uv pip compile pyproject.toml --extra voice -o requirements.txt

# 4. Test locally
uv sync --extra voice

# 5. Test Docker build
docker-compose build backend
docker-compose build voice-agent

# 6. Commit changes
git add pyproject.toml uv.lock requirements.txt
git commit -m "Update dependencies"
```

### Important Files

1. **pyproject.toml** - Source of truth for dependencies
2. **uv.lock** - Locked versions for reproducibility
3. **requirements.txt** - Auto-generated during Docker build (or manually with `make requirements`)

**Note**: Docker builds will auto-generate `requirements.txt` from `pyproject.toml`, so you don't strictly need to commit `requirements.txt`. However, keeping it in the repo allows for faster builds via Docker layer caching.

## Troubleshooting

### Missing Packages in Docker

If Docker build fails with "package not found":
1. Check if package is in `pyproject.toml`
2. Regenerate requirements.txt with `--extra voice`
3. Verify package is in requirements.txt: `grep package_name requirements.txt`

### Version Conflicts

If uv reports version conflicts:
1. Check incompatible version constraints in pyproject.toml
2. Review dependency tree: `uv pip tree`
3. Loosen constraints if needed
4. Re-compile

### Large Image Size

The requirements.txt includes heavy packages:
- torch (ML framework) ~2GB
- CUDA libraries ~1GB each
- sentence-transformers models

To reduce size:
- Use multi-stage Docker builds
- Remove unused ML dependencies
- Use CPU-only torch builds

## Reference

- **uv Documentation**: https://github.com/astral-sh/uv
- **PEP 621**: https://peps.python.org/pep-0621/ (pyproject.toml standard)
- **Old requirements.txt**: `/home/ben/integro-agents-wip/requirements.txt`
- **New requirements.txt**: `/home/ben/integro-content/requirements.txt`

---

**Last Updated**: 2025-10-15
**Generated with**: `uv pip compile pyproject.toml --extra voice -o requirements.txt`
