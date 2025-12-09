import os
import io
import base64
import glob
import json
import requests
import logging
from datetime import datetime
import streamlit as st
from ollama import Client
from gtts import gTTS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_BASE_URL = os.getenv("LLAVA_BASE_URL", "http://localhost:11434")
GITHUB_MCP_SERVER_URL = os.getenv("GITHUB_MCP_SERVER_URL", "http://agentgateway.mcp.svc.cluster.local:3000/mcp")
EVENT_NAME = os.getenv("EVENT_NAME", "apidays-paris-2025")
GITHUB_REPO = os.getenv("GITHUB_REPO", "gen-ai-demo")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

def process_stream(stream):
  for chunk in stream:
   yield chunk['message']['content']

def collect_stream_text(stream):
  """Collect all text from the stream for TTS conversion"""
  full_text = ""
  for chunk in stream:
    full_text += chunk['message']['content']
  return full_text

def text_to_speech(text, lang='en'):
  """Convert text to speech using gTTS and return audio bytes"""
  if not text.strip():
    return None
  
  tts = gTTS(text=text, lang=lang, slow=False)
  audio_buffer = io.BytesIO()
  tts.write_to_fp(audio_buffer)
  audio_buffer.seek(0)
  return audio_buffer.getvalue()

def create_autoplay_audio(audio_bytes, hidden=True):
  """Create HTML audio element with autoplay"""
  b64_audio = base64.b64encode(audio_bytes).decode()
  
  # Determine styling - hidden or visible controls
  if hidden:
    style_attr = 'style="display: none;"'
    controls_attr = ''  # No controls for hidden audio
  else:
    style_attr = 'style="width: 100%;"'
    controls_attr = 'controls'
  
  audio_html = f"""
  <audio {controls_attr} autoplay {style_attr}>
    <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
    Your browser does not support the audio element.
  </audio>
  """
  return audio_html

def play_anticipation_sound(audio_file_path):
  """Play anticipation sound - uses custom audio file"""
  with open(audio_file_path, 'rb') as audio_file:
    return audio_file.read()

def create_audio_element(audio_bytes, autoplay=True, loop=False, audio_id=None, volume=0.3, hidden=False):
  """Create an audio element that can autoplay"""
  b64_audio = base64.b64encode(audio_bytes).decode()
  id_attr = f'id="{audio_id}"' if audio_id else ''
  
  # Determine styling - hidden or visible controls
  if hidden:
    style_attr = 'style="display: none;"'
    controls_attr = ''  # No controls for hidden audio
  else:
    style_attr = 'style="width: 100%;"'
    controls_attr = 'controls'
  
  audio_html = f"""
  <audio {id_attr} {'autoplay' if autoplay else ''} {'loop' if loop else ''} {controls_attr} {style_attr} volume="{volume}">
    <source src="data:audio/wav;base64,{b64_audio}" type="audio/wav">
    <source src="data:audio/mpeg;base64,{b64_audio}" type="audio/mpeg">
  </audio>
  <script>
    // Set volume programmatically since HTML volume attribute isn't always reliable
    const audio = document.getElementById('{audio_id}');
    if (audio) {{
      audio.volume = {volume};
    }}
  </script>
  """
  return audio_html

def stop_background_music():
  """Completely stop background music before text-to-speech"""
  stop_html = """
  <script>
    function stopMusic() {
      console.log('Stopping background music for text-to-speech...');
      
      // Wait a bit to ensure audio elements are loaded
      setTimeout(() => {
        // Get all audio elements
        const audioElements = document.querySelectorAll('audio');
        console.log('Found', audioElements.length, 'audio elements');
        
        audioElements.forEach((audio, index) => {
          console.log('Stopping audio element', index);
          
          try {
            // Stop the audio completely
            if (!audio.paused) {
              console.log('Pausing audio element', index);
              audio.pause();
            }
            
            // Reset to beginning and mute
            audio.currentTime = 0;
            audio.volume = 0;
            
            // Store original volume for later restoration
            audio.dataset.originalVolume = audio.dataset.originalVolume || '0.2';
            
          } catch (e) {
            console.log('Error stopping audio element', index, ':', e);
          }
        });
        
        // Specifically target background music by ID
        const bgMusic = document.getElementById('background-music');
        if (bgMusic) {
          console.log('Stopping background-music element specifically');
          if (!bgMusic.paused) {
            bgMusic.pause();
          }
          bgMusic.currentTime = 0;
          bgMusic.volume = 0;
          bgMusic.dataset.originalVolume = bgMusic.dataset.originalVolume || '0.2';
        }
        
      }, 100);  // 100ms delay
    }
    
    // Execute multiple times to ensure it works
    stopMusic();
    setTimeout(stopMusic, 300);
    setTimeout(stopMusic, 800);
  </script>
  """
  return stop_html

