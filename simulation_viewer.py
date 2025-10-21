#!/usr/bin/env python3
"""
Simple web viewer for simulation JSON files.

Usage:
    # View specific file
    python simulation_viewer.py path/to/simulation.json

    # Browse all simulations in directory
    python simulation_viewer.py Agents/test_simulations/

    # Default: browse batch_simulations directory
    python simulation_viewer.py
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="Simulation Viewer")

# Global state
SIMULATION_DATA: Optional[Dict[str, Any]] = None
SIMULATIONS_DIR: Optional[Path] = None
AVAILABLE_SIMULATIONS: List[Dict[str, str]] = []


def load_simulation(file_path: Path) -> Dict[str, Any]:
    """Load simulation JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def scan_simulations(directory: Path) -> List[Dict[str, str]]:
    """Scan directory for simulation JSON files."""
    simulations = []

    if directory.is_file() and directory.suffix == '.json':
        # Single file mode
        return [{
            'path': str(directory),
            'name': directory.name,
            'relative_path': str(directory)
        }]

    # Directory mode - scan recursively
    for json_file in directory.rglob('*.json'):
        if 'simulation' in json_file.name.lower():
            simulations.append({
                'path': str(json_file),
                'name': json_file.name,
                'relative_path': str(json_file.relative_to(directory))
            })

    return sorted(simulations, key=lambda x: x['relative_path'])


