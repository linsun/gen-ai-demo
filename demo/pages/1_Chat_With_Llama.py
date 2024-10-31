
import os
import streamlit as st
from ollama import Client

ollama_base_url = os.getenv("OLLAMA_BASE_URL")
llm_name = os.getenv("LLM")

def process_stream(stream):
  for chunk in stream:
   yield chunk['message']['content']

# Streamlit UI
st.set_page_config(
    page_title="Chat With Llama 💬",
    page_icon="👋",
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

st.title(':grey[Chat with Llama on Anything 💬 ]')
st.header(':grey[Ask llama anything:]')

question = st.text_input("")
if question:
  # Initialize the Ollama client
  client = Client(host=ollama_base_url)

  # Prepare the message to send to the llama3.2 model
  message = {
      'role': 'user',
      'content': question
  }

  # Use the ollama.chat function to send the question and retrieve the answer
  stream = client.chat(
      model="llama3.2",  # Specify the desired model
      messages=[message],
      stream=True,
  )
  st.write("👋", process_stream(stream))