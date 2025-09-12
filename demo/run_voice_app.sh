#!/bin/bash

# Voice with Llama + Google Slides Integration Runner
# This script sets up the environment and runs the Streamlit app

# Set default values
export MCP_SERVER_URL="${MCP_SERVER_URL:-http://agentgw.mcp.svc.cluster.local:3000/mcp}"
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"

echo "🚀 Starting Voice with Llama + Google Slides Integration"
echo "================================="
echo "🌐 MCP Server URL: $MCP_SERVER_URL"
echo "🦙 Ollama URL: $OLLAMA_BASE_URL"
echo "================================="

# Test MCP connection first
echo "🧪 Testing MCP connection..."
python test_mcp_connection.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ MCP connection test successful!"
    echo "🎯 Starting Streamlit app..."
    echo ""
    streamlit run pages/2_Voice_With_Llama.py --server.port 8501
else
    echo "❌ MCP connection test failed!"
    echo "Please check your MCP server configuration before running the app."
    echo ""
    echo "You can still run the app manually with:"
    echo "streamlit run pages/2_Voice_With_Llama.py"
fi
