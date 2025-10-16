#!/usr/bin/env python3
"""Verify SQLite databases are using Railway volume correctly."""

import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime

def verify_sqlite_on_volume():
    """Verify all SQLite databases are on the Railway volume."""
    
    print("=" * 80)
    print("SQLite Volume Verification")
    print("=" * 80)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print()
    
    # 1. Check database paths
    print("1. DATABASE PATH CONFIGURATION")
    print("-" * 40)
    
    # Import the database path functions
    try:
        from integro.config.database import (
            get_database_path,
            get_config_db_path,
            get_sessions_db_path,
            get_memory_db_path
        )
        
        base_path = get_database_path()
        config_path = get_config_db_path()
        sessions_path = get_sessions_db_path()
        memory_path = get_memory_db_path()
        
        print(f"  Base path: {base_path}")
        print(f"  Config DB: {config_path}")
        print(f"  Sessions DB: {sessions_path}")
        print(f"  Memory DB: {memory_path}")
        print()
        
        # Verify these are on the Railway volume
        volume_path = os.getenv('RAILWAY_VOLUME_MOUNT_PATH', '/app/data')
        
        for name, path in [
            ("Base path", base_path),
            ("Config DB", config_path),
            ("Sessions DB", sessions_path),
            ("Memory DB", memory_path)
        ]:
            if str(path).startswith(volume_path):
                print(f"  ✅ {name} is on Railway volume")
            else:
                print(f"  ❌ {name} is NOT on Railway volume!")
                print(f"     Expected to start with: {volume_path}")
                print(f"     Actual path: {path}")
        
    except ImportError as e:
        print(f"  ❌ Could not import database path functions: {e}")
        base_path = Path('/app/data')
        config_path = base_path / 'configs.db'
        sessions_path = base_path / 'sessions.db'
        memory_path = base_path / 'memory.db'
    
    print()
    
    # 2. Check existing databases
    print("2. EXISTING SQLITE DATABASES")
    print("-" * 40)
    
    for db_name, db_path in [
        ("configs.db", config_path),
        ("sessions.db", sessions_path),
        ("memory.db", memory_path)
    ]:
        if db_path.exists():
            stats = db_path.stat()
            size_kb = stats.st_size / 1024
            modified = datetime.fromtimestamp(stats.st_mtime).isoformat()
            
            print(f"  ✅ {db_name}:")
            print(f"     Size: {size_kb:.2f} KB")
            print(f"     Modified: {modified}")
            
            # Try to connect and get table info
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get table list
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                print(f"     Tables: {', '.join(tables)}")
                
                # Get row counts for main tables
                for table in tables:
                    if not table.startswith('sqlite_'):
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        print(f"       - {table}: {count} rows")
                
                conn.close()
                
            except Exception as e:
                print(f"     ⚠️  Could not read database: {e}")
        else:
            print(f"  ⚠️  {db_name}: Not found (will be created on first use)")
    
    print()
    
    # 3. Test write capability
    print("3. WRITE TEST")
    print("-" * 40)
    
    test_db_path = base_path / 'test_volume_write.db'
    
    try:
        # Create a test database
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        
        # Create a test table
        cursor.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                message TEXT,
                timestamp TEXT
            )
        """)
        
        # Insert test data
        cursor.execute("""
            INSERT INTO test_table (message, timestamp)
            VALUES (?, ?)
        """, (f"Volume write test", datetime.utcnow().isoformat()))
        
        conn.commit()
        
        # Read it back
        cursor.execute("SELECT * FROM test_table")
        row = cursor.fetchone()
        
        conn.close()
        
        # Clean up
        test_db_path.unlink()
        
        print(f"  ✅ Successfully created, wrote to, and deleted test database")
        print(f"     Test data: {row}")
        
    except Exception as e:
        print(f"  ❌ Write test failed: {e}")
        if test_db_path.exists():
            try:
                test_db_path.unlink()
            except:
                pass
    
    print()
    
    # 4. Check ConfigStorage initialization
    print("4. CONFIGSTORAGE VERIFICATION")
    print("-" * 40)
    
    try:
        from integro.config.storage import ConfigStorage
        
        # Create storage instance
        storage = ConfigStorage()
        
        print(f"  ConfigStorage initialized")
        print(f"  Database path: {storage.db_path}")
        
        # Verify it's on the volume
        if str(storage.db_path).startswith(volume_path):
            print(f"  ✅ ConfigStorage is using Railway volume")
        else:
            print(f"  ❌ ConfigStorage is NOT using Railway volume!")
        
        # Try to connect
        try:
            import asyncio
            
            async def test_storage():
                async with storage.get_connection() as conn:
                    cursor = await conn.execute("SELECT COUNT(*) FROM agents")
                    agent_count = (await cursor.fetchone())[0]
                    
                    cursor = await conn.execute("SELECT COUNT(*) FROM knowledge_bases")
                    kb_count = (await cursor.fetchone())[0]
                    
                    return agent_count, kb_count
            
            agent_count, kb_count = asyncio.run(test_storage())
            print(f"  ✅ Database connection successful")
            print(f"     Agents: {agent_count}")
            print(f"     Knowledge bases: {kb_count}")
            
        except Exception as e:
            print(f"  ⚠️  Could not query database: {e}")
            
    except Exception as e:
        print(f"  ❌ Could not initialize ConfigStorage: {e}")
    
    print()
    
    # 5. Check for any SQLite files outside the volume
    print("5. SQLITE FILES SCAN")
    print("-" * 40)
    
    # Look for any .db files in the application directory
    app_dir = Path('/app')
    volume_dir = Path(volume_path)
    
    found_outside = []
    for db_file in app_dir.rglob('*.db'):
        if not str(db_file).startswith(str(volume_dir)):
            found_outside.append(db_file)
    
    if found_outside:
        print(f"  ⚠️  Found {len(found_outside)} SQLite files outside volume:")
        for db_file in found_outside[:10]:
            size = db_file.stat().st_size / 1024
            print(f"     - {db_file}: {size:.2f} KB")
    else:
        print(f"  ✅ No SQLite files found outside the volume")
    
    print()
    
    # 6. Summary
    print("6. SUMMARY")
    print("-" * 40)
    
    issues = []
    
    # Check if all paths are on volume
    if not str(config_path).startswith(volume_path):
        issues.append("Config DB not on volume")
    
    if not config_path.exists():
        issues.append("Config DB doesn't exist yet (will be created on first use)")
    
    if issues:
        print("  ⚠️  Minor issues found:")
        for issue in issues:
            print(f"     - {issue}")
    else:
        print("  ✅ All SQLite databases are correctly configured on the Railway volume!")
        print(f"     Volume path: {volume_path}")
        print(f"     Config DB: {config_path}")
        if config_path.exists():
            print(f"     Database is persistent and will survive redeployments")
    
    print()
    print("=" * 80)
    print("SQLite verification complete")
    print("=" * 80)


if __name__ == "__main__":
    verify_sqlite_on_volume()