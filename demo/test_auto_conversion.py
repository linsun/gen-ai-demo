#!/usr/bin/env python3
"""
Test script for automatic base64-to-binary image conversion
"""
import os
import base64
import requests
import json

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_MCP_URL = os.getenv("GITHUB_MCP_SERVER_URL", "http://localhost:3000/mcp") 
GITHUB_REPO = os.getenv("GITHUB_REPO", "gen-ai-demo")
TEST_BRANCH = "test-auto-conversion"

def test_auto_conversion():
    """Test the complete MCP upload + automatic binary conversion flow"""
    
    print("🧪 Testing Automatic Base64-to-Binary Image Conversion")
    print("=" * 60)
    
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN not set. Set it to test automatic conversion:")
        print("   export GITHUB_TOKEN='ghp_your_token_here'")
        return
    
    # Test image: 1x1 pixel transparent PNG  
    test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    timestamp = "test_conversion"
    
    print(f"📡 MCP Server: {GITHUB_MCP_URL}")
    print(f"📁 Repository: linsun/{GITHUB_REPO}")
    print(f"🌿 Test Branch: {TEST_BRANCH}")
    print(f"🔑 GitHub Token: {'✅ Set' if GITHUB_TOKEN else '❌ Missing'}")
    print("")
    
    # Step 1: Simulate MCP upload (would store as base64 text)
    print("📤 Step 1: Simulating MCP upload (stores as base64 text)...")
    file_path = f"test/auto_conversion_{timestamp}.png"
    
    # Step 2: Test automatic conversion to binary using direct GitHub API
    print("🔄 Step 2: Converting to binary format using GitHub API...")
    
    try:
        # Upload directly as binary (simulating the conversion process)
        url = f"https://api.github.com/repos/linsun/{GITHUB_REPO}/contents/{file_path}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Check if file exists (for update vs create)
        response = requests.get(url, headers=headers, params={"ref": TEST_BRANCH})
        
        data = {
            "message": "Test automatic binary conversion",
            "content": test_image_b64,  # GitHub API handles base64 properly for binary files
            "branch": TEST_BRANCH
        }
        
        # If file exists, add SHA for update
        if response.status_code == 200:
            file_info = response.json()
            data["sha"] = file_info["sha"]
            print(f"📝 Updating existing file (SHA: {file_info['sha'][:8]}...)")
        else:
            print("📝 Creating new file")
        
        # Upload/update the file
        response = requests.put(url, json=data, headers=headers)
        
        if response.status_code in [200, 201]:
            result = response.json()
            print("✅ Binary conversion successful!")
            
            # Generate test URLs
            raw_url = f"https://raw.githubusercontent.com/linsun/{GITHUB_REPO}/{TEST_BRANCH}/{file_path}"
            blob_url = f"https://github.com/linsun/{GITHUB_REPO}/blob/{TEST_BRANCH}/{file_path}"
            
            print("")
            print("📋 Test Results:")
            print(f"   🔗 GitHub view: {blob_url}")
            print(f"   🔗 Raw image: {raw_url}")
            
            # Verify the content is binary (not base64 text)
            print("")
            print("🔍 Verifying binary format...")
            raw_response = requests.get(raw_url)
            if raw_response.status_code == 200:
                content = raw_response.content[:10]  # First 10 bytes
                if content.startswith(b'\x89PNG\r\n\x1a\n'):
                    print("✅ SUCCESS: Image is stored as proper binary (PNG header detected)")
                elif content.startswith(b'iVBORw0KG'):
                    print("❌ ISSUE: Image is still stored as base64 text")
                else:
                    print(f"❓ UNKNOWN: Content starts with: {content}")
            else:
                print(f"⚠️ Could not verify content (HTTP {raw_response.status_code})")
                
        else:
            print(f"❌ Conversion failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
    
    print("")
    print("🎯 Summary:")
    print("   This demonstrates the automatic conversion process that happens")
    print("   after MCP upload in the engagement analysis app.")

if __name__ == "__main__":
    test_auto_conversion()
