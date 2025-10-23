# Quick Reference Guide

## Quick Start

### 1. Build and Start Services

```bash
make docker-build && make docker-up
```

### 2. Access Services

- **Backend:** http://localhost:8888
- **Frontend:** http://localhost:8889
- **Qdrant:** http://localhost:6333
- **Simulation Viewer:** http://localhost:8890

### 3. Run Single Simulation Test

```bash
docker exec integro_simulation_backend python test_two_agent_simulation.py \
    --workflow-id roots_of_healing_-_day_1_workflow_1 \
    --persona-id ellen_persona_4 \
    --max-rounds 20 \
    --output Agents/test_simulations/roots_ellen_test.json
```

### 4. Run Full Batch Test (All 13 Personas)

```bash
docker exec integro_simulation_backend python test_roots_healing_batch.py
```

### 5. Start Simulation Viewer

```bash
docker exec -d integro_simulation_backend python simulation_viewer.py
# Then visit http://localhost:8890
# - Select "Most Recent" to see latest simulations first
# - Browse through 470+ simulations with dropdown selector
```

---

## Common Commands

### Docker Management

```bash
# Start all services
make docker-up

# Stop all services
make docker-down

# View logs
make docker-logs

# Rebuild containers
make docker-build

# Check service status
docker-compose ps
```

### Database Operations

```bash
# Access PostgreSQL
docker exec -it integro_simulation_db psql -U integro -d integro

# Backup database
docker exec integro_simulation_db pg_dump -U integro integro > backup.sql

# Restore database
docker exec -i integro_simulation_db psql -U integro integro < backup.sql
```

### Qdrant Operations

```bash
# Check Qdrant status
docker exec integro_simulation_qdrant wget -O- http://localhost:6333/health

# View collections via CLI
curl http://localhost:6333/collections

# Browse UI
open http://localhost:6333/dashboard
```

---

## Simulation Workflows

### Single Simulation

**Test specific workflow vs persona:**

```bash
docker exec integro_simulation_backend python test_two_agent_simulation.py \
    --workflow-id <workflow_id> \
    --persona-id <persona_id> \
    --max-rounds 20 \
    --output Agents/test_simulations/test.json
```

**Available workflow IDs:**
- `intentions_workflow_8`
- `roots_of_healing_-_day_1_workflow_1`
- `roots_of_healing_-_day_1_workflow_(version_2)_workflow_1`
- `roots_of_healing_-_day_1_workflow_(version_3)_workflow_1`

**Available persona IDs:** See [personas.md](./personas.md) for full list

### Batch Testing

**Test Roots of Healing against all personas:**

```bash
docker exec integro_simulation_backend python test_roots_healing_batch.py
```

**Test intentions workflow:**

```bash
docker exec integro_simulation_backend python test_mixed_persona_batch.py
```

**Output location:**
```
Agents/batch_simulations/roots_healing_all_personas_YYYYMMDD_HHMMSS/
```

---

## Agent Creation

### Create Agent from Markdown

**Basic agent:**

```bash
docker exec integro_simulation_backend python create_agent_from_md.py \
    Agents/workflow.md --type workflow
```

**With knowledge base:**

```bash
docker exec integro_simulation_backend python create_agent_from_md.py \
    Agents/workflow.md --type workflow \
    --knowledge Agents/knowledge/doc1.pdf \
    --knowledge Agents/knowledge/doc2.epub
```

**With custom knowledge base name:**

```bash
docker exec integro_simulation_backend python create_agent_from_md.py \
    Agents/workflow.md --type workflow \
    --kb-name "My Knowledge Base" \
    --knowledge Agents/knowledge/*.pdf
```

---

## Evaluation

### Using simulation-evaluator Subagent

**Evaluate batch directory:**

```
Task(
  subagent_type="simulation-evaluator",
  description="Evaluate roots V6 simulations",
  prompt="Evaluate all therapeutic conversation simulations in:
  Agents/batch_simulations/roots_v6_batch_YYYYMMDD_HHMMSS/

  Create detailed JSON analysis reports and provide batch summary."
)
```

### Using evaluate_simulation.py

**Basic evaluation:**

```bash
docker exec integro_simulation_backend python evaluate_simulation.py \
    --simulation "Agents/test_simulations/roots_ellen_test.json" \
    --workflow "Agents/roots_of_healing_workflow_3.md"
```

