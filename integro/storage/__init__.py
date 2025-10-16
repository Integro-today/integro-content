"""Storage module for Integro agents."""

from integro.storage.factory import (
    create_storage_adapter,
    get_storage_info,
    test_storage_connection
)

__all__ = [
    'create_storage_adapter',
    'get_storage_info',
    'test_storage_connection'
]