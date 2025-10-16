"""Agent configuration loader for YAML, JSON, and SQLite storage."""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict, field
from integro.agent import IntegroAgent
from integro.agent.config import ModelConfig
from integro.utils.logging import get_logger
import os

logger = get_logger(__name__)


@dataclass
class AgentConfig:
    """Configuration for an Integro agent."""
    
    name: str
    description: str = ""
    user_id: str = "default"
    models: List[Dict[str, Any]] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)  # Ben, tool names/paths to load
    instructions: List[str] = field(default_factory=list)
    knowledge_base_id: Optional[str] = None  # Ben, reference to KB by ID
    
    # Behavior settings
    stream: bool = False
    stream_intermediate_steps: bool = False
    markdown: bool = True
    # show_tool_calls removed in v2 - always enabled
    tool_call_limit: int = 20
    
    # Memory settings
    enable_memory: bool = True
    memory_type: str = "sqlite"  # sqlite or qdrant
    memory_config: Dict[str, Any] = field(default_factory=dict)
    
    # Storage settings
    enable_storage: bool = True
    storage_db_file: str = "sessions.db"
    add_history_to_messages: bool = True
    num_history_runs: int = 5
    
    # Knowledge settings
    search_knowledge: bool = True
    add_references: bool = False
    
    # State & context
    session_state: Dict[str, Any] = field(default_factory=dict)
    add_state_in_messages: bool = True
    context: Dict[str, Any] = field(default_factory=dict)
    add_context: bool = True
    
    # Reasoning
    reasoning: bool = False
    reasoning_model: Optional[Dict[str, Any]] = None
    
    # Output
    response_model: Optional[Any] = None
    use_json_mode: bool = False
    
    # Metadata
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        """Create from dictionary with v1 to v2 migration."""
        # Map v1 parameters to v2 equivalents
        param_mapping = {
            'storage': 'enable_storage',  # v1 storage -> v2 enable_storage 
            'add_history_to_messages': 'add_history_to_messages',  # Keep for now, mapped in integro.py
            'add_state_in_messages': 'add_state_in_messages',  # Keep for now, mapped in integro.py
            'context': 'context',  # Keep for now, mapped in integro.py
            'response_model': 'response_model',  # Keep for now, mapped in integro.py
        }
        
        # Parameters to completely remove (deprecated with no replacement)
        deprecated_params = [
            'show_tool_calls',  # Removed in v2 - always enabled
            'mode',  # Storage mode deprecated
            'add_datetime_to_instructions',  # Now add_datetime_to_context
        ]
        
        # Create filtered data
        filtered_data = {}
        for k, v in data.items():
            if k in deprecated_params:
                continue  # Skip deprecated params
            elif k in param_mapping:
                filtered_data[param_mapping[k]] = v
            else:
                filtered_data[k] = v
        
        return cls(**filtered_data)


class AgentLoader:
    """Loader for agent configurations from various sources."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize agent loader.
        
        Args:
            base_path: Base directory for resolving relative paths
        """
        self.base_path = base_path or Path.cwd()
    
    def load_from_file(self, file_path: Union[str, Path]) -> AgentConfig:
        """
        Load agent configuration from YAML or JSON file.
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            AgentConfig object
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        with open(path, 'r') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            elif path.suffix.lower() == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {path.suffix}")
        
        logger.info(f"Loaded agent configuration from {path}")
        return AgentConfig.from_dict(data)
    
    def save_to_file(self, config: AgentConfig, file_path: Union[str, Path]) -> None:
        """
        Save agent configuration to YAML or JSON file.
        
        Args:
            config: AgentConfig object
            file_path: Path to save configuration
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path
        
        # Ben, ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = config.to_dict()
        
        with open(path, 'w') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
            elif path.suffix.lower() == '.json':
                json.dump(data, f, indent=2)
            else:
                raise ValueError(f"Unsupported file format: {path.suffix}")
        
        logger.info(f"Saved agent configuration to {path}")
    
    def create_agent(self, config: AgentConfig, knowledge_base=None, tools=None) -> IntegroAgent:
        """
        Create an IntegroAgent instance from configuration.
        
        Args:
            config: AgentConfig object
            knowledge_base: Optional knowledge base instance
            tools: Optional list of tool functions
            
        Returns:
            Configured IntegroAgent instance
        """
        # Ben, prepare memory configuration
        memory = None
        if config.enable_memory:
            if config.memory_type == "qdrant":
                from integro.memory.qdrant import QdrantMemory
                memory = QdrantMemory(
                    user_id=config.user_id,
                    **config.memory_config
                )
        
        # Ben, convert model configs
        models = []
        for model_dict in config.models:
            if isinstance(model_dict, dict):
                models.append(model_dict)
            else:
                models.append(ModelConfig.from_dict(model_dict))
        
        # Ben, create the agent
        agent = IntegroAgent(
            name=config.name,
            description=config.description,
            user_id=config.user_id,
            models=models or None,  # Use default if empty
            tools=tools or [],
            instructions=config.instructions,
            memory=memory,
            knowledge=knowledge_base,
            stream=config.stream,
            stream_intermediate_steps=config.stream_intermediate_steps,
            markdown=config.markdown,
            # show_tool_calls removed in v2,
            tool_call_limit=config.tool_call_limit,
            enable_memory=config.enable_memory,
            enable_storage=config.enable_storage,
            storage_db_file=config.storage_db_file,
            add_history_to_messages=config.add_history_to_messages,
            num_history_runs=config.num_history_runs,
            search_knowledge=config.search_knowledge,
            add_references=config.add_references,
            session_state=config.session_state,
            add_state_in_messages=config.add_state_in_messages,
            context=config.context,
            add_context=config.add_context,
            reasoning=config.reasoning,
            reasoning_model=config.reasoning_model,
            response_model=config.response_model,
            use_json_mode=config.use_json_mode
        )
        
        logger.info(f"Created agent '{config.name}' from configuration")
        # Log DB backend choices for visibility
        try:
            backend = "PostgreSQL" if os.getenv("DATABASE_URL") else "SQLite"
        except Exception:
            backend = "<unknown>"
        logger.info(f"Agent storage/memory backend preference: {backend}")
        return agent
    
    @staticmethod
    def create_default_config(name: str = "Assistant") -> AgentConfig:
        """
        Create a default agent configuration.
        
        Args:
            name: Agent name
            
        Returns:
            Default AgentConfig
        """
        return AgentConfig(
            name=name,
            description=f"A helpful AI assistant named {name}",
            models=[
                {
                    "provider": "groq",
                    "model_id": "moonshotai/kimi-k2-instruct-0905",
                    "params": {"temperature": 0.7}
                }
            ],
            instructions=[
                "Be helpful and friendly",
                "Provide clear and concise answers",
                "If you don't know something, say so"
            ]
        )