def extract_messages(sim_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract and order messages from simulation data."""
    messages = []
    max_turns = sim_data.get('max_turns', 20)

    # Extract all system/user message pairs
    for i in range(max_turns):
        # System message (workflow/guide)
        system_key = f'system{i}'
        if system_key in sim_data and sim_data[system_key]:
            messages.append({
                'role': 'system',
                'content': sim_data[system_key],
                'index': i
            })

        # User message (persona)
        user_key = f'user{i}'
        if user_key in sim_data and sim_data[user_key]:
            messages.append({
                'role': 'user',
                'content': sim_data[user_key],
                'index': i
            })

    return messages


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the viewer HTML."""
    return HTML_TEMPLATE


@app.get("/api/simulations")
async def list_simulations():
    """List all available simulations."""
    return {
        'simulations': AVAILABLE_SIMULATIONS,
        'count': len(AVAILABLE_SIMULATIONS)
    }


@app.get("/api/simulation")
async def get_simulation(path: Optional[str] = None):
    """Get simulation data."""
    global SIMULATION_DATA

    # If specific path requested, load it
    if path:
        file_path = Path(path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Simulation file not found")
        sim_data = load_simulation(file_path)
    elif SIMULATION_DATA:
        # Use pre-loaded data
        sim_data = SIMULATION_DATA
    elif AVAILABLE_SIMULATIONS:
        # Load first available simulation
        file_path = Path(AVAILABLE_SIMULATIONS[0]['path'])
        sim_data = load_simulation(file_path)
    else:
        raise HTTPException(status_code=404, detail="No simulation data available")

    # Extract messages
    messages = extract_messages(sim_data)

    return {
        'metadata': {
            'session': sim_data.get('session', 'N/A'),
            'datetime': sim_data.get('datetime', 'N/A'),
            'notes': sim_data.get('notes', ''),
            'seed_message': sim_data.get('seed_message', ''),
            'system_agent_id': sim_data.get('system_agent_id', 'Unknown'),
            'user_agent_id': sim_data.get('user_agent_id', 'Unknown'),
            'max_turns': sim_data.get('max_turns', 0),
            'message_count': len(messages)
        },
        'messages': messages
    }


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simulation Viewer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .header h1 {
            font-size: 24px;
            margin-bottom: 10px;
            color: #2c3e50;
        }

        .metadata {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 4px;
        }

        .metadata-item {
            font-size: 14px;
        }

        .metadata-label {
            font-weight: 600;
            color: #555;
            margin-right: 8px;
        }

        .metadata-value {
            color: #333;
        }

        .simulation-selector {
            margin-bottom: 15px;
        }

        .simulation-selector select {
            width: 100%;
            padding: 10px;
            font-size: 14px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: white;
        }

        .chat-container {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            min-height: 500px;
        }

        .message {
            margin-bottom: 24px;
            display: flex;
            flex-direction: column;
        }

        .message.system {
            align-items: flex-start;
        }

        .message.user {
            align-items: flex-end;
        }

        .message-header {
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .message.system .message-header {
            color: #3498db;
        }

        .message.user .message-header {
            color: #27ae60;
        }

        .message-bubble {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 12px;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 15px;
            line-height: 1.5;
            text-align: left;
        }

        .message.system .message-bubble {
            background: #e3f2fd;
            border: 1px solid #90caf9;
        }

        .message.user .message-bubble {
            background: #e8f5e9;
            border: 1px solid #a5d6a7;
        }

        .loading {
            text-align: center;
            padding: 40px;
            font-size: 18px;
            color: #666;
        }

        .error {
            background: #ffebee;
            color: #c62828;
            padding: 16px;
            border-radius: 4px;
            margin: 20px 0;
            border: 1px solid #ef5350;
        }

        .message-index {
            font-size: 11px;
            color: #999;
            margin-left: 8px;
        }

        @media (max-width: 768px) {
            .message-bubble {
                max-width: 90%;
            }

            .metadata {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔬 Simulation Viewer</h1>
            <div id="simulation-selector-container"></div>
            <div id="metadata-container"></div>
        </div>

        <div class="chat-container">
            <div id="messages-container" class="loading">Loading simulation...</div>
        </div>
    </div>

    <script>
        let availableSimulations = [];
        let currentSimulation = null;

        async function loadSimulationsList() {
            try {
                const response = await fetch('/api/simulations');
                const data = await response.json();
                availableSimulations = data.simulations;

                if (availableSimulations.length > 1) {
                    renderSimulationSelector();
                }

                // Load first simulation
                if (availableSimulations.length > 0) {
                    loadSimulation(availableSimulations[0].path);
                } else {
                    loadSimulation();
                }
            } catch (error) {
                console.error('Error loading simulations list:', error);
                loadSimulation(); // Try loading default
            }
        }

        function renderSimulationSelector() {
            const container = document.getElementById('simulation-selector-container');

            const html = `
                <div class="simulation-selector">
                    <select id="simulation-select" onchange="onSimulationChange()">
                        ${availableSimulations.map((sim, idx) => `
                            <option value="${sim.path}">${sim.relative_path}</option>
                        `).join('')}
                    </select>
                </div>
            `;

            container.innerHTML = html;
        }

        function onSimulationChange() {
            const select = document.getElementById('simulation-select');
            const selectedPath = select.value;
            loadSimulation(selectedPath);
        }

        async function loadSimulation(path = null) {
            const messagesContainer = document.getElementById('messages-container');
            const metadataContainer = document.getElementById('metadata-container');

            messagesContainer.innerHTML = '<div class="loading">Loading simulation...</div>';

            try {
                const url = path ? `/api/simulation?path=${encodeURIComponent(path)}` : '/api/simulation';
                const response = await fetch(url);

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                currentSimulation = data;

                renderMetadata(data.metadata);
                renderMessages(data.messages);
            } catch (error) {
                messagesContainer.innerHTML = `
                    <div class="error">
                        <strong>Error loading simulation:</strong><br>
                        ${error.message}
                    </div>
                `;
            }
        }

        function renderMetadata(metadata) {
            const container = document.getElementById('metadata-container');

            const html = `
                <div class="metadata">
                    <div class="metadata-item">
                        <span class="metadata-label">Session:</span>
                        <span class="metadata-value">${metadata.session}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Workflow Agent:</span>
                        <span class="metadata-value">${metadata.system_agent_id}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Persona Agent:</span>
                        <span class="metadata-value">${metadata.user_agent_id}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Messages:</span>
                        <span class="metadata-value">${metadata.message_count} (${metadata.max_turns} rounds)</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Timestamp:</span>
                        <span class="metadata-value">${metadata.datetime}</span>
                    </div>
                    ${metadata.notes ? `
                        <div class="metadata-item" style="grid-column: 1 / -1;">
                            <span class="metadata-label">Notes:</span>
                            <span class="metadata-value">${metadata.notes}</span>
                        </div>
                    ` : ''}
                </div>
            `;

            container.innerHTML = html;
        }

        function renderMessages(messages) {
            const container = document.getElementById('messages-container');

            if (messages.length === 0) {
                container.innerHTML = '<div class="loading">No messages found</div>';
                return;
            }

            const html = messages.map(msg => {
                const roleLabel = msg.role === 'system' ? 'Workflow' : 'Persona';
                return `
                    <div class="message ${msg.role}">
                        <div class="message-header">
                            ${roleLabel}
                            <span class="message-index">#${msg.index}</span>
                        </div>
                        <div class="message-bubble">${escapeHtml(msg.content)}</div>
                    </div>
                `;
            }).join('');

            container.innerHTML = html;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Load on page load
        loadSimulationsList();
    </script>
</body>
</html>
"""


def main():
    global SIMULATION_DATA, SIMULATIONS_DIR, AVAILABLE_SIMULATIONS

    # Parse command line arguments
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])

        if target.is_file():
            # Single file mode
            print(f"Loading simulation: {target}")
            SIMULATION_DATA = load_simulation(target)
            SIMULATIONS_DIR = target.parent
            AVAILABLE_SIMULATIONS = scan_simulations(target)
        elif target.is_dir():
            # Directory mode
            print(f"Scanning directory: {target}")
            SIMULATIONS_DIR = target
            AVAILABLE_SIMULATIONS = scan_simulations(target)
            print(f"Found {len(AVAILABLE_SIMULATIONS)} simulation files")
        else:
            print(f"Error: {target} does not exist")
            sys.exit(1)
    else:
        # Default: scan batch_simulations directory
        default_dir = Path("Agents/batch_simulations")
        if default_dir.exists():
            print(f"Scanning default directory: {default_dir}")
            SIMULATIONS_DIR = default_dir
            AVAILABLE_SIMULATIONS = scan_simulations(default_dir)
            print(f"Found {len(AVAILABLE_SIMULATIONS)} simulation files")
        else:
            print("No simulation path provided and default directory not found")
            print("\nUsage:")
            print("  python simulation_viewer.py path/to/simulation.json")
            print("  python simulation_viewer.py Agents/test_simulations/")
            sys.exit(1)

    # Start server
    port = 8890
    print(f"\n{'='*60}")
    print(f"🚀 Simulation Viewer starting on http://localhost:{port}")
    print(f"{'='*60}\n")

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