**With agent caching (faster):**

```bash
# First run - save agent
docker exec integro_simulation_backend python evaluate_simulation.py \
    --simulation "path/to/simulation.json" \
    --workflow "path/to/workflow.md" \
    --save-agent

# Subsequent runs - reuse agent
docker exec integro_simulation_backend python evaluate_simulation.py \
    --simulation "path/to/simulation.json" \
    --workflow "path/to/workflow.md" \
    --agent-id simulation_evaluator_workflow_1
```

---

## Simulation Viewer

### Start Viewer

```bash
# Scan all directories
docker exec -d integro_simulation_backend python simulation_viewer.py

# Specific directory
docker exec -d integro_simulation_backend python simulation_viewer.py \
    Agents/test_simulations/

# Specific file
docker exec -d integro_simulation_backend python simulation_viewer.py \
    Agents/test_simulations/roots_ellen_test.json
```

### Access

**URL:** http://localhost:8890

**Features:**
- Select "Most Recent" to see latest simulations
- Browse 470+ simulations via dropdown
- View color-coded messages (blue=workflow, green=persona)

---

## Development

### Makefile Commands

```bash
make install          # Install dependencies with uv
make docker-build     # Build containers (auto-generates requirements.txt)
make docker-up        # Start all services
make docker-logs      # View container logs
make test-simulation  # Run single simulation test
make docker-down      # Stop all services
```

### Python Dependencies

```bash
# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .

# Update dependencies
uv add <package>
```

### Git Operations

```bash
# Check status
git status

# Create feature branch
git checkout -b feature/your-feature

# Commit changes
git add .
git commit -m "Your message"

# Push to remote
git push origin feature/your-feature
```

---

## File Locations

### Agent Definitions

- **Workflows:** `Agents/roots_of_healing_workflow_*.md`
- **Personas:** `Agents/personas/*_Persona_*.md`
- **Tegra Voice:** `Agents/tegra_voice.md`

### Simulations

- **Test outputs:** `Agents/test_simulations/`
- **Batch outputs:** `Agents/batch_simulations/`
- **Historical:** `Agents/simulations/`

### Knowledge Base

- **Documents:** `Agents/knowledge/`
- **Qdrant collections:** Accessible via http://localhost:6333/dashboard

### Scripts

- **Testing:** `test_two_agent_simulation.py`, `test_roots_healing_batch.py`
- **Evaluation:** `evaluate_simulation.py`
- **Agent creation:** `create_agent_from_md.py`
- **Viewer:** `simulation_viewer.py`

---

## Troubleshooting

### Services Won't Start

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs

# Restart services
make docker-down && make docker-up
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker exec integro_simulation_db pg_isready

# View PostgreSQL logs
docker logs integro_simulation_db
```

### Qdrant Connection Issues

```bash
# Verify QDRANT_URL in .env
cat .env | grep QDRANT_URL
# Should be: QDRANT_URL=http://qdrant:6333

# Check Qdrant health
curl http://localhost:6333/health
```

### Simulation Failures

```bash
# Check backend logs
docker logs integro_simulation_backend

# Verify agent exists in database
docker exec -it integro_simulation_db psql -U integro -d integro \
    -c "SELECT id, name FROM agents;"
```

---

## Environment Variables

**Required in `.env`:**

```bash
# Database
DATABASE_URL=postgresql://integro:integro@integro_simulation_db:5432/integro

# Qdrant (use Docker network URL, not localhost)
QDRANT_URL=http://qdrant:6333

# API Keys (if using external LLMs)
GROQ_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

---

## Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| Backend API | 8888 | FastAPI application |
| Frontend UI | 8889 | Next.js application |
| Qdrant | 6333 | Vector database + dashboard |
| Simulation Viewer | 8890 | Web-based simulation browser |
| PostgreSQL | 5432 | Database (internal) |

---

## Documentation

- **[CLAUDE.md](.claude/CLAUDE.md)** - Main project documentation
- **[personas.md](.claude/personas.md)** - Persona system details
- **[simulation-tools.md](.claude/simulation-tools.md)** - Testing tools
- **[evaluation.md](.claude/evaluation.md)** - Evaluation workflows
- **[knowledge-base.md](.claude/knowledge-base.md)** - KB and RAG docs
- **[quick-reference.md](.claude/quick-reference.md)** - This file

---

**Last Updated:** 2025-10-23
