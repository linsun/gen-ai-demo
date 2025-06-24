
import os
import openai
import streamlit as st
from openai import OpenAI

openai_api_key = os.getenv("SECRET_OPENAI")

print(openai_api_key)

def process_stream(stream):
  for chunk in stream:
   yield chunk['message']['content']

# Streamlit UI
st.set_page_config(
    page_title="Chat With OpenAI 🤖 ",
    page_icon="🤖",
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

st.title(':grey[Chat With OpenAI on Anything 🤖 ]')

# with st.sidebar:
#    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please configure your OpenAI API key to continue.")
        st.stop()

    client = OpenAI(api_key=openai_api_key)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    try:
        response = client.chat.completions.create(model="gpt-3.5-turbo", messages=st.session_state.messages)
        msg = response.choices[0].message.content
    except openai.APIConnectionError as e:
        msg = "APIConnectionError: The server could not be reached"
    except:
        msg = "Error connecting to the server"
    
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)