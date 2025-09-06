import os
import io
import streamlit as st
from ollama import Client
import speech_recognition as sr
from pydub import AudioSegment
from pydub.playback import play

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def process_stream(stream):
  for chunk in stream:
   yield chunk['message']['content']

def collect_stream_text(stream):
  """Collect all text from the stream for TTS conversion"""
  full_text = ""
  for chunk in stream:
    full_text += chunk['message']['content']
  return full_text

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
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Initialize the Ollama client
    client = Client(host=OLLAMA_BASE_URL)

    try:
        stream = client.chat(model="llama3.2", messages=st.session_state.messages, stream=True)
        msg = collect_stream_text(stream)

        print(f"Raw Ollama response: {msg}")  # Debug: print the full response
    except Exception as e:
        print(f"Exception occurred: {e}")  # Debug: print the exception
        msg = f"Error: {str(e)}"

    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
