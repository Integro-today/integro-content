"""Embedded Qdrant service management for Railway deployment."""

import os
import time
import signal
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from integro.config.database import get_qdrant_data_path, get_logs_path
from integro.utils.logging import get_logger

logger = get_logger(__name__)


class QdrantEmbeddedService:
    """Manages embedded Qdrant service within the main application container."""
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 6333,
        grpc_port: int = 6334,
        max_retries: int = 20,  # Increased from 10 to 20 for Railway
        retry_delay: float = 3.0  # Increased from 2.0 to 3.0 seconds
    ):
        """
        Initialize embedded Qdrant service manager.
        
        Args:
            host: Host to bind Qdrant service to
            port: HTTP API port
            grpc_port: gRPC API port
            max_retries: Maximum startup retries
            retry_delay: Delay between retries in seconds
        """
        self.host = host
        self.port = port
        self.grpc_port = grpc_port
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.process: Optional[subprocess.Popen] = None
        self.storage_path = get_qdrant_data_path()
        self.logs_path = get_logs_path()
        self.log_file_path = self.logs_path / "qdrant.log"
        
        # Health check state
        self.last_health_check = None
        self.is_healthy = False
        self.startup_time = None
        
        logger.info(f"Qdrant embedded service initialized - storage: {self.storage_path}")
    

    def _get_qdrant_command(self) -> list[str]:
        """Get the Qdrant command to execute."""
        # Qdrant v1.15.1 uses the config file from current directory
        # We'll set environment variables instead of command-line args
        return ["qdrant"]
    
    async def start(self) -> bool:
        """
        Start the embedded Qdrant service.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.is_running():
            logger.info("Qdrant service is already running")
            return True
        
        logger.info("Starting embedded Qdrant service...")
        
        # Verify we're using the Railway volume if in Railway environment
        if os.getenv('RAILWAY_ENVIRONMENT'):
            volume_path = os.getenv('RAILWAY_VOLUME_MOUNT_PATH', '/app/data')
            if not str(self.storage_path).startswith(volume_path):
                logger.warning(f"⚠️ Qdrant storage path {self.storage_path} is not on Railway volume {volume_path}")
                logger.warning("Data will NOT persist across deployments!")
            else:
                logger.info(f"✅ Qdrant will use Railway volume at {self.storage_path}")
                
                # Check for existing data from previous deployments
                collections_dir = self.storage_path / "collections"
                if collections_dir.exists():
                    existing_collections = list(collections_dir.iterdir())
                    if existing_collections:
                        logger.info(f"✅ Found {len(existing_collections)} existing collections from previous deployment")
                        for coll in existing_collections[:5]:
                            logger.info(f"  - {coll.name}")
        
        try:
            # Ensure all required directories exist
            self.storage_path.mkdir(parents=True, exist_ok=True)
            (self.storage_path.parent / 'snapshots').mkdir(parents=True, exist_ok=True)
            (self.storage_path.parent / 'temp').mkdir(parents=True, exist_ok=True)
            self.logs_path.mkdir(parents=True, exist_ok=True)
            
            # Open log file for Qdrant output
            log_file = open(self.log_file_path, "a", encoding="utf-8")
            
            # Create config directory structure that Qdrant expects
            config_dir = self.storage_path.parent / 'config'
            config_dir.mkdir(parents=True, exist_ok=True)
            
            # Write config to the location Qdrant expects
            config_file_path = config_dir / 'config.yaml'
            
            # Simplified config for Qdrant v1.15.1
            config_content = f"""
storage:
  storage_path: "{str(self.storage_path)}"
  snapshots_path: "{str(self.storage_path.parent / 'snapshots')}"
  on_disk_payload: true
  wal:
    wal_capacity_mb: 8
    wal_segments_ahead: 0

service:
  host: "{self.host}"
  http_port: {self.port}
  grpc_port: {self.grpc_port}
  max_request_size_mb: 8
