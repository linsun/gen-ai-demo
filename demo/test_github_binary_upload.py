#!/usr/bin/env python3
"""
Test script to debug GitHub MCP server binary file upload issues
"""
import os
import base64
import json
import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
GITHUB_MCP_SERVER_URL = os.getenv("GITHUB_MCP_SERVER_URL", "http://agentgateway.mcp.svc.cluster.local:3000/mcp")
GITHUB_REPO = os.getenv("GITHUB_REPO", "gen-ai-demo")
TEST_BRANCH = "test-binary-upload"

def call_github_mcp_tool(tool_name, arguments):
    """Simplified GitHub MCP tool call for testing"""
    try:
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = requests.post(
            GITHUB_MCP_SERVER_URL,
            json=mcp_request,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            timeout=60
        )
        
        if response.status_code != 200:
            logger.error(f"❌ HTTP Error: {response.status_code} - {response.text}")
            return None
        
        # Parse response (handle SSE format)
        if response.headers.get('content-type', '').startswith('text/event-stream'):
            sse_lines = response.text.strip().split('\n')
            for line in sse_lines:
                if line.startswith('data: '):
                    json_str = line[6:]  # Remove "data: " prefix
                    response_data = json.loads(json_str)
                    break
        else:
            response_data = response.json()
        
        if "error" in response_data:
            logger.error(f"❌ MCP Error: {response_data['error']}")
            return None
        
        return response_data.get("result", {})
        
    except Exception as e:
        logger.error(f"❌ Error calling GitHub MCP tool: {e}")
        return None

def create_test_image():
    """Create a small test image (1x1 pixel PNG)"""
    # 1x1 pixel transparent PNG in base64
    png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    return png_base64

def test_binary_upload_methods():
    """Test different methods for uploading binary content"""
    
    print("🧪 Testing GitHub MCP Binary Upload Methods")
    print("=" * 50)
    
    # Create test image data
    test_image_base64 = create_test_image()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    test_methods = [
        {
            "name": "Method 1: No encoding parameter (GitHub API standard)",
            "tool": "create_or_update_file", 
            "params": {
                "owner": "linsun",
                "repo": GITHUB_REPO,
                "path": f"test/binary_test_{timestamp}_method1.png",
                "content": test_image_base64,
                "message": "Test binary upload - Method 1 (no encoding)",
                "branch": TEST_BRANCH
            }
        },
        {
            "name": "Method 2: encoding=base64 parameter",
            "tool": "create_or_update_file",
            "params": {
                "owner": "linsun", 
                "repo": GITHUB_REPO,
                "path": f"test/binary_test_{timestamp}_method2.png",
                "content": test_image_base64,
                "message": "Test binary upload - Method 2 (encoding=base64)",
                "branch": TEST_BRANCH,
                "encoding": "base64"
            }
        },
        {
            "name": "Method 3: content_encoding parameter",
            "tool": "create_or_update_file",
            "params": {
                "owner": "linsun",
                "repo": GITHUB_REPO, 
                "path": f"test/binary_test_{timestamp}_method3.png",
                "content": test_image_base64,
                "message": "Test binary upload - Method 3 (content_encoding)",
                "branch": TEST_BRANCH,
                "content_encoding": "base64"
            }
        },
        {
            "name": "Method 4: create_file tool",
            "tool": "create_file",
            "params": {
                "owner": "linsun",
                "repo": GITHUB_REPO,
                "path": f"test/binary_test_{timestamp}_method4.png", 
                "content": test_image_base64,
                "message": "Test binary upload - Method 4 (create_file)",
                "branch": TEST_BRANCH
            }
        }
    ]
    
    results = []
    
    for i, method in enumerate(test_methods):
        print(f"\n🧪 Testing {method['name']}")
        print(f"   Tool: {method['tool']}")
        print(f"   Path: {method['params']['path']}")
        
        result = call_github_mcp_tool(method['tool'], method['params'])
        
        if result:
            print(f"   ✅ Upload successful")
            file_path = method['params']['path'] 
            raw_url = f"https://raw.githubusercontent.com/linsun/{GITHUB_REPO}/{TEST_BRANCH}/{file_path}"
            blob_url = f"https://github.com/linsun/{GITHUB_REPO}/blob/{TEST_BRANCH}/{file_path}"
            
            print(f"   🔗 Raw URL: {raw_url}")
            print(f"   🔗 Blob URL: {blob_url}")
            
            results.append({
                "method": method['name'],
                "success": True,
                "raw_url": raw_url,
                "blob_url": blob_url
            })
        else:
            print(f"   ❌ Upload failed")
            results.append({
                "method": method['name'],
                "success": False
            })
    
    print(f"\n📊 Test Results Summary:")
    print("=" * 30)
    
    successful_methods = [r for r in results if r['success']]
    failed_methods = [r for r in results if not r['success']]
    
    if successful_methods:
        print(f"✅ Successful methods ({len(successful_methods)}):")
        for method in successful_methods:
            print(f"   - {method['method']}")
            print(f"     Raw: {method['raw_url']}")
        
        print(f"\n💡 Recommendation: Use the first successful method in your app")
        
        # Test if images display correctly
        print(f"\n🔍 Verifying Image Display:")
        for method in successful_methods[:1]:  # Test first successful method
            try:
                response = requests.get(method['raw_url'], timeout=10)
                if response.status_code == 200:
                    content = response.content[:20]  # First 20 bytes
                    if content.startswith(b'\x89PNG\r\n\x1a\n'):
                        print(f"   ✅ {method['method']}: Image displays correctly as PNG")
                    elif content.startswith(b'/9j/'):
                        print(f"   ❌ {method['method']}: Still showing as base64 text")
                    else:
                        print(f"   ❓ {method['method']}: Unknown format: {content}")
                else:
                    print(f"   ❌ {method['method']}: Cannot access URL ({response.status_code})")
            except Exception as e:
                print(f"   ❌ {method['method']}: Error testing URL: {e}")
    else:
        print("❌ No methods succeeded")
    
    if failed_methods:
        print(f"\n❌ Failed methods ({len(failed_methods)}):")
        for method in failed_methods:
            print(f"   - {method['method']}")
    
    return results

if __name__ == "__main__":
    test_binary_upload_methods()