def play_streamlit_audio(audio_bytes):
  """Alternative method using Streamlit's audio component"""
  st.audio(audio_bytes, format="audio/wav", start_time=0)

# GitHub MCP integration functions
_github_mcp_initialized = False
_github_mcp_session_id = None

def initialize_github_mcp_session():
    """Initialize GitHub MCP session before making tool calls"""
    logger.info("🔧 Initializing GitHub MCP session...")
    global _github_mcp_session_id
    
    try:
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "engagement-analyzer-client",
                    "version": "1.0.0"
                }
            }
        }
        
        logger.info(f"🔧 Sending GitHub MCP initialize request")
        
        response = requests.post(
            GITHUB_MCP_SERVER_URL,
            json=init_request,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            timeout=30
        )
        
        logger.info(f"🔧 GitHub MCP Initialize response status: {response.status_code}")
        
        # Extract session ID from headers
        _github_mcp_session_id = response.headers.get('mcp-session-id')
        if _github_mcp_session_id:
            logger.info(f"🔧 Extracted GitHub MCP session ID: {_github_mcp_session_id}")
        
        if response.status_code == 200:
            # Parse response (handle both SSE and regular JSON)
            if response.headers.get('content-type', '').startswith('text/event-stream'):
                # Parse SSE format
                sse_lines = response.text.strip().split('\n')
                for line in sse_lines:
                    if line.startswith('data: '):
                        json_str = line[6:]  # Remove "data: " prefix
                        response_data = json.loads(json_str)
                        break
            else:
                response_data = response.json()
            
            logger.info("✅ GitHub MCP session initialized successfully")
            return True
        else:
            logger.error(f"❌ GitHub MCP Initialize failed: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error initializing GitHub MCP session: {e}")
        return False

