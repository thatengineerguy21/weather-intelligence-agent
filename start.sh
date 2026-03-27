#!/bin/bash
# Start MCP Toolbox in background
./toolbox --tools-file tools.yaml &

# Wait for toolbox to be ready
sleep 3

# Start the FastAPI agent server
python main.py