import os
import io
import re
import json
import requests
import logging
import streamlit as st
from ollama import Client
import speech_recognition as sr
from pydub import AudioSegment
from pydub.playback import play

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://agentgw.mcp.svc.cluster.local:3000")

def process_stream(stream):
  for chunk in stream:
   yield chunk['message']['content']

def collect_stream_text(stream):
  """Collect all text from the stream for TTS conversion"""
  full_text = ""
  for chunk in stream:
    full_text += chunk['message']['content']
  return full_text

def detect_slide_creation_intent(text):
    """Detect if user wants to create slides for a place"""
    logger.info(f"🔍 Analyzing text for slide creation intent: '{text}'")
    return None

def initialize_mcp_session():
    """Initialize MCP session before making tool calls"""
    logger.info("🔧 Initializing MCP session...")
    
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
                    "name": "voice-llama-client",
                    "version": "1.0.0"
                }
            }
        }
        
        logger.info(f"🔧 Sending initialize request: {json.dumps(init_request, indent=2)}")
        
        response = requests.post(
            MCP_SERVER_URL,
            json=init_request,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            timeout=30
        )
        
        logger.info(f"🔧 Initialize response status: {response.status_code}")
        logger.info(f"🔧 Initialize response headers: {dict(response.headers)}")
        logger.info(f"🔧 Initialize response content: {repr(response.text)}")
        logger.info(f"🔧 Initialize response content length: {len(response.text)}")
        
        # Extract session ID from headers
        global _mcp_session_id
        _mcp_session_id = response.headers.get('mcp-session-id')
        if _mcp_session_id:
            logger.info(f"🔧 Extracted MCP session ID: {_mcp_session_id}")
        else:
            logger.info("🔧 No MCP session ID found in response headers")
        
        if response.status_code == 200:
            if response.text.strip():
                try:
                    # Check if response is Server-Sent Events format
                    if response.headers.get('content-type', '').startswith('text/event-stream'):
                        logger.info("🔧 Response is Server-Sent Events format")
                        # Parse SSE format - extract only the data line
                        sse_lines = response.text.strip().split('\n')
                        json_str = None
                        
                        for line in sse_lines:
                            if line.startswith('data: '):
                                json_str = line[6:]  # Remove "data: " prefix
                                break
                        
                        if json_str:
                            logger.info(f"🔧 Extracted JSON from SSE: {repr(json_str)}")
                            response_data = json.loads(json_str)
                            logger.info(f"🔧 Parsed SSE data: {json.dumps(response_data, indent=2)}")
                        else:
                            logger.error(f"❌ No data line found in SSE response: {repr(response.text)}")
                            return False
                    else:
                        # Regular JSON response
                        response_data = response.json()
                        logger.info(f"🔧 Initialize response: {json.dumps(response_data, indent=2)}")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse initialize response as JSON: {e}")
                    logger.error(f"❌ Raw response: {repr(response.text)}")
                    return False
                except Exception as e:
                    logger.error(f"❌ Error parsing response: {e}")
                    logger.error(f"❌ Raw response: {repr(response.text)}")
                    return False
            else:
                logger.info("🔧 Initialize response is empty - this might be normal for MCP")
                response_data = None
            
            # Send initialized notification
            initialized_request = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            
            logger.info("🔧 Sending initialized notification")
            logger.info(f"🔧 Notification request: {json.dumps(initialized_request, indent=2)}")
            
            # Prepare notification headers with session ID if available
            notification_headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
            if _mcp_session_id:
                notification_headers["mcp-session-id"] = _mcp_session_id
                logger.info(f"🔧 Including session ID in notification: {_mcp_session_id}")
            
            notification_response = requests.post(
                MCP_SERVER_URL,
                json=initialized_request,
                headers=notification_headers,
                timeout=30
            )
            
            logger.info(f"🔧 Notification response status: {notification_response.status_code}")
            logger.info(f"🔧 Notification response: {repr(notification_response.text)}")
            
            logger.info("✅ MCP session initialized successfully")
            return True
        else:
            logger.error(f"❌ Initialize failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error initializing MCP session: {e}")
        return False

# Global variables to track MCP session state
_mcp_initialized = False
_mcp_session_id = None

