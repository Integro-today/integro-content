"""Containerized deployment health check and connection verification."""

import os
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from integro.utils.logging import get_logger
from integro.config.database import get_database_path, get_config_db_path
from integro.config.storage import ConfigStorage

logger = get_logger(__name__)


class RailwayHealthChecker:
    """Health checker for containerized deployment with Qdrant verification."""
    
    def __init__(self):
        self.is_railway = False
        self.health_status = {
            "service": "integro-web",
            "environment": "railway" if self.is_railway else "local",
            "timestamp": datetime.utcnow().isoformat(),
            "volumes": {},
            "databases": {},
            "services": {}
        }
    
    async def check_sqlite_volume(self) -> Dict[str, Any]:
        """Check SQLite volume mount and database connectivity."""
        try:
            data_dir = get_database_path()
            config_db_path = get_config_db_path()
            
            # Check volume mount
            volume_status = {
                "mounted": data_dir.exists(),
                "path": str(data_dir),
                "writable": False,
                "databases": {}
            }
            
            if data_dir.exists():
                # Test write permissions
                test_file = data_dir / "health_check.tmp"
                try:
                    test_file.write_text("health_check")
                    test_file.unlink()
                    volume_status["writable"] = True
                except Exception as e:
                    logger.warning(f"Volume not writable: {e}")
            
            # Test SQLite database connection
            if volume_status["writable"]:
                try:
                    storage = ConfigStorage()
                    
                    # Test basic database operations
                    agents = await storage.list_agents()
                    kbs = await storage.list_knowledge_bases()
                    
                    volume_status["databases"] = {
                        "configs_db": {
                            "exists": config_db_path.exists(),
                            "size_bytes": config_db_path.stat().st_size if config_db_path.exists() else 0,
                            "agents_count": len(agents),
                            "knowledge_bases_count": len(kbs),
                            "readable": True
                        }
                    }
                    
                    logger.info(f"SQLite volume healthy: {len(agents)} agents, {len(kbs)} knowledge bases")
                    
                except Exception as e:
                    logger.error(f"SQLite connection failed: {e}")
                    volume_status["databases"]["configs_db"] = {
                        "exists": config_db_path.exists(),
                        "readable": False,
                        "error": str(e)
                    }
            
            return volume_status
            
        except Exception as e:
            logger.error(f"SQLite volume check failed: {e}")
            return {
                "mounted": False,
                "error": str(e)
            }
    
    async def check_qdrant_connection(self) -> Dict[str, Any]:
        """Check Qdrant connection and verify it's using Railway volume for persistence."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http.exceptions import UnexpectedResponse
            from integro.config.database import get_database_path, get_qdrant_data_path
            
            # Verify Qdrant data dir exists (for local dev; optional)
            data_path = get_database_path()
            qdrant_storage = get_qdrant_data_path()
            
            volume_verification = {
                "volume_path": str(data_path),
                "qdrant_storage_path": str(qdrant_storage),
                "storage_exists": qdrant_storage.exists(),
                "is_on_volume": False,
                "has_collections": False,
                "persistence_verified": False
            }
            
            # Check if we're actually on the Railway volume
            volume_verification["expected_volume"] = str(data_path)
            volume_verification["is_on_volume"] = str(qdrant_storage).startswith(str(data_path))
            
            # Check for existing collections (indicates persistence from previous deployments)
            collections_dir = qdrant_storage / "collections"
            if collections_dir.exists():
                existing_collections = list(collections_dir.iterdir())
                volume_verification["has_collections"] = len(existing_collections) > 0
                volume_verification["existing_collections_count"] = len(existing_collections)
                
                if existing_collections:
                    logger.info(f"✅ Found {len(existing_collections)} existing collections on volume")
                    volume_verification["persistence_verified"] = True
                    # List first few collection names
                    volume_verification["collection_names"] = [c.name for c in existing_collections[:5]]
            
            # Check if there's a persistence marker from previous deployments
            persistence_marker = data_path / "qdrant" / ".persistence_check"
            if persistence_marker.exists():
                try:
                    marker_data = json.loads(persistence_marker.read_text())
                    volume_verification["previous_deployment"] = marker_data
                    volume_verification["persistence_verified"] = True
                    logger.info(f"✅ Found persistence marker from {marker_data.get('timestamp', 'unknown')}")
                except Exception as e:
                    logger.warning(f"Could not read persistence marker: {e}")
            
            # Write a new persistence marker for next deployment
            try:
                persistence_marker.parent.mkdir(parents=True, exist_ok=True)
                marker_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "deployment_id": os.getenv("RAILWAY_DEPLOYMENT_ID", "unknown"),
                    "qdrant_storage": str(qdrant_storage)
                }
                persistence_marker.write_text(json.dumps(marker_data, indent=2))
                volume_verification["marker_written"] = True
            except Exception as e:
                logger.warning(f"Could not write persistence marker: {e}")
                volume_verification["marker_written"] = False
            
            # Get Qdrant connection details with detailed logging
            qdrant_url = os.getenv('QDRANT_URL', f"http://{os.getenv('QDRANT_HOST', 'qdrant')}:{os.getenv('QDRANT_PORT', '6333')}")
            
            qdrant_status = {
                "url": qdrant_url,
                "connected": False,
                "collections": [],
                "version": None,
                "volume_verification": volume_verification
            }
            
            # Test connection with increased timeout and retries for Railway
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(1, max_retries + 1):
                try:
                    client = QdrantClient(url=qdrant_url, timeout=30, prefer_grpc=False)  # Increased from 10 to 30 seconds
                    
                    # Test basic connection by getting collections
                    collections = client.get_collections()
                    qdrant_status["connected"] = True
                    qdrant_status["collections_count"] = len(collections.collections)
                    logger.info(f"Qdrant connected at {qdrant_url}")
                    break  # Success, exit retry loop
                except Exception as e:
                    if attempt < max_retries:
                        logger.warning(f"Qdrant health check attempt {attempt}/{max_retries} failed: {e}")
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error(f"Qdrant health check failed after {max_retries} attempts: {e}")
                        qdrant_status["error"] = str(e)
                        qdrant_status["fallback"] = "Will use SQLite memory if Qdrant unavailable"
                        return qdrant_status
            
            # List collections
            try:
                collections_response = client.get_collections()
                collections = []
                for c in collections_response.collections:
                    info = {"name": getattr(c, 'name', 'unknown')}
                    # Some client versions expose nested info; be defensive
                    vc = getattr(c, 'vectors_count', None)
                    pc = getattr(c, 'points_count', None)
                    if vc is not None:
                        info["vectors_count"] = vc
                    if pc is not None:
                        info["points_count"] = pc
                    collections.append(info)
                qdrant_status["collections"] = collections
                qdrant_status["total_collections"] = len(collections)
                logger.info(f"Qdrant collections: {len(collections)} found")
            except Exception as e:
                logger.warning(f"Could not list Qdrant collections: {e}")
                qdrant_status["collections_error"] = str(e)
            
            return qdrant_status
            
        except ImportError:
            return {
                "connected": False,
                "error": "qdrant-client not installed"
            }
        except Exception as e:
            logger.error(f"Qdrant connection check failed: {e}")
            return {
                "connected": False,
                "error": str(e)
            }
    
    async def verify_agent_memory_integration(self) -> Dict[str, Any]:
        """Test that agents can connect to both SQLite and Qdrant."""
        try:
            from integro.memory.qdrant import QdrantMemory
            
            # Test memory system initialization
            test_user_id = "health_check_user"
            
            try:
                # Create QdrantMemory instance
                memory = QdrantMemory(
                    user_id=test_user_id,
                    collection_prefix="health_check"
                )
                
                # Test basic memory operations
                memory_id = await memory.add_memory(
                    content="Health check memory test",
                    metadata={"test": True, "timestamp": datetime.utcnow().isoformat()}
                )
                
                # Search for the memory
                results = await memory.search_memories("health check", limit=1)
                
                # Clean up test memory
                await memory.delete_memory(memory_id)
                
                return {
                    "memory_integration": True,
                    "test_memory_created": bool(memory_id),
                    "test_memory_found": len(results) > 0,
                    "collection_name": memory.collection_name
                }
                
            except Exception as e:
                logger.error(f"Memory integration test failed: {e}")
                return {
                    "memory_integration": False,
                    "error": str(e)
                }
                
        except ImportError:
            return {
                "memory_integration": False,
                "error": "Memory dependencies not available"
            }
    
    async def run_full_health_check(self) -> Dict[str, Any]:
        """Run complete health check of all systems."""
        logger.info("Starting Railway health check...")
        
        # Check SQLite volume
        self.health_status["volumes"]["sqlite"] = await self.check_sqlite_volume()
        
        # Check Qdrant connection
        self.health_status["services"]["qdrant"] = await self.check_qdrant_connection()
        
        # Test memory integration
        self.health_status["integration"] = await self.verify_agent_memory_integration()
        
        # Overall health assessment
        sqlite_healthy = self.health_status["volumes"]["sqlite"].get("writable", False)
        qdrant_healthy = self.health_status["services"]["qdrant"].get("connected", False)
        memory_healthy = self.health_status["integration"].get("memory_integration", False)
        
        self.health_status["overall"] = {
            "healthy": sqlite_healthy and qdrant_healthy,
            "sqlite_ok": sqlite_healthy,
            "qdrant_ok": qdrant_healthy,
            "memory_ok": memory_healthy,
            "ready_for_agents": sqlite_healthy and qdrant_healthy and memory_healthy
        }
        
        if self.health_status["overall"]["healthy"]:
            logger.info("✅ Railway deployment health check PASSED")
        else:
            logger.error("❌ Railway deployment health check FAILED")
            
        return self.health_status
    
    async def create_initial_agent_if_empty(self) -> bool:
        """Create a default trauma guide agent if no agents exist."""
        try:
            from integro.config.storage import ConfigStorage
            from integro.config.agent_loader import AgentConfig
            
            storage = ConfigStorage()
            agents = await storage.list_agents()
            
            if len(agents) == 0:
                logger.info("No agents found - creating default trauma guide agent")
                
                # Create trauma guide agent configuration
                trauma_agent_config = AgentConfig(
                    name="Trauma Guide",
                    description="A compassionate guide for trauma recovery using evidence-based approaches",
                    instructions=[
                        "You are a trauma-informed guide specializing in helping people understand and process trauma.",
                        "Always respond with empathy, validation, and evidence-based information.",
                        "Reference 'The Body Keeps the Score' and other trauma research when appropriate.",
                        "Encourage professional help when needed and never provide medical diagnoses.",
                        "Use a warm, supportive tone while maintaining professional boundaries."
                    ],
                    models=[{
                        "provider": "groq",
                        "model_id": "llama-3.1-8b-instant"
                    }],
                    enable_memory=True,
                    memory_type="qdrant",
                    search_knowledge=True
                )
                
                agent_id = await storage.save_agent(trauma_agent_config)
                logger.info(f"Created trauma guide agent: {agent_id}")
                return True
                
            else:
                logger.info(f"Found {len(agents)} existing agents - no default creation needed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create initial agent: {e}")
            return False


async def railway_startup_check():
    """Run health check on Railway startup."""
    checker = RailwayHealthChecker()
    health_status = await checker.run_full_health_check()
    
    # Create initial agent if needed
    await checker.create_initial_agent_if_empty()
    
    # Log summary
    if health_status["overall"]["healthy"]:
        logger.info("🚀 Railway deployment ready for agents!")
    else:
        logger.error("💥 Railway deployment has connection issues")
        
        # Log specific issues
        if not health_status["overall"]["sqlite_ok"]:
            logger.error("- SQLite volume not properly mounted or writable")
        if not health_status["overall"]["qdrant_ok"]:
            logger.error("- Qdrant service not accessible")
    
    return health_status


if __name__ == "__main__":
    asyncio.run(railway_startup_check())