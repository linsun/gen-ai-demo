import os
import io
import base64
import streamlit as st
from ollama import Client
from gtts import gTTS

# OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_BASE_URL = os.getenv("LLAVA_BASE_URL", "http://localhost:11434")

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

def create_autoplay_audio(audio_bytes):
  """Create HTML audio element with autoplay"""
  b64_audio = base64.b64encode(audio_bytes).decode()
  audio_html = f"""
  <audio controls autoplay style="width: 100%;">
    <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
    Your browser does not support the audio element.
  </audio>
  """
  return audio_html



# Streamlit UI
st.set_page_config(
    page_title="Analyze a Image Mood with LLaVa 📸",
    page_icon="📸",
)

styl = f"""
<style>
    .main {{
        background-repeat: repeat;
        background-size: cover;
        background-attachment: fixed;
    }}
</style>
"""
st.markdown(styl, unsafe_allow_html=True)

st.title(':grey[Analyze the mood in an image with LLaVa 📸]')
picture = st.camera_input("")

if picture:
  with open ('snap.jpg','wb') as f:
    f.write(picture.getbuffer())

  # Initialize the Ollama client
  client = Client(host=OLLAMA_BASE_URL)

  # Define the path to your image
  image_path = 'snap.jpg'

  # Prepare the message to send to the LLaVA model
  message = {
      'role': 'user',
      'content': 'Analyze the image and describe the mood. Keep the response within 50 words.',
      'images': [image_path]
  }

  # Use the ollama.chat function to send the image and retrieve the description
  stream = client.chat(
      model="llava",  # Specify the desired LLaVA model size
      messages=[message],
      stream=True,
  )
  
  # Collect the complete response text for TTS
  with st.spinner('Analyzing the image...'):
    response_text = collect_stream_text(stream)
  
  # Display the full response
  # st.write("**Analysis Result:**")
  st.write("Hello! " + response_text)

  # Generate a 5-word summary
  with st.spinner('Creating summary...'):
    summary_message = {
        'role': 'user',
        'content': f'Summarize this mood analysis in exactly 5 words: {response_text}',
    }
    summary_stream = client.chat(model="llava", messages=[summary_message], stream=True)
    summary_text = collect_stream_text(summary_stream)
  

  # Convert to speech and auto-play audio using summary
  if summary_text:
    with st.spinner('Generating voice...'):
      try:
        # Generate main audio
        audio_bytes = text_to_speech(summary_text + " This is cool!")
        if audio_bytes:
          # st.write("🔊 **Listen to the analysis (auto-playing):**")
          # Create and display auto-playing audio
          audio_html = create_autoplay_audio(audio_bytes)
          st.markdown(audio_html, unsafe_allow_html=True)
          # st.success("🎵 Audio is now playing automatically!")
      except Exception as e:
        st.error(f"Could not generate speech: {str(e)}")
        st.info("Note: Make sure you have internet connection for text-to-speech functionality.")