"""
            
            with open(config_file_path, 'w') as f:
                f.write(config_content.strip())
            
            logger.info(f"Created Qdrant config at: {config_file_path}")
            
            # Start Qdrant process
            cmd = self._get_qdrant_command()
            logger.info(f"Executing: {' '.join(cmd)}")
            logger.info(f"Working directory: {str(self.storage_path.parent)}")
            
            # Set environment variables for Qdrant
            env = os.environ.copy()
            env['QDRANT__STORAGE__STORAGE_PATH'] = str(self.storage_path)
            env['QDRANT__STORAGE__SNAPSHOTS_PATH'] = str(self.storage_path.parent / 'snapshots')
            env['QDRANT__STORAGE__ON_DISK_PAYLOAD'] = 'true'
            env['QDRANT__SERVICE__HTTP_PORT'] = str(self.port)
            env['QDRANT__SERVICE__GRPC_PORT'] = str(self.grpc_port)
            env['QDRANT__SERVICE__HOST'] = self.host
            env['QDRANT__LOG_LEVEL'] = 'INFO'
            
            # For Railway, ensure memory constraints are respected
            if os.getenv('RAILWAY_ENVIRONMENT'):
                env['QDRANT_TELEMETRY_DISABLED'] = 'true'  # Disable telemetry to save memory
            
            self.process = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=env,
                preexec_fn=os.setsid if os.name != 'nt' else None,
                cwd=str(self.storage_path.parent)  # Set working directory
            )
            
            self.startup_time = datetime.now()
            logger.info(f"Qdrant process started with PID: {self.process.pid}")
            
            # Wait for service to become available
            if await self._wait_for_startup():
                self.is_healthy = True
                logger.info("✅ Qdrant embedded service started successfully")
                return True
            else:
                logger.error("❌ Qdrant service failed to start within timeout")
                await self.stop()
                return False
                
        except Exception as e:
            logger.error(f"Failed to start Qdrant service: {e}")
            await self.stop()
            return False
    
    async def _wait_for_startup(self) -> bool:
        """Wait for Qdrant to become available with exponential backoff."""
        from qdrant_client import QdrantClient
        from qdrant_client.http.exceptions import UnexpectedResponse
        
        for attempt in range(self.max_retries):
            try:
                # Check if process is still running
                if self.process and self.process.poll() is not None:
                    exit_code = self.process.returncode
                    logger.error(f"Qdrant process died during startup (exit code: {exit_code})")
                    
                    # Read the last few lines of the log file for debugging
                    try:
                        if self.log_file_path.exists():
                            with open(self.log_file_path, 'r') as f:
                                lines = f.readlines()
                                if lines:
                                    logger.error("Last Qdrant log entries:")
                                    for line in lines[-10:]:  # Show last 10 lines
                                        logger.error(f"  {line.strip()}")
                    except Exception as e:
                        logger.error(f"Could not read Qdrant log file: {e}")
                    
                    return False
                
                # Try to connect to Qdrant with proper URL format
                client = QdrantClient(
                    url=f"http://{self.host}:{self.port}",
                    timeout=5,
                    prefer_grpc=False
                )
                
                # Test actual connectivity
                collections = client.get_collections()
                
                logger.info(f"✅ Qdrant startup successful after {attempt + 1} attempts")
                logger.info(f"Collections available: {len(collections.collections)}")
                
                # Mark as healthy
                self.last_health_check = datetime.now()
                self.is_healthy = True
                
                return True
                
            except (ConnectionError, UnexpectedResponse, Exception) as e:
                if attempt < self.max_retries - 1:
                    # Exponential backoff: 2, 3, 4.5, 6.75, 10.125... seconds
                    wait_time = self.retry_delay * (1.5 ** attempt)
                    wait_time = min(wait_time, 10.0)  # Cap at 10 seconds
                    
                    logger.info(f"Waiting for Qdrant... (attempt {attempt + 1}/{self.max_retries})")
                    logger.debug(f"Error was: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Qdrant failed to start after {self.max_retries} attempts: {e}")
        
        return False
    
    async def stop(self) -> bool:
        """
        Stop the embedded Qdrant service gracefully.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.process:
            logger.info("Qdrant service is not running")
            return True
        
        logger.info("Stopping embedded Qdrant service...")
        
        try:
            # Try graceful shutdown first
            if os.name != 'nt':
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            else:
                self.process.terminate()
            
            # Wait for graceful shutdown
            try:
                self.process.wait(timeout=10)
                logger.info("✅ Qdrant service stopped gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                logger.warning("Forcing Qdrant service shutdown...")
                if os.name != 'nt':
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                else:
                    self.process.kill()
                self.process.wait()
                logger.info("✅ Qdrant service force stopped")
            
            self.process = None
            self.is_healthy = False
            return True
            
        except Exception as e:
            logger.error(f"Error stopping Qdrant service: {e}")
            return False
    
    def is_running(self) -> bool:
        """Check if the Qdrant process is running."""
        if not self.process:
            return False
        
        # Check if process is still alive
        poll_result = self.process.poll()
        if poll_result is not None:
            logger.warning(f"Qdrant process exited with code: {poll_result}")
            self.process = None
            self.is_healthy = False
            return False
        
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check of Qdrant service.
        
        Returns:
            Dictionary with health status and metrics
        """
        health_status = {
            "service_running": self.is_running(),
            "api_responsive": False,
            "collections_accessible": False,
            "last_check": datetime.utcnow().isoformat(),
            "uptime_seconds": None,
            "pid": self.process.pid if self.process else None,
            "error": None
        }
        
        # Calculate uptime
        if self.startup_time:
            uptime = datetime.now() - self.startup_time
            health_status["uptime_seconds"] = int(uptime.total_seconds())
        
        if not self.is_running():
            health_status["error"] = "Qdrant process not running"
            self.is_healthy = False
            return health_status
        
        try:
            from qdrant_client import QdrantClient
            
            client = QdrantClient(host=self.host, port=self.port, timeout=5, prefer_grpc=False)
            
            # Test API responsiveness
            collections = client.get_collections()
            health_status["api_responsive"] = True
            health_status["collections_count"] = len(collections.collections)
            
            # Test collections access
            collections = client.get_collections()
            health_status["collections_accessible"] = True
            health_status["collections_count"] = len(collections.collections)
            
            self.is_healthy = True
            self.last_health_check = datetime.now()
            
        except Exception as e:
            health_status["error"] = str(e)
            self.is_healthy = False
            logger.warning(f"Qdrant health check failed: {e}")
        
        return health_status
    
    async def restart(self) -> bool:
        """
        Restart the Qdrant service.
        
        Returns:
            True if restarted successfully, False otherwise
        """
        logger.info("Restarting embedded Qdrant service...")
        
        # Stop current instance
        await self.stop()
        
        # Wait a moment before starting
        await asyncio.sleep(1)
        
        # Start new instance
        return await self.start()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics and statistics."""
        metrics = {
            "service_name": "qdrant_embedded",
            "is_running": self.is_running(),
            "is_healthy": self.is_healthy,
            "startup_time": self.startup_time.isoformat() if self.startup_time else None,
            "storage_path": str(self.storage_path),
            "log_path": str(self.log_file_path),
            "host": self.host,
            "port": self.port,
            "grpc_port": self.grpc_port
        }
        
        # Add storage size if available
        try:
            if self.storage_path.exists():
                storage_size = sum(
                    f.stat().st_size 
                    for f in self.storage_path.rglob('*') 
                    if f.is_file()
                )
                metrics["storage_size_bytes"] = storage_size
        except Exception as e:
            logger.debug(f"Could not calculate storage size: {e}")
        
        return metrics
    
    def get_logs(self, lines: int = 100) -> list[str]:
        """
        Get recent Qdrant service logs.
        
        Args:
            lines: Number of recent lines to return
            
        Returns:
            List of log lines
        """
        try:
            if not self.log_file_path.exists():
                return ["Log file not found"]
            
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
                
        except Exception as e:
            logger.error(f"Error reading Qdrant logs: {e}")
            return [f"Error reading logs: {e}"]


# Global instance for application-wide use
_qdrant_service: Optional[QdrantEmbeddedService] = None


def get_qdrant_service() -> QdrantEmbeddedService:
    """Get the global Qdrant embedded service instance."""
    global _qdrant_service
    
    if _qdrant_service is None:
        _qdrant_service = QdrantEmbeddedService()
    
    return _qdrant_service


async def start_qdrant_service() -> bool:
    """Start the global Qdrant embedded service."""
    service = get_qdrant_service()
    return await service.start()


async def stop_qdrant_service() -> bool:
    """Stop the global Qdrant embedded service."""
    service = get_qdrant_service()
    return await service.stop()


async def restart_qdrant_service() -> bool:
    """Restart the global Qdrant embedded service."""
    service = get_qdrant_service()
    return await service.restart()


def is_qdrant_running() -> bool:
    """Check if the global Qdrant service is running."""
    if _qdrant_service is None:
        return False
    return _qdrant_service.is_running()