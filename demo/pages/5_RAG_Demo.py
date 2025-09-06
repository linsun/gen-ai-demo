import streamlit as st
import requests
import json
import mimetypes
import os

st.set_page_config(page_title="RAG Demo", page_icon="🔍")
st.write("# RAG Demo 🔍")

RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://rag:80")

# File uploader
uploaded_file = st.file_uploader("Upload a document", type=['pdf', 'txt'], help="Supported formats: PDF, TXT")

# Process the uploaded file
if uploaded_file is not None:
    try:
        with st.spinner('Processing document...'):
            # Get file extension and set correct MIME type
            file_extension = uploaded_file.name.split('.')[-1].lower()
            content_type = 'application/pdf' if file_extension == 'pdf' else 'text/plain'
            
            # Log file details
            st.write(f"Processing file: {uploaded_file.name} ({content_type})")
            
            # Create a files dictionary with the correct filename and MIME type
            files = {
                "file": (
                    uploaded_file.name,  # Use original filename
                    uploaded_file,
                    content_type
                )
            }
            
            # Send the request
            response = requests.post(f"{RAG_SERVICE_URL}/upload", files=files)
            
            # Check response status and content
            if response.status_code != 200:
                error_detail = response.json().get('detail', 'Unknown error')
                st.error(f"Server error: {error_detail}")
            else:
                st.success("Document processed successfully!")
    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with RAG service: {str(e)}")
    except Exception as e:
        st.error(f"Error processing document: {str(e)}")

# Query interface
query = st.text_input("Ask a question about your document:")

if query:
    try:
        with st.spinner('Searching for answer...'):
            # Send the query as JSON with the correct structure
            response = requests.post(
                f"{RAG_SERVICE_URL}/query",
                json={"question": query},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()
            
            # Display answer
            st.write("### Answer:")
            st.write(result["answer"])
            
            # Display only the first source
            if result["sources"]:
                st.write("### Source:")
                st.text(result["sources"][0]["content"][:200] + "...")
    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with RAG service: {str(e)}")
    except Exception as e:
        st.error(f"Error processing response: {str(e)}") 