# Knowledge Base & RAG Documentation

## Overview

Integro agents support knowledge bases with RAG (Retrieval-Augmented Generation) for enhanced responses using semantic search over document collections.

**Status:** ✅ Fully integrated and verified working (2025-10-22)

---

## Architecture

### Integration Flow

```
Integro KnowledgeBase (Qdrant + FastEmbed)
    ↓
Converts to Agno Knowledge (vector_db)
    ↓
Agent initialization
    ↓
search_knowledge_base() tool available during conversations
```

### Components

- **Integro `KnowledgeBase`** - Wrapper around Qdrant + FastEmbed
- **Agno `Knowledge`** - Agno's native knowledge system with vector DB
- **Agent configuration** - Stores `knowledge_base_id` linking to collections
- **PostgreSQL** - Stores knowledge base metadata and document references
- **Qdrant** - External vector DB storing embeddings persistently

---

## Creating Knowledge Bases

### Using create_agent_from_md.py

**Basic agent with knowledge base:**

```bash
# With knowledge base (single document)
docker exec integro_simulation_backend python create_agent_from_md.py \
    Agents/workflow.md --type workflow \
    --knowledge path/to/document.pdf

# With multiple knowledge documents
docker exec integro_simulation_backend python create_agent_from_md.py \
    Agents/workflow.md --type workflow \
    --knowledge doc1.pdf --knowledge doc2.docx --knowledge doc3.epub

# With custom knowledge base name
docker exec integro_simulation_backend python create_agent_from_md.py \
    Agents/workflow.md --type workflow \
    --kb-name "Custom KB Name" --knowledge documents/*.pdf
```

### Knowledge Base Creation Process

1. Creates knowledge base config with pattern: `[Agent Name] Knowledge Base 1`
2. Extracts text from all documents (supports 7+ formats)
3. Chunks content (500 chars with 50 char overlap)
4. Generates embeddings using FastEmbed (BAAI/bge-small-en-v1.5)
5. Uploads to Qdrant vector database
6. Links agent to knowledge base via `knowledge_base_id`
7. Enables semantic search during conversations

### Supported Document Formats

- **PDF** (.pdf)
- **DOCX** (.docx)
- **EPUB** (.epub)
- **TXT** (.txt)
- **MD** (.md)
- **XLSX** (.xlsx)
- **PPTX** (.pptx)

---

## Agno Knowledge Integration

### What Works

- ✅ Agents created with knowledge bases properly load documents from DB
- ✅ Knowledge automatically converts to Agno's `Knowledge` format
- ✅ `search_knowledge=True` enables semantic search during conversations
- ✅ External Qdrant instance (`http://qdrant:6333`) stores embeddings persistently
- ✅ Knowledge search returns relevant documents using `agent.knowledge.search(query, max_results=N)`
- ✅ Multiple agents can share same knowledge base collection

### Configuration Requirements

**.env file:**

```bash
# Must use Docker network URL, NOT localhost
QDRANT_URL=http://qdrant:6333  # NOT localhost:6333 in Docker
```

**Dockerfile:**

```dockerfile
# Comment out RAILWAY_ENVIRONMENT for local dev
# ENV RAILWAY_ENVIRONMENT=production  ← Comment this out
```

### Testing Knowledge

**Python example:**

```python
# Load agent with knowledge
config = await storage.load_agent('agent_with_kb')
kb_config = await storage.load_knowledge_base(config.knowledge_base_id)
kb = KnowledgeBase(collection_name=kb_config.collection_name, url='http://qdrant:6333')
agent = loader.create_agent(config, knowledge_base=kb)
await agent.initialize()

# Agno knowledge is automatically available
results = agent.agent.knowledge.search('trauma', max_results=5)
# Returns: List[Document] with relevant content
```

---

## Current Knowledge Bases

### Roots of Healing Knowledge Base

**Collection:** `kb_roots_of_healing_knowledge_base`

**Documents:** 5,390 chunks from 4 therapeutic books

**Sources:**
1. Gabor Maté - When the Body Says No
2. Rupert Ross - Indigenous Healing
3. Carl Jung - Memories, Dreams, Reflections
4. Integration principles guide

