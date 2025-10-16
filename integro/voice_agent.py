"""Voice agent server with dynamic agent loading for LiveKit integration."""

import asyncio
import os
import json
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import AgentSession
from livekit.agents.llm import LLM, ChatContext
from livekit.plugins import assemblyai, cartesia

# Import Integro agent components
from integro.config import AgentLoader, ConfigStorage
from integro.agent import IntegroAgent
from integro.memory.knowledge import KnowledgeBase
from integro.utils.logging import get_logger

logger = get_logger(__name__)
load_dotenv()
logger.info("Environment variables loaded")
logger.info(f"CARTESIA_API_KEY {os.environ.get('CARTESIA_API_KEY', 'not set')}")

# Global storage for agent instances
agent_cache: Dict[str, IntegroAgent] = {}
kb_cache: Dict[str, KnowledgeBase] = {}

# Global variable to store the latest STT transcript across all sessions
latest_stt_transcript = ""


class IntegroLLMAdapter(LLM):
    """Adapter to make IntegroAgent work with LiveKit's LLM interface"""

    def __init__(self, integro_agent: IntegroAgent, session_id: str):
        super().__init__()
        self.agent = integro_agent
        self.session_id = session_id
        self.room = None  # Will be set by entrypoint to publish data messages
        self.latest_transcript = ""  # Store the latest STT transcript

    def _extract_user_input(self, chat_ctx: ChatContext) -> str:
        """Extract user text from LiveKit ChatContext.
        
        LiveKit's ChatContext is an iterable container that stores messages.
        We need to iterate through it to find the most recent user message.
        """
        def content_to_text(content: Any) -> str:
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, str):
                        parts.append(item)
                    else:
                        txt = getattr(item, "text", None)
                        if isinstance(txt, str):
                            parts.append(txt)
                return " ".join(parts).strip()
            if isinstance(content, dict):
                for k in ("text", "content", "message", "transcript"):
                    v = content.get(k)
                    if isinstance(v, str):
                        return v
            return ""

        try:
            # Try accessing as a dict-like object first (most likely to work)
            if hasattr(chat_ctx, 'to_dict'):
                ctx_dict = chat_ctx.to_dict()
                logger.debug(f"ChatContext.to_dict(): {ctx_dict}")
                
                # Look for messages in the dict - check both 'messages' and 'items' keys
                items_to_check = []
                if 'messages' in ctx_dict and ctx_dict['messages']:
                    items_to_check = ctx_dict['messages']
                elif 'items' in ctx_dict and ctx_dict['items']:
                    items_to_check = ctx_dict['items']
                
                if items_to_check:
                    logger.debug(f"Found {len(items_to_check)} items in ChatContext dict")
                    for i, msg in enumerate(reversed(items_to_check)):
                        if isinstance(msg, dict) and msg.get('role') == 'user':
                            content = msg.get('content', '')
                            logger.debug(f"User message content: {content}, type: {type(content)}")
                            if content:
                                text = content_to_text(content)
                                if text:
                                    logger.info(f"Extracted from dict items: {text[:100]}...")
                                    return text
        except Exception as e:
            logger.debug(f"Error accessing ChatContext.to_dict(): {e}")
        
        # Try using the items() method since it was in the available methods
        try:
            if hasattr(chat_ctx, 'items'):
                items = list(chat_ctx.items())
                logger.debug(f"ChatContext.items(): {items}")
                for item in reversed(items):
                    if hasattr(item, 'role') and item.role == 'user':
                        content = getattr(item, 'content', None)
                        if content:
                            text = content_to_text(content)
                            if text:
                                logger.info(f"Extracted from items: {text[:100]}...")
                                return text
        except Exception as e:
            logger.debug(f"Error accessing ChatContext.items(): {e}")
        
        try:
            # Log available methods for debugging
            methods = [m for m in dir(chat_ctx) if not m.startswith("_")]
            logger.debug(f"ChatContext methods: {methods}")
            
            # ChatContext is iterable, so we can iterate through messages
            messages = list(chat_ctx)
            logger.debug(f"Found {len(messages)} messages in ChatContext iteration")
            
            if messages:
                # Find the most recent user message
                last_user_msg = None
                for i, msg in enumerate(reversed(messages)):
                    role = getattr(msg, "role", None)
                    content = getattr(msg, "content", None)
                    logger.debug(f"Message {len(messages)-1-i}: role={role}, content_type={type(content)}")
                    
                    if role == "user":
                        last_user_msg = msg
                        break
                
                # Use the last user message or fallback to the most recent message
                target_msg = last_user_msg or messages[-1]
                content = getattr(target_msg, "content", None)
                
                if content:
                    text = content_to_text(content)
                    if text:
                        logger.info(f"Successfully extracted text: {text[:100]}...")
                        return text
                        
        except Exception as e:
            logger.debug(f"Error iterating ChatContext: {e}")
        
        # Try other potential attributes
        for attr in ("text", "input_text", "message", "content", "utterance", "transcript"):
            if hasattr(chat_ctx, attr):
                val = getattr(chat_ctx, attr)
                text = content_to_text(val)
                if text:
                    logger.info(f"Extracted from {attr}: {text[:100]}...")
                    return text

        # If ChatContext is empty but we have a stored transcript, use that
        if self.latest_transcript:
            logger.info(f"Using adapter stored STT transcript: {self.latest_transcript[:100]}...")
            # Clear the stored transcript after using it to avoid reuse
            transcript = self.latest_transcript
            self.latest_transcript = ""
            return transcript
        
        # Check global transcript as fallback
        global latest_stt_transcript
        if latest_stt_transcript:
            logger.info(f"Using global STT transcript: {latest_stt_transcript[:100]}...")
            # Clear the global transcript after using it to avoid reuse
            transcript = latest_stt_transcript
            latest_stt_transcript = ""
            return transcript
        
        # Last resort: convert to string and warn
        logger.warning("Could not extract meaningful text from ChatContext; this may indicate a LiveKit integration issue")
        logger.warning("No stored transcript available either - STT events may not be working")
        return ""

    def chat(
        self,
        *,
        chat_ctx: ChatContext,
        fnc_ctx: Optional[Any] = None,
        temperature: Optional[float] = None,
        n: Optional[int] = None,
        parallel_tool_calls: Optional[bool] = None,
        tools: Optional[Any] = None,
        tool_choice: Optional[Any] = None,
        **kwargs: Any,
    ) -> Any:
        """Return an async context manager + iterator for LiveKit Agents."""

        class ChatStream:
            def __init__(self, adapter: "IntegroLLMAdapter", ctx: ChatContext):
                self._adapter = adapter
                self._ctx = ctx
                self._chunks = []
                self._index = 0

            async def __aenter__(self):
                logger.debug(f"ChatContext type: {type(self._ctx)}")
                logger.debug(f"ChatContext repr: {repr(self._ctx)}")
                
                # Add comprehensive debugging of ChatContext
                try:
                    ctx_dict = self._ctx.to_dict() if hasattr(self._ctx, 'to_dict') else {}
                    logger.debug(f"ChatContext.to_dict(): {ctx_dict}")
                    if 'messages' in ctx_dict:
                        for i, msg in enumerate(ctx_dict['messages']):
                            logger.debug(f"Message {i}: {msg}")
                    elif 'items' in ctx_dict:
                        for i, msg in enumerate(ctx_dict['items']):
                            logger.debug(f"Item {i}: {msg}")
                except Exception as e:
                    logger.debug(f"Error debugging ChatContext: {e}")
                
                user_input = self._adapter._extract_user_input(self._ctx)
                logger.info(f"Extracted user input: '{user_input}'")

                # Publish user transcript so frontend shows the utterance
                try:
                    if getattr(self._adapter, "room", None) and user_input:
                        payload = json.dumps({
                            "type": "user_transcript",
                            "role": "user",
                            "text": user_input,
                        }).encode("utf-8")
                        logger.info(f"Publishing user transcript: {user_input[:50]}...")
                        await self._adapter.room.local_participant.publish_data(payload, reliable=True)
                        logger.info("User transcript published successfully")
                    else:
                        logger.warning(f"Cannot publish user transcript - room: {getattr(self._adapter, 'room', None)}, user_input: '{user_input}'")
                except Exception as pub_err:
                    logger.error(f"Failed to publish user transcript: {pub_err}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")

                response = await self._adapter.agent.arun(
                    message=user_input,
                    session_id=self._adapter.session_id,
                    stream=False,
                )

                if hasattr(response, "content"):
                    content = response.content
                else:
                    content = str(response)

                words = content.split()
                for i in range(0, len(words), 3):
                    chunk = " ".join(words[i : i + 3])
                    if i + 3 < len(words):
                        chunk += " "
                    self._chunks.append(chunk)

                # Publish assistant transcript over data channel for the frontend
                try:
                    if getattr(self._adapter, "room", None):
                        payload = json.dumps({
                            "type": "assistant_transcript",
                            "role": "assistant",
                            "text": content,
                        }).encode("utf-8")
                        logger.info(f"Publishing assistant transcript: {content[:50]}...")
                        await self._adapter.room.local_participant.publish_data(payload, reliable=True)
                        logger.info("Assistant transcript published successfully")
                    else:
                        logger.warning(f"Cannot publish assistant transcript - room: {getattr(self._adapter, 'room', None)}")
                except Exception as pub_err:
                    logger.error(f"Failed to publish assistant transcript: {pub_err}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")

                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self._index >= len(self._chunks):
                    raise StopAsyncIteration
                chunk = self._chunks[self._index]
                self._index += 1
                return chunk

        return ChatStream(self, chat_ctx)


