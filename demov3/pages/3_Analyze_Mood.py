
import os
import streamlit as st
from ollama import Client

ollama_base_url = os.getenv("OLLAMA_BASE_URL")

def process_stream(stream):
  for chunk in stream:
   yield chunk['message']['content']

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

st.title(':grey[Analyze the mood in an image and anything unusual with LLaVa 📸]')
picture = st.camera_input("")

if picture:
  with open ('snap.jpg','wb') as f:
    f.write(picture.getbuffer())

  # Initialize the Ollama client
  client = Client(host=ollama_base_url)

  # Define the path to your image
  image_path = 'snap.jpg'

  # Prepare the message to send to the LLaVA model
  message = {
      'role': 'user',
      'content': 'Analyze the image and describe the mood and anything unusual.',
      'images': [image_path]
  }

  # Use the ollama.chat function to send the image and retrieve the description
  stream = client.chat(
      model="llava",  # Specify the desired LLaVA model size
      messages=[message],
      stream=True,
  )
  
  st.write_stream(process_stream(stream))
