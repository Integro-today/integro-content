"""FastAPI server with WebSocket support for Integro chat interface."""

import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field
from pathlib import Path
import tempfile
import shutil
import os

from integro.config import AgentLoader, ConfigStorage, KnowledgeBaseLoader, AgentConfig, KnowledgeBaseConfig
from integro.agent import IntegroAgent
from integro.agent.config import ModelConfig
from integro.memory.knowledge import KnowledgeBase
from integro.utils.logging import get_logger
from integro.utils.document_processor import DocumentProcessor
from integro.utils.railway_health import RailwayHealthChecker, railway_startup_check

logger = get_logger(__name__)

# Global simulation viewer state
AVAILABLE_SIMULATIONS: List[Dict[str, Any]] = []

# Import LiveKit API
try:
    from livekit import api as livekit_api
    LIVEKIT_AVAILABLE = True
except ImportError:
    logger.warning("LiveKit not available - install livekit package for voice features")
    LIVEKIT_AVAILABLE = False
def _normalize_timestamps(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Convert datetime fields to ISO strings if present."""
    result = dict(obj)
    for key in ("created_at", "updated_at"):
        value = result.get(key)
        if hasattr(value, "isoformat"):
            result[key] = value.isoformat()
    return result


# Import Agno therapeutic workflow
try:
    from integro.workflows.therapeutic import TherapeuticWorkflow
    WORKFLOW_AVAILABLE = True
except ImportError:
    logger.warning("Therapeutic workflow not available - Agno dependencies may be missing")
    WORKFLOW_AVAILABLE = False

# Import multi-agent clients
try:
    from integro.models.external_clients import MultiAgentManager
    MULTI_AGENT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Multi-agent functionality not available: {e}")
    MULTI_AGENT_AVAILABLE = False


class AgentInfo(BaseModel):
    """Agent information model."""
    id: str
    name: str
    description: str
    knowledge_base_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class KnowledgeBaseInfo(BaseModel):
    """Knowledge base information model."""
    id: str
    name: str
    description: str
    collection_name: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CreateAgentRequest(BaseModel):
    """Request model for creating an agent."""
    name: str
    description: str = "AI Assistant"
    user_id: str = "default"
    instructions: List[str] = Field(default_factory=list)
    models: List[Dict[str, Any]] = Field(default_factory=lambda: [
        {"provider": "groq", "model_id": "moonshotai/kimi-k2-instruct-0905", "params": {"temperature": 0.7}}
    ])
    stream: bool = False
    markdown: bool = True
    enable_memory: bool = True
    enable_storage: bool = True
    knowledge_base_id: Optional[str] = None


class UpdateAgentRequest(BaseModel):
    """Request model for updating an agent."""
    name: Optional[str] = None
    description: Optional[str] = None
    user_id: Optional[str] = None
    instructions: Optional[List[str]] = None
    models: Optional[List[Dict[str, Any]]] = None
    stream: Optional[bool] = None
    markdown: Optional[bool] = None
    enable_memory: Optional[bool] = None
    enable_storage: Optional[bool] = None
    knowledge_base_id: Optional[str] = None


class LiveKitTokenRequest(BaseModel):
    """Request model for LiveKit token generation"""
    room_name: str
    participant_name: str
    agent_id: Optional[str] = None
    kb_id: Optional[str] = None
    agent_name: Optional[str] = None


class CreateKnowledgeBaseRequest(BaseModel):
    """Request model for creating a knowledge base."""
    name: str
    description: str = "Knowledge Base"
    collection_name: Optional[str] = None
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    chunk_size: int = 1000
    chunk_overlap: int = 200


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_agents: Dict[str, IntegroAgent] = {}
        self.user_agent_ids: Dict[str, str] = {}
        self.user_kb_ids: Dict[str, Optional[str]] = {}
        self.user_workflows: Dict[str, 'TherapeuticWorkflow'] = {}  # Add workflow storage
        self.user_sessions: Dict[str, str] = {}
        self.connection_modes: Dict[str, str] = {}  # Track if using 'agent' or 'workflow' mode
        # Multi-agent connections
        self.multi_agent_connections: Dict[str, WebSocket] = {}
        self.multi_agent_manager = MultiAgentManager() if MULTI_AGENT_AVAILABLE else None
        # Coordination events for multi-agent streaming
        self.integro_start_events: Dict[str, asyncio.Event] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and store connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.user_sessions[client_id] = datetime.now().isoformat()
        self.connection_modes[client_id] = "agent"  # Default to agent mode
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        """Remove connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.user_agents:
            del self.user_agents[client_id]
        if client_id in self.user_workflows:
            # Save final workflow state before disconnecting
            workflow = self.user_workflows[client_id]
            if hasattr(workflow, 'state_manager'):
                workflow.state_manager.update_state(workflow.session_state)
            del self.user_workflows[client_id]
        if client_id in self.user_sessions:
            del self.user_sessions[client_id]
        if client_id in self.connection_modes:
            del self.connection_modes[client_id]
        logger.info(f"Client {client_id} disconnected")
    
    async def send_message(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific client with error handling."""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
            except (RuntimeError, ConnectionError) as e:
                # Handle "Cannot call send once a close message has been sent" 
                logger.warning(f"Failed to send message to {client_id}: {e}")
                # Remove from active connections if sending failed
                if client_id in self.active_connections:
                    del self.active_connections[client_id]
                raise  # Re-raise to let caller handle it
    
    def set_agent(self, client_id: str, agent: IntegroAgent):
        """Set agent for a client."""
        self.user_agents[client_id] = agent
        self.connection_modes[client_id] = "agent"
    
    def get_agent(self, client_id: str) -> Optional[IntegroAgent]:
        """Get agent for a client."""
        return self.user_agents.get(client_id)
    
    def set_workflow(self, client_id: str, workflow: 'TherapeuticWorkflow'):
        """Set therapeutic workflow for a client."""
        self.user_workflows[client_id] = workflow
        self.connection_modes[client_id] = "workflow"
    
    def get_workflow(self, client_id: str) -> Optional['TherapeuticWorkflow']:
        """Get workflow for a client."""
        return self.user_workflows.get(client_id)
    
    def get_mode(self, client_id: str) -> str:
        """Get the current mode for a client ('agent' or 'workflow')."""
        return self.connection_modes.get(client_id, "agent")
    
    def get_session(self, client_id: str) -> str:
        """Get session ID for a client."""
        return self.user_sessions.get(client_id, datetime.now().isoformat())
    
    async def connect_multi_agent(self, websocket: WebSocket, client_id: str):
        """Accept and store multi-agent connection."""
        await websocket.accept()
        self.multi_agent_connections[client_id] = websocket
        logger.info(f"Multi-agent client {client_id} connected")
    
    def disconnect_multi_agent(self, client_id: str):
        """Remove multi-agent connection."""
        if client_id in self.multi_agent_connections:
            del self.multi_agent_connections[client_id]
        if client_id in self.integro_start_events:
            del self.integro_start_events[client_id]
        logger.info(f"Multi-agent client {client_id} disconnected")
    
    async def send_multi_agent_message(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific multi-agent client with error handling."""
        if client_id in self.multi_agent_connections:
            websocket = self.multi_agent_connections[client_id]
            try:
                await websocket.send_json(message)
            except (RuntimeError, ConnectionError) as e:
                logger.warning(f"Failed to send multi-agent message to {client_id}: {e}")
                if client_id in self.multi_agent_connections:
                    del self.multi_agent_connections[client_id]
                raise


# Global instances
manager = ConnectionManager()
storage: Optional[ConfigStorage] = None
agent_loader = AgentLoader()
kb_loader = KnowledgeBaseLoader()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for app initialization."""
    global storage
    
    # Load environment variables
    load_dotenv()
    # Set tokenizers parallelism to avoid warnings
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    
    logger.info("🚀 Starting Integro application initialization...")
    
    # Initialize storage (now uses volume-aware paths)
    from integro.config.storage import ConfigStorage
    storage = ConfigStorage()
    logger.info("📦 Configuration storage initialized")
    
    # Simplified: rely on external Qdrant (docker-compose) or configured URL
    qdrant_url = os.getenv('QDRANT_URL', 'http://qdrant:6333')
    logger.info(f"Qdrant endpoint configured: {qdrant_url}")
    
    # NOW run health checks with Qdrant running
    logger.info("🔍 Running startup health check...")
    health_status = await railway_startup_check()
    
    # Store health status for endpoint access
    app.state.startup_health = health_status
    
    if health_status["overall"]["healthy"]:
        logger.info("🎉 All systems healthy - ready for agents!")
    else:
        logger.warning("⚠️  Some systems have issues - check /health/detailed endpoint")
    
    logger.info("✅ Integro web server initialization complete")

    # Attempt automatic migration from SQLite if PostgreSQL is enabled and tables are empty
    try:
        if os.getenv("DATABASE_URL"):
            # Check if any agents/KBs exist; if not, try migration
            agents = await storage.list_agents()
            kbs = await storage.list_knowledge_bases()
            if not agents or not kbs:
                logger.info("Empty Postgres config tables detected - attempting auto-migration from SQLite if available")
                try:
                    import sqlite3
                    from integro.config.database import get_config_db_path
                    sqlite_path = get_config_db_path()
                    if sqlite_path.exists():
                        logger.info(f"Found SQLite at {sqlite_path}, importing agents and KBs...")
                        with sqlite3.connect(str(sqlite_path)) as sconn:
                            sconn.row_factory = sqlite3.Row
                            cur = sconn.cursor()
                            # Import KBs if none exist in PG
                            if not kbs:
                                rows = cur.execute("SELECT config FROM knowledge_bases").fetchall()
                                for r in rows:
                                    try:
                                        from integro.config.kb_loader import KnowledgeBaseConfig
                                        kb_cfg = KnowledgeBaseConfig.from_dict(json.loads(r["config"]))
                                        await storage.save_knowledge_base(kb_cfg)
                                    except Exception as e:
                                        logger.warning(f"KB import skipped: {e}")
                            # Import agents if none exist in PG
                            if not agents:
                                rows = cur.execute("SELECT config FROM agents").fetchall()
                                for r in rows:
                                    try:
                                        from integro.config.agent_loader import AgentConfig
                                        ag_cfg = AgentConfig.from_dict(json.loads(r["config"]))
                                        await storage.save_agent(ag_cfg)
                                    except Exception as e:
                                        logger.warning(f"Agent import skipped: {e}")
                        logger.info("Auto-migration from SQLite complete")
                    else:
                        logger.info("No SQLite configs.db found; skipping auto-migration")
                except Exception as e:
                    logger.warning(f"Auto-migration failed: {e}")

            # Import KB documents if none present for all KBs
            try:
                # Re-fetch KBs after potential import
                kbs_current = await storage.list_knowledge_bases()
                # Determine if any KB has documents
                any_docs = False
                for kb_row in kbs_current:
                    kb_docs = await storage.load_kb_documents(kb_row['id'])
                    if kb_docs:
                        any_docs = True
                        break
                if not any_docs:
                    from integro.config.database import get_config_db_path
                    import sqlite3
                    import json as _json
                    import struct as _struct
                    sqlite_path = get_config_db_path()
                    if sqlite_path.exists():
                        logger.info("Importing kb_documents from SQLite into PostgreSQL...")
                        with sqlite3.connect(str(sqlite_path)) as sconn:
                            sconn.row_factory = sqlite3.Row
                            cur = sconn.cursor()
                            rows = cur.execute(
                                "SELECT kb_id, doc_id, file_path, content, metadata, embedding, created_at FROM kb_documents"
                            ).fetchall()
                            imported = 0
                            for r in rows:
                                try:
                                    metadata = None
                                    if r["metadata"]:
                                        try:
                                            metadata = _json.loads(r["metadata"]) if isinstance(r["metadata"], str) else r["metadata"]
                                        except Exception:
                                            metadata = None
                                    embedding_list = None
                                    emb = r["embedding"]
                                    if emb and isinstance(emb, (bytes, bytearray)) and len(emb) >= 4:
                                        num_floats = len(emb) // 4
                                        embedding_list = list(_struct.unpack(f"{num_floats}f", emb))
                                    await storage.save_kb_document(
                                        kb_id=r["kb_id"],
                                        doc_id=r["doc_id"],
                                        content=r["content"] or "",
                                        file_path=r["file_path"],
                                        metadata=metadata,
                                        embedding=embedding_list,
                                    )
                                    imported += 1
                                except Exception as imp_err:
                                    logger.warning(f"Skipping kb_document import for {r.get('doc_id')}: {imp_err}")
                            logger.info(f"Imported {imported} kb_documents from SQLite")
                    else:
                        logger.info("No SQLite configs.db found for kb_documents import")
            except Exception as docs_err:
                logger.warning(f"KB documents auto-import failed: {docs_err}")
    except Exception as e:
        logger.warning(f"Startup migration check failed: {e}")
    
    yield
    
    # Cleanup on shutdown
    logger.info("🛑 Integro web server shutting down...")
    
    # Stop embedded Qdrant service if running
    if os.getenv('RAILWAY_ENVIRONMENT'):
        try:
            from integro.utils.qdrant_embedded import stop_qdrant_service
            logger.info("Stopping embedded Qdrant service...")
            await stop_qdrant_service()
            logger.info("✅ Qdrant service stopped")
        except Exception as e:
            logger.warning(f"Error stopping Qdrant service: {e}")
    
    logger.info("👋 Integro web server shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Integro Web Interface",
    description="Web interface for Integro AI agents",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
# Configure CORS to allow Next.js frontend origin (default: http://localhost:8889)
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:8889")
additional_origins = os.getenv("ADDITIONAL_ALLOWED_ORIGINS", "")
allowed_origins = [o for o in [frontend_origin] + [x.strip() for x in additional_origins.split(",") if x.strip()] if o]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["http://localhost:8889"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Basic health check endpoint for Railway deployment."""
    return {"status": "healthy", "service": "integro-web", "timestamp": datetime.now().isoformat()}


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with database and service connectivity."""
    try:
        # Run fresh health check
        checker = RailwayHealthChecker()
        health_status = await checker.run_full_health_check()
        
        # Return with appropriate HTTP status
        if health_status["overall"]["healthy"]:
            return health_status
        else:
            # Return 503 Service Unavailable for unhealthy systems
            from fastapi import Response
            response = Response(
                content=json.dumps(health_status),
                status_code=503,
                media_type="application/json"
            )
            return response
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "service": "integro-web",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


@app.get("/health/startup")
async def startup_health_status():
    """Get the health status from startup check."""
    try:
        if hasattr(app.state, 'startup_health'):
            return app.state.startup_health
        else:
            return {
                "status": "unknown",
                "message": "Startup health check not available"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/api/agents")
async def get_agents() -> List[AgentInfo]:
    """Get list of available agents."""
    if not storage:
        raise HTTPException(status_code=500, detail="Storage not initialized")
    
    agents = await storage.list_agents()
    # Normalize datetime fields to ISO strings for pydantic
    normalized = []
    for a in agents:
        a = dict(a)
        ca = a.get("created_at")
        ua = a.get("updated_at")
        if hasattr(ca, "isoformat"):
            a["created_at"] = ca.isoformat()
        if hasattr(ua, "isoformat"):
            a["updated_at"] = ua.isoformat()
        normalized.append(a)
    return [AgentInfo(**agent) for agent in normalized]


@app.get("/api/knowledge-bases")
async def get_knowledge_bases() -> List[KnowledgeBaseInfo]:
    """Get list of available knowledge bases."""
    if not storage:
        raise HTTPException(status_code=500, detail="Storage not initialized")
    
    kbs = await storage.list_knowledge_bases()
    normalized = []
    for kb in kbs:
        kb = dict(kb)
        ca = kb.get("created_at")
        ua = kb.get("updated_at")
        if hasattr(ca, "isoformat"):
            kb["created_at"] = ca.isoformat()
        if hasattr(ua, "isoformat"):
            kb["updated_at"] = ua.isoformat()
        normalized.append(kb)
    return [KnowledgeBaseInfo(**kb) for kb in normalized]


@app.post("/api/agents")
async def create_agent(request: CreateAgentRequest) -> AgentInfo:
    """Create a new agent."""
    if not storage:
        raise HTTPException(status_code=500, detail="Storage not initialized")
    
    try:
        # Create agent configuration
        config = agent_loader.create_default_config(request.name)
        config.description = request.description
        config.user_id = request.user_id
        config.instructions = request.instructions
        config.models = [ModelConfig(**m) if isinstance(m, dict) else m for m in request.models]
        config.stream = request.stream
        config.markdown = request.markdown
        config.enable_memory = request.enable_memory
        config.enable_storage = request.enable_storage
        config.knowledge_base_id = request.knowledge_base_id
        
        # Save to storage
        agent_id = await storage.save_agent(config)
        
        # Return agent info with normalized timestamps
        agents = await storage.list_agents()
        agent_data = next((a for a in agents if a['id'] == agent_id), None)
        
        if agent_data:
            return AgentInfo(**_normalize_timestamps(agent_data))
        
        raise HTTPException(status_code=500, detail="Failed to create agent")
        
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str) -> Dict[str, Any]:
    """Get a specific agent configuration."""
    if not storage:
        raise HTTPException(status_code=500, detail="Storage not initialized")
    
    config = await storage.load_agent(agent_id)
    if not config:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return config.to_dict()


@app.put("/api/agents/{agent_id}")
async def update_agent(agent_id: str, request: UpdateAgentRequest) -> AgentInfo:
    """Update an existing agent."""
    if not storage:
        raise HTTPException(status_code=500, detail="Storage not initialized")
    
    try:
        # Load existing config
        config = await storage.load_agent(agent_id)
        if not config:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Update fields if provided
        if request.name is not None:
            config.name = request.name
        if request.description is not None:
            config.description = request.description
        if request.user_id is not None:
            config.user_id = request.user_id
        if request.instructions is not None:
            config.instructions = request.instructions
        if request.models is not None:
            from integro.agent.config import ModelConfig
            config.models = [ModelConfig(**m) if isinstance(m, dict) else m for m in request.models]
        if request.stream is not None:
            config.stream = request.stream
        if request.markdown is not None:
            config.markdown = request.markdown
        if request.enable_memory is not None:
            config.enable_memory = request.enable_memory
        if request.enable_storage is not None:
            config.enable_storage = request.enable_storage
        if request.knowledge_base_id is not None:
            config.knowledge_base_id = request.knowledge_base_id
        
        # Save updated config
        await storage.save_agent(config)
        
        # Return updated info with normalized timestamps
        agents = await storage.list_agents()
        agent_data = next((a for a in agents if a['id'] == agent_id), None)
        
        if agent_data:
            return AgentInfo(**_normalize_timestamps(agent_data))
        
        raise HTTPException(status_code=500, detail="Failed to update agent")
        
    except Exception as e:
        logger.error(f"Error updating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str) -> Dict[str, str]:
    """Delete an agent."""
    if not storage:
        raise HTTPException(status_code=500, detail="Storage not initialized")
    
    success = await storage.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"message": f"Agent {agent_id} deleted successfully"}


@app.post("/api/knowledge-bases")
async def create_knowledge_base(request: CreateKnowledgeBaseRequest) -> KnowledgeBaseInfo:
    """Create a new knowledge base."""
    if not storage:
        raise HTTPException(status_code=500, detail="Storage not initialized")
    
    try:
        # Create KB configuration
        config = kb_loader.create_default_config(request.name)
        config.description = request.description
        if request.collection_name:
            config.collection_name = request.collection_name
        config.embedding_model = request.embedding_model
        config.chunk_size = request.chunk_size
        config.chunk_overlap = request.chunk_overlap
        
        # Save to storage
        kb_id = await storage.save_knowledge_base(config)
        
        # Return KB info with normalized timestamps
        kbs = await storage.list_knowledge_bases()
        kb_data = next((k for k in kbs if k['id'] == kb_id), None)
        
        if kb_data:
            return KnowledgeBaseInfo(**_normalize_timestamps(kb_data))
        
        raise HTTPException(status_code=500, detail="Failed to create knowledge base")
        
    except Exception as e:
        logger.error(f"Error creating knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge-bases/{kb_id}")
async def get_knowledge_base(kb_id: str) -> Dict[str, Any]:
    """Get a specific knowledge base configuration."""
    if not storage:
        raise HTTPException(status_code=500, detail="Storage not initialized")
    
    config = await storage.load_knowledge_base(kb_id)
    if not config:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    return config.to_dict()


@app.delete("/api/knowledge-bases/{kb_id}")
async def delete_knowledge_base(kb_id: str) -> Dict[str, str]:
    """Delete a knowledge base."""
    if not storage:
        raise HTTPException(status_code=500, detail="Storage not initialized")
    
    success = await storage.delete_knowledge_base(kb_id)
    if not success:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    return {"message": f"Knowledge base {kb_id} deleted successfully"}


@app.post("/api/knowledge-bases/{kb_id}/documents")
async def upload_documents(
    kb_id: str,
    files: List[UploadFile] = File(...)
) -> Dict[str, Any]:
    """Upload and process documents for a knowledge base."""
    if not storage:
        raise HTTPException(status_code=500, detail="Storage not initialized")
    
    # Load KB configuration
    kb_config = await storage.load_knowledge_base(kb_id)
    if not kb_config:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    processor = DocumentProcessor(
        chunk_size=kb_config.chunk_size,
        chunk_overlap=kb_config.chunk_overlap
    )
    
    # Create in-memory KB for vectorization
    # Use default model if "fastembed" is specified (which is not a valid model name)
    embedding_model = kb_config.embedding_model
    if embedding_model == "fastembed":
        embedding_model = "BAAI/bge-small-en-v1.5"  # Default FastEmbed model
    
    kb = KnowledgeBase(
        collection_name=kb_config.collection_name or kb_id,
        in_memory=True,
        embedding_model=embedding_model
    )
    
    results = []
    errors = []
    
    for file in files:
        try:
            # Check if file type is supported
            if not DocumentProcessor.is_supported(file.filename):
                errors.append({
                    "file": file.filename,
                    "error": f"Unsupported file type. Supported types: {', '.join(DocumentProcessor.get_supported_formats())}"
                })
                continue
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
                shutil.copyfileobj(file.file, tmp_file)
                tmp_path = tmp_file.name
            
            try:
                # Process the document
                chunks, metadata = processor.process_file(tmp_path)
                
                # Add chunks to KB and store in database
                doc_ids = []
                for i, chunk in enumerate(chunks):
                    # Generate unique doc ID
                    doc_id = f"{kb_id}_{file.filename}_{i}"
                    
                    # Add to in-memory KB for vectorization
                    embedding = kb._get_embedding(chunk['content'])
                    
                    # Store in database with embedding
                    await storage.save_kb_document(
                        kb_id=kb_id,
                        doc_id=doc_id,
                        content=chunk['content'],
                        file_path=file.filename,
                        metadata=chunk['metadata'],
                        embedding=embedding
                    )
                    
                    doc_ids.append(doc_id)
                
                results.append({
                    "file": file.filename,
                    "chunks": len(chunks),
                    "doc_ids": doc_ids,
                    "metadata": metadata
                })
                
            finally:
                # Clean up temp file
                os.unlink(tmp_path)
                
        except Exception as e:
            logger.error(f"Error processing {file.filename}: {e}")
            errors.append({
                "file": file.filename,
                "error": str(e)
            })
    
    return {
        "success": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }


@app.get("/api/knowledge-bases/{kb_id}/documents")
async def list_documents(kb_id: str) -> List[Dict[str, Any]]:
    """List all documents in a knowledge base."""
    if not storage:
        raise HTTPException(status_code=500, detail="Storage not initialized")
    
    documents = await storage.load_kb_documents(kb_id)
    
    # Group by file and track embedding status
    files = {}
    for doc in documents:
        file_path = doc.get('file_path', 'unknown')
        if file_path not in files:
            files[file_path] = {
                'file_path': file_path,
                'chunks': 0,
                'chunks_with_embeddings': 0,
                'chunks_without_embeddings': 0,
                'doc_ids': [],
                'created_at': doc.get('created_at'),
                'needs_repair': False
            }
        files[file_path]['chunks'] += 1
        files[file_path]['doc_ids'].append(doc['doc_id'])
        
        # Check if this chunk has a valid embedding (bytes with actual content)
        if doc.get('embedding') and isinstance(doc['embedding'], bytes) and len(doc['embedding']) >= 4:
            files[file_path]['chunks_with_embeddings'] += 1
        else:
            files[file_path]['chunks_without_embeddings'] += 1
            files[file_path]['needs_repair'] = True
    
    return list(files.values())


@app.delete("/api/knowledge-bases/{kb_id}/documents/{doc_id}")
async def delete_document(kb_id: str, doc_id: str) -> Dict[str, str]:
    """Delete a specific document from a knowledge base."""
    if not storage:
        raise HTTPException(status_code=500, detail="Storage not initialized")
    
    # This would need to be implemented in storage.py
    # For now, we'll return a placeholder
    return {"message": f"Document {doc_id} deleted from knowledge base {kb_id}"}


@app.delete("/api/knowledge-bases/{kb_id}/documents")
async def clear_knowledge_base(kb_id: str) -> Dict[str, str]:
    """Clear all documents from a knowledge base."""
    if not storage:
        raise HTTPException(status_code=500, detail="Storage not initialized")
    
    # Delete all documents for this KB using storage abstraction
    await storage.clear_kb_documents(kb_id)
    
    return {"message": f"All documents cleared from knowledge base {kb_id}"}


@app.get("/api/knowledge-bases/{kb_id}/health")
async def check_kb_health(kb_id: str) -> Dict[str, Any]:
    """Check the health of a knowledge base, including embedding status."""
    if not storage:
        raise HTTPException(status_code=500, detail="Storage not initialized")
    
    # Load KB configuration
    kb_config = await storage.load_knowledge_base(kb_id)
    if not kb_config:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # Load all documents
    documents = await storage.load_kb_documents(kb_id)
    
    total_chunks = len(documents)
    # Only count as having embedding if it's bytes with actual content (at least 4 bytes for 1 float)
    chunks_with_embeddings = sum(
        1 for doc in documents 
        if doc.get('embedding') and isinstance(doc['embedding'], bytes) and len(doc['embedding']) >= 4
    )
    chunks_without_embeddings = total_chunks - chunks_with_embeddings
    
    # Group by file to find problematic files
    problem_files = []
    files_data = {}
    
    for doc in documents:
        file_path = doc.get('file_path', 'unknown')
        if file_path not in files_data:
            files_data[file_path] = {
                'total': 0,
                'missing_embeddings': 0
            }
        files_data[file_path]['total'] += 1
        # Check for valid embedding (bytes with actual content)
        if not (doc.get('embedding') and isinstance(doc['embedding'], bytes) and len(doc['embedding']) >= 4):
            files_data[file_path]['missing_embeddings'] += 1
    
    for file_path, data in files_data.items():
        if data['missing_embeddings'] > 0:
            problem_files.append({
                'file': file_path,
                'total_chunks': data['total'],
                'missing_embeddings': data['missing_embeddings']
            })
    
    health_status = "healthy" if chunks_without_embeddings == 0 else "needs_repair"
    
    return {
        "kb_id": kb_id,
        "name": kb_config.name,
        "health_status": health_status,
        "total_chunks": total_chunks,
        "chunks_with_embeddings": chunks_with_embeddings,
        "chunks_without_embeddings": chunks_without_embeddings,
        "embedding_coverage": f"{(chunks_with_embeddings / total_chunks * 100) if total_chunks > 0 else 0:.1f}%",
        "needs_repair": chunks_without_embeddings > 0,
        "problem_files": problem_files,
        "embedding_model": kb_config.embedding_model
    }


@app.post("/api/knowledge-bases/{kb_id}/repair")
async def repair_kb_embeddings(kb_id: str) -> Dict[str, Any]:
    """Repair missing embeddings in a knowledge base."""
    if not storage:
        raise HTTPException(status_code=500, detail="Storage not initialized")
    
    # Load KB configuration
    kb_config = await storage.load_knowledge_base(kb_id)
    if not kb_config:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # Create a KB instance for generating embeddings
    embedding_model = kb_config.embedding_model
    if embedding_model == "fastembed":
        embedding_model = "BAAI/bge-small-en-v1.5"  # Default FastEmbed model
    
    kb = KnowledgeBase(
        collection_name=kb_config.collection_name or kb_id,
        in_memory=True,
        embedding_model=embedding_model
    )
    
    # Load all documents
    documents = await storage.load_kb_documents(kb_id)
    
    repaired = 0
    failed = 0
    errors = []
    
    for doc in documents:
        # Skip if already has a valid embedding (bytes with actual content)
        if doc.get('embedding') and isinstance(doc['embedding'], bytes) and len(doc['embedding']) >= 4:
            continue
        
        try:
            # Generate embedding for this document
            content = doc.get('content', '')
            if not content:
                errors.append({
                    'doc_id': doc['doc_id'],
                    'error': 'No content found'
                })
                failed += 1
                continue
            
            logger.info(f"Generating embedding for document {doc['doc_id']}")
            embedding = kb._get_embedding(content)
            
            # Update the document with the new embedding
            await storage.update_kb_document_embedding(
                kb_id=kb_id,
                doc_id=doc['doc_id'],
                embedding=embedding
            )
            
            repaired += 1
            
        except Exception as e:
            logger.error(f"Failed to repair embedding for {doc['doc_id']}: {e}")
            errors.append({
                'doc_id': doc['doc_id'],
                'error': str(e)
            })
            failed += 1
    
    return {
        "kb_id": kb_id,
        "repaired": repaired,
        "failed": failed,
        "total_processed": repaired + failed,
        "errors": errors[:10],  # Limit errors to first 10
        "message": f"Successfully repaired {repaired} document embeddings"
    }


@app.post("/api/livekit-token")
async def generate_livekit_token(request: LiveKitTokenRequest) -> Dict[str, str]:
    """Generate a LiveKit token for voice chat"""
    if not LIVEKIT_AVAILABLE:
        raise HTTPException(status_code=503, detail="LiveKit not available - install livekit package")

    try:
        # Prepare room metadata
        # Use existing chat session_id for continuity with voice
        existing_session_id = manager.get_session(request.participant_name) if request.participant_name else None
        room_metadata = {
            "client_id": request.participant_name,
            "agent_id": request.agent_id,
            "kb_id": request.kb_id,
            "agent_name": request.agent_name or "AI Assistant",
            "session_id": existing_session_id or f"voice_{request.participant_name}"
        }
        logger.info(f"generate_livekit_token: room={request.room_name} metadata={room_metadata}")

        # First, try to create the room with metadata using the Room Service API
        try:
            from livekit import api as lk_api
            livekit_host = os.getenv("LIVEKIT_URL", "wss://integro-srj80gdl.livekit.cloud").replace("wss://", "https://").replace("ws://", "http://")

            logger.info(f"Creating LiveKit API client for {livekit_host}")
            # Create LiveKit API client
            lk_client = lk_api.LiveKitAPI(
                url=livekit_host,
                api_key=os.getenv("LIVEKIT_API_KEY", "devkey"),
                api_secret=os.getenv("LIVEKIT_API_SECRET", "secret")
            )

            # Try to create room with metadata
            try:
                logger.info(f"Attempting to create room {request.room_name} with metadata: {room_metadata}")
                created_room = await lk_client.room.create_room(
                    lk_api.CreateRoomRequest(
                        name=request.room_name,
                        metadata=json.dumps(room_metadata)
                    )
                )
                logger.info(f"Successfully created room {request.room_name} with metadata")
            except Exception as create_error:
                # Room might already exist - try to update metadata
                logger.warning(f"Room creation failed ({create_error}), trying to update metadata")
                try:
                    updated_room = await lk_client.room.update_room_metadata(
                        lk_api.UpdateRoomMetadataRequest(
                            room=request.room_name,
                            metadata=json.dumps(room_metadata)
                        )
                    )
                    logger.info(f"Successfully updated room {request.room_name} metadata")
                except Exception as update_error:
                    logger.error(f"Failed to update room metadata: {update_error}")
        except Exception as e:
            logger.error(f"Failed to initialize LiveKit API client: {e}")
            logger.error(f"Will proceed with participant metadata only")

        # Create access token
        token = livekit_api.AccessToken(
            api_key=os.getenv("LIVEKIT_API_KEY", "devkey"),
            api_secret=os.getenv("LIVEKIT_API_SECRET", "secret")
        )

        # Configure token with participant metadata too (for redundancy)
        token.with_identity(request.participant_name)\
             .with_name(request.participant_name)\
             .with_metadata(json.dumps(room_metadata))\
             .with_grants(livekit_api.VideoGrants(
                 room_join=True,
                 room=request.room_name,
                 can_publish=True,
                 can_subscribe=True,
                 can_publish_data=True,
                 room_create=True  # Allow room creation
             ))

        return {
            "token": token.to_jwt(),
            "room_name": request.room_name,
            "livekit_url": os.getenv("LIVEKIT_URL", "wss://integro-srj80gdl.livekit.cloud")
        }

    except Exception as e:
        logger.error(f"Error generating LiveKit token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice-session/start")
async def start_voice_session(client_id: str) -> Dict[str, Any]:
    """Start a voice session for a client"""
    try:
        # Get current agent for this client
        agent = manager.get_agent(client_id)
        if not agent:
            raise HTTPException(status_code=400, detail="No agent loaded. Please load an agent first.")

        # Generate unique room name
        room_name = f"agent_{client_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Get agent configuration for metadata
        agent_name = getattr(agent.config, 'name', 'AI Assistant') if hasattr(agent, 'config') else 'AI Assistant'
        # Prefer stored ids from manager if present
        agent_id = manager.user_agent_ids.get(client_id) or (getattr(agent.config, 'id', None) if hasattr(agent, 'config') else None)
        kb_id = manager.user_kb_ids.get(client_id) or (getattr(agent.config, 'knowledge_base_id', None) if hasattr(agent, 'config') else None)
        logger.info(f"start_voice_session: client_id={client_id} agent_id={agent_id} kb_id={kb_id} agent_name={agent_name}")

        session_info = {
            "room_name": room_name,
            "session_id": f"voice_{room_name}",
            "client_id": client_id,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "kb_id": kb_id,
            "livekit_url": os.getenv("LIVEKIT_URL", "wss://integro-srj80gdl.livekit.cloud")
        }

        # Note: In production, you'd trigger the voice agent to join via webhook
        # For now, the agent will join when it sees the room created

        return session_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting voice session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/multi-agent/{client_id}")
async def multi_agent_websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for multi-agent comparison."""
    if not MULTI_AGENT_AVAILABLE:
        await websocket.close(code=4000, reason="Multi-agent functionality not available")
        return
    
    await manager.connect_multi_agent(websocket, client_id)
    
    try:
        # Send initial status
        available_providers = manager.multi_agent_manager.get_available_providers()
        await manager.send_multi_agent_message(client_id, {
            "type": "multi_agent_ready",
            "providers": available_providers,
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "load_agent":
                # Load agent for multi-agent comparison
                agent_id = data.get("agent_id")
                kb_id = data.get("kb_id")
                
                try:
                    await load_agent_for_client(client_id, agent_id, kb_id)
                    await manager.send_multi_agent_message(client_id, {
                        "type": "agent_loaded",
                        "agent_id": agent_id,
                        "kb_id": kb_id,
                        "message": f"Agent loaded successfully",
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    logger.error(f"Error loading agent: {e}")
                    await manager.send_multi_agent_message(client_id, {
                        "type": "error",
                        "message": f"Failed to load agent: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    })
            
            elif message_type == "load_workflow":
                # Load therapeutic workflow for multi-agent comparison
                if not WORKFLOW_AVAILABLE:
                    await manager.send_multi_agent_message(client_id, {
                        "type": "error",
                        "message": "Therapeutic workflow not available. Please install Agno dependencies.",
                        "timestamp": datetime.now().isoformat()
                    })
                    continue
                
                try:
                    # Create workflow instance
                    user_id = data.get("user_id", client_id)
                    session_id = f"therapeutic_{client_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    
                    workflow = TherapeuticWorkflow(
                        session_id=session_id,
                        user_id=user_id
                    )
                    
                    # Store workflow for client
                    manager.set_workflow(client_id, workflow)
                    
                    await manager.send_multi_agent_message(client_id, {
                        "type": "workflow_loaded",
                        "session_id": session_id,
                        "current_activity": workflow.session_state.get("current_activity"),
                        "available_activities": ["daily_content", "byron_katie", "ifs"],
                        "timestamp": datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"Error loading workflow: {e}")
                    await manager.send_multi_agent_message(client_id, {
                        "type": "error",
                        "message": f"Failed to load workflow: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    })
            
            elif message_type == "multi_agent_message":
                message = data.get("message", "")
                conversation_history = data.get("conversation_history", [])
                
                if not message.strip():
                    continue
                
                # Log received conversation history for debugging
                logger.info(f"Received conversation history with {len(conversation_history)} messages")
                
                # Send typing indicators for all providers
                await manager.send_multi_agent_message(client_id, {
                    "type": "typing_status",
                    "providers": {
                        "integro": True,
                        "openai": True, 
                        "anthropic": True,
                        "gemini": True
                    },
                    "timestamp": datetime.now().isoformat()
                })
                
                # Start streaming from all providers
                try:
                    # Create coordination event for this client
                    manager.integro_start_events[client_id] = asyncio.Event()
                    
                    # Get or create Integro workflow or agent
                    integro_workflow = manager.get_workflow(client_id)
                    integro_agent = manager.get_agent(client_id)
                    
                    # If no workflow or agent exists, create a default workflow
                    if not integro_workflow and not integro_agent:
                        if WORKFLOW_AVAILABLE:
                            try:
                                # Create default therapeutic workflow
                                session_id = f"therapeutic_{client_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                integro_workflow = TherapeuticWorkflow(
                                    session_id=session_id,
                                    user_id=client_id
                                )
                                manager.set_workflow(client_id, integro_workflow)
                                logger.info(f"Auto-created therapeutic workflow for multi-agent comparison")
                            except Exception as e:
                                logger.error(f"Failed to auto-create workflow: {e}")
                    
                    # Create tasks for each provider
                    tasks = []
                    
                    # Integro task (start first, others wait for it to begin)
                    if integro_workflow:
                        tasks.append(asyncio.create_task(
                            stream_integro_workflow(client_id, message, integro_workflow, conversation_history)
                        ))
                    elif integro_agent:
                        tasks.append(asyncio.create_task(
                            stream_integro_agent(client_id, message, integro_agent, conversation_history)
                        ))
                    else:
                        # No Integro source available, signal immediately
                        manager.integro_start_events[client_id].set()
                    
                    # External API tasks (will wait for Integro to start)
                    for provider in ['openai', 'anthropic', 'gemini']:
                        client_obj = manager.multi_agent_manager.get_client(provider)
                        if client_obj:
                            tasks.append(asyncio.create_task(
                                stream_external_provider(client_id, provider, message, client_obj, conversation_history)
                            ))
                    
                    # Wait for all tasks to complete
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                    
                except Exception as e:
                    logger.error(f"Error processing multi-agent message: {e}")
                    await manager.send_multi_agent_message(client_id, {
                        "type": "error",
                        "message": f"Error: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    })
                finally:
                    # Stop all typing indicators
                    await manager.send_multi_agent_message(client_id, {
                        "type": "typing_status",
                        "providers": {
                            "integro": False,
                            "openai": False,
                            "anthropic": False,
                            "gemini": False
                        },
                        "timestamp": datetime.now().isoformat()
                    })
            
            elif message_type == "ping":
                await manager.send_multi_agent_message(client_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        manager.disconnect_multi_agent(client_id)
    except Exception as e:
        logger.error(f"Multi-agent WebSocket error: {e}")
        manager.disconnect_multi_agent(client_id)


async def stream_integro_workflow(client_id: str, message: str, workflow, conversation_history: list = None):
    """Stream response from Integro workflow."""
    # Build context-aware message for workflow if history provided
    if conversation_history and len(conversation_history) > 1:
        # Build a context string from the conversation history
        context_parts = []
        for msg in conversation_history[:-1]:  # All except the last message
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                context_parts.append(f"User: {content}")
            else:
                context_parts.append(f"Assistant: {content}")
        
        # Add context to the current message
        full_context = "\n".join(context_parts)
        contextual_message = f"Previous conversation:\n{full_context}\n\nCurrent question: {message}"
        logger.info(f"Integro workflow processing with context from {len(conversation_history)} messages")
        message = contextual_message
    try:
        response_chunks = []
        
        for response in workflow.run(message=message):
            if hasattr(response, 'content') and response.content is not None:
                content = response.content
            elif response is not None:
                content = str(response)
            else:
                continue
                
            response_chunks.append(content)
            
            # Check if client is still connected
            if client_id not in manager.multi_agent_connections:
                break
            
            # Send chunk
            try:
                await manager.send_multi_agent_message(client_id, {
                    "type": "provider_chunk",
                    "provider": "integro",
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                })
            except (RuntimeError, ConnectionError):
                break
            
            await asyncio.sleep(0.01)
        
        # Signal that other providers can start
        if client_id in manager.integro_start_events:
            manager.integro_start_events[client_id].set()
        
        await manager.send_multi_agent_message(client_id, {
            "type": "integro_started",
            "timestamp": datetime.now().isoformat()
        })
        
        # Send complete message
        full_content = "".join([chunk for chunk in response_chunks if chunk is not None])
        if client_id in manager.multi_agent_connections:
            await manager.send_multi_agent_message(client_id, {
                "type": "provider_complete",
                "provider": "integro",
                "content": full_content,
                "timestamp": datetime.now().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Error streaming Integro workflow: {e}")
        if client_id in manager.multi_agent_connections:
            await manager.send_multi_agent_message(client_id, {
                "type": "provider_error",
                "provider": "integro",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })


async def stream_integro_agent(client_id: str, message: str, agent, conversation_history: list = None):
    """Stream response from Integro agent."""
    try:
        session_id = manager.get_session(client_id)
        
        # Build context-aware message if conversation history provided
        if conversation_history and len(conversation_history) > 1:
            # Build a context string from the conversation history
            context_parts = []
            for msg in conversation_history[:-1]:  # All except the last message
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    context_parts.append(f"User: {content}")
                else:
                    context_parts.append(f"Assistant: {content}")
            
            # Add context to the current message
            full_context = "\n".join(context_parts)
            contextual_message = f"Previous conversation:\n{full_context}\n\nCurrent question: {message}"
            logger.info(f"Integro agent processing with context from {len(conversation_history)} messages")
            
            # Use the contextual message
            response = await agent.arun(message=contextual_message, session_id=session_id, stream=False)
        else:
            # No history or single message
            response = await agent.arun(message=message, session_id=session_id, stream=False)
        
        if hasattr(response, 'content'):
            content = response.content
        else:
            content = str(response)
        
        # Send as single chunk for now (since astream is not available)
        if client_id in manager.multi_agent_connections:
            await manager.send_multi_agent_message(client_id, {
                "type": "provider_chunk",
                "provider": "integro",
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
            
            # Signal that other providers can start
            if client_id in manager.integro_start_events:
                manager.integro_start_events[client_id].set()
            
            await manager.send_multi_agent_message(client_id, {
                "type": "integro_started",
                "timestamp": datetime.now().isoformat()
            })
            
            await manager.send_multi_agent_message(client_id, {
                "type": "provider_complete",
                "provider": "integro",
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Error streaming Integro agent: {e}")
        if client_id in manager.multi_agent_connections:
            await manager.send_multi_agent_message(client_id, {
                "type": "provider_error",
                "provider": "integro", 
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })


async def stream_external_provider(client_id: str, provider: str, message: str, client_obj, conversation_history: list = None):
    """Stream response from external provider."""
    # Wait for Integro to start first
    if client_id in manager.integro_start_events:
        try:
            await asyncio.wait_for(manager.integro_start_events[client_id].wait(), timeout=30.0)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for Integro to start for {provider}")
        
        # Check if we're still connected after waiting
        if client_id not in manager.multi_agent_connections:
            return
    
    try:
        response_chunks = []
        
        # Use conversation history if available, otherwise just the message
        if conversation_history and hasattr(client_obj, 'stream_response_with_history'):
            async for chunk in client_obj.stream_response_with_history(conversation_history):
                if not chunk:
                    continue
                    
                response_chunks.append(chunk)
                
                # Check if client is still connected
                if client_id not in manager.multi_agent_connections:
                    break
                
                # Send chunk
                try:
                    await manager.send_multi_agent_message(client_id, {
                        "type": "provider_chunk",
                        "provider": provider,
                        "content": chunk,
                        "timestamp": datetime.now().isoformat()
                    })
                except (RuntimeError, ConnectionError):
                    break
                
                await asyncio.sleep(0.01)
        else:
            # Fallback to simple message if no history support
            async for chunk in client_obj.stream_response(message):
                if not chunk:
                    continue
                
                response_chunks.append(chunk)
                
                # Check if client is still connected
                if client_id not in manager.multi_agent_connections:
                    break
            
                # Send chunk
                try:
                    await manager.send_multi_agent_message(client_id, {
                        "type": "provider_chunk",
                        "provider": provider,
                        "content": chunk,
                        "timestamp": datetime.now().isoformat()
                    })
                except (RuntimeError, ConnectionError):
                    break
                
                await asyncio.sleep(0.01)
        
        # Send complete message
        full_content = "".join(response_chunks)
        if client_id in manager.multi_agent_connections:
            await manager.send_multi_agent_message(client_id, {
                "type": "provider_complete",
                "provider": provider,
                "content": full_content,
                "timestamp": datetime.now().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Error streaming {provider}: {e}")
        if client_id in manager.multi_agent_connections:
            await manager.send_multi_agent_message(client_id, {
                "type": "provider_error",
                "provider": provider,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for chat communication."""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "load_agent":
                # Load agent with optional knowledge base
                agent_id = data.get("agent_id")
                kb_id = data.get("kb_id")
                
                try:
                    await load_agent_for_client(client_id, agent_id, kb_id)
                    # Cache the requested ids for voice session continuity
                    manager.user_agent_ids[client_id] = agent_id
                    manager.user_kb_ids[client_id] = kb_id
                    await manager.send_message(client_id, {
                        "type": "agent_loaded",
                        "agent_id": agent_id,
                        "kb_id": kb_id,
                        "message": f"Agent loaded successfully"
                    })
                except Exception as e:
                    logger.error(f"Error loading agent: {e}")
                    await manager.send_message(client_id, {
                        "type": "error",
                        "message": f"Failed to load agent: {str(e)}"
                    })
            
            elif message_type == "load_workflow":
                # Load therapeutic workflow
                if not WORKFLOW_AVAILABLE:
                    await manager.send_message(client_id, {
                        "type": "error",
                        "message": "Therapeutic workflow not available. Please install Agno dependencies."
                    })
                    continue
                
                try:
                    # Create workflow instance
                    user_id = data.get("user_id", client_id)
                    session_id = f"therapeutic_{client_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    
                    workflow = TherapeuticWorkflow(
                        session_id=session_id,
                        user_id=user_id
                    )
                    
                    # Store workflow for client
                    manager.set_workflow(client_id, workflow)
                    
                    # Send workflow loaded confirmation first
                    await manager.send_message(client_id, {
                        "type": "workflow_loaded",
                        "session_id": session_id,
                        "current_activity": workflow.session_state.get("current_activity"),
                        "available_activities": ["daily_content", "byron_katie", "ifs"]
                    })
                    
                    # Automatically trigger startup content by sending a welcome message
                    # This will invoke the workflow's _handle_session_startup() method
                    try:
                        # Check if connection is still active
                        if client_id not in manager.active_connections:
                            logger.warning(f"Client {client_id} disconnected before startup content")
                            return
                            
                        # Send typing indicator for startup content
                        await manager.send_message(client_id, {
                            "type": "typing",
                            "status": True
                        })
                        
                        # Small delay to ensure client is ready
                        await asyncio.sleep(0.1)
                        
                        # Trigger startup behavior with empty message (first interaction)
                        welcome_message = "Welcome to your integration session"  # This will trigger startup
                        startup_chunks = []
                        
                        # Use our custom run method exclusively
                        # Avoid Agno's run_workflow which doesn't accept parameters
                        try:
                            startup_responses = workflow.run(message=welcome_message)
                        except Exception as run_error:
                            logger.error(f"Error calling workflow.run(): {run_error}")
                            logger.error(f"Error details: {type(run_error).__name__}: {str(run_error)}")
                            raise
                        
                        for response in startup_responses:
                            # Check connection state before each send
                            if client_id not in manager.active_connections:
                                logger.warning(f"Client {client_id} disconnected during startup streaming")
                                break
                                
                            if hasattr(response, 'content'):
                                content = response.content
                            else:
                                content = str(response)
                            
                            startup_chunks.append(content)
                            
                            # Send chunk for streaming startup content
                            try:
                                await manager.send_message(client_id, {
                                    "type": "workflow_chunk",
                                    "content": content
                                })
                            except (RuntimeError, ConnectionError) as e:
                                logger.warning(f"Client {client_id} disconnected during startup streaming: {e}")
                                break
                            
                            # Delay for visible streaming effect (increased from 0.01)
                            await asyncio.sleep(0.05)
                        
                        # Send completion message for startup with accumulated content
                        if client_id in manager.active_connections:
                            startup_content = "".join(startup_chunks)
                            try:
                                await manager.send_message(client_id, {
                                    "type": "workflow_complete", 
                                    "content": startup_content,  # Send accumulated content for reliability
                                    "current_activity": workflow.session_state.get("current_activity"),
                                    "completed_activities": list(workflow.session_state.get("completed_activities", {}).keys())
                                })
                            except (RuntimeError, ConnectionError) as e:
                                logger.warning(f"Client {client_id} disconnected before startup complete could be sent: {e}")
                        
                    except Exception as startup_error:
                        logger.error(f"Error triggering startup content: {startup_error}")
                        # Fallback to simple welcome if startup fails (only if connected)
                        if client_id in manager.active_connections:
                            await manager.send_message(client_id, {
                                "type": "workflow_chunk",
                                "content": "Welcome to your psychedelic integration session. I'm here to support your journey with therapeutic activities and conversation."
                            })
                    finally:
                        # Stop typing indicator (only if still connected)
                        if client_id in manager.active_connections:
                            await manager.send_message(client_id, {
                                "type": "typing",
                                "status": False
                            })
                    
                except Exception as e:
                    logger.error(f"Error loading workflow: {e}")
                    await manager.send_message(client_id, {
                        "type": "error",
                        "message": f"Failed to load workflow: {str(e)}"
                    })
            
            elif message_type == "chat_message":
                # Process chat message based on mode
                message = data.get("message", "")
                mode = manager.get_mode(client_id)
                
                if mode == "workflow":
                    # Handle workflow message
                    workflow = manager.get_workflow(client_id)
                    
                    if not workflow:
                        await manager.send_message(client_id, {
                            "type": "error",
                            "message": "No workflow active. Please start a therapeutic session first."
                        })
                        continue
                    
                    # Send typing indicator
                    await manager.send_message(client_id, {
                        "type": "typing",
                        "status": True
                    })
                    
                    try:
                        # Process through workflow
                        response_chunks = []
                        
                        # Use our custom run method exclusively
                        # Avoid Agno's run_workflow which doesn't accept parameters
                        try:
                            workflow_responses = workflow.run(message=message)
                        except Exception as run_error:
                            logger.error(f"Error calling workflow.run() in chat: {run_error}")
                            logger.error(f"Error details: {type(run_error).__name__}: {str(run_error)}")
                            raise
                        
                        for response in workflow_responses:
                            if hasattr(response, 'content') and response.content is not None:
                                content = response.content
                            elif response is not None:
                                content = str(response)
                            else:
                                # Skip None responses
                                continue
                            
                            response_chunks.append(content)
                            
                            # Check if client is still connected before sending
                            if client_id not in manager.active_connections:
                                logger.warning(f"Client {client_id} disconnected during streaming")
                                break
                            
                            # Send chunk for streaming effect
                            try:
                                await manager.send_message(client_id, {
                                    "type": "workflow_chunk",
                                    "content": content
                                })
                            except (WebSocketDisconnect, RuntimeError, ConnectionError) as e:
                                logger.warning(f"Client {client_id} disconnected while sending chunk: {e}")
                                break
                            
                            # Small delay for streaming
                            await asyncio.sleep(0.01)
                        
                        # Send complete message with full accumulated content as safety net
                        # Filter out any None values that might have slipped through
                        filtered_chunks = [chunk for chunk in response_chunks if chunk is not None]
                        full_content = "".join(filtered_chunks)
                        
                        # Check connection state before sending complete message
                        if client_id in manager.active_connections:
                            try:
                                await manager.send_message(client_id, {
                                    "type": "workflow_complete",
                                    "content": full_content,  # Send accumulated content for reliability
                                    "current_activity": workflow.session_state.get("current_activity"),
                                    "completed_activities": list(workflow.session_state.get("completed_activities", {}).keys())
                                })
                            except (RuntimeError, ConnectionError) as e:
                                logger.warning(f"Client {client_id} disconnected before workflow_complete could be sent: {e}")
                        else:
                            logger.warning(f"Client {client_id} disconnected before workflow_complete could be sent")
                        
                    except Exception as e:
                        logger.error(f"Error processing workflow message: {e}", exc_info=True)
                        
                        # Try fallback approach if primary method fails
                        fallback_successful = False
                        try:
                            # This shouldn't normally be reached since we're calling run_workflow() correctly above
                            # But keep as safety net in case of other errors
                            logger.info("Primary run_workflow() failed, attempting fallback with run()")
                            # Try the custom run() method if run_workflow() fails - use positional argument
                            workflow_responses = workflow.run(message=message)
                            response_chunks = []
                            
                            for response in workflow_responses:
                                if hasattr(response, 'content') and response.content is not None:
                                    content = response.content
                                elif response is not None:
                                    content = str(response)
                                else:
                                    continue
                                
                                response_chunks.append(content)
                                await manager.send_message(client_id, {
                                    "type": "workflow_chunk",
                                    "content": content
                                })
                                await asyncio.sleep(0.01)
                            
                            # Send complete message
                            filtered_chunks = [chunk for chunk in response_chunks if chunk is not None]
                            full_response = "".join(filtered_chunks)
                            await manager.send_message(client_id, {
                                "type": "workflow_complete",
                                "content": full_response,
                                "current_activity": workflow.session_state.get("current_activity"),
                                "completed_activities": list(workflow.session_state.get("completed_activities", {}).keys())
                            })
                            fallback_successful = True
                            
                        except Exception as fallback_error:
                            logger.error(f"Fallback also failed: {fallback_error}")
                        
                        if not fallback_successful:
                            await manager.send_message(client_id, {
                                "type": "error",
                                "message": f"Error: {str(e)}"
                            })
                    finally:
                        # Stop typing indicator
                        await manager.send_message(client_id, {
                            "type": "typing",
                            "status": False
                        })
                    
                else:
                    # Handle agent message (existing code)
                    agent = manager.get_agent(client_id)
                    
                    if not agent:
                        await manager.send_message(client_id, {
                            "type": "error",
                            "message": "No agent loaded. Please select an agent first."
                        })
                        continue
                    
                    # Send typing indicator
                    await manager.send_message(client_id, {
                        "type": "typing",
                        "status": True
                    })
                    
                    try:
                        # Run agent 
                        session_id = manager.get_session(client_id)
                        
                        # Use arun with stream=False for now since astream is not available
                        response = await agent.arun(
                            message=message,
                            session_id=session_id,
                            stream=False
                        )
                        
                        # Extract content from response
                        if hasattr(response, 'content'):
                            content = response.content
                        else:
                            content = str(response)
                        
                        # Send complete response
                        await manager.send_message(client_id, {
                            "type": "chat_response",
                            "content": content
                        })
                        
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        await manager.send_message(client_id, {
                            "type": "error",
                            "message": f"Error: {str(e)}"
                        })
                    finally:
                        # Stop typing indicator
                        await manager.send_message(client_id, {
                            "type": "typing",
                            "status": False
                        })
            
            elif message_type == "new_session":
                # Start new session
                manager.user_sessions[client_id] = datetime.now().isoformat()
                await manager.send_message(client_id, {
                    "type": "session_created",
                    "session_id": manager.user_sessions[client_id]
                })
            
            elif message_type == "ping":
                # Respond to ping
                await manager.send_message(client_id, {
                    "type": "pong"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(client_id)


def scan_simulations_directory() -> List[Dict[str, Any]]:
    """Scan for all simulation JSON files."""
    simulation_dirs = [
        Path("Agents/simulations"),
        Path("Agents/batch_simulations"),
        Path("Agents/test_simulations")
    ]

    all_simulations = []
    base_dir = Path("Agents")

    for sim_dir in simulation_dirs:
        if sim_dir.exists():
            for json_file in sim_dir.rglob('*.json'):
                if 'simulation' in json_file.name.lower():
                    all_simulations.append({
                        'path': str(json_file),
                        'name': json_file.name,
                        'relative_path': str(json_file.relative_to(base_dir)),
                        'mtime': json_file.stat().st_mtime
                    })

    return all_simulations


def load_simulation_data(file_path: Path) -> Dict[str, Any]:
    """Load simulation JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def extract_simulation_messages(sim_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract and order messages from simulation data."""
    messages = []
    max_turns = sim_data.get('max_turns', 20)

    for i in range(max_turns):
        system_key = f'system{i}'
        if system_key in sim_data and sim_data[system_key]:
            messages.append({
                'role': 'system',
                'content': sim_data[system_key],
                'index': i
            })

        user_key = f'user{i}'
        if user_key in sim_data and sim_data[user_key]:
            messages.append({
                'role': 'user',
                'content': sim_data[user_key],
                'index': i
            })

    return messages


@app.get("/api/simulations/list")
async def list_simulations_api(sort_by: str = "path"):
    """List all available simulations."""
    global AVAILABLE_SIMULATIONS

    # Refresh simulation list
    AVAILABLE_SIMULATIONS = scan_simulations_directory()

    simulations = AVAILABLE_SIMULATIONS.copy()

    if sort_by == "recent":
        simulations = sorted(simulations, key=lambda x: x['mtime'], reverse=True)

    return {
        'simulations': simulations,
        'count': len(simulations)
    }


@app.get("/api/simulations/data")
async def get_simulation_data(path: str):
    """Get specific simulation data."""
    file_path = Path(path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Simulation file not found")

    sim_data = load_simulation_data(file_path)
    messages = extract_simulation_messages(sim_data)

    return {
        'metadata': {
            'session': sim_data.get('session', 'N/A'),
            'datetime': sim_data.get('datetime', 'N/A'),
            'notes': sim_data.get('notes', ''),
            'seed_message': sim_data.get('seed_message', ''),
            'system_agent_id': sim_data.get('system_agent_id', 'Unknown'),
            'user_agent_id': sim_data.get('user_agent_id', 'Unknown'),
            'max_turns': sim_data.get('max_turns', 0),
            'message_count': len(messages)
        },
        'messages': messages
    }


@app.get("/simulations", response_class=HTMLResponse)
async def simulations_viewer():
    """Serve the simulation viewer HTML."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simulation Viewer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
            background: #f5f5f5; color: #333; line-height: 1.6;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header {
            background: white; padding: 20px; border-radius: 8px;
            margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 24px; margin-bottom: 10px; color: #2c3e50; }
        .metadata {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px; margin-top: 15px; padding: 15px;
            background: #f8f9fa; border-radius: 4px;
        }
        .metadata-item { font-size: 14px; }
        .metadata-label { font-weight: 600; color: #555; margin-right: 8px; }
        .metadata-value { color: #333; }
        .simulation-controls {
            display: grid; grid-template-columns: 1fr auto;
            gap: 10px; margin-bottom: 15px;
        }
        .simulation-selector select, .sort-selector select {
            width: 100%; padding: 10px; font-size: 14px;
            border: 1px solid #ddd; border-radius: 4px; background: white;
        }
        .sort-selector { min-width: 200px; }
        .sort-selector label {
            display: block; font-size: 12px; font-weight: 600;
            color: #555; margin-bottom: 4px;
        }
        .chat-container {
            background: white; border-radius: 8px; padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); min-height: 500px;
        }
        .message {
            margin-bottom: 24px; display: flex; flex-direction: column;
        }
        .message.system { align-items: flex-start; }
        .message.user { align-items: flex-end; }
        .message-header {
            font-size: 12px; font-weight: 600; margin-bottom: 6px;
            text-transform: uppercase; letter-spacing: 0.5px;
        }
        .message.system .message-header { color: #3498db; }
        .message.user .message-header { color: #27ae60; }
        .message-bubble {
            max-width: 80%; padding: 12px 16px; border-radius: 12px;
            white-space: pre-wrap; word-wrap: break-word;
            font-size: 15px; line-height: 1.5; text-align: left;
        }
        .message.system .message-bubble {
            background: #e3f2fd; border: 1px solid #90caf9;
        }
        .message.user .message-bubble {
            background: #e8f5e9; border: 1px solid #a5d6a7;
        }
        .loading { text-align: center; padding: 40px; font-size: 18px; color: #666; }
        .error {
            background: #ffebee; color: #c62828; padding: 16px;
            border-radius: 4px; margin: 20px 0; border: 1px solid #ef5350;
        }
        .message-index { font-size: 11px; color: #999; margin-left: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔬 Simulation Viewer</h1>
            <div id="simulation-selector-container"></div>
            <div id="metadata-container"></div>
        </div>
        <div class="chat-container">
            <div id="messages-container" class="loading">Loading simulations...</div>
        </div>
    </div>
    <script>
        let availableSimulations = [];
        let currentSortOrder = 'path';
        let currentSelectedPath = null;

        async function loadSimulationsList(sortBy = 'path') {
            try {
                const response = await fetch(`/api/simulations/list?sort_by=${sortBy}`);
                const data = await response.json();
                availableSimulations = data.simulations;
                currentSortOrder = sortBy;

                if (availableSimulations.length > 0) {
                    renderSimulationSelector();
                    if (!currentSelectedPath) {
                        currentSelectedPath = availableSimulations[0].path;
                    }
                    loadSimulation(currentSelectedPath);
                } else {
                    document.getElementById('messages-container').innerHTML =
                        '<div class="error">No simulation files found</div>';
                }
            } catch (error) {
                console.error('Error loading simulations list:', error);
                document.getElementById('messages-container').innerHTML =
                    `<div class="error">Error loading simulations: ${error.message}</div>`;
            }
        }

        function renderSimulationSelector() {
            const container = document.getElementById('simulation-selector-container');
            const html = `
                <div class="simulation-controls">
                    <div class="simulation-selector">
                        <select id="simulation-select" onchange="onSimulationChange()">
                            ${availableSimulations.map(sim => `
                                <option value="${sim.path}" ${sim.path === currentSelectedPath ? 'selected' : ''}>
                                    ${sim.relative_path}
                                </option>
                            `).join('')}
                        </select>
                    </div>
                    <div class="sort-selector">
                        <label for="sort-select">Sort by:</label>
                        <select id="sort-select" onchange="onSortChange()">
                            <option value="path" ${currentSortOrder === 'path' ? 'selected' : ''}>Path (A-Z)</option>
                            <option value="recent" ${currentSortOrder === 'recent' ? 'selected' : ''}>Most Recent</option>
                        </select>
                    </div>
                </div>
            `;
            container.innerHTML = html;
        }

        function onSimulationChange() {
            const select = document.getElementById('simulation-select');
            currentSelectedPath = select.value;
            loadSimulation(currentSelectedPath);
        }

        function onSortChange() {
            const select = document.getElementById('sort-select');
            loadSimulationsList(select.value);
        }

        async function loadSimulation(path) {
            const messagesContainer = document.getElementById('messages-container');
            messagesContainer.innerHTML = '<div class="loading">Loading simulation...</div>';

            try {
                const response = await fetch(`/api/simulations/data?path=${encodeURIComponent(path)}`);
                if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);

                const data = await response.json();
                renderMetadata(data.metadata);
                renderMessages(data.messages);
            } catch (error) {
                messagesContainer.innerHTML = `
                    <div class="error">
                        <strong>Error loading simulation:</strong><br>${error.message}
                    </div>
                `;
            }
        }

        function renderMetadata(metadata) {
            const container = document.getElementById('metadata-container');
            container.innerHTML = `
                <div class="metadata">
                    <div class="metadata-item">
                        <span class="metadata-label">Session:</span>
                        <span class="metadata-value">${metadata.session}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Workflow Agent:</span>
                        <span class="metadata-value">${metadata.system_agent_id}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Persona Agent:</span>
                        <span class="metadata-value">${metadata.user_agent_id}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Messages:</span>
                        <span class="metadata-value">${metadata.message_count} (${metadata.max_turns} rounds)</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Timestamp:</span>
                        <span class="metadata-value">${metadata.datetime}</span>
                    </div>
                </div>
            `;
        }

        function renderMessages(messages) {
            const container = document.getElementById('messages-container');
            if (messages.length === 0) {
                container.innerHTML = '<div class="loading">No messages found</div>';
                return;
            }

            const html = messages.map(msg => {
                const roleLabel = msg.role === 'system' ? 'Workflow' : 'Persona';
                const escaped = document.createElement('div');
                escaped.textContent = msg.content;
                return `
                    <div class="message ${msg.role}">
                        <div class="message-header">
                            ${roleLabel}<span class="message-index">#${msg.index}</span>
                        </div>
                        <div class="message-bubble">${escaped.innerHTML}</div>
                    </div>
                `;
            }).join('');

            container.innerHTML = html;
        }

        loadSimulationsList();
    </script>
</body>
</html>"""


async def load_agent_for_client(client_id: str, agent_id: str, kb_id: Optional[str] = None):
    """Load agent for a specific client."""
    print(f"\n=== Starting agent load for client {client_id} ===", flush=True)
    print(f"Agent ID: {agent_id}, KB ID: {kb_id}", flush=True)
    logger.info(f"=== Starting agent load for client {client_id} ===")
    logger.info(f"Agent ID: {agent_id}, KB ID: {kb_id}")
    
    if not storage:
        print("ERROR: Storage not initialized", flush=True)
        logger.error("Storage not initialized")
        raise Exception("Storage not initialized")
    
    # Load agent configuration
    print("Loading agent configuration from storage...", flush=True)
    logger.info("Loading agent configuration from storage...")
    start_time = asyncio.get_event_loop().time()
    agent_config = await storage.load_agent(agent_id)
    elapsed = asyncio.get_event_loop().time() - start_time
    print(f"Agent config loaded in {elapsed:.3f}s", flush=True)
    logger.info(f"Agent config loaded in {elapsed:.3f}s")
    
    if not agent_config:
        print(f"ERROR: Agent {agent_id} not found", flush=True)
        logger.error(f"Agent {agent_id} not found")
        raise Exception(f"Agent {agent_id} not found")
    
    # Load knowledge base if specified
    kb = None
    if kb_id and kb_id != "none":
        print(f"\n>>> LOADING KNOWLEDGE BASE: {kb_id}", flush=True)
        logger.info(f"Loading knowledge base {kb_id}...")
        kb_start = asyncio.get_event_loop().time()
        
        print("  1. Loading KB config from storage...", flush=True)
        kb_config = await storage.load_knowledge_base(kb_id)
        print(f"  1. KB config loaded in {asyncio.get_event_loop().time() - kb_start:.3f}s", flush=True)
        logger.info(f"KB config loaded in {asyncio.get_event_loop().time() - kb_start:.3f}s")
        
        if kb_config:
            print("  2. Creating in-memory Qdrant instance...", flush=True)
            logger.info("Creating in-memory Qdrant instance...")
            qdrant_start = asyncio.get_event_loop().time()
            
            # Create a dummy embedding model that doesn't load anything
            class DummyEmbedder:
                def embed(self, text):
                    raise NotImplementedError("This is a read-only KB, embedding not supported")
            
            print("  3. Initializing KnowledgeBase object...", flush=True)
            logger.info("Initializing KnowledgeBase object...")
            kb = KnowledgeBase(
                collection_name=kb_config.collection_name or kb_id,
                in_memory=True,
                embedding_model=DummyEmbedder(),  # Pass dummy to skip FastEmbed initialization
                vector_size=384  # Specify vector size to avoid test embedding
            )
            print(f"  3. KnowledgeBase initialized in {asyncio.get_event_loop().time() - qdrant_start:.3f}s", flush=True)
            logger.info(f"KnowledgeBase initialized in {asyncio.get_event_loop().time() - qdrant_start:.3f}s")
            
            # Load stored documents asynchronously
            print(f"  4. Loading documents from storage for KB {kb_id}...", flush=True)
            logger.info(f"Loading documents from storage for KB {kb_id}...")
            doc_start = asyncio.get_event_loop().time()
            try:
                documents = await asyncio.wait_for(
                    storage.load_kb_documents(kb_id),
                    timeout=5.0  # 5 second timeout for loading docs
                )
                print(f"  4. Loaded {len(documents)} documents in {asyncio.get_event_loop().time() - doc_start:.3f}s", flush=True)
                logger.info(f"Loaded {len(documents)} documents in {asyncio.get_event_loop().time() - doc_start:.3f}s")
            except asyncio.TimeoutError:
                print(f"  4. TIMEOUT: Loading documents took > 5s for KB {kb_id}", flush=True)
                logger.error(f"TIMEOUT: Loading documents took > 5s for KB {kb_id}")
                kb = None
                documents = []
            
            if documents:
                print(f"  5. Processing {len(documents)} documents...", flush=True)
                logger.info(f"Processing {len(documents)} documents...")
                process_start = asyncio.get_event_loop().time()
                
                # Process documents in a separate task to avoid blocking
                import struct
                from qdrant_client.models import PointStruct
                import uuid
                
                # Quick filter for valid docs
                points = []
                skipped = 0
                
                print("  5a. Checking document embeddings...", flush=True)
                logger.info("Checking document embeddings...")
                for i, doc in enumerate(documents):
                    if i % 100 == 0 and i > 0:
                        print(f"    Processed {i}/{len(documents)} documents...", flush=True)
                        logger.info(f"  Processed {i}/{len(documents)} documents...")
                    
                    embedding_bytes = doc.get('embedding')
                    if not embedding_bytes or not isinstance(embedding_bytes, bytes) or len(embedding_bytes) < 4:
                        skipped += 1
                        continue
                    
                    try:
                        # Reconstruct embedding
                        num_floats = len(embedding_bytes) // 4
                        embedding = list(struct.unpack(f'{num_floats}f', embedding_bytes))
                        
                        # Create point for Qdrant
                        doc_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, doc['doc_id']))
                        points.append(
                            PointStruct(
                                id=doc_uuid,
                                vector=embedding,
                                payload={
                                    "content": doc['content'],
                                    "doc_id": doc['doc_id'],
                                    **(doc.get('metadata', {}))
                                }
                            )
                        )
                    except Exception as e:
                        logger.debug(f"Failed to process doc {doc.get('doc_id')}: {e}")
                        skipped += 1
                
                logger.info(f"Document processing took {asyncio.get_event_loop().time() - process_start:.3f}s")
                logger.info(f"Prepared {len(points)} valid points, skipped {skipped}")
                
                # Bulk upsert if we have valid points
                if points:
                    try:
                        logger.info(f"Upserting {len(points)} points to Qdrant...")
                        upsert_start = asyncio.get_event_loop().time()
                        kb.client.upsert(
                            collection_name=kb.collection_name,
                            points=points,
                            wait=False  # Don't wait for indexing
                        )
                        logger.info(f"Qdrant upsert completed in {asyncio.get_event_loop().time() - upsert_start:.3f}s")
                    except Exception as e:
                        logger.error(f"FAILED to upsert points to Qdrant: {e}")
                        kb = None
                else:
                    logger.warning(f"All {len(documents)} documents missing valid embeddings - KB will be None")
                    kb = None
            else:
                logger.warning("No documents found for knowledge base")
            
    
    # Create and initialize agent
    print("\n>>> CREATING AND INITIALIZING AGENT", flush=True)
    logger.info("Creating agent instance...")
    agent_create_start = asyncio.get_event_loop().time()
    try:
        print("  Creating agent instance...", flush=True)
        agent = agent_loader.create_agent(agent_config, knowledge_base=kb)
        print(f"  Agent created in {asyncio.get_event_loop().time() - agent_create_start:.3f}s", flush=True)
        logger.info(f"Agent created in {asyncio.get_event_loop().time() - agent_create_start:.3f}s")
    except Exception as e:
        print(f"  FAILED to create agent: {e}", flush=True)
        logger.error(f"FAILED to create agent: {e}", exc_info=True)
        raise
    
    print("  Initializing agent (this may load models)...", flush=True)
    logger.info("Initializing agent (this may load models)...")
    init_start = asyncio.get_event_loop().time()
    try:
        await agent.initialize()
        print(f"  Agent initialized in {asyncio.get_event_loop().time() - init_start:.3f}s", flush=True)
        logger.info(f"Agent initialized in {asyncio.get_event_loop().time() - init_start:.3f}s")
    except Exception as e:
        print(f"  FAILED to initialize agent: {e}", flush=True)
        logger.error(f"FAILED to initialize agent: {e}", exc_info=True)
        raise
    
    # Store agent for client
    logger.info("Storing agent for client...")
    manager.set_agent(client_id, agent)
    
    total_time = asyncio.get_event_loop().time() - start_time
    logger.info(f"=== Agent loading completed in {total_time:.3f}s ===")
    logger.info(f"Loaded agent '{agent_config.name}' for client {client_id}")


# Mount static files (we'll create the frontend next)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    @app.get("/")
    async def serve_index():
        """Serve the main HTML page."""
        app_file = static_dir / "app.html"
        if app_file.exists():
            return FileResponse(str(app_file))
        # Fallback to simple chat interface
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "Integro Web Interface - Frontend not found"}
else:
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {"message": "Integro Web Interface - API is running"}


def run_server(host: str = "0.0.0.0", port: int = 8888, reload: bool = False, log_level: str = "info"):
    """Run the FastAPI server."""
    import logging
    import sys
    
    # Configure root logger for better visibility
    logging.basicConfig(
        level=logging.DEBUG if log_level == "debug" else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout,
        force=True  # Override any existing configuration
    )
    
    uvicorn.run(
        "integro.web_server:app" if reload else app,
        host=host,
        port=port,
        reload=reload,
        log_level=log_level
    )


if __name__ == "__main__":
    run_server(reload=True)