async def load_agent_from_metadata(metadata: Dict[str, Any]) -> Optional[IntegroLLMAdapter]:
    """Load an Integro agent based on room metadata"""
    client_id = metadata.get("client_id")
    session_id = metadata.get("session_id", f"voice_{client_id}")
    agent_id = metadata.get("agent_id")
    kb_id = metadata.get("kb_id")

    if not agent_id:
        logger.error("No agent_id provided in room metadata")
        return None

    logger.info(f"Loading agent {agent_id} for client {client_id}")

    # Try to get agent from cache
    cache_key = f"{agent_id}_{kb_id}" if kb_id else agent_id
    if cache_key in agent_cache:
        logger.info(f"Using cached agent {cache_key}")
        return IntegroLLMAdapter(agent_cache[cache_key], session_id)

    # Load agent configuration
    storage = ConfigStorage()
    agent_loader = AgentLoader()

    agent_config = await storage.load_agent(agent_id)
    if not agent_config:
        logger.error(f"Agent {agent_id} not found")
        return None

    # Load knowledge base if specified
    kb = None
    if kb_id and kb_id != "none":
        logger.info(f"Loading knowledge base {kb_id}")
        kb_config = await storage.load_knowledge_base(kb_id)

        if kb_config:
            # Check cache first
            if kb_id in kb_cache:
                kb = kb_cache[kb_id]
            else:
                # Create knowledge base
                kb = KnowledgeBase(
                    collection_name=kb_config.collection_name or kb_id,
                    in_memory=True,
                    embedding_model=kb_config.embedding_model
                )

                # Load documents
                documents = await storage.load_kb_documents(kb_id)
                if documents:
                    import struct
                    from qdrant_client.models import PointStruct
                    import uuid

                    points = []
                    for doc in documents:
                        embedding_bytes = doc.get('embedding')
                        if embedding_bytes and isinstance(embedding_bytes, bytes) and len(embedding_bytes) >= 4:
                            try:
                                num_floats = len(embedding_bytes) // 4
                                embedding = list(struct.unpack(f'{num_floats}f', embedding_bytes))

                                doc_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, doc['doc_id']))
                                points.append(
                                    PointStruct(
                                        id=doc_uuid,
                                        vector=embedding,
                                        payload={
                                            "content": doc['content'],
                                            "doc_id": doc['doc_id'],
                                            **(doc.get('metadata', {}))
                                        }
                                    )
                                )
                            except Exception as e:
                                logger.debug(f"Failed to process doc {doc.get('doc_id')}: {e}")

                    if points:
                        kb.client.upsert(
                            collection_name=kb.collection_name,
                            points=points,
                            wait=False
                        )

                # Cache the knowledge base
                kb_cache[kb_id] = kb

    # Create and initialize agent
    agent = agent_loader.create_agent(agent_config, knowledge_base=kb)
    await agent.initialize()

    # Cache the agent
    agent_cache[cache_key] = agent
    logger.info(f"Agent {agent_id} initialized and cached")

    return IntegroLLMAdapter(agent, session_id)


