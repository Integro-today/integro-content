"""Groq model adapter for Integro."""

import os
from typing import Optional
from dataclasses import dataclass
# Direct Agno v2 import
from agno.models.groq import Groq as AgnoGroq


@dataclass
class Groq(AgnoGroq):
    """
    Groq model adapter that automatically uses GROQ_API_KEY from environment.
    """
    
    def __init__(self, id: str, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Groq model.
        
        Args:
            id: Model ID (e.g., 'moonshotai/kimi-k2-instruct-0905')
            api_key: Optional API key (defaults to GROQ_API_KEY env var)
            **kwargs: Additional parameters
        """
        # Ben, grab API key from env if not explicitly passed. We will need to adapt this to whatever live envrionment we run in eventually.
        if not api_key:
            api_key = os.getenv('GROQ_API_KEY')
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment and not provided")
        
        # Ben, we need to pass everything up to agno's Groq class
        super().__init__(id=id, api_key=api_key, **kwargs)