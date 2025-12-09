#!/bin/bash
# Simple test for GitHub MCP binary upload without Python dependencies

echo "🧪 Testing GitHub MCP Binary Upload..."

# Test 1x1 pixel PNG (base64)
TEST_IMAGE="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
GITHUB_MCP_URL="${GITHUB_MCP_SERVER_URL:-http://localhost:3000/mcp}"
REPO="${GITHUB_REPO:-gen-ai-demo}"

echo "📡 MCP Server: $GITHUB_MCP_URL"
echo "📁 Repository: $REPO"
echo "🖼️ Test image size: ${#TEST_IMAGE} chars"

# Step 1: Initialize MCP session
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

# Extract session ID from response headers (case-insensitive)  
SESSION_ID=$(echo "$INIT_RESPONSE" | grep -i "mcp-session-id:" | sed 's/.*mcp-session-id: *\([^ ]*\).*/\1/' | tr -d '\r\n')

# If not in headers, try extracting from body content
if [ -z "$SESSION_ID" ]; then
  SESSION_ID=$(echo "$INIT_RESPONSE" | grep -o '"mcp-session-id":"[^"]*"' | cut -d'"' -f4)
fi

echo "🔑 Session ID: ${SESSION_ID:-NOT_FOUND}"
echo "📄 Init response preview: $(echo "$INIT_RESPONSE" | tail -3 | head -1)"

# Step 2: Send initialized notification
echo "📡 Sending initialized notification..."
curl -s -X POST "$GITHUB_MCP_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "method": "notifications/initialized"
  }' > /dev/null

# Step 3: Test binary upload with session
echo ""
echo "🧪 Method 1: No encoding parameter..."
UPLOAD_RESPONSE=$(curl -s -X POST "$GITHUB_MCP_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0", 
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "create_or_update_file",
      "arguments": {
        "owner": "linsun",
        "repo": "'$REPO'",
        "path": "test/diagnostic_'$TIMESTAMP'_method1.png", 
        "content": "'$TEST_IMAGE'",
        "message": "Test binary upload - Method 1",
        "branch": "test-binary-upload"
      }
    }
  }')

echo "📤 Upload response: $(echo "$UPLOAD_RESPONSE" | head -c 200)..."

echo ""
echo "✅ Test completed!"
echo ""
echo "📋 Check results at:"
echo "   https://github.com/linsun/$REPO/blob/test-binary-upload/test/"
echo "   https://raw.githubusercontent.com/linsun/$REPO/test-binary-upload/test/diagnostic_${TIMESTAMP}_method1.png"
echo ""
echo "🔍 If the raw URL shows base64 text (starts with 'iVBORw0KG'), the issue persists."
echo "🔍 If the raw URL shows a 1x1 pixel image, the upload worked correctly."
