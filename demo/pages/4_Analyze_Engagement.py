import os
import io
import base64
import glob
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