async def entrypoint(ctx: JobContext):
    """Main entry point for the voice agent"""

    # IMPORTANT: Connect to the room first before accessing participants
    await ctx.connect()

    room = ctx.room
    metadata = {}

    logger.info(f"Room name: {room.name}")
    # room.sid is async; await to avoid runtime warning
    try:
        sid = await room.sid
    except Exception:
        sid = "<unavailable>"
    logger.info(f"Room SID: {sid}")
    logger.info(f"Room metadata raw: {room.metadata}")
    logger.info(f"Number of participants: {len(room.remote_participants)}")

    # Try room metadata first
    if room.metadata:
        try:
            metadata = json.loads(room.metadata)
            logger.info(f"Parsed room metadata: {metadata}")
        except json.JSONDecodeError:
            logger.error(f"Failed to parse room metadata: {room.metadata}")

    # If no room metadata, check participants
    if not metadata and room.remote_participants:
        logger.info("No room metadata, checking participants...")
        # Iterate through participants using items() method
        for participant_sid, participant in room.remote_participants.items():
            logger.info(f"Checking participant {participant.identity} (SID: {participant_sid})")
            logger.info(f"Participant metadata: {participant.metadata}")

            if participant.metadata:
                try:
                    metadata = json.loads(participant.metadata)
                    logger.info(f"Using metadata from participant {participant.identity}: {metadata}")
                    break
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse participant metadata: {participant.metadata}")

    # If still no metadata, poll for participants/metadata for a short window
    if not metadata:
        logger.info("No metadata yet; polling for participant metadata...")
        for attempt in range(20):  # ~10s total @ 0.5s intervals
            try:
                # Refresh participants snapshot
                if room.remote_participants:
                    for participant_sid, participant in room.remote_participants.items():
                        pid = getattr(participant, 'identity', '<unknown>')
                        pmeta = getattr(participant, 'metadata', None)
                        if pmeta:
                            try:
                                metadata = json.loads(pmeta)
                                logger.info(f"Discovered metadata from participant {pid} on attempt {attempt+1}: {metadata}")
                                break
                            except Exception:
                                continue
                if metadata:
                    break
            except Exception as e:
                logger.debug(f"Polling metadata error on attempt {attempt+1}: {e}")
            await asyncio.sleep(0.5)

        if not metadata:
            logger.warning("Proceeding without participant metadata after timeout; agent may not load")

    # Initialize STT with AssemblyAI
    stt = assemblyai.STT(
        api_key=os.getenv("ASSEMBLYAI_API_KEY"),
        sample_rate=16000,
        encoding="pcm_s16le",
    )
    
    logger.info(f"STT object type: {type(stt)}")
    logger.info(f"STT object methods: {[m for m in dir(stt) if not m.startswith('_')]}")

    # Initialize TTS with Cartesia
    tts = cartesia.TTS(
        model=os.getenv("CARTESIA_MODEL", "sonic-2"),
        voice=os.getenv("CARTESIA_VOICE_ID", "00a77add-48d5-4ef6-8157-71e5437b282d"),
    )

    # Load the Integro agent
    logger.info("Loading Integro agent...")
    logger.info(f"Metadata for agent loading: {metadata}")
    integro_llm = await load_agent_from_metadata(metadata)
    if not integro_llm:
        logger.error("Failed to load agent, exiting")
        await ctx.shutdown()
        return

    # Create agent session with the three components
    from livekit.agents import Agent

    session = AgentSession(
        stt=stt,  # AssemblyAI for STT
        llm=integro_llm,  # Your Agno agent wrapped
        tts=tts,  # Cartesia for TTS
        use_tts_aligned_transcript=True,
    )

    # Create a simple agent wrapper
    agent = Agent(
        instructions="You are a helpful assistant. Respond naturally and conversationally."
    )

    # Attach room reference to adapter for data publishing
    integro_llm.room = room

    # Set up STT event handling to capture transcripts
    def handle_stt_transcript_sync(*args, **kwargs):
        """Synchronous wrapper for STT transcript handling"""
        async def async_handler():
            # Extract transcript from various possible argument formats
            transcript = None
            
            # Check if first arg is the transcript string
            if args and isinstance(args[0], str):
                transcript = args[0]
            # Check if it's in kwargs
            elif 'transcript' in kwargs:
                transcript = kwargs['transcript']
            elif 'text' in kwargs:
                transcript = kwargs['text']
            # Check if it's an event object with transcript
            elif args and hasattr(args[0], 'transcript'):
                transcript = args[0].transcript
            elif args and hasattr(args[0], 'text'):
                transcript = args[0].text
                
            if transcript and isinstance(transcript, str):
                logger.info(f"STT transcript received: {transcript[:100]}...")
                # Store in both the adapter instance and globally
                integro_llm.latest_transcript = transcript
                global latest_stt_transcript
                latest_stt_transcript = transcript
                # Also publish to frontend
                try:
                    if room and transcript:
                        payload = json.dumps({
                            "type": "user_transcript",
                            "role": "user", 
                            "text": transcript,
                        }).encode("utf-8")
                        await room.local_participant.publish_data(payload, reliable=True)
                except Exception as e:
                    logger.debug(f"Failed to publish STT transcript: {e}")
            else:
                logger.debug(f"Could not extract transcript from STT event args: {args}, kwargs: {kwargs}")
        
        # Create async task as recommended by the error message
        asyncio.create_task(async_handler())
    
    # Try to attach STT event handler if the STT supports it
    try:
        if hasattr(stt, 'on') or hasattr(stt, 'add_event_listener'):
            # Try different event names that might exist
            for event_name in ['transcript', 'final_transcript', 'speech_final', 'result', 'on_final_transcript']:
                try:
                    if hasattr(stt, 'on'):
                        stt.on(event_name, handle_stt_transcript_sync)
                        logger.info(f"Attached STT event handler for '{event_name}' via .on()")
                        break
                    elif hasattr(stt, 'add_event_listener'):
                        stt.add_event_listener(event_name, handle_stt_transcript_sync)
                        logger.info(f"Attached STT event handler for '{event_name}' via .add_event_listener()")
                        break
                except Exception as e:
                    logger.debug(f"Failed to attach '{event_name}' handler: {e}")
                    continue
    except Exception as e:
        logger.debug(f"Could not attach STT event handler: {e}")

    # Start the session with the agent and room
    await session.start(agent=agent, room=room)

    # Publish agent connected event to frontend
    try:
        payload = json.dumps({
            "type": "agent_connected",
            "role": "system",
            "text": f"Voice agent {metadata.get('agent_name', 'AI Assistant')} is ready",
        }).encode("utf-8")
        logger.info(f"Publishing agent connected event to room: {room.name}")
        await room.local_participant.publish_data(payload, reliable=True)
        logger.info("Published agent connected event to frontend successfully")
    except Exception as e:
        logger.error(f"Failed to publish agent connected event: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

    # The session will handle the conversation automatically


async def request_handler(request: agents.JobRequest) -> agents.JobProcess:
    """Handle incoming job requests"""
    # Accept all requests for now
    await request.accept()


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            request_fnc=request_handler,
        )
    )