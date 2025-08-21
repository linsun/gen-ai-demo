
import os
import streamlit as st
from ollama import Client

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def process_stream(stream):
  for chunk in stream:
   yield chunk['message']['content']

# Streamlit UI

st.set_page_config(
    page_title="Describe a Picture with LLaVa 🖼",
    page_icon="🖼",
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

st.title(':grey[Describe a picture with LLaVa 🖼 ]')
picture = st.file_uploader('Upload a PNG image', type='png')

if picture:
  with open ('snap.jpg','wb') as f:
    f.write(picture.getbuffer())

  # Initialize the Ollama client
  client = Client(host=OLLAMA_BASE_URL)

  # Define the path to your image
  image_path = 'snap.jpg'
  st.image(image_path, caption="Just uploaded picture")

  # Prepare the message to send to the LLaVA model
  message = {
      'role': 'user',
      'content': 'Analyze the image very briefly and describe the mood of the people in the image. Keep the response within 50 words.',
      'images': [image_path]
  }

  # Use the ollama.chat function to send the image and retrieve the description
  stream = client.chat(
      model="llava",  # Specify the desired LLaVA model size
      messages=[message],
      stream=True,
  )
  
  st.write_stream(process_stream(stream))
