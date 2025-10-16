"""Main Integro agent implementation."""

from typing import List, Dict, Any, Optional, Callable, Union
import os
from datetime import datetime
from integro.agent.base import BaseAgent
from integro.agent.config import ModelConfig, AgentConfig
from integro.memory.qdrant import QdrantMemory
from integro.tools.registry import ToolRegistry
from integro.utils.logging import get_logger
# Direct Agno v2 imports
from agno.db.sqlite import SqliteDb as Storage  # Using db not storage
from agno.db.sqlite import SqliteDb  # For memory database
from agno.memory.manager import MemoryManager as Memory  # Using manager not v2
from integro.storage.factory import create_storage_adapter, get_storage_info

AGNO_VERSION = 2

logger = get_logger(__name__)


class IntegroAgent(BaseAgent):
    """
    A configurable AI agent with runtime tool configuration and memory support.
    
    This agent provides:
    - Runtime configurable tools and models
    - User-scoped memory with Qdrant
    - Conversation history management
    - Clean, extensible architecture
    """
    
    def __init__(
        self,
        name: str = "Integro",
        description: str = "A configurable AI assistant",
        user_id: str = "default",
        models: Optional[List[Union[Dict[str, Any], ModelConfig]]] = None,
        tools: Optional[List[Callable]] = None,
        instructions: Optional[List[str]] = None,
        memory: Optional[Union[QdrantMemory, Memory]] = None,
        storage: Optional[Any] = None,
        knowledge: Optional[Any] = None,
        # Ben, these control how the agent behaves during execution
        stream: bool = False,
        stream_intermediate_steps: bool = False,
        markdown: bool = True,
        # show_tool_calls removed in v2 - always enabled
        tool_call_limit: int = 20,
        # Ben, memory lets the agent remember things across sessions
        enable_memory: bool = True,
        memory_db_file: str = "memory.db",
        # Ben, storage keeps conversation history
        enable_storage: bool = True,
        storage_db_file: str = "sessions.db",
        add_history_to_messages: bool = True,
        num_history_runs: int = 5,
        # Ben, knowledge base for RAG (retrieval-augmented generation)
        search_knowledge: Optional[bool] = None,  # Auto-enabled if knowledge is provided
        add_references: bool = False,
        # Ben, state and context get injected into conversations
        session_state: Optional[Dict[str, Any]] = None,
        add_state_in_messages: bool = True,
        context: Optional[Dict[str, Any]] = None,
        add_context: bool = True,
        # Ben, reasoning enables multi-step thinking before responding
        reasoning: bool = False,
        reasoning_model: Optional[Union[Dict[str, Any], ModelConfig]] = None,
        # Ben, controls how the agent formats its responses
        response_model: Optional[Any] = None,
        use_json_mode: bool = False,
        # Ben, extra params to pass to the model
        temperature: Optional[float] = None,
        **kwargs
    ):
        """
        Initialize the Integro agent.
        
        Args:
            name: Agent name
            description: Agent description
            user_id: User identifier for scoping
            models: List of model configurations
            tools: List of tool functions
            instructions: Custom instructions
            memory: Memory adapter (QdrantMemory or agno Memory)
            storage: Storage adapter
            knowledge: Knowledge base
            ... (other parameters as documented)
        """
        self.user_id = user_id
        self.tool_registry = ToolRegistry()
        
        # Ben, add any tools the user gave us
        if tools:
            self.tool_registry.register_batch(tools)
        
        # Keep track of user's custom instructions
        self.custom_instructions = instructions or []
        
        # Ben, normalize model configs to our format
        model_configs = []
        if models:
            for model in models:
                if isinstance(model, dict):
                    model_configs.append(ModelConfig(**model))
                else:
                    model_configs.append(model)
        else:
            # Ben, fallback to Claude Sonnet if no models specified
            model_configs = [
                ModelConfig(
                    provider="anthropic",
                    model_id="claude-3-sonnet-20240229",
                    params={"temperature": 0.7}
                )
            ]
        
        # Ben, separate model for reasoning steps if enabled
        reasoning_model_config = None
        if reasoning_model:
            if isinstance(reasoning_model, dict):
                reasoning_model_config = ModelConfig(**reasoning_model)
            else:
                reasoning_model_config = reasoning_model
        
        # Ben, configure memory adapter (prefer PostgreSQL when available)
        memory_adapter = memory
        if enable_memory and not memory_adapter:
            if isinstance(memory, QdrantMemory):
                memory_adapter = memory
            else:
                db_url = os.getenv("DATABASE_URL")
                if db_url:
                    try:
                        from agno.db.postgres import PostgresDb as Storage
                        # Try multiple constructor signatures to be compatible across versions
                        attempts = [
                            {"db_url": db_url},
                            {"url": db_url},
                        ]
                        storage_db = None
                        last_err = None
                        for params in attempts:
                            try:
                                storage_db = Storage(**params)
                                break
                            except Exception as e:  # noqa: BLE001
                                last_err = e
                                continue
                        if storage_db is None:
                            raise RuntimeError(f"Failed to init PostgresDb for memory: {last_err}")
                        memory_adapter = Memory(db=storage_db)
                        logger.info("Memory configured to use PostgreSQL (DATABASE_URL detected)")
                    except Exception as e:
                        logger.warning(f"PostgreSQL memory setup failed ({e}); falling back to SQLite")
                        memory_adapter = Memory(db=SqliteDb(db_file=memory_db_file))
                else:
                    # Ben, SQLite is our fallback if PostgreSQL isn't configured
                    memory_adapter = Memory(db=SqliteDb(db_file=memory_db_file))
                
                try:
                    db_kind = type(getattr(memory_adapter, 'db', None)).__name__
                except Exception:
                    db_kind = "<unknown>"
                logger.info(f"Memory adapter initialized (type={db_kind})")
        
        # Ben, configure conversation storage with auto-detection (prefers PostgreSQL)
        storage_adapter = storage
        if enable_storage and not storage_adapter:
            # Use factory to auto-detect PostgreSQL or fallback to SQLite
            storage_adapter = create_storage_adapter(
                name=name,
                enable_storage=True,
                storage_db_file=storage_db_file
            )
            
            # Log storage info for debugging
            storage_info = get_storage_info()
            logger.info(f"Storage configuration: {storage_info['storage_type']} "
                       f"(env: {storage_info.get('railway_environment', 'local')})")
        
        # Ben, auto-enable search_knowledge if knowledge base is provided
        if search_knowledge is None:
            search_knowledge = knowledge is not None
            if search_knowledge:
                logger.info("Auto-enabled search_knowledge since knowledge base was provided")
        
        # Ben, if we have a custom KnowledgeBase, convert it to AgentKnowledge
        agent_knowledge = knowledge
        if knowledge and not hasattr(knowledge, 'vector_db'):
            # This looks like our custom KnowledgeBase, convert it
            try:
                from integro.memory.agno_knowledge import create_agent_knowledge
                from integro.memory.knowledge import KnowledgeBase as IntegroKB
                
                if isinstance(knowledge, IntegroKB):
                    logger.info("Converting Integro KnowledgeBase to AgentKnowledge")
                    agent_knowledge = create_agent_knowledge(
                        integro_kb=knowledge,
                        collection_name=f"{name.lower().replace(' ', '_')}_knowledge",
                        in_memory=False  # CRITICAL: Use disk storage for Railway
                    )
            except Exception as e:
                logger.warning(f"Could not convert knowledge base: {e}")
                agent_knowledge = knowledge
        
        # Ben, bundle everything into our config object
        config = AgentConfig(
            name=name,
            description=description,
            models=model_configs,
            instructions=self.custom_instructions,
            tools=self.tool_registry.get_all(),
            stream=stream,
            stream_intermediate_steps=stream_intermediate_steps,
            markdown=markdown,
            # show_tool_calls removed in v2
            tool_call_limit=tool_call_limit,  # Ben, max tool calls per run to prevent loops
            enable_memory=enable_memory,
            memory_adapter=memory_adapter,
            enable_storage=enable_storage,
            storage_adapter=storage_adapter,
            add_history_to_messages=add_history_to_messages,
            num_history_runs=num_history_runs,
            knowledge=agent_knowledge,
            search_knowledge=search_knowledge,
            add_references=add_references,
            session_state=session_state or {"user_id": user_id},
            add_state_in_messages=add_state_in_messages,
            context=context or {},
            add_context=add_context,
            reasoning=reasoning,
            reasoning_model=reasoning_model_config,
            response_model=response_model,
            use_json_mode=use_json_mode
        )
        
        # Ben, call parent class to set everything up
        super().__init__(config)
        
        # Ben, keep a reference to Qdrant for direct access if needed
        self.qdrant_memory = memory if isinstance(memory, QdrantMemory) else None
    
    def get_instructions(self) -> List[str]:
        """
        Return agent instructions.
        
        Combines default instructions with custom ones.
        """
        instructions = []
        
        # Ben, tell the agent who it is
        instructions.extend([
            f"You are {self.config.name}, {self.config.description}",
            "",
            "Core principles:",
            "- Provide helpful, accurate information",
            "- Be concise and clear in responses",
            "- Use available tools when appropriate",
            "- Maintain context across conversations",
            ""
        ])
        
        # Ben, list out available tools for the agent to know about
        if len(self.tool_registry) > 0:
            instructions.append("Available tool categories:")
            categories = self.tool_registry.list_tools()
            for category, tool_names in categories.items():
                instructions.append(f"- {category}: {', '.join(tool_names)}")
            instructions.append("")
        
        # Ben, append any custom instructions from the user
        if self.custom_instructions:
            instructions.extend(self.custom_instructions)
            instructions.append("")
        
        # Ben, inject current user and time context
        instructions.extend([
            f"Current user: {self.user_id}",
            f"Current timestamp: {datetime.utcnow().isoformat()}",
        ])
        
        return instructions
    
    def get_tools(self) -> List[Callable]:
        """
        Return the list of registered tools.
        """
        return self.tool_registry.get_all()
    
    def register_tool(
        self,
        tool: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: str = "general"
    ) -> None:
        """
        Register a new tool at runtime.
        
        Args:
            tool: Tool function
            name: Tool name
            description: Tool description
            category: Tool category
        """
        self.tool_registry.register(tool, name, description, category)
        
        # Ben, refresh the agent's tool list if it's already running
        if self.agent:
            self.agent.tools = self.get_tools()
    
    def register_tools(
        self,
        tools: List[Callable],
        category: str = "general"
    ) -> None:
        """
        Register multiple tools at runtime.
        
        Args:
            tools: List of tool functions
            category: Category for all tools
        """
        self.tool_registry.register_batch(tools, category)
        
        # Ben, refresh the agent's tool list if it's already running
        if self.agent:
            self.agent.tools = self.get_tools()
    
    def unregister_tool(self, name: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            name: Tool name
            
        Returns:
            Success status
        """
        success = self.tool_registry.unregister(name)
        
        # Ben, refresh the agent's tool list if it's already running
        if success and self.agent:
            self.agent.tools = self.get_tools()
        
        return success
    
    def list_tools(self) -> Dict[str, List[str]]:
        """
        List all registered tools by category.
        
        Returns:
            Dictionary of category -> tool names
        """
        return self.tool_registry.list_tools()
    
    async def save_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        memory_type: str = "conversation"
    ) -> Optional[str]:
        """
        Save a memory using Qdrant if available.
        
        Args:
            content: Memory content
            metadata: Optional metadata
            memory_type: Memory type
            
        Returns:
            Memory ID if saved
        """
        if self.qdrant_memory:
            return await self.qdrant_memory.add_memory(content, metadata, memory_type)
        return None
    
    async def search_memories(
        self,
        query: str,
        limit: int = 10,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search memories using Qdrant if available.
        
        Args:
            query: Search query
            limit: Maximum results
            memory_type: Optional memory type filter
            
        Returns:
            List of matching memories
        """
        if self.qdrant_memory:
            return await self.qdrant_memory.search_memories(query, limit, memory_type)
        return []
    
    def setup_agent(self, agent):
        """
        Additional setup after agent initialization.
        """
        # Ben, stash user info in the session state for context
        if hasattr(agent, 'session_state'):
            agent.session_state['user_id'] = self.user_id
            agent.session_state['agent_type'] = 'integro'
        
        logger.info(f"IntegroAgent initialized for user {self.user_id}")


# Ben, here's how you'd use this in practice
if __name__ == "__main__":
    import asyncio
    from agno.tools import tool
    
    # Ben, example tools to show how it works
    @tool
    def calculate(expression: str) -> str:
        """Calculate a mathematical expression."""
        try:
            result = eval(expression)
            return f"The result is: {result}"
        except Exception as e:
            return f"Error calculating: {e}"
    
    @tool
    def get_time() -> str:
        """Get the current time."""
        return datetime.now().isoformat()
    
    # Ben, set up an agent with all the bells and whistles
    agent = IntegroAgent(
        name="Math Assistant",
        description="An AI assistant that can perform calculations",
        user_id="user123",
        models=[
            {"provider": "anthropic", "model_id": "claude-3-sonnet-20240229"}
        ],
        tools=[calculate, get_time],
        instructions=[
            "You are a helpful math assistant.",
            "Always show your work when solving problems.",
            "Be encouraging and patient."
        ],
        memory=QdrantMemory(user_id="user123"),
        stream=True
    )
    
    # Ben, typical usage pattern
    async def main():
        # Get the agent ready
        await agent.initialize()
        
        # Try a math question
        response = await agent.arun("What is 15 * 23?")
        print(response)
        
        # Store something for later
        await agent.save_memory(
            "User asked about 15 * 23, result was 345",
            metadata={"topic": "multiplication"}
        )
        
        # Find related memories
        memories = await agent.search_memories("multiplication")
        print(f"Found {len(memories)} related memories")
    
    # Ben, uncomment to run the example
    # asyncio.run(main())