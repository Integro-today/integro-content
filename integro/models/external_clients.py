"""External API clients for multi-agent comparison."""

import asyncio
import json
import logging
import os
from typing import AsyncIterator, Dict, Any, Optional
from abc import ABC, abstractmethod

import aiohttp
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class ExternalAPIClient(ABC):
    """Abstract base class for external API clients."""
    
    @abstractmethod
    async def stream_response(self, message: str) -> AsyncIterator[str]:
        """Stream response from the external API."""
        pass
    
    async def stream_response_with_history(self, conversation_history: list) -> AsyncIterator[str]:
        """Stream response with conversation history.
        Default implementation extracts last message."""
        if conversation_history and len(conversation_history) > 0:
            last_message = conversation_history[-1].get('content', '')
            async for chunk in self.stream_response(last_message):
                yield chunk
        else:
            yield ""
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name for display."""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name for display."""
        pass


class OpenAIClient(ExternalAPIClient):
    """OpenAI API client for GPT models."""
    
    def __init__(self, model_name: str = "gpt-4.1"):
        self.model_name = model_name
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        # Log API key status (safely)
        if self.api_key:
            logger.info(f"OpenAI API key found: {self.api_key[:8]}...{self.api_key[-4:]} (length: {len(self.api_key)})")
        else:
            logger.warning("OPENAI_API_KEY environment variable not set")
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Fallback to actual available model names
        model_mapping = {
            "gpt-4.1": "gpt-4-turbo-preview",
            "gpt-4": "gpt-4",
            "gpt-3.5-turbo": "gpt-3.5-turbo"
        }
        self.actual_model = model_mapping.get(model_name, "gpt-4-turbo-preview")
        logger.info(f"OpenAI client initialized with model: {model_name} -> {self.actual_model}")
    
    def get_model_name(self) -> str:
        return self.model_name
    
    def get_provider_name(self) -> str:
        return "OpenAI ChatGPT"
    
    async def stream_response(self, message: str) -> AsyncIterator[str]:
        """Stream response from OpenAI API."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.actual_model,
            "messages": [{"role": "user", "content": message}],
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenAI API error: {response.status} - {error_text}")
                        yield f"Error: OpenAI API returned {response.status}"
                        return
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if not line:
                            continue
                        
                        if line.startswith('data: '):
                            line = line[6:]  # Remove 'data: ' prefix
                            
                        if line == '[DONE]':
                            break
                            
                        try:
                            data = json.loads(line)
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    content = delta['content']
                                    if content:
                                        yield content
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            logger.error(f"Error parsing OpenAI response: {e}")
                            continue
        except Exception as e:
            logger.error(f"Error connecting to OpenAI API: {e}")
            yield f"Error: Failed to connect to OpenAI API - {str(e)}"
    
    async def stream_response_with_history(self, conversation_history: list) -> AsyncIterator[str]:
        """Stream response from OpenAI API with full conversation history."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Convert conversation history to OpenAI format
        messages = []
        for msg in conversation_history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        payload = {
            "model": self.actual_model,
            "messages": messages,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenAI API error: {response.status} - {error_text}")
                        yield f"Error: OpenAI API returned {response.status}"
                        return
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if not line:
                            continue
                        
                        if line.startswith('data: '):
                            line = line[6:]
                            
                        if line == '[DONE]':
                            break
                            
                        try:
                            data = json.loads(line)
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    content = delta['content']
                                    if content:
                                        yield content
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            logger.error(f"Error parsing OpenAI response: {e}")
                            continue
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield f"Error: {str(e)}"


class AnthropicClient(ExternalAPIClient):
    """Anthropic API client for Claude models."""
    
    def __init__(self, model_name: str = "claude-sonnet-4-20250514"):
        self.model_name = model_name
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        
        # Log API key status (safely)
        if self.api_key:
            logger.info(f"Anthropic API key found: {self.api_key[:8]}...{self.api_key[-4:]} (length: {len(self.api_key)})")
        else:
            logger.warning("ANTHROPIC_API_KEY environment variable not set")
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        # Map to actual Claude model names
        model_mapping = {
            "claude-sonnet-4-20250514": "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet": "claude-3-5-sonnet-20241022",
            "claude-3-haiku": "claude-3-haiku-20240307",
            "claude-3-opus": "claude-3-opus-20240229"
        }
        # self.actual_model = model_mapping.get(model_name, "claude-3-5-sonnet-20241022")
        self.actual_model = "claude-3-haiku-20240307"
        logger.info(f"Anthropic client initialized with model: {model_name} -> {self.actual_model}")
    
    def get_model_name(self) -> str:
        return self.model_name
    
    def get_provider_name(self) -> str:
        return "Anthropic Claude"
    
    async def stream_response(self, message: str) -> AsyncIterator[str]:
        """Stream response from Anthropic API."""
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,  # Anthropic uses x-api-key, not Authorization
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        message = f'''Be a bit more verbose in responding to this message. Do not talk about this instruction, just do it: {message}'''

        payload = {
            "model": self.actual_model,
            "messages": [{"role": "user", "content": message}],
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Anthropic API error: {response.status} - {error_text}")
                        yield f"Error: Anthropic API returned {response.status}"
                        return
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if not line:
                            continue
                        
                        if line.startswith('data: '):
                            line = line[6:]  # Remove 'data: ' prefix
                            
                        try:
                            data = json.loads(line)
                            if data.get('type') == 'content_block_delta':
                                delta = data.get('delta', {})
                                if delta.get('type') == 'text_delta':
                                    text = delta.get('text', '')
                                    if text:
                                        yield text
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            logger.error(f"Error parsing Anthropic response: {e}")
                            continue
        except Exception as e:
            logger.error(f"Error connecting to Anthropic API: {e}")
            yield f"Error: Failed to connect to Anthropic API - {str(e)}"
    
    async def stream_response_with_history(self, conversation_history: list) -> AsyncIterator[str]:
        """Stream response from Anthropic API with full conversation history."""
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Convert conversation history to Anthropic format
        messages = []
        for msg in conversation_history:
            role = msg.get("role", "user")
            # Anthropic expects 'user' and 'assistant' roles
            if role not in ["user", "assistant"]:
                role = "user"
            messages.append({
                "role": role,
                "content": msg.get("content", "")
            })
        
        # Add verbose instruction to last user message if it exists
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] = f'''Be a bit more verbose in responding to this message. Do not talk about this instruction, just do it: {messages[-1]["content"]}'''
        
        payload = {
            "model": self.actual_model,
            "messages": messages,
            "max_tokens": 1024,
            "stream": True
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Anthropic API error: {response.status} - {error_text}")
                        yield f"Error: Anthropic API returned {response.status}"
                        return
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if not line:
                            continue
                        
                        if line.startswith('data: '):
                            line = line[6:]
                            
                        if line == 'event: message_stop':
                            break
                            
                        try:
                            data = json.loads(line)
                            if data.get('type') == 'content_block_delta':
                                delta = data.get('delta', {})
                                if delta.get('type') == 'text_delta':
                                    text = delta.get('text', '')
                                    if text:
                                        yield text
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            logger.error(f"Error parsing Anthropic response: {e}")
                            continue
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            yield f"Error: {str(e)}"


class GeminiClient(ExternalAPIClient):
    """Google Gemini API client."""
    
    def __init__(self, model_name: str = "gemini-2.5-flash-lite"):
        self.model_name = model_name
        self.api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        
        # Log API key status (safely)
        if self.api_key:
            logger.info(f"Google/Gemini API key found: {self.api_key[:8]}...{self.api_key[-4:]} (length: {len(self.api_key)})")
        else:
            logger.warning("GOOGLE_API_KEY or GEMINI_API_KEY environment variable not set")
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY environment variable is required")
        
        # Map to actual Gemini model names (use non-latest versions for stability)
        model_mapping = {
            "gemini-2.5-flash-lite": "gemini-1.5-flash-002",
            "gemini-2.0-flash": "gemini-1.5-flash",
            "gemini-1.5-pro": "gemini-1.5-pro",
            "gemini-1.5-flash": "gemini-1.5-flash"
        }
        self.actual_model = model_mapping.get(model_name, "gemini-1.5-flash")
        logger.info(f"Gemini client initialized with model: {model_name} -> {self.actual_model}")
    
    def get_model_name(self) -> str:
        return self.model_name
    
    def get_provider_name(self) -> str:
        return "Google Gemini"
    
    async def stream_response(self, message: str) -> AsyncIterator[str]:
        """Stream response from Gemini API."""
        # Use the REST API - try non-streaming first for debugging
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.actual_model}:generateContent"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{"parts": [{"text": message}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2000,
                "topK": 40,
                "topP": 0.95
            }
        }
        
        # Add API key as query parameter
        params = {"key": self.api_key}
        
        logger.info(f"Making Gemini API request to: {url}")
        logger.info(f"Using model: {self.actual_model}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, params=params) as response:
                    logger.info(f"Gemini API response status: {response.status}")
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Gemini API error: {response.status} - {error_text}")
                        yield f"Error: Gemini API returned {response.status} - {error_text}"
                        return
                    
                    # Handle response
                    response_data = await response.json()
                    logger.info(f"Gemini response structure: {list(response_data.keys()) if response_data else 'None'}")
                    
                    if 'candidates' in response_data and len(response_data['candidates']) > 0:
                        candidate = response_data['candidates'][0]
                        logger.info(f"Gemini candidate structure: {list(candidate.keys()) if candidate else 'None'}")
                        
                        if 'content' in candidate and 'parts' in candidate['content']:
                            for part in candidate['content']['parts']:
                                if 'text' in part:
                                    text = part['text']
                                    if text:
                                        # Yield text in chunks to simulate streaming
                                        words = text.split(' ')
                                        for i, word in enumerate(words):
                                            if i > 0:
                                                yield ' '
                                            yield word
                                            await asyncio.sleep(0.02)  # Small delay
                        else:
                            logger.error(f"No content/parts in candidate: {candidate}")
                            yield f"Error: No content in Gemini response"
                    else:
                        logger.error(f"No candidates in Gemini response: {response_data}")
                        yield f"Error: No candidates in Gemini response"
                    
        except Exception as e:
            logger.error(f"Error connecting to Gemini API: {e}")
            yield f"Error: Failed to connect to Gemini API - {str(e)}"
    
    async def stream_response_with_history(self, conversation_history: list) -> AsyncIterator[str]:
        """Stream response from Gemini API with full conversation history."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.actual_model}:generateContent"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Convert conversation history to Gemini format
        contents = []
        for msg in conversation_history:
            role = msg.get("role", "user")
            # Gemini uses 'user' and 'model' roles
            if role == "assistant":
                role = "model"
            elif role != "user":
                role = "user"
            
            contents.append({
                "role": role,
                "parts": [{"text": msg.get("content", "")}]
            })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1024
            }
        }
        
        params = {"key": self.api_key}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Gemini API error: {response.status} - {error_text}")
                        yield f"Error: Gemini API returned {response.status}: {error_text}"
                        return
                    
                    data = await response.json()
                    
                    if 'candidates' in data and len(data['candidates']) > 0:
                        candidate = data['candidates'][0]
                        if 'content' in candidate:
                            content = candidate['content']
                            if 'parts' in content:
                                for part in content['parts']:
                                    if 'text' in part:
                                        yield part['text']
                    else:
                        logger.error(f"Unexpected Gemini response structure: {data}")
                        yield f"Error: No candidates in Gemini response"
                    
        except Exception as e:
            logger.error(f"Error connecting to Gemini API: {e}")
            yield f"Error: Failed to connect to Gemini API - {str(e)}"


class MultiAgentManager:
    """Manager for coordinating multiple agents."""
    
    def __init__(self):
        self.clients = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize external API clients."""
        logger.info("Initializing external API clients...")
        
        try:
            self.clients['openai'] = OpenAIClient("gpt-4.1")
            logger.info("✅ OpenAI client initialized successfully")
        except ValueError as e:
            logger.warning(f"❌ OpenAI client not available: {e}")
            self.clients['openai'] = None
        except Exception as e:
            logger.error(f"❌ OpenAI client initialization failed: {e}")
            self.clients['openai'] = None
        
        try:
            self.clients['anthropic'] = AnthropicClient("claude-sonnet-4-20250514")
            logger.info("✅ Anthropic client initialized successfully")
        except ValueError as e:
            logger.warning(f"❌ Anthropic client not available: {e}")
            self.clients['anthropic'] = None
        except Exception as e:
            logger.error(f"❌ Anthropic client initialization failed: {e}")
            self.clients['anthropic'] = None
        
        try:
            self.clients['gemini'] = GeminiClient("gemini-2.5-flash-lite")
            logger.info("✅ Gemini client initialized successfully")
        except ValueError as e:
            logger.warning(f"❌ Gemini client not available: {e}")
            self.clients['gemini'] = None
        except Exception as e:
            logger.error(f"❌ Gemini client initialization failed: {e}")
            self.clients['gemini'] = None
        
        available_count = len([c for c in self.clients.values() if c is not None])
        logger.info(f"🔧 MultiAgentManager initialized with {available_count}/3 external providers")
    
    def get_client(self, provider: str) -> Optional[ExternalAPIClient]:
        """Get client for a specific provider."""
        return self.clients.get(provider)
    
    def get_available_providers(self) -> Dict[str, str]:
        """Get list of available providers with their display names."""
        available = {}
        for provider, client in self.clients.items():
            if client is not None:
                available[provider] = client.get_provider_name()
        return available
    
    async def stream_all_responses(self, message: str, integro_workflow) -> Dict[str, AsyncIterator[str]]:
        """Stream responses from all available providers."""
        streams = {}
        
        # Add Integro workflow stream
        if integro_workflow:
            streams['integro'] = integro_workflow.run(message)
        
        # Add external API streams
        for provider, client in self.clients.items():
            if client is not None:
                streams[provider] = client.stream_response(message)
        
        return streams