#!/usr/bin/env python3
"""Debug script to verify Railway volume mounting and Qdrant data persistence."""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

def debug_volume_setup():
    """Debug Railway volume configuration and Qdrant data location."""
    
    print("=" * 80)
    print("Railway Volume Debug Report")
    print("=" * 80)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print()
    
    # 1. Check environment variables
    print("1. ENVIRONMENT VARIABLES")
    print("-" * 40)
    env_vars = {
        "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT", "NOT SET"),
        "RAILWAY_VOLUME_MOUNT_PATH": os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "NOT SET"),
        "RAILWAY_VOLUME_NAME": os.getenv("RAILWAY_VOLUME_NAME", "NOT SET"),
        "RAILWAY_RUN_UID": os.getenv("RAILWAY_RUN_UID", "NOT SET"),
        "PORT": os.getenv("PORT", "NOT SET"),
        "PWD": os.getcwd()
    }
    
    for key, value in env_vars.items():
        status = "✅" if value != "NOT SET" else "❌"
        print(f"  {status} {key}: {value}")
    print()
    
    # 2. Check volume mount point
    print("2. VOLUME MOUNT VERIFICATION")
    print("-" * 40)
    
    # Expected mount path
    mount_path = Path("/app/data")
    volume_env_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
    
    if volume_env_path:
        mount_path = Path(volume_env_path)
        print(f"  Using RAILWAY_VOLUME_MOUNT_PATH: {mount_path}")
    else:
        print(f"  Using default path: {mount_path}")
    
    # Check if mount exists
    if mount_path.exists():
        print(f"  ✅ Mount path exists: {mount_path}")
        
        # Check permissions
        if os.access(mount_path, os.R_OK):
            print(f"  ✅ Mount path is readable")
        else:
            print(f"  ❌ Mount path is NOT readable")
            
        if os.access(mount_path, os.W_OK):
            print(f"  ✅ Mount path is writable")
        else:
            print(f"  ❌ Mount path is NOT writable")
            
        # Test write
        try:
            test_file = mount_path / "volume_test.txt"
            test_file.write_text(f"Volume test at {datetime.utcnow().isoformat()}")
            print(f"  ✅ Successfully wrote test file: {test_file}")
            
            # Read it back
            content = test_file.read_text()
            print(f"  ✅ Successfully read test file: {content[:50]}...")
            
            # Clean up
            test_file.unlink()
            print(f"  ✅ Successfully deleted test file")
        except Exception as e:
            print(f"  ❌ Write test failed: {e}")
    else:
        print(f"  ❌ Mount path does NOT exist: {mount_path}")
        print(f"     This means the volume is not mounted!")
    print()
    
    # 3. Check Qdrant data directory
    print("3. QDRANT DATA DIRECTORY")
    print("-" * 40)
    
    qdrant_storage = mount_path / "qdrant" / "storage"
    qdrant_snapshots = mount_path / "qdrant" / "snapshots"
    qdrant_config = mount_path / "qdrant" / "production.yaml"
    
    print(f"  Expected Qdrant storage: {qdrant_storage}")
    print(f"  Exists: {'✅ Yes' if qdrant_storage.exists() else '❌ No'}")
    
    if qdrant_storage.exists():
        # List contents
        try:
            contents = list(qdrant_storage.iterdir())
            print(f"  Storage contents ({len(contents)} items):")
            for item in contents[:10]:  # Show first 10 items
                size = item.stat().st_size if item.is_file() else "DIR"
                print(f"    - {item.name}: {size}")
            if len(contents) > 10:
                print(f"    ... and {len(contents) - 10} more items")
                
            # Check for collections
            collections_dir = qdrant_storage / "collections"
            if collections_dir.exists():
                collections = list(collections_dir.iterdir())
                print(f"  ✅ Collections directory exists with {len(collections)} collections")
                for coll in collections[:5]:
                    print(f"    - {coll.name}")
            else:
                print(f"  ⚠️  No collections directory found")
                
        except Exception as e:
            print(f"  ❌ Error reading Qdrant storage: {e}")
    else:
        print(f"  ⚠️  Qdrant storage directory doesn't exist yet")
        print(f"     It will be created when Qdrant starts")
    
    print()
    print(f"  Qdrant snapshots: {qdrant_snapshots}")
    print(f"  Exists: {'✅ Yes' if qdrant_snapshots.exists() else '❌ No'}")
    
    print()
    print(f"  Qdrant config: {qdrant_config}")
    print(f"  Exists: {'✅ Yes' if qdrant_config.exists() else '❌ No'}")
    
    if qdrant_config.exists():
        try:
            config_content = qdrant_config.read_text()
            print(f"  Config file content (first 500 chars):")
            print(f"  {config_content[:500]}")
        except Exception as e:
            print(f"  ❌ Error reading config: {e}")
    print()
    
    # 4. Check SQLite databases
    print("4. SQLITE DATABASES")
    print("-" * 40)
    
    for db_name in ["configs.db", "sessions.db", "memory.db"]:
        db_path = mount_path / db_name
        if db_path.exists():
            size = db_path.stat().st_size
            print(f"  ✅ {db_name}: {size:,} bytes")
        else:
            print(f"  ⚠️  {db_name}: Not found (will be created on first use)")
    print()
    
    # 5. Directory structure
    print("5. VOLUME DIRECTORY STRUCTURE")
    print("-" * 40)
    
    if mount_path.exists():
        def show_tree(path, prefix="", max_depth=3, current_depth=0):
            if current_depth >= max_depth:
                return
            
            try:
                items = sorted(path.iterdir())
                for i, item in enumerate(items[:20]):  # Limit to 20 items per level
                    is_last = i == len(items) - 1
                    connector = "└── " if is_last else "├── "
                    print(f"{prefix}{connector}{item.name}")
                    
                    if item.is_dir() and current_depth < max_depth - 1:
                        extension = "    " if is_last else "│   "
                        show_tree(item, prefix + extension, max_depth, current_depth + 1)
                        
                if len(items) > 20:
                    print(f"{prefix}... and {len(items) - 20} more items")
                    
            except PermissionError:
                print(f"{prefix}[Permission Denied]")
        
        show_tree(mount_path)
    else:
        print("  Volume not mounted - cannot show structure")
    print()
    
    # 6. Process information
    print("6. PROCESS INFORMATION")
    print("-" * 40)
    print(f"  Current user: {os.getuid() if hasattr(os, 'getuid') else 'N/A'}")
    print(f"  Current group: {os.getgid() if hasattr(os, 'getgid') else 'N/A'}")
    print(f"  Process PID: {os.getpid()}")
    
    # Check if qdrant binary exists
    qdrant_binary = Path("/usr/local/bin/qdrant")
    if qdrant_binary.exists():
        print(f"  ✅ Qdrant binary found: {qdrant_binary}")
        # Check if executable
        if os.access(qdrant_binary, os.X_OK):
            print(f"  ✅ Qdrant binary is executable")
        else:
            print(f"  ❌ Qdrant binary is NOT executable")
    else:
        print(f"  ❌ Qdrant binary NOT found at {qdrant_binary}")
    print()
    
    # 7. Recommendations
    print("7. RECOMMENDATIONS")
    print("-" * 40)
    
    issues = []
    
    if not os.getenv("RAILWAY_VOLUME_MOUNT_PATH"):
        issues.append("RAILWAY_VOLUME_MOUNT_PATH not set - ensure volume is attached in Railway dashboard")
    
    if not mount_path.exists():
        issues.append(f"Volume not mounted at {mount_path} - check Railway volume configuration")
    elif not os.access(mount_path, os.W_OK):
        issues.append("Volume not writable - set RAILWAY_RUN_UID=0 in environment variables")
    
    if not (mount_path / "qdrant" / "storage").exists():
        issues.append("Qdrant storage not initialized - will be created on first run")
    
    if issues:
        print("  ⚠️  Issues found:")
        for issue in issues:
            print(f"     - {issue}")
    else:
        print("  ✅ Everything looks good!")
        print("     Volume is mounted and writable")
        print("     Qdrant should persist data correctly")
    
    print()
    print("=" * 80)
    print("End of debug report")
    print("=" * 80)


if __name__ == "__main__":
    debug_volume_setup()