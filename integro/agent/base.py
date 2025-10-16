"""Base agent class for Integro."""

from typing import List, Dict, Any, Optional, Union, Callable
from abc import ABC, abstractmethod
import asyncio
import os
from integro.agent.config import ModelConfig, AgentConfig
from integro.utils.logging import get_logger
# Direct Agno v2 import
from agno.agent import Agent

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Extensible base agent class with LLM fallback support.
    
    Subclasses should override:
    - get_instructions() - to provide custom instructions
    - get_tools() - to provide custom tools
    - setup_agent() - for additional agent configuration
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the base agent.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.agent = None
        self.current_model_index = 0
        self._initialized = False
        
        # Ben, handle different event loop types gracefully
        self._setup_environment()
    
    def _setup_environment(self):
        """Setup environment variables for compatibility with various event loops."""
        try:
            # Ben, check what kind of event loop we're in
            loop = asyncio.get_running_loop()
            logger.debug(f"Current event loop: {loop} (type: {type(loop)})")
            
            # Ben, uvloop needs special handling to avoid conflicts with agno
            if 'uvloop' in str(type(loop)).lower():
                logger.info("Detected uvloop environment, configuring for compatibility")
                os.environ['UVLOOP_DISABLE_PATCHING'] = '1'
                os.environ['AGNO_UVLOOP_COMPAT'] = '1'
                os.environ['OPENAI_ASYNC_HTTP_CLIENT'] = '1'
                os.environ['OPENAI_HTTP_CLIENT_BACKEND'] = 'aiohttp'
                os.environ['AGNO_DISABLE_LOOP_PATCHING'] = '1'
                os.environ['ANYIO_DISABLE_LOOP_PATCHING'] = '1'
        except RuntimeError:
            # No loop running yet, we're good
            logger.debug("No current event loop detected")
    
    async def initialize(self):
        """Initialize the agent with the first available model."""
        if self._initialized:
            logger.debug("Agent already initialized, skipping")
            return
        
        logger.info(f"Initializing agent {self.config.name}...")
        self.current_model_index = 0
        await self._create_agent_with_current_model()
        self._initialized = True
        logger.info(f"Agent {self.config.name} initialization complete")
    
    async def _create_agent_with_current_model(self):
        """Create agent instance with the current model."""
        if self.current_model_index >= len(self.config.models):
            raise RuntimeError("All models have failed. No more fallback options.")
        
        model_config = self.config.models[self.current_model_index]
        logger.info(f"Creating model: {model_config.provider} ({model_config.model_id})")
        try:
            import time
            model_start = time.time()
            model = model_config.create_model()
            logger.info(f"Model created in {time.time() - model_start:.3f}s")
            
            # Grab our tools and instructions for the agent
            logger.debug("Getting tools and instructions...")
            tools = self.get_tools()
            instructions = self.get_instructions()
            logger.debug(f"Got {len(tools)} tools and {len(instructions)} instructions")
            
            # Convert config to dict format
            agent_config = self.config.to_dict()
            
            # Ben, agno's Agent only accepts certain params - filter out the rest
            # Based on agno_v1_to_v2_migration.txt and agno_documentation.md
            valid_agent_params = {
                'name', 'description', 'instructions', 'tools', 'model',
                'db',  # v2 uses 'db' instead of 'storage' (Section 2.1)
                # 'memory',  # REMOVED in v2 - use db + enable_user_memories instead (Section 3.2)
                'knowledge',  # knowledge base
                'add_history_to_context',  # v2 uses this instead of add_history_to_messages
                'add_datetime_to_context',  # adds current date/time to context
                'num_history_runs',  # number of previous runs to include
                # 'add_session_state_to_context',  # Not found in docs, likely not valid
                'session_state',  # session state dict
                'reasoning',  # enable reasoning
                'reasoning_model',  # model for reasoning
                'output_schema',  # structured output schema
                'use_json_mode',  # force JSON output
                'markdown',  # markdown formatting
                'tool_call_limit',  # max tool calls
                'search_knowledge',  # enable knowledge search
                'add_references',  # add knowledge references  
                'enable_agentic_memory',  # enable memory management
                'enable_user_memories',  # enable user memory tracking (Section 3.2)
                'enable_session_summaries',  # enable session summaries
                'read_chat_history',  # enable chat history reading
                'search_session_history',  # search across sessions
                'num_history_sessions',  # number of sessions to search
                'input_schema',  # input validation schema
                'parser_model',  # model for parsing output
                'output_model',  # model for generating output
                'dependencies',  # dependency injection (Section 1.6 - renamed from context)
                'add_dependencies_to_context',  # add dependencies to context
                'knowledge_retriever',  # custom knowledge retriever (Section 4.5)
                'knowledge_filters',  # filters for knowledge search
                'session_summary_manager',  # custom session summary manager
                'session_id',  # fixed session ID
                'user_id',  # user identifier
                'enable_agentic_state',  # enable state management tool
                'enable_agentic_knowledge_filters',  # enable dynamic knowledge filters
                'store_events',  # store run events
                'events_to_skip',  # events to not store
            }
            
            # Map old v1 parameters to v2 equivalents for backward compatibility
            # Based on agno_v1_to_v2_migration.txt
            param_mapping = {
                # Storage -> Db (Section 2.1)
                'storage': 'db',  # v1 used 'storage', v2 uses 'db'
                
                # Memory -> removed (Section 3.2)
                'memory': None,  # Deprecated - use db + enable_user_memories instead
                
                # Agent parameter changes (Section 1.5, 1.6)  
                'add_state_in_messages': None,  # Deprecated - variables in instructions resolved automatically
                'context': 'dependencies',  # Renamed to dependencies (Section 1.6)
                
                # These are confirmed from migration guide
                'add_history_to_messages': 'add_history_to_context',
                'response_model': 'output_schema',  # response_model is deprecated alias
                'retriever': 'knowledge_retriever',  # Section 4.5
                'add_references': 'add_knowledge_to_context',  # Section 4.6 - though we use add_references still
            }
            
            # Apply parameter mapping and filter
            filtered_config = {}
            for k, v in agent_config.items():
                # Skip None values
                if v is None:
                    continue
                    
                # Check if this is a mapped parameter
                if k in param_mapping:
                    mapped_key = param_mapping[k]
                    # If mapped to None, it's deprecated with no replacement
                    if mapped_key is None:
                        logger.debug(f"Skipping deprecated parameter with no v2 equivalent: {k}")
                        continue
                    # Otherwise use the mapped key
                    if mapped_key in valid_agent_params:
                        filtered_config[mapped_key] = v
                # Not in mapping, use original key
                elif k in valid_agent_params:
                    filtered_config[k] = v
                else:
                    # Log parameters we're filtering out (except known old ones)
                    deprecated_params = [
                        'show_tool_calls', 'add_history_to_messages', 'add_state_in_messages', 
                        'storage', 'context', 'add_context', 'response_model', 'stream',
                        'stream_intermediate_steps', 'add_datetime_to_instructions', 'mode'
                    ]
                    if k not in deprecated_params:
                        logger.debug(f"Filtering out unrecognized Agent parameter: {k}")
            
            # Special handling for 'db' vs 'storage'
            # If we have 'storage' from config but no 'db', use storage as db
            if 'db' in filtered_config and 'storage' in agent_config:
                # Prefer db over storage if both exist
                pass
            elif 'storage' in agent_config and 'db' not in filtered_config:
                filtered_config['db'] = agent_config['storage']
            
            logger.info("Creating agno Agent instance...")
            agent_start = time.time()
            self.agent = Agent(
                name=self.config.name,
                model=model,
                instructions=instructions,
                tools=tools,
                **filtered_config
            )
            logger.info(f"Agent instance created in {time.time() - agent_start:.3f}s")
            
            # Ben, let subclasses hook in here for extra setup
            self.setup_agent(self.agent)
            
            logger.info(f"Successfully initialized {self.config.name} with {model_config.provider} ({model_config.model_id})")
            
        except Exception as e:
            logger.error(f"Failed to initialize model {model_config.provider} ({model_config.model_id}): {e}")
            self.current_model_index += 1
            if self.current_model_index < len(self.config.models):
                await self._create_agent_with_current_model()
            else:
                raise RuntimeError(f"All model attempts failed. Last error: {e}")
    
    @abstractmethod
    def get_instructions(self) -> List[str]:
        """
        Return the list of instructions for the agent.
        Must be overridden by subclasses.
        """
        pass
    
    @abstractmethod
    def get_tools(self) -> List[Callable]:
        """
        Return the list of tools for the agent.
        Must be overridden by subclasses.
        """
        pass
    
    def setup_agent(self, agent: Agent):
        """
        Optional method for subclasses to perform additional agent setup.
        Called after agent initialization.
        """
        pass
    
    def _handle_model_error(self, error: Exception) -> bool:
        """
        Handle model errors and attempt fallback.
        Returns True if fallback was successful, False otherwise.
        """
        logger.warning(f"Model error encountered: {error}. Attempting fallback...")
        self.current_model_index += 1
        
        if self.current_model_index < len(self.config.models):
            # Ben, we have more models to try but need async context
            # Return True to signal the caller should retry
            return True
        return False
    
    def run(self, message: str, **kwargs) -> Any:
        """
        Run the agent with automatic fallback on errors.
        """
        if self.agent is None:
            # Ben, try to init the agent in sync mode if possible
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    raise RuntimeError("Cannot run async initialization in sync context. Call initialize() first.")
                else:
                    loop.run_until_complete(self.initialize())
            except RuntimeError:
                # Ben, no loop exists so we'll make one just for init
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.initialize())
                loop.close()
        
        max_retries = len(self.config.models)
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Ben, use config's streaming settings unless caller overrides
                if 'stream' not in kwargs:
                    kwargs['stream'] = self.config.stream
                if 'stream_intermediate_steps' not in kwargs:
                    kwargs['stream_intermediate_steps'] = self.config.stream_intermediate_steps
                
                # In Agno v2, run() takes input as first positional arg
                return self.agent.run(message, **kwargs)
            
            except Exception as e:
                last_error = e
                logger.error(f"Error during run (attempt {attempt + 1}/{max_retries}): {e}")
                
                if not self._handle_model_error(e):
                    break
        
        # Ben, we tried all models and they all failed
        raise RuntimeError(f"All model attempts failed. Last error: {last_error}")
    
    async def arun(self, message: str, **kwargs) -> Any:
        """
        Async run the agent with automatic fallback on errors.
        """
        if not self._initialized:
            await self.initialize()
        
        max_retries = len(self.config.models)
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Ben, use config's streaming settings unless caller overrides
                if 'stream' not in kwargs:
                    kwargs['stream'] = self.config.stream
                if 'stream_intermediate_steps' not in kwargs:
                    kwargs['stream_intermediate_steps'] = self.config.stream_intermediate_steps
                
                # In Agno v2, arun() takes input as first positional arg
                result = await self.agent.arun(message, **kwargs)
                
                # Ben, sometimes arun returns a coroutine we need to await
                if asyncio.iscoroutine(result):
                    logger.debug("Agent.arun returned a coroutine, awaiting it")
                    result = await result
                
                return result
            
            except Exception as e:
                last_error = e
                logger.error(f"Error during async run (attempt {attempt + 1}/{max_retries}): {e}")
                
                if self._handle_model_error(e):
                    # Ben, try the next model in our fallback list
                    await self._create_agent_with_current_model()
                else:
                    break
        
        # Ben, we tried all models and they all failed
        raise RuntimeError(f"All model attempts failed. Last error: {last_error}")