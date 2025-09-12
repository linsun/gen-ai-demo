#!/usr/bin/env python3
"""
Simple test script to verify MCP server HTTP connection
"""
import os
import json
import requests

# Configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://agentgw.mcp.svc.cluster.local:3000/mcp")

def test_mcp_connection():
    """Test basic connection to MCP server"""
    try:
        # Test 1: List available tools
        print("🔍 Testing MCP server connection...")
        print(f"🌐 Server URL: {MCP_SERVER_URL}")
        
        list_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }
        
        response = requests.post(
            MCP_SERVER_URL,
            json=list_request,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            timeout=10
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            # Handle both SSE and regular JSON format
            try:
                if response.headers.get('content-type', '').startswith('text/event-stream'):
                    print("📡 Response is Server-Sent Events format")
                    sse_lines = response.text.strip().split('\n')
                    json_str = None
                    for line in sse_lines:
                        if line.startswith('data: '):
                            json_str = line[6:]  # Remove "data: " prefix
                            break
                    if json_str:
                        data = json.loads(json_str)
                    else:
                        print(f"❌ No data line found in SSE response: {response.text}")
                        return False
                else:
                    data = response.json()
                    
                print("✅ Connection successful!")
                print("🛠️  Available tools:")
                
                if "result" in data and "tools" in data["result"]:
                    for tool in data["result"]["tools"]:
                        print(f"   - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
                else:
                    print("   No tools found in response")
                    
                return True
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"📄 Raw response: {response.text}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectException as e:
        print(f"❌ Connection Error: Cannot connect to {MCP_SERVER_URL}")
        print(f"   Error: {e}")
        print("💡 Make sure the MCP server container is running")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout Error: Request timed out")
        print(f"   Error: {e}")
        print("💡 The MCP server might be starting up or overloaded")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def test_create_presentation():
    """Test creating a simple presentation"""
    try:
        print("\n📝 Testing presentation creation...")
        
        create_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "create_presentation",
                "arguments": {
                    "title": "MCP Test Presentation"
                }
            }
        }
        
        response = requests.post(
            MCP_SERVER_URL,
            json=create_request,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Presentation creation test successful!")
            print(f"📄 Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing presentation creation: {e}")
        return False

if __name__ == "__main__":
    print("🧪 MCP Server Connection Test")
    print("=" * 40)
    
    # Test basic connection
    connection_ok = test_mcp_connection()
    
    if connection_ok:
        # Test presentation creation
        test_create_presentation()
        print("\n🎉 All tests completed!")
    else:
        print("\n⚠️  Connection failed - check MCP server status")
        print("💡 Verify MCP_SERVER_URL is correct and server is running")
