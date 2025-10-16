#!/bin/bash
# Clean corrupted Qdrant WAL files when switching to external Qdrant

echo "=========================================="
echo "🧹 Cleaning Qdrant WAL Files"
echo "=========================================="

DATA_PATH="${RAILWAY_VOLUME_MOUNT_PATH:-/app/data}"
QDRANT_STORAGE="$DATA_PATH/qdrant/storage"

if [ -d "$QDRANT_STORAGE/collections" ]; then
    echo "📁 Found Qdrant storage at: $QDRANT_STORAGE"
    
    # Remove WAL files that cause "Resource temporarily unavailable" errors
    echo "🗑️  Removing corrupted WAL files..."
    find "$QDRANT_STORAGE" -name "wal" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$QDRANT_STORAGE" -name "*.wal" -type f -delete 2>/dev/null || true
    
    # Remove raft state that might be corrupted
    if [ -f "$QDRANT_STORAGE/raft_state.json" ]; then
        echo "🗑️  Removing raft_state.json..."
        rm -f "$QDRANT_STORAGE/raft_state.json"
    fi
    
    echo "✅ WAL cleanup complete"
else
    echo "📍 No Qdrant storage found at $QDRANT_STORAGE"
fi

echo "=========================================="