def call_mcp_tool(tool_name, arguments):
    """Call a tool in the Google Slides MCP server via HTTP"""
    global _mcp_initialized, _mcp_session_id
    
    logger.info(f"🌐 Calling MCP tool: {tool_name}")
    logger.info(f"🌐 Server URL: {MCP_SERVER_URL}")
    logger.info(f"🌐 Arguments: {json.dumps(arguments, indent=2)}")
    
    # Initialize MCP session if not already done
    if not _mcp_initialized:
        logger.info("🔧 MCP not initialized, initializing now...")
        if initialize_mcp_session():
            _mcp_initialized = True
        else:
            logger.error("❌ Failed to initialize MCP session")
            return None
    
    logger.info(f"🌐 Using MCP session ID: {_mcp_session_id}")
    
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
        
        logger.info(f"🌐 Sending request: {json.dumps(mcp_request, indent=2)}")
        
        # Prepare headers with session ID if available
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
        if _mcp_session_id:
            headers["mcp-session-id"] = _mcp_session_id
            logger.info(f"🌐 Including session ID in headers: {_mcp_session_id}")
        
        # Make HTTP POST request to the MCP server
        response = requests.post(
            MCP_SERVER_URL,
            json=mcp_request,
            headers=headers,
            timeout=60
        )
        
        logger.info(f"🌐 Response status: {response.status_code}")
        logger.info(f"🌐 Response headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            logger.error(f"❌ HTTP Error: {response.status_code} - {response.text}")
            print(f"HTTP Error: {response.status_code} - {response.text}")
            return None
        
        # Parse response (handle both SSE and regular JSON)
        try:
            if response.headers.get('content-type', '').startswith('text/event-stream'):
                logger.info("🌐 Response is Server-Sent Events format")
                # Parse SSE format - extract only the data line
                sse_lines = response.text.strip().split('\n')
                json_str = None
                
                for line in sse_lines:
                    if line.startswith('data: '):
                        json_str = line[6:]  # Remove "data: " prefix
                        break
                
                if json_str:
                    logger.info(f"🌐 Extracted JSON from SSE: {repr(json_str)}")
                    response_data = json.loads(json_str)
                    logger.info(f"🌐 Parsed SSE data: {json.dumps(response_data, indent=2)}")
                else:
                    logger.error(f"❌ No data line found in SSE response: {repr(response.text)}")
                    return None
            else:
                # Regular JSON response
                response_data = response.json()
                logger.info(f"🌐 Response data: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse tool response: {e}")
            logger.error(f"❌ Raw response: {repr(response.text)}")
            return None
        except Exception as e:
            logger.error(f"❌ Error parsing tool response: {e}")
            logger.error(f"❌ Raw response: {repr(response.text)}")
            return None
        
        if "error" in response_data:
            logger.error(f"❌ MCP Error: {response_data['error']}")
            print(f"MCP Error: {response_data['error']}")
            return None
            
        result = response_data.get("result", {}).get("content", [])
        logger.info(f"✅ MCP tool success: {tool_name} returned {len(result) if isinstance(result, list) else 'data'}")
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ HTTP request error: {e}")
        print(f"HTTP request error: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON decode error: {e}")
        print(f"JSON decode error: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error calling MCP tool: {e}")
        print(f"Error calling MCP tool: {e}")
        return None

def generate_place_slides_content(place):
    """Generate content for slides about a specific place"""
    logger.info(f"🤖 Generating content for place: {place}")
    logger.info(f"🤖 Using Ollama at: {OLLAMA_BASE_URL}")
    
    # Use Llama to generate structured content for the place
    client = Client(host=OLLAMA_BASE_URL)
    
    prompt = f"""Generate information about {place} that would be suitable for a presentation. 
    Please provide:
    1. A brief introduction/overview
    2. Key attractions or features
    3. Fun facts
    
    Format your response as clear, concise points suitable for 1 presentation slide. Add a slide at the end of the presentation with the title 'Have fun exploring {place}!'"""
    
    logger.info(f"🤖 Sending prompt to Llama: {prompt[:100]}...")
    
    try:
        response = client.chat(model="llama3.2", messages=[
            {"role": "user", "content": prompt}
        ])
        content = response['message']['content']
        logger.info(f"✅ Content generated successfully ({len(content)} characters)")
        logger.info(f"🤖 Content preview: {content[:200]}...")
        return content
    except Exception as e:
        logger.error(f"❌ Error generating content: {e}")
        return f"Error generating content: {e}"

def create_slides_for_place(place):
    """Create Google Slides presentation for a place"""
    logger.info(f"📊 Starting slide creation for place: {place}")
    
    try:
        # First, create a new presentation
        presentation_title = f"Discover {place.title()}"
        logger.info(f"📊 Creating presentation with title: {presentation_title}")
        
        create_result = call_mcp_tool("create_presentation", {
            "title": presentation_title
        })
        
        logger.info(f"📊 Create presentation result: {create_result}")
        
        if not create_result:
            logger.error("❌ Failed to create presentation - no result from MCP")
            return "Failed to create presentation"
            
        # Extract presentation ID from the result
        presentation_info = create_result[0] if isinstance(create_result, list) else create_result
        logger.info(f"📊 Presentation info: {presentation_info}")
        logger.info(f"📊 Presentation info type: {type(presentation_info)}")
        
        # Try to extract presentation ID from different possible response formats
        presentation_id = None
        if isinstance(presentation_info, dict):
            logger.info("📊 Parsing presentation ID from dict response")
            # Check if it's directly in the response
            if "presentationId" in presentation_info:
                presentation_id = presentation_info["presentationId"]
                logger.info(f"📊 Found presentation ID in 'presentationId' field: {presentation_id}")
            # Check if it's in the text field
            elif "text" in presentation_info and "ID: " in presentation_info["text"]:
                presentation_id = presentation_info["text"].split("ID: ")[-1].split("\n")[0]
                logger.info(f"📊 Extracted presentation ID from text field: {presentation_id}")
            else:
                logger.info(f"📊 Dict keys available: {list(presentation_info.keys())}")
        elif isinstance(presentation_info, str) and "ID: " in presentation_info:
            presentation_id = presentation_info.split("ID: ")[-1].split("\n")[0]
            logger.info(f"📊 Extracted presentation ID from string: {presentation_id}")
        else:
            logger.error(f"📊 Unable to parse presentation ID from: {type(presentation_info)} - {presentation_info}")
        
        if not presentation_id:
            logger.error("❌ Failed to extract presentation ID")
            return f"Failed to get presentation ID from response: {create_result}"
        
        logger.info(f"✅ Successfully extracted presentation ID: {presentation_id}")
        
        # Generate content for the place
        logger.info(f"📊 Generating content for {place}")
        content = generate_place_slides_content(place)
        
        if content.startswith("Error generating content"):
            logger.error(f"❌ Content generation failed: {content}")
            return f"Failed to generate content for {place}: {content}"
        
        logger.info(f"📊 Content generated successfully, proceeding to create slides")
        
        # Create slides with content using batch_update_presentation
        # First, create additional slides (the presentation starts with one slide)
        slide_id_title = f"slide_title_{place.lower().replace(' ', '_')}"
        slide_id_content = f"slide_content_{place.lower().replace(' ', '_')}"
        
        update_requests = [
            # Create a title slide (replace the default slide)
            {
                "createSlide": {
                    "objectId": slide_id_title,
                    "insertionIndex": 1,
                    "slideLayoutReference": {
                        "predefinedLayout": "TITLE"
                    }
                }
            },
            # Create a content slide  
            {
                "createSlide": {
                    "objectId": slide_id_content,
                    "insertionIndex": 2,
                    "slideLayoutReference": {
                        "predefinedLayout": "TITLE_AND_BODY"
                    }
                }
            }
        ]
        
        logger.info(f"📊 Creating slides with {len(update_requests)} requests")
        logger.info(f"📊 Slide IDs: title={slide_id_title}, content={slide_id_content}")
        
        # Apply the slide creation updates
        update_result = call_mcp_tool("batch_update_presentation", {
            "presentationId": presentation_id,
            "requests": update_requests
        })
        
        if not update_result:
            logger.error("❌ Failed to add slides to presentation")
            return f"Created presentation but failed to add slides. Presentation ID: {presentation_id}"
        
        logger.info(f"✅ Successfully added slides to presentation")
        
        logger.info(f"🎉 Slide creation completed successfully!")
        result_message = f"✅ Successfully created Google Slides presentation '{presentation_title}' about {place}!\n\n📊 **Presentation Details:**\n- Title: {presentation_title}\n- Slides: Title slide + Content slide\n- Presentation ID: `{presentation_id}`\n\n🔗 You can access your presentation at: https://docs.google.com/presentation/d/{presentation_id}"
        logger.info(f"📊 Final result message: {result_message}")
        return result_message
        
    except Exception as e:
        logger.error(f"❌ Exception in create_slides_for_place: {e}", exc_info=True)
        return f"Error creating slides: {str(e)}"

def speech_to_text(audio_bytes):
  """Convert audio bytes to text using speech recognition"""
  if audio_bytes is None:
    return None
  
  try:
    # Convert audio bytes to AudioSegment
    audio = AudioSegment.from_wav(io.BytesIO(audio_bytes))
    
    # Export as wav for speech recognition
    wav_io = io.BytesIO()
    audio.export(wav_io, format="wav")
    wav_io.seek(0)
    
    # Initialize recognizer
    recognizer = sr.Recognizer()
    
    # Use speech recognition
    with sr.AudioFile(wav_io) as source:
      audio_data = recognizer.record(source)
      try:
        # Use Google's speech recognition API
        text = recognizer.recognize_google(audio_data)
        return text
      except sr.UnknownValueError:
        return "Could not understand the audio"
      except sr.RequestError as e:
        return f"Speech recognition error: {str(e)}"
        
  except Exception as e:
    return f"Error processing audio: {str(e)}"

# Streamlit UI
st.set_page_config(
    page_title="Chat With Llama 💬",
    page_icon="💬",
    layout="wide"
)

styl = f"""
<style>
    .main {{
        background-repeat: repeat;
        background-size: cover;
        background-attachment: fixed;
    }}
    
    /* Ensure all columns are perfectly aligned */
    .stColumn > div {{
        height: auto !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-end !important;
        min-height: 60px !important;
    }}
    
    /* Align text input, audio input, and button at the same level */
    .stTextInput > div > div > input {{
        margin-bottom: 0 !important;
    }}
    
    .stAudioInput {{
        margin-bottom: 0 !important;
    }}
    
    /* Make audio input button same height as send button */
    .stAudioInput > div > div > div > button {{
        height: 30px !important;
        min-height: 30px !important;
        max-height: 30px !important;
        padding: 8px 12px !important;
        font-size: 14px !important;
    }}
    
    .stButton > button {{
        margin-bottom: 0 !important;
        height: 40px !important;
    }}
    
    /* Remove extra spacing from audio input */
    .stAudioInput > div {{
        margin-bottom: 0 !important;
    }}
    
    /* Make sure all form elements align to bottom of their containers */
    .stColumn .stTextInput,
    .stColumn .stAudioInput,
    .stColumn .stButton {{
        margin-top: auto !important;
        margin-bottom: 0 !important;
    }}
</style>
"""
st.markdown(styl, unsafe_allow_html=True)

st.title(':grey[Chat with Llama - Type or Speak! 💬🎤]')

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]
if "input_text" not in st.session_state:
    st.session_state["input_text"] = ""
