"""Configuration classes for Integro agents."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for a model with provider and parameters."""
    
    provider: str  # Ben, which AI provider to use
    model_id: str
    params: Dict[str, Any] = field(default_factory=dict)
    
    def create_model(self):
        """Factory method to create the appropriate model instance."""
        # Ben, import only what's installed to avoid crashes
        model_classes = {}
        
        try:
            from agno.models.anthropic import Claude
            model_classes['anthropic'] = Claude
        except ImportError:
            pass
            
        try:
            # Direct Agno v2 import
            from agno.models.openai import OpenAIChat as OpenAI
            model_classes['openai'] = OpenAI
        except ImportError:
            pass
            
        try:
            from agno.models.google import Gemini
            model_classes['google'] = Gemini
        except ImportError:
            pass
            
        try:
            # Ben, we have our own Groq wrapper that handles things better
            from integro.models.groq import Groq
            model_classes['groq'] = Groq
        except ImportError:
            try:
                # Use agno's version if ours isn't there
                # Direct Agno v2 import
                from agno.models.groq import Groq
                model_classes['groq'] = Groq
            except ImportError:
                pass
        
        model_class = model_classes.get(self.provider.lower())
        if not model_class:
            raise ValueError(f"Unknown or unavailable provider: {self.provider}")
            
        # Ben, some params go to init, others go per-request
        params = self.params.copy()
        
        # Ben, normalize common params across providers
        max_completion_tokens = params.pop('max_completion_tokens', None)
        reasoning_effort = params.pop('reasoning_effort', None)
        parallel_tool_calls = params.pop('parallel_tool_calls', None)
        
        # Ben, figure out what params the model's constructor accepts
        init_kwargs: Dict[str, Any] = {}
        extra_request_params: Dict[str, Any] = {}
        
        try:
            # Ben, check dataclass fields first (cleaner)
            from dataclasses import fields as dataclass_fields, is_dataclass
            if is_dataclass(model_class):
                init_field_names = {f.name for f in dataclass_fields(model_class)}
            else:
                raise TypeError
        except Exception:
            # Ben, if not a dataclass, inspect the constructor
            import inspect
            sig = inspect.signature(model_class)
            init_field_names = {
                name for name, p in sig.parameters.items() 
                if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)
            }
        
        for key, value in params.items():
            if key in init_field_names:
                init_kwargs[key] = value
            else:
                extra_request_params[key] = value
        
        # Ben, map our generic params to provider-specific ones
        if max_completion_tokens is not None:
            extra_request_params['max_tokens'] = max_completion_tokens
        
        if parallel_tool_calls is not None:
            extra_request_params['parallel_tool_calls'] = parallel_tool_calls
        
        if reasoning_effort is not None:
            if self.provider.lower() == 'openai':
                extra_request_params['reasoning'] = {"effort": reasoning_effort}
            else:
                extra_request_params['reasoning_effort'] = reasoning_effort
        
        # Ben, bundle extra params into request_params if the model supports it
        if 'request_params' in init_field_names and extra_request_params:
            init_kwargs['request_params'] = {
                **(init_kwargs.get('request_params') or {}),
                **extra_request_params,
            }
        
        return model_class(id=self.model_id, **init_kwargs)


@dataclass
class AgentConfig:
    """Configuration for an Integro agent."""
    
    name: str = "Integro"
    description: str = "A configurable AI assistant"
    models: List[ModelConfig] = field(default_factory=list)
    instructions: List[str] = field(default_factory=list)
    tools: List[Any] = field(default_factory=list)
    
    # Ben, how the agent behaves during execution
    stream: bool = False
    stream_intermediate_steps: bool = False
    markdown: bool = True
    # show_tool_calls removed in v2 - always enabled
    tool_call_limit: int = 20
    
    # Ben, for long-term memory across sessions
    enable_memory: bool = True
    memory_adapter: Optional[Any] = None
    
    # Ben, conversation history management
    enable_storage: bool = True
    storage_adapter: Optional[Any] = None
    add_history_to_messages: bool = True
    num_history_runs: int = 5
    
    # Ben, RAG configuration
    knowledge: Optional[Any] = None
    search_knowledge: bool = True
    add_references: bool = False
    
    # Ben, runtime state and context injection
    session_state: Dict[str, Any] = field(default_factory=dict)
    add_state_in_messages: bool = True
    context: Dict[str, Any] = field(default_factory=dict)
    add_context: bool = True
    
    # Ben, multi-step thinking config
    reasoning: bool = False
    reasoning_model: Optional[ModelConfig] = None
    
    # Ben, response formatting options
    response_model: Optional[Any] = None
    use_json_mode: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for Agent initialization."""
        config = {
            'description': self.description,
            'markdown': self.markdown,
            # 'show_tool_calls' removed in v2,
            'tool_call_limit': self.tool_call_limit,
            'add_history_to_messages': self.add_history_to_messages,
            'num_history_runs': self.num_history_runs,
            'session_state': self.session_state,
            'add_state_in_messages': self.add_state_in_messages,
            'context': self.context,
            'add_context': self.add_context,
            'reasoning': self.reasoning,
            'response_model': self.response_model,
            'use_json_mode': self.use_json_mode,
            'add_datetime_to_instructions': True,
        }
        
        # Ben, only include adapters if they're enabled
        if self.enable_memory and self.memory_adapter:
            config['memory'] = self.memory_adapter
        
        if self.enable_storage and self.storage_adapter:
            config['storage'] = self.storage_adapter
        
        if self.knowledge:
            config['knowledge'] = self.knowledge
            config['search_knowledge'] = self.search_knowledge
            config['add_references'] = self.add_references
        
        if self.reasoning_model:
            try:
                config['reasoning_model'] = self.reasoning_model.create_model()
            except Exception as e:
                logger.warning(f"Failed to create reasoning model: {e}")
        
        return config