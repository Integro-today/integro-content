"""Tool registry for runtime configuration."""

from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from integro.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ToolInfo:
    """Information about a registered tool."""
    
    name: str
    function: Callable
    description: str
    category: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolRegistry:
    """
    Registry for managing tools at runtime.
    
    Allows dynamic registration and retrieval of tools.
    """
    
    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, ToolInfo] = {}
        self._categories: Dict[str, List[str]] = {}
    
    def register(
        self,
        tool: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a tool in the registry.
        
        Args:
            tool: The tool function/callable
            name: Tool name (defaults to function name)
            description: Tool description (defaults to docstring)
            category: Tool category for organization
            metadata: Additional metadata
        """
        # Ben, get the tool's name from function or fallback
        tool_name = name or getattr(tool, '__name__', str(tool))
        
        # Ben, pull description from docstring if not provided
        tool_description = description or getattr(tool, '__doc__', '') or "No description"
        
        # Ben, bundle all the tool metadata together
        tool_info = ToolInfo(
            name=tool_name,
            function=tool,
            description=tool_description.strip(),
            category=category,
            metadata=metadata or {}
        )
        
        # Store it in our registry
        self._tools[tool_name] = tool_info
        
        # Ben, add to category tracking for easy lookup
        if category not in self._categories:
            self._categories[category] = []
        if tool_name not in self._categories[category]:
            self._categories[category].append(tool_name)
        
        logger.debug(f"Registered tool: {tool_name} in category: {category}")
    
    def register_batch(
        self,
        tools: List[Callable],
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register multiple tools at once.
        
        Args:
            tools: List of tool functions
            category: Category for all tools
            metadata: Metadata for all tools
        """
        for tool in tools:
            self.register(tool, category=category, metadata=metadata)
    
    def get(self, name: str) -> Optional[Callable]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool function or None
        """
        tool_info = self._tools.get(name)
        return tool_info.function if tool_info else None
    
    def get_info(self, name: str) -> Optional[ToolInfo]:
        """
        Get tool information by name.
        
        Args:
            name: Tool name
            
        Returns:
            ToolInfo or None
        """
        return self._tools.get(name)
    
    def get_by_category(self, category: str) -> List[Callable]:
        """
        Get all tools in a category.
        
        Args:
            category: Category name
            
        Returns:
            List of tool functions
        """
        tool_names = self._categories.get(category, [])
        return [self._tools[name].function for name in tool_names if name in self._tools]
    
    def get_all(self) -> List[Callable]:
        """
        Get all registered tools.
        
        Returns:
            List of all tool functions
        """
        return [info.function for info in self._tools.values()]
    
    def list_tools(self) -> Dict[str, List[str]]:
        """
        List all tools organized by category.
        
        Returns:
            Dictionary of category -> tool names
        """
        return self._categories.copy()
    
    def list_categories(self) -> List[str]:
        """
        List all categories.
        
        Returns:
            List of category names
        """
        return list(self._categories.keys())
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            name: Tool name
            
        Returns:
            Success status
        """
        if name in self._tools:
            tool_info = self._tools[name]
            del self._tools[name]
            
            # Ben, clean up category tracking too
            if tool_info.category in self._categories:
                self._categories[tool_info.category].remove(name)
                if not self._categories[tool_info.category]:
                    del self._categories[tool_info.category]
            
            logger.debug(f"Unregistered tool: {name}")
            return True
        
        return False
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._categories.clear()
        logger.debug("Cleared tool registry")
    
    def __len__(self) -> int:
        """Get number of registered tools."""
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools
    
    def __repr__(self) -> str:
        """String representation."""
        return f"ToolRegistry({len(self._tools)} tools in {len(self._categories)} categories)"