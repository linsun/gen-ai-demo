import os
import streamlit as st
from ollama import Client

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

# Streamlit UI
st.set_page_config(
    page_title="Chat With Llama 💬",
    page_icon="💬",
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

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

msg = "collecting stream text"
if prompt := st.chat_input():
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
