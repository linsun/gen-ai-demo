#!/bin/bash
# Debug MCP server responses

echo "🔍 Debugging MCP Server Responses"
echo "=================================="

GITHUB_MCP_URL="${GITHUB_MCP_SERVER_URL:-http://localhost:3000/mcp}"
REPO="${GITHUB_REPO:-gen-ai-demo}"

echo "📡 MCP Server: $GITHUB_MCP_URL"

# Initialize session
echo ""
echo "🔧 Step 1: Initialize Session"
INIT_RESPONSE=$(curl -s -i -X POST "$GITHUB_MCP_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 0, 
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {"tools": {}},
      "clientInfo": {"name": "debug-test", "version": "1.0.0"}
    }
  }')

echo "📄 Full init response:"
echo "$INIT_RESPONSE"
echo ""

# Extract session ID
SESSION_ID=$(echo "$INIT_RESPONSE" | grep -i "mcp-session-id:" | sed 's/.*mcp-session-id: *\([^ ]*\).*/\1/' | tr -d '\r\n')
echo "🔑 Extracted Session ID: '$SESSION_ID'"

# Send initialized notification  
curl -s -X POST "$GITHUB_MCP_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc": "2.0", "method": "notifications/initialized"}' > /dev/null

echo ""
echo "🔧 Step 2: List Tools"
TOOLS_RESPONSE=$(curl -s -X POST "$GITHUB_MCP_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0", 
    "id": 1,
    "method": "tools/list"
  }')

echo "📄 Full tools response:"
echo "$TOOLS_RESPONSE"
echo ""

# Extract and parse tools
TOOLS_JSON=$(echo "$TOOLS_RESPONSE" | grep "^data: " | sed 's/^data: //')
echo "📄 Extracted JSON:"
echo "$TOOLS_JSON"
echo ""

echo "🔧 Step 3: Test List Branches"
BRANCHES_RESPONSE=$(curl -s -X POST "$GITHUB_MCP_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0", 
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "list_branches",
      "arguments": {
        "owner": "linsun",
        "repo": "'$REPO'"
      }
    }
  }')

echo "📄 Full branches response:"  
echo "$BRANCHES_RESPONSE"
echo ""

BRANCHES_JSON=$(echo "$BRANCHES_RESPONSE" | grep "^data: " | sed 's/^data: //')
echo "📄 Extracted branches JSON:"
echo "$BRANCHES_JSON"

echo ""
echo "🎯 Key Findings:"
if [ -n "$SESSION_ID" ]; then
    echo "✅ Session initialization: SUCCESS" 
else
    echo "❌ Session initialization: FAILED"
fi

if [ -n "$TOOLS_JSON" ] && echo "$TOOLS_JSON" | grep -q '"tools"'; then
    echo "✅ Tools list: SUCCESS"
else
    echo "❌ Tools list: FAILED or empty"
fi

if [ -n "$BRANCHES_JSON" ] && echo "$BRANCHES_JSON" | grep -q '"result"'; then
    echo "✅ GitHub API access: SUCCESS"
elif echo "$BRANCHES_JSON" | grep -q '"error"'; then
    echo "❌ GitHub API access: ERROR"
    echo "    $(echo "$BRANCHES_JSON" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)"
else
    echo "❌ GitHub API access: NO RESPONSE"
fi
