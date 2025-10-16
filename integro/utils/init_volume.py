"""Volume initialization for Railway deployment."""

import os
import sys
import asyncio
import time
from pathlib import Path
from datetime import datetime

from integro.config.database import (
    get_database_path, 
    get_qdrant_data_path, 
    get_qdrant_snapshots_path,
    get_backup_path,
    get_logs_path
)
from integro.utils.logging import get_logger

logger = get_logger(__name__)


class VolumeInitializer:
    """Handles Railway volume initialization and verification."""
    
    def __init__(self):
        self.is_railway = bool(os.getenv('RAILWAY_ENVIRONMENT'))
        self.data_dir = get_database_path()
        self.initialization_log = get_logs_path() / "volume_init.log"
        
    def log_init_message(self, message: str):
        """Log initialization message to both logger and init log file."""
        timestamp = datetime.utcnow().isoformat()
        log_message = f"[{timestamp}] {message}"
        
        logger.info(message)
        
        # Also write to initialization log
        try:
            self.initialization_log.parent.mkdir(parents=True, exist_ok=True)
            with open(self.initialization_log, "a", encoding="utf-8") as f:
                f.write(log_message + "\n")
        except Exception as e:
            logger.warning(f"Could not write to init log: {e}")
    
    def check_volume_mount(self) -> bool:
        """Check if volume is properly mounted and accessible."""
        self.log_init_message("🔍 Checking volume mount status...")
        
        # Check if data directory exists
        if not self.data_dir.exists():
            self.log_init_message(f"❌ Data directory does not exist: {self.data_dir}")
            return False
        
        # Test write permissions
        test_file = self.data_dir / "volume_test.tmp"
        try:
            test_file.write_text("volume test")
            test_file.unlink()
            self.log_init_message(f"✅ Volume mount verified at: {self.data_dir}")
            return True
        except Exception as e:
            self.log_init_message(f"❌ Volume not writable: {e}")
            return False
    
    def create_directory_structure(self) -> bool:
        """Create required directory structure on volume."""
        self.log_init_message("📁 Creating directory structure...")
        
        directories = [
            get_qdrant_data_path(),
            get_qdrant_snapshots_path(),
            get_backup_path(),
            get_logs_path()
        ]
        
        try:
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                self.log_init_message(f"   Created: {directory}")
            
            self.log_init_message("✅ Directory structure created successfully")
            return True
            
        except Exception as e:
            self.log_init_message(f"❌ Failed to create directory structure: {e}")
            return False
    
    def initialize_sqlite_databases(self) -> bool:
        """Initialize SQLite databases if they don't exist."""
        self.log_init_message("🗃️ Checking SQLite database initialization...")
        
        try:
            from integro.config.storage import ConfigStorage
            
            # Initialize config storage (will create database if needed)
            storage = ConfigStorage()
            self.log_init_message("✅ SQLite databases initialized")
            return True
            
        except Exception as e:
            self.log_init_message(f"❌ Failed to initialize SQLite databases: {e}")
            return False
    
    async def start_qdrant_service(self) -> bool:
        """Start the embedded Qdrant service."""
        # Check if using external Qdrant
        if os.getenv('USE_EXTERNAL_QDRANT') or os.getenv('QDRANT_HOST'):
            self.log_init_message("📡 Using external Qdrant service - skipping embedded startup")
            return True
            
        self.log_init_message("🚀 Starting embedded Qdrant service...")
        
        try:
            from integro.utils.qdrant_embedded import start_qdrant_service
            
            success = await start_qdrant_service()
            if success:
                self.log_init_message("✅ Qdrant service started successfully")
                return True
            else:
                self.log_init_message("❌ Failed to start Qdrant service")
                return False
                
        except Exception as e:
            self.log_init_message(f"❌ Error starting Qdrant service: {e}")
            return False
    
    async def verify_services(self) -> bool:
        """Verify all services are healthy and accessible."""
        self.log_init_message("🔍 Verifying service health...")
        
        try:
            # Check SQLite access
            from integro.config.storage import ConfigStorage
            storage = ConfigStorage()
            agents = await storage.list_agents()
            self.log_init_message(f"   SQLite: ✅ ({len(agents)} agents configured)")
            
            # Check Qdrant access
            from integro.utils.qdrant_embedded import get_qdrant_service
            service = get_qdrant_service()
            health = await service.health_check()
            
            if health.get("api_responsive", False):
                collections_count = health.get("collections_count", 0)
                self.log_init_message(f"   Qdrant: ✅ ({collections_count} collections)")
            else:
                self.log_init_message(f"   Qdrant: ❌ {health.get('error', 'Unknown error')}")
                return False
            
            self.log_init_message("✅ All services verified successfully")
            return True
            
        except Exception as e:
            self.log_init_message(f"❌ Service verification failed: {e}")
            return False
    
    def create_railway_marker(self):
        """Create a marker file indicating successful Railway initialization."""
        try:
            marker_file = self.data_dir / ".railway_initialized"
            marker_content = {
                "initialized_at": datetime.utcnow().isoformat(),
                "environment": "railway" if self.is_railway else "local",
                "volume_path": str(self.data_dir),
                "version": "1.0.0"
            }
            
            import json
            with open(marker_file, "w", encoding="utf-8") as f:
                json.dump(marker_content, f, indent=2)
            
            self.log_init_message(f"✅ Railway marker created: {marker_file}")
            
        except Exception as e:
            self.log_init_message(f"⚠️ Could not create Railway marker: {e}")
    
    async def initialize(self) -> bool:
        """
        Complete volume initialization process.
        
        Returns:
            True if initialization successful, False otherwise
        """
        start_time = time.time()
        
        self.log_init_message("=" * 60)
        self.log_init_message("🚀 Starting Railway volume initialization...")
        self.log_init_message(f"   Environment: {'Railway' if self.is_railway else 'Local'}")
        self.log_init_message(f"   Volume path: {self.data_dir}")
        self.log_init_message("=" * 60)
        
        # Check if already initialized
        marker_file = self.data_dir / ".railway_initialized"
        if marker_file.exists() and self.is_railway:
            self.log_init_message("✅ Volume already initialized, skipping setup...")
            # Still start services
            await self.start_qdrant_service()
            return True
        
        try:
            # Step 1: Check volume mount
            if not self.check_volume_mount():
                return False
            
            # Step 2: Create directory structure
            if not self.create_directory_structure():
                return False
            
            # Step 3: Initialize SQLite databases
            if not self.initialize_sqlite_databases():
                return False
            
            # Step 4: Start Qdrant service
            if not await self.start_qdrant_service():
                return False
            
            # Step 5: Verify all services
            if not await self.verify_services():
                return False
            
            # Step 6: Create Railway marker
            if self.is_railway:
                self.create_railway_marker()
            
            elapsed_time = time.time() - start_time
            self.log_init_message("=" * 60)
            self.log_init_message(f"🎉 Volume initialization completed successfully!")
            self.log_init_message(f"   Total time: {elapsed_time:.2f} seconds")
            self.log_init_message("=" * 60)
            
            return True
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.log_init_message("=" * 60)
            self.log_init_message(f"💥 Volume initialization failed after {elapsed_time:.2f} seconds")
            self.log_init_message(f"   Error: {e}")
            self.log_init_message("=" * 60)
            return False


async def initialize_volume() -> bool:
    """
    Initialize Railway volume and start services.
    
    Returns:
        True if initialization successful, False otherwise
    """
    initializer = VolumeInitializer()
    return await initializer.initialize()


def main():
    """Main entry point for volume initialization."""
    try:
        success = asyncio.run(initialize_volume())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Volume initialization interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Volume initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()