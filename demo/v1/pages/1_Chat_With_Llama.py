import os
import streamlit as st
from ollama import Client

ollama_base_url = os.getenv("OLLAMA_BASE_URL")

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

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Initialize the Ollama client
    client = Client(host=ollama_base_url)
    stream = client.chat(model="llama3.2", messages=st.session_state.messages, stream=False,)
    msg = stream['message']['content']
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)

