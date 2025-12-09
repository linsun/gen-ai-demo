#!/bin/bash
# Comprehensive GitHub MCP diagnostic test

echo "🧪 Comprehensive GitHub MCP Binary Upload Diagnostic"
echo "============================================================"

# Configuration
TEST_IMAGE="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
GITHUB_MCP_URL="${GITHUB_MCP_SERVER_URL:-http://localhost:3000/mcp}"
REPO="${GITHUB_REPO:-gen-ai-demo}"
BRANCH="test-binary-upload"

echo "📡 MCP Server: $GITHUB_MCP_URL"
echo "📁 Repository: linsun/$REPO"
echo "🌿 Test Branch: $BRANCH"
echo ""

# Function to initialize MCP session
init_mcp_session() {
    echo "🔧 Initializing MCP session..."
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
          "clientInfo": {"name": "diagnostic-test", "version": "1.0.0"}
        }
      }')

    # Extract session ID from response headers
    SESSION_ID=$(echo "$INIT_RESPONSE" | grep -i "mcp-session-id:" | sed 's/.*mcp-session-id: *\([^ ]*\).*/\1/' | tr -d '\r\n')
    
    if [ -z "$SESSION_ID" ]; then
        echo "❌ Failed to get session ID"
        exit 1
    fi
    
    echo "✅ Session ID: $SESSION_ID"
    
    # Send initialized notification
    curl -s -X POST "$GITHUB_MCP_URL" \
      -H "Content-Type: application/json" \
      -H "Accept: application/json, text/event-stream" \
      -H "mcp-session-id: $SESSION_ID" \
      -d '{"jsonrpc": "2.0", "method": "notifications/initialized"}' > /dev/null
}

# Function to call MCP tool with better error handling
call_mcp_tool() {
    local tool_name="$1"
    local arguments="$2"
    local description="$3"
    
    echo "🔧 Calling: $tool_name ($description)"
    
    RESPONSE=$(curl -s -X POST "$GITHUB_MCP_URL" \
      -H "Content-Type: application/json" \
      -H "Accept: application/json, text/event-stream" \
      -H "mcp-session-id: $SESSION_ID" \
      -d '{
        "jsonrpc": "2.0", 
        "id": 1,
        "method": "tools/call",
        "params": {
          "name": "'$tool_name'",
          "arguments": '$arguments'
        }
      }')
    
    # Extract JSON from SSE response
    JSON_RESPONSE=$(echo "$RESPONSE" | grep "^data: " | sed 's/^data: //')
    
    # Check for errors
    if echo "$JSON_RESPONSE" | grep -q '"error"'; then
        ERROR_MSG=$(echo "$JSON_RESPONSE" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)
        echo "❌ Error: $ERROR_MSG"
        echo "📄 Full response: $JSON_RESPONSE"
        return 1
    elif echo "$JSON_RESPONSE" | grep -q '"result"'; then
        echo "✅ Success: $tool_name"
        return 0
    else
        echo "❓ Unexpected response: $JSON_RESPONSE"
        return 1
    fi
}

# Initialize session
init_mcp_session

echo ""
echo "🧪 Step 1: List available tools"
echo "🔧 Calling: tools/list (Check what tools are available)"

TOOLS_RESPONSE=$(curl -s -X POST "$GITHUB_MCP_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0", 
    "id": 1,
    "method": "tools/list"
  }')

TOOLS_JSON=$(echo "$TOOLS_RESPONSE" | grep "^data: " | sed 's/^data: //')
if echo "$TOOLS_JSON" | grep -q '"error"'; then
    echo "❌ Error listing tools: $(echo "$TOOLS_JSON" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)"
else
    TOOL_COUNT=$(echo "$TOOLS_JSON" | grep -o '"name":"[^"]*"' | wc -l)
    echo "✅ Found $TOOL_COUNT available tools"
fi

echo ""
echo "🧪 Step 2: List branches" 
call_mcp_tool "list_branches" '{
  "owner": "linsun",
  "repo": "'$REPO'"
}' "Check repository access and existing branches"

echo ""
echo "🧪 Step 3: Create test branch (if needed)"
call_mcp_tool "create_branch" '{
  "owner": "linsun", 
  "repo": "'$REPO'",
  "branch": "'$BRANCH'",
  "from_branch": "main"  
}' "Create test branch for uploads"

echo ""
echo "🧪 Step 4: Test binary upload (no encoding parameter)"
call_mcp_tool "create_or_update_file" '{
  "owner": "linsun",
  "repo": "'$REPO'",
  "path": "test/diagnostic_'$TIMESTAMP'_no_encoding.png",
  "content": "'$TEST_IMAGE'",
  "message": "Test binary upload - no encoding parameter",
  "branch": "'$BRANCH'"
}' "Upload test image without encoding parameter"

echo ""
echo "🧪 Step 5: Test binary upload (with encoding=base64)"
call_mcp_tool "create_or_update_file" '{
  "owner": "linsun",
  "repo": "'$REPO'", 
  "path": "test/diagnostic_'$TIMESTAMP'_with_encoding.png",
  "content": "'$TEST_IMAGE'",
  "message": "Test binary upload - with encoding parameter",
  "branch": "'$BRANCH'",
  "encoding": "base64"
}' "Upload test image with encoding parameter"

echo ""
echo "📊 Test Results:"
echo "=================="
echo "🔗 Branch: https://github.com/linsun/$REPO/tree/$BRANCH/test/"
echo "🔗 No encoding: https://raw.githubusercontent.com/linsun/$REPO/$BRANCH/test/diagnostic_${TIMESTAMP}_no_encoding.png"  
echo "🔗 With encoding: https://raw.githubusercontent.com/linsun/$REPO/$BRANCH/test/diagnostic_${TIMESTAMP}_with_encoding.png"
echo ""
echo "🔍 Check if the raw URLs show:"
echo "   ✅ A 1x1 transparent image (SUCCESS - proper binary)"
echo "   ❌ Base64 text starting with 'iVBORw0KG' (ISSUE - still text)"
