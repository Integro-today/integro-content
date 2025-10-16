#!/usr/bin/env python
"""Run the voice agent server for LiveKit integration."""

import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from integro.voice_agent import cli, WorkerOptions, entrypoint, request_handler

if __name__ == "__main__":
    import os
    livekit_url = os.getenv("LIVEKIT_URL", "wss://your-project.livekit.cloud")

    print("Starting Integro Voice Agent Server...")
    print(f"Connecting to LiveKit at {livekit_url}")
    print("Press Ctrl+C to stop\n")

    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            request_fnc=request_handler,
        )
    )