if "processing_voice" not in st.session_state:
    st.session_state["processing_voice"] = False

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# iMessage-style input interface
st.markdown("---")

# Create columns for text input, voice button, and send button
col1, col2, col3 = st.columns([4, 1, 1])  # Text input, voice button, send button

# Voice recording processing
with col2:
    audio_data = st.audio_input("")
    
    if audio_data and not st.session_state.get("processing_voice", False):
        st.session_state["processing_voice"] = True
        # st.info("🎤 Processing...")
        with st.spinner("..."):
            try:
                # st.audio_input returns bytes directly, perfect for speech_to_text
                voice_prompt = speech_to_text(audio_data.getbuffer())
                
                if voice_prompt and not voice_prompt.startswith("Could not understand") and not voice_prompt.startswith("Speech recognition error") and not voice_prompt.startswith("Error processing"):
                    st.session_state["input_text"] = voice_prompt  # Populate text input
                    # st.success(f"✅ Voice recognized: **{voice_prompt}**")
                    #st.info("👆 Text has been added to the input field above. Edit if needed and click Send.")
                else:
                    st.error(f"❌ {voice_prompt}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        st.session_state["processing_voice"] = False

# Text input and send button
with col1:
    user_input = st.text_input(
        "Type your message here...", 
        value=st.session_state["input_text"],
        key="message_input",
        label_visibility="collapsed"
    )
    # Reset voice processing flag when user types manually
    if user_input != st.session_state["input_text"]:
        st.session_state["processing_voice"] = False

with col3:
    send_button = st.button("Send", type="primary")

# Process the input when send button is clicked or Enter is pressed
prompt = None
if send_button and user_input.strip():
    prompt = user_input.strip()
    st.session_state["input_text"] = ""  # Clear the input after sending
    st.session_state["processing_voice"] = False  # Reset processing flag

msg = "collecting stream text"
if prompt:
    logger.info(f"💬 User input received: '{prompt}'")
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Check if user wants to create slides for a place
    logger.info("🔍 Checking for slide creation intent...")
    place = detect_slide_creation_intent(prompt)
    
    if place:
        logger.info(f"🎯 Slide creation intent detected for place: {place}")
        with st.spinner(f"Creating Google Slides presentation for {place}..."):
            logger.info(f"📊 Starting slide creation process...")
            slides_result = create_slides_for_place(place)
            logger.info(f"📊 Slide creation result: {slides_result[:100]}...")
            msg = slides_result
    else:
        logger.info("💭 No slide creation intent detected, proceeding with regular chat")
        # Initialize the Ollama client for regular chat
        client = Client(host=OLLAMA_BASE_URL)

        try:
            logger.info("🦙 Sending request to Ollama for regular chat")
            stream = client.chat(model="llama3.2", messages=st.session_state.messages, stream=True)
            msg = collect_stream_text(stream)

            logger.info(f"🦙 Ollama response received ({len(msg)} chars)")
            print(f"Raw Ollama response: {msg}")  # Debug: print the full response
        except Exception as e:
            logger.error(f"❌ Ollama error: {e}")
            print(f"Exception occurred: {e}")  # Debug: print the exception
            msg = f"Error: {str(e)}"

    logger.info(f"💬 Final response ready ({len(msg)} chars)")
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