def call_github_mcp_tool(tool_name, arguments):
    """Call a tool in the GitHub MCP server via HTTP"""
    global _github_mcp_initialized, _github_mcp_session_id
    
    logger.info(f"🌐 Calling GitHub MCP tool: {tool_name}")
    
    # Initialize GitHub MCP session if not already done
    if not _github_mcp_initialized:
        logger.info("🔧 GitHub MCP not initialized, initializing now...")
        if initialize_github_mcp_session():
            _github_mcp_initialized = True
        else:
            logger.error("❌ Failed to initialize GitHub MCP session")
            return None
    
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
        
        # Prepare headers with session ID if available
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
        if _github_mcp_session_id:
            headers["mcp-session-id"] = _github_mcp_session_id
        
        # Make HTTP POST request to the GitHub MCP server with extended timeout for GitHub operations  
        timeout_duration = 120 if tool_name in ['create_branch', 'create_or_update_file', 'list_branches'] else 60
        logger.info(f"🕐 Using {timeout_duration}s timeout for {tool_name}")
        
        response = requests.post(
            GITHUB_MCP_SERVER_URL,
            json=mcp_request,
            headers=headers,
            timeout=timeout_duration
        )
        
        logger.info(f"🌐 GitHub MCP Response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"❌ GitHub MCP HTTP Error: {response.status_code} - {response.text}")
            return None
        
        # Parse response (handle both SSE and regular JSON)
        try:
            if response.headers.get('content-type', '').startswith('text/event-stream'):
                # Parse SSE format
                sse_lines = response.text.strip().split('\n')
                json_str = None
                for line in sse_lines:
                    if line.startswith('data: '):
                        json_str = line[6:]  # Remove "data: " prefix
                        break
                if json_str:
                    response_data = json.loads(json_str)
                else:
                    logger.error(f"❌ No data line found in GitHub MCP SSE response")
                    return None
            else:
                response_data = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse GitHub MCP response: {e}")
            return None
        
        if "error" in response_data:
            logger.error(f"❌ GitHub MCP Error: {response_data['error']}")
            return None
        
        result = response_data.get("result", {})
        logger.info(f"✅ GitHub MCP tool success: {tool_name}")
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ GitHub MCP HTTP request error: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error calling GitHub MCP tool: {e}")
        return None

def convert_base64_to_binary_image(file_path, base64_content, branch_name, commit_message):
    """
    Convert uploaded base64 text file to proper binary image using direct GitHub API
    """
    if not GITHUB_TOKEN:
        logger.warning("⚠️ GITHUB_TOKEN not set, skipping binary conversion")
        return False
    
    try:
        logger.info(f"🔄 Converting {file_path} from base64 text to binary image...")
        
        # Get the current file SHA (needed for updates)
        get_url = f"https://api.github.com/repos/linsun/{GITHUB_REPO}/contents/{file_path}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get(get_url, headers=headers, params={"ref": branch_name})
        if response.status_code != 200:
            logger.error(f"❌ Failed to get current file info: {response.status_code}")
            return False
        
        file_info = response.json()
        file_sha = file_info["sha"]
        
        logger.info(f"📄 Current file SHA: {file_sha}")
        
        # Upload the binary content (GitHub API will handle base64 properly)
        update_data = {
            "message": f"{commit_message} (converted to binary)",
            "content": base64_content,  # GitHub API expects base64 for binary files
            "branch": branch_name,
            "sha": file_sha
        }
        
        response = requests.put(get_url, json=update_data, headers=headers)
        
        if response.status_code in [200, 201]:
            logger.info(f"✅ Successfully converted {file_path} to binary image")
            return True
        else:
            logger.error(f"❌ Failed to convert to binary: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error converting to binary: {e}")
        return False

def test_github_mcp_connection():
    """Test if GitHub MCP server is accessible"""
    try:
        logger.info("🔍 Testing GitHub MCP server connection...")
        
        # Try a simple request with short timeout
        response = requests.get(
            GITHUB_MCP_SERVER_URL.replace('/mcp', '/health'),  # Try health endpoint first
            timeout=10
        )
        return True
        
    except:
        try:
            # Fallback: try to initialize session
            response = requests.post(
                GITHUB_MCP_SERVER_URL,
                json={"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}},
                headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ GitHub MCP server connection test failed: {e}")
            return False

def check_branch_exists(branch_name):
    """Check if a branch exists in the repository using list_branches"""
    logger.info(f"🔍 Checking if branch exists: {branch_name}")
    
    try:
        result = call_github_mcp_tool("list_branches", {
            "owner": "linsun",
            "repo": GITHUB_REPO
        })
        
        logger.info(f"🔍 List branches result: {result}")
        
        if result and "content" in result:
            # Parse the response to get branch list
            branches_data = result["content"]
            logger.info(f"🔍 Branches data type: {type(branches_data)}")
            logger.info(f"🔍 Branches data: {branches_data}")
            
            if isinstance(branches_data, list):
                branch_names = []
                for branch_info in branches_data:
                    logger.info(f"🔍 Processing branch info: {branch_info}")
                    if isinstance(branch_info, dict) and "text" in branch_info:
                        # Extract branch names from the text content
                        text = branch_info["text"]
                        logger.info(f"🔍 Branch text content: {text}")
                        
                        # Try different parsing approaches
                        if "name:" in text.lower():
                            # Parse branch name from format like "name: branch-name"
                            lines = text.split('\n')
                            for line in lines:
                                if line.strip().lower().startswith('name:'):
                                    name = line.split(':', 1)[1].strip()
                                    branch_names.append(name)
                        elif branch_name in text:
                            # Simple substring match as fallback
                            branch_names.append(branch_name)
                        else:
                            # Try to extract any potential branch name from text
                            words = text.strip().split()
                            if words:
                                # Assume first word might be branch name
                                potential_name = words[0].strip()
                                branch_names.append(potential_name)
                
                branch_exists = branch_name in branch_names
                logger.info(f"📝 Extracted branch names: {branch_names}")
                
                if branch_exists:
                    logger.info(f"✅ Branch {branch_name} found in list")
                    return True
                else:
                    logger.info(f"❌ Branch {branch_name} not found in list")
                    return False
            else:
                logger.warning(f"⚠️ Unexpected branches data format: {type(branches_data)}")
                return False
        else:
            logger.warning("⚠️ No branches data returned or missing 'content' key")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error checking branch existence: {e}")
        # Assume branch doesn't exist if we can't check
        return False

def create_branch_with_retry(branch_name, max_retries=2):
    """Create branch with retry logic"""
    for attempt in range(max_retries):
        try:
            logger.info(f"🌿 Creating branch: {branch_name} (attempt {attempt + 1}/{max_retries})")
            
            create_branch_result = call_github_mcp_tool("create_branch", {
                "repo": GITHUB_REPO,
                "owner": "linsun",
                "branch": branch_name,
                "from_branch": "main"
            })
            
            if create_branch_result:
                logger.info(f"✅ Successfully created branch: {branch_name}")
                return True
            else:
                logger.warning(f"⚠️ Branch creation attempt {attempt + 1} failed")
                if attempt < max_retries - 1:
                    logger.info("🔄 Retrying branch creation...")
                
        except Exception as e:
            logger.error(f"❌ Branch creation attempt {attempt + 1} error: {e}")
            if attempt < max_retries - 1:
                logger.info("🔄 Retrying branch creation...")
    
    logger.error(f"❌ Failed to create branch after {max_retries} attempts")
    return False

def store_engagement_analysis_to_github(image1_path, image2_path, analysis_data):
    """Store engagement analysis results and images to GitHub"""
    logger.info(f"📁 Storing engagement analysis to GitHub for event: {EVENT_NAME}")
    
    # First test connection to GitHub MCP server
    if not test_github_mcp_connection():
        logger.error("❌ Cannot connect to GitHub MCP server")
        return {
            "success": False, 
            "error": "Cannot connect to GitHub MCP server. Please check server status and network connectivity."
        }
    
    try:
        # Create branch name from event name
        branch_name = EVENT_NAME.lower().replace(' ', '-')
        folder_path = f"events/{EVENT_NAME}"
        
        # Generate timestamp for unique filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Check if branch exists first
        branch_exists = check_branch_exists(branch_name)
        
        if not branch_exists:
            # Try to create branch with retry logic
            branch_created = create_branch_with_retry(branch_name)
            if not branch_created:
                logger.warning("⚠️ Branch creation failed, will try to use main branch")
                branch_name = "main"  # Fallback to main branch
                folder_path = f"events/{EVENT_NAME}"
        else:
            logger.info(f"📝 Using existing branch: {branch_name}")
        
        # 2. Create analysis report
        analysis_report = f"""# Engagement Analysis Report - {EVENT_NAME}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Analysis Results

### First Image Analysis
{analysis_data['response1']}

### Second Image Analysis  
{analysis_data['response2']}

### Comparison Analysis
{analysis_data['comparison']}

### Summary
{analysis_data['summary']}

## Files
- Image 1: ![Image 1](image1_{timestamp}.jpg)
- Image 2: ![Image 2](image2_{timestamp}.jpg)
"""
        
        # 3. Upload files with better error handling
        uploaded_files = []
        upload_errors = []
        
        # Upload analysis report
        logger.info(f"📄 Uploading analysis report to {folder_path}")
        try:
            report_result = call_github_mcp_tool("create_or_update_file", {
                "owner": "linsun",
                "repo": GITHUB_REPO,
                "path": f"{folder_path}/analysis_report_{timestamp}.md",
                "content": analysis_report,
                "message": f"Add engagement analysis report for {EVENT_NAME}",
                "branch": branch_name
            })
            
            if report_result:
                uploaded_files.append(f"analysis_report_{timestamp}.md")
                logger.info("✅ Analysis report uploaded successfully")
            else:
                upload_errors.append("Analysis report upload failed")
                logger.error("❌ Analysis report upload failed")
                
        except Exception as e:
            upload_errors.append(f"Analysis report error: {str(e)}")
            logger.error(f"❌ Analysis report upload error: {e}")
        
        # Upload first image
        logger.info(f"📸 Uploading first image")
        try:
            with open(image1_path, 'rb') as f:
                image1_bytes = f.read()
                image1_content = base64.b64encode(image1_bytes).decode('utf-8')
                
            logger.info(f"📸 Image1 size: {len(image1_bytes)} bytes, base64 length: {len(image1_content)}")
            logger.info(f"📸 Image1 base64 preview: {image1_content[:50]}...")
            
            # Verify it's a valid JPEG by checking header
            if image1_bytes.startswith(b'\xff\xd8\xff'):
                logger.info("✅ Image1 is a valid JPEG file")
            else:
                logger.warning("⚠️ Image1 doesn't appear to be a valid JPEG")
            
            # Try GitHub API standard format (no encoding parameter - auto-detection)
            logger.info("📸 Trying GitHub API standard format (no encoding parameter)")
            image1_result = call_github_mcp_tool("create_or_update_file", {
                "owner": "linsun",
                "repo": GITHUB_REPO,
                "path": f"{folder_path}/image1_{timestamp}.jpg",
                "content": image1_content,
                "message": f"Add first engagement image for {EVENT_NAME}",
                "branch": branch_name
            })
            
            # If that fails, try with explicit encoding
            if not image1_result:
                logger.info("📸 Retrying image1 with explicit encoding...")
                image1_result = call_github_mcp_tool("create_or_update_file", {
                    "owner": "linsun",
                    "repo": GITHUB_REPO,
                    "path": f"{folder_path}/image1_{timestamp}.jpg",
                    "content": image1_content,
                    "message": f"Add first engagement image for {EVENT_NAME}",
                    "branch": branch_name,
                    "encoding": "base64"
                })
            
            # If still failing, try alternative tool name
            if not image1_result:
                logger.info("📸 Retrying image1 with create_file tool...")
                image1_result = call_github_mcp_tool("create_file", {
                    "owner": "linsun",
                    "repo": GITHUB_REPO,
                    "path": f"{folder_path}/image1_{timestamp}.jpg",
                    "content": image1_content,
                    "message": f"Add first engagement image for {EVENT_NAME}",
                    "branch": branch_name
                })
                
            # If still failing, try storing as .b64 file (experimental)
            if not image1_result:
                logger.info("📸 EXPERIMENTAL: Storing image1 as .b64 file...")
                image1_result = call_github_mcp_tool("create_or_update_file", {
                    "owner": "linsun",
                    "repo": GITHUB_REPO,
                    "path": f"{folder_path}/image1_{timestamp}.jpg.b64",
                    "content": image1_content,
                    "message": f"Add first engagement image (base64) for {EVENT_NAME}",
                    "branch": branch_name
                })
                if image1_result:
                    logger.warning("⚠️ Image1 stored as .b64 file - manual conversion needed")
            
            if image1_result:
                uploaded_files.append(f"image1_{timestamp}.jpg")
                logger.info("✅ First image uploaded successfully")
                
                # Automatically convert base64 text to binary image
                image1_path_github = f"{folder_path}/image1_{timestamp}.jpg"
                conversion_success = convert_base64_to_binary_image(
                    image1_path_github, 
                    image1_content, 
                    branch_name, 
                    f"Add first engagement image for {EVENT_NAME}"
                )
                if conversion_success:
                    logger.info("🔄 Image1 converted to binary format")
                else:
                    logger.warning("⚠️ Image1 remains as base64 text (check GITHUB_TOKEN)")
            else:
                upload_errors.append("First image upload failed")
                logger.error("❌ First image upload failed")
                
        except Exception as e:
            upload_errors.append(f"First image error: {str(e)}")
            logger.error(f"❌ First image upload error: {e}")
        
        # Upload second image
        logger.info(f"📸 Uploading second image")
        try:
            with open(image2_path, 'rb') as f:
                image2_bytes = f.read()
                image2_content = base64.b64encode(image2_bytes).decode('utf-8')
                
            logger.info(f"📸 Image2 size: {len(image2_bytes)} bytes, base64 length: {len(image2_content)}")
            logger.info(f"📸 Image2 base64 preview: {image2_content[:50]}...")
            
            # Verify it's a valid JPEG by checking header  
            if image2_bytes.startswith(b'\xff\xd8\xff'):
                logger.info("✅ Image2 is a valid JPEG file")
            else:
                logger.warning("⚠️ Image2 doesn't appear to be a valid JPEG")
            
            # Try GitHub API standard format (no encoding parameter - auto-detection)
            logger.info("📸 Trying GitHub API standard format (no encoding parameter)")
            image2_result = call_github_mcp_tool("create_or_update_file", {
                "owner": "linsun",
                "repo": GITHUB_REPO,
                "path": f"{folder_path}/image2_{timestamp}.jpg",
                "content": image2_content,
                "message": f"Add second engagement image for {EVENT_NAME}",
                "branch": branch_name
            })
            
            # If that fails, try with explicit encoding
            if not image2_result:
                logger.info("📸 Retrying image2 with explicit encoding...")
                image2_result = call_github_mcp_tool("create_or_update_file", {
                    "owner": "linsun",
                    "repo": GITHUB_REPO,
                    "path": f"{folder_path}/image2_{timestamp}.jpg",
                    "content": image2_content,
                    "message": f"Add second engagement image for {EVENT_NAME}",
                    "branch": branch_name,
                    "encoding": "base64"
                })
            
            # If still failing, try alternative tool name  
            if not image2_result:
                logger.info("📸 Retrying image2 with create_file tool...")
                image2_result = call_github_mcp_tool("create_file", {
                    "owner": "linsun",
                    "repo": GITHUB_REPO,
                    "path": f"{folder_path}/image2_{timestamp}.jpg",
                    "content": image2_content,
                    "message": f"Add second engagement image for {EVENT_NAME}",
                    "branch": branch_name
                })
                
            # If still failing, try storing as .b64 file (experimental)
            if not image2_result:
                logger.info("📸 EXPERIMENTAL: Storing image2 as .b64 file...")
                image2_result = call_github_mcp_tool("create_or_update_file", {
                    "owner": "linsun",
                    "repo": GITHUB_REPO,
                    "path": f"{folder_path}/image2_{timestamp}.jpg.b64",
                    "content": image2_content,
                    "message": f"Add second engagement image (base64) for {EVENT_NAME}",
                    "branch": branch_name
                })
                if image2_result:
                    logger.warning("⚠️ Image2 stored as .b64 file - manual conversion needed")
            
            if image2_result:
                uploaded_files.append(f"image2_{timestamp}.jpg")
                logger.info("✅ Second image uploaded successfully")
                
                # Automatically convert base64 text to binary image
                image2_path_github = f"{folder_path}/image2_{timestamp}.jpg"
                conversion_success = convert_base64_to_binary_image(
                    image2_path_github, 
                    image2_content, 
                    branch_name, 
                    f"Add second engagement image for {EVENT_NAME}"
                )
                if conversion_success:
                    logger.info("🔄 Image2 converted to binary format")
                else:
                    logger.warning("⚠️ Image2 remains as base64 text (check GITHUB_TOKEN)")
            else:
                upload_errors.append("Second image upload failed")
                logger.error("❌ Second image upload failed")
                
        except Exception as e:
            upload_errors.append(f"Second image error: {str(e)}")
            logger.error(f"❌ Second image upload error: {e}")
        
        # Return results
        if len(uploaded_files) > 0:
            logger.info(f"✅ Successfully uploaded {len(uploaded_files)}/3 files to GitHub")
            
            # Validate image uploads by constructing expected URLs
            validation_info = []
            full_repo_path = f"linsun/{GITHUB_REPO}"
            for file_name in uploaded_files:
                if file_name.endswith('.jpg'):
                    raw_url = f"https://raw.githubusercontent.com/{full_repo_path}/{branch_name}/{folder_path}/{file_name}"
                    blob_url = f"https://github.com/{full_repo_path}/blob/{branch_name}/{folder_path}/{file_name}"
                    validation_info.append({
                        "file": file_name,
                        "raw_url": raw_url,
                        "blob_url": blob_url
                    })
            
            return {
                "success": True,
                "branch": branch_name,
                "folder": folder_path,
                "files": uploaded_files,
                "partial": len(uploaded_files) < 3,
                "errors": upload_errors,
                "validation_info": validation_info
            }
        else:
            logger.error("❌ Failed to upload any files to GitHub")
            return {
                "success": False, 
                "error": "All file uploads failed",
                "detailed_errors": upload_errors
            }
            
    except Exception as e:
        logger.error(f"❌ Error storing to GitHub: {e}")
        return {"success": False, "error": str(e)}



# Streamlit UI
st.set_page_config(
    page_title="Analyze a Image Mood with LLaVa 📸",
    page_icon="📸",
    layout="wide"  # Use wide layout for better camera resolution
)

styl = f"""
<style>
    .main {{
        background-repeat: repeat;
        background-size: cover;
        background-attachment: fixed;
    }}
    
    /* Make camera input widgets larger for better resolution */
    .stCameraInput > div > div > div {{
        width: 100% !important;
        max-width: 800px !important;
        height: 600px !important;
    }}
    
    /* Ensure video element is larger */
    .stCameraInput video {{
        width: 100% !important;
        height: 600px !important;
        max-width: 800px !important;
    }}
    
    /* Make the camera capture area larger */
    [data-testid="camera-input"] {{
        width: 100% !important;
    }}
    
    [data-testid="camera-input"] > div {{
        width: 100% !important;
        max-width: 800px !important;
    }}
</style>
"""
st.markdown(styl, unsafe_allow_html=True)

st.title(':grey[Compare engagement levels with LLaVa 📸📸]')

# Auto-detect and use audio file
current_dir = os.path.dirname(__file__)
# st.sidebar.write(f"📁 Looking for audio in: {current_dir}")

audio_extensions = ['*.mp3', '*.wav', '*.m4a', '*.ogg']
audio_files = []
for ext in audio_extensions:
    pattern = os.path.join(current_dir, ext)
    found_files = glob.glob(pattern)
    audio_files.extend(found_files)

# st.sidebar.write(f"🔍 Found {len(audio_files)} audio files: {[os.path.basename(f) for f in audio_files]}")

if audio_files:
    # Automatically use the first audio file found
    custom_audio_file = audio_files[0]
    audio_filename = os.path.basename(custom_audio_file)
    # st.sidebar.success(f"✅ Using Audio: {audio_filename}")
    # st.sidebar.write(f"📂 Full path: {custom_audio_file}")
else:
    # No audio files found, no audio will play
    custom_audio_file = None
    # st.sidebar.warning("⚠️ No audio files found - no background music will play")

# Create two columns for better layout and larger camera inputs
col1, col2 = st.columns(2)

with col1:
    st.subheader("📷 First Image")
    picture1 = st.camera_input("", key="cam1")

with col2:
    st.subheader("📷 Second Image") 
    picture2 = st.camera_input("", key="cam2")

if picture1 and picture2:
  # Save both images
  with open('image1.jpg', 'wb') as f:
    f.write(picture1.getbuffer())
  with open('image2.jpg', 'wb') as f:
    f.write(picture2.getbuffer())

  # Initialize the Ollama client
  client = Client(host=OLLAMA_BASE_URL)

  # Start mood analysis session
  # st.markdown("---")
  # st.subheader("🎵 Starting Mood Analysis Session")
  
  if custom_audio_file:
    # Play the custom audio file once during analysis (hidden from UI)
    background_audio = play_anticipation_sound(custom_audio_file)
    st.markdown(create_audio_element(background_audio, autoplay=True, loop=False, audio_id="background-music", volume=0.9, hidden=True), unsafe_allow_html=True)
    # st.info(f"🎶 Playing background music: {os.path.basename(custom_audio_file)}")
  else:
    # No audio file found, skip audio
    st.info("🔇 No background music - continuing with silent analysis...")

  # Analyze first image
  
  with st.spinner('🎵 Analyzing first image...'):
    message1 = {
        'role': 'user',
        'content': 'Analyze the image and describe the engagement level. Keep the response within 30 words',
        'images': ['image1.jpg']
    }
    stream1 = client.chat(model="llava", messages=[message1], stream=True)
    response1_text = collect_stream_text(stream1)

  # Analyze second image
  with st.spinner('🎵 Analyzing second image...'):
    message2 = {
        'role': 'user',
        'content': 'Analyze the image and describe the engagement level. Keep the response within 30 words',
        'images': ['image2.jpg']
    }
    stream2 = client.chat(model="llava", messages=[message2], stream=True)
    response2_text = collect_stream_text(stream2)

  # Compare the two images
  with st.spinner('🎵 ...'):
    comparison_message = {
        'role': 'user',
        'content': f'Compare these two engagement level analyses and explain the differences or similarities. First image engagement level: {response1_text}. Second image engagement level: {response2_text}. Keep response within 40 words.',
        'images': ['image1.jpg', 'image2.jpg']
    }
    comparison_stream = client.chat(model="llava", messages=[comparison_message], stream=True)
    comparison_text = collect_stream_text(comparison_stream)

  # Display results in rows
  st.markdown("---")
  st.subheader("🎭 First Image Engagement Level Analysis")
  st.write(response1_text)
  
  st.subheader("🎭 Second Image Engagement Level Analysis") 
  st.write(response2_text)
  
  st.markdown("---")
  st.subheader("🔍 Engagement Level Comparison")
  st.write(comparison_text)

  # Generate a summary of the comparison
  with st.spinner('🎵 Creating comparison summary...'):
    summary_message = {
        'role': 'user',
        'content': f'Summarize this engagement level comparison in less than 15 words and inform the user which picture has higher engagement level: {comparison_text}',
    }
    summary_stream = client.chat(model="llava", messages=[summary_message], stream=True)
    summary_text = collect_stream_text(summary_stream)
  
  # Convert comparison summary to speech and auto-play
  if summary_text:
    # Stop background music completely before text-to-speech
    # st.info("🔇 Stopping background music for clear voice playback...")
    # st.markdown(stop_background_music(), unsafe_allow_html=True)
    
    with st.spinner('🎵 Generating voice...'):
      try:
        # Generate main audio
        audio_bytes = text_to_speech(summary_text + " This is cool!")
        if audio_bytes:
          # Create and display auto-playing audio
          audio_html = create_autoplay_audio(audio_bytes)
          st.markdown(audio_html, unsafe_allow_html=True)
      except Exception as e:
        st.error(f"Could not generate speech: {str(e)}")
        st.info("Note: Make sure you have internet connection for text-to-speech functionality.")

  # Store analysis results to GitHub
  st.markdown("---")
  st.subheader("📁 Storing Results to GitHub")
  
  with st.spinner(f'🌿 Storing analysis results to GitHub for event: {EVENT_NAME}...'):
    try:
      analysis_data = {
        'response1': response1_text,
        'response2': response2_text,
        'comparison': comparison_text,
        'summary': summary_text,
        'event_name': EVENT_NAME,
        'timestamp': datetime.now().isoformat()
      }
      
      storage_result = store_engagement_analysis_to_github('image1.jpg', 'image2.jpg', analysis_data)
      
      if storage_result['success']:
        if storage_result.get('partial', False):
          st.warning(f"⚠️ Partially stored analysis to GitHub ({len(storage_result['files'])}/3 files)")
          if storage_result.get('errors'):
            st.error("**Upload Errors:**")
            for error in storage_result['errors']:
              st.error(f"- {error}")
        else:
          st.success(f"✅ Successfully stored analysis to GitHub!")
        
        # Show GitHub links  
        full_repo_path = f"linsun/{GITHUB_REPO}"
        branch_url = f"https://github.com/{full_repo_path}/tree/{storage_result['branch']}"
        folder_url = f"https://github.com/{full_repo_path}/tree/{storage_result['branch']}/{storage_result['folder']}"
        
        st.markdown(f"🔗 **GitHub Links:**")
        st.markdown(f"- [View Branch]({branch_url})")
        st.markdown(f"- [View Event Folder]({folder_url})")
        
      else:
        st.error(f"❌ Failed to store to GitHub: {storage_result.get('error', 'Unknown error')}")
        if storage_result.get('detailed_errors'):
          st.error("**Detailed Errors:**")
          for error in storage_result['detailed_errors']:
            st.error(f"- {error}")
        
    except Exception as e:
      st.error(f"❌ Error storing to GitHub: {str(e)}")
      logger.error(f"GitHub storage error: {e}")