**Used by:**
- Roots of Healing Workflow 2 (`roots_of_healing_-_day_1_workflow_(version_2)_workflow_1`)
- Roots of Healing Workflow 3 (`roots_of_healing_-_day_1_workflow_(version_3)_workflow_1`)

### Test Knowledge Workflow

**Collection:** `kb_test_knowledge_workflow_1_knowledge_base_1`

**Purpose:** Test KB for IFS content

**Used by:** Test agents for knowledge base validation

---

## Qdrant UI Access

**URL:** http://localhost:6333/dashboard

**Features:**
- Browse all collections
- View document counts and metadata
- Inspect embeddings
- Test semantic searches

---

## Knowledge Search in Conversations

### Automatic Tool Availability

When `search_knowledge=True` is set in agent config:

- `search_knowledge_base()` tool automatically available
- Agent can semantically search knowledge during conversations
- Returns relevant document chunks based on query similarity

### Search Parameters

```python
agent.knowledge.search(
    query="trauma and healing",  # Search query
    max_results=5                # Number of results to return
)
```

**Returns:** `List[Document]` with relevant content and metadata

---

## Database Schema

### knowledge_bases table

```sql
CREATE TABLE knowledge_bases (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    collection_name TEXT NOT NULL,
    config JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### kb_documents table

```sql
CREATE TABLE kb_documents (
    id TEXT PRIMARY KEY,
    kb_id TEXT REFERENCES knowledge_bases(id),
    doc_id TEXT NOT NULL,
    file_path TEXT,
    content TEXT,
    metadata JSONB,
    embedding VECTOR,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### agents table

```sql
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    config JSONB,
    knowledge_base_id TEXT REFERENCES knowledge_bases(id),  -- Links to KB
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## Troubleshooting

### Common Issues

**Issue:** Agent can't connect to Qdrant

**Solution:** Ensure `QDRANT_URL=http://qdrant:6333` in `.env` (not localhost)

---

**Issue:** Knowledge search returns no results

**Solution:**
1. Verify collection exists in Qdrant UI
2. Check document count in collection
3. Test with broader search queries

---

**Issue:** Documents not loading during agent initialization

**Solution:**
1. Verify `knowledge_base_id` is set in agent config
2. Check PostgreSQL for knowledge base record
3. Verify Qdrant collection name matches DB config

---

## Helper Scripts

### create_roots_with_knowledge.py

Helper script for creating Roots of Healing workflows with knowledge base.

**Usage:**

```bash
docker exec integro_simulation_backend python create_roots_with_knowledge.py
```

---

## Performance Considerations

### Chunking Strategy

- **Chunk size:** 500 characters
- **Overlap:** 50 characters
- **Rationale:** Balance between context and precision

### Embedding Model

- **Model:** BAAI/bge-small-en-v1.5 (FastEmbed)
- **Dimensions:** 384
- **Performance:** Fast inference, good quality for therapeutic content

### Search Performance

- **Typical query time:** < 100ms
- **Concurrent searches:** Supported (Qdrant handles parallel queries)
- **Scaling:** Add more documents without performance degradation

---

## Best Practices

### When to Use Knowledge Bases

✅ **Good use cases:**
- Therapeutic content with references to research/books
- Daily curriculum with supporting educational material
- Agents needing access to large corpus of information
- Workflows requiring specific domain knowledge

❌ **Avoid for:**
- Simple conversational agents without reference needs
- Agents that shouldn't cite external sources
- Very small knowledge sets (< 10 documents)

### Document Preparation

1. **Clean formatting** - Remove headers/footers, page numbers
2. **Meaningful filenames** - Use descriptive names for source tracking
3. **Related content** - Group thematically related documents
4. **Quality over quantity** - Curate documents, don't dump everything

### Knowledge Base Naming

Use descriptive names that indicate:
- Purpose (e.g., "Therapeutic Resources")
- Scope (e.g., "IFS Trauma Healing")
- Version if applicable (e.g., "V2 Updated")

---

**Last Updated:** 2025-10-23
**Status:** ✅ Production-ready with 5,390+ documents across 2 knowledge bases
