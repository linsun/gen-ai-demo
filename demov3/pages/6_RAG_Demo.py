import streamlit as st
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
import tempfile


ollama_base_url = os.getenv("OLLAMA_BASE_URL")
#ollama_base_url = "http://localhost:11434"

st.set_page_config(page_title="RAG Demo", page_icon="🔍")
st.write("# RAG Demo 🔍")

# Initialize session state for vector store
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = None

# File uploader
uploaded_file = st.file_uploader("Upload a PDF document", type=['pdf'])

# Process the uploaded file
if uploaded_file is not None:
    # Create a temporary file to store the uploaded PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name

    try:
        with st.spinner('Processing document...'):
            # Load the PDF
            loader = PyPDFLoader(tmp_file_path)
            documents = loader.load()

            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            splits = text_splitter.split_documents(documents)

            # Create embeddings and vector store
            embeddings = OllamaEmbeddings(
                model="llama3.2",
                base_url=ollama_base_url
            )
            vector_store = Chroma.from_documents(
                documents=splits,
                embedding=embeddings,
                persist_directory="./chroma_db"
            )

            st.session_state.vector_store = vector_store
            st.success("Document processed successfully!")

    except Exception as e:
        st.error(f"Error processing document: {str(e)}")
    finally:
        # Clean up the temporary file
        os.unlink(tmp_file_path)

# Query interface
if st.session_state.vector_store is not None:
    query = st.text_input("Ask a question about your document:")
    
    if query:
        with st.spinner('Searching for answer...'):
            # Initialize Ollama
            llm = Ollama(
                model="llama3.2",
                base_url=ollama_base_url
            )

            # Create QA chain
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=st.session_state.vector_store.as_retriever(
                    search_kwargs={"k": 10}
                ),
                return_source_documents=True,
            )

            # Get response
            response = qa_chain({"query": query})
            
            # Display answer
            st.write("### Answer:")
            st.write(response["result"])
            
            # Display sources
            st.write("### Sources:")
            for i, doc in enumerate(response["source_documents"]):
                st.write(f"Source {i+1}:")
                st.text(doc.page_content[:200] + "...")
else:
    st.info("Please upload a document to start asking questions.") 