from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
import tempfile
import os
import shutil
import logging
import chromadb
from chromadb.config import Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Ollama base URL from environment variable
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")

# Set ChromaDB directory
PERSIST_DIRECTORY = os.path.join(os.getcwd(), "chroma_db")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to store the vector store
vector_store = None

class Query(BaseModel):
    question: str

def init_chroma():
    """Initialize ChromaDB with proper settings"""
    client = chromadb.PersistentClient(
        path=PERSIST_DIRECTORY,
        settings=Settings(
            allow_reset=True,
            anonymized_telemetry=False
        )
    )
    return client

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global vector_store
    
    file_extension = file.filename.split('.')[-1].lower()
    logger.info(f"Starting to check file extension: {file.filename}")
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only PDF files are supported. Received: {file_extension}"
        )
    
    try:
        logger.info(f"Starting to process file: {file.filename}")
        
        # Create a temporary file to store the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            logger.info(f"Created temporary file: {tmp_file.name}")
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # Load and process the document
        logger.info("Loading PDF document")
        loader = PyPDFLoader(tmp_file_path)
        documents = loader.load()
        logger.info(f"Loaded {len(documents)} pages from PDF")

        # Split documents into chunks
        logger.info("Splitting documents into chunks")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(documents)
        logger.info(f"Created {len(splits)} text chunks")

        # Create embeddings and vector store
        logger.info(f"Creating embeddings using Ollama at {OLLAMA_BASE_URL}")
        embeddings = OllamaEmbeddings(
            model="llama3.2",
            base_url=OLLAMA_BASE_URL
        )

        # Ensure the directory exists with proper permissions
        os.makedirs(PERSIST_DIRECTORY, exist_ok=True)
        logger.info(f"Ensuring directory exists: {PERSIST_DIRECTORY}")

        # Initialize ChromaDB client
        logger.info("Initializing ChromaDB client")
        client = init_chroma()

        # Create new vector store
        logger.info("Creating new vector store")
        vector_store = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=PERSIST_DIRECTORY,
            client=client
        )
        vector_store.persist()
        logger.info("Vector store created and persisted successfully")

        return {"message": "Document processed successfully"}

    except Exception as e:
        logger.error(f"Error processing document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
    finally:
        # Clean up the temporary file
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
                logger.info(f"Cleaned up temporary file: {tmp_file_path}")
            except Exception as e:
                logger.error(f"Error cleaning up temporary file: {str(e)}")

@app.post("/query")
async def query_document(query: Query):
    global vector_store
    
    if not vector_store:
        raise HTTPException(status_code=400, detail="No document has been processed yet")
    
    try:
        logger.info(f"Processing query: {query.question}")
        # Initialize Ollama
        llm = Ollama(
            model="llama3.2",
            base_url=OLLAMA_BASE_URL
        )

        # Create QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(
                search_kwargs={"k": 3}
            ),
            return_source_documents=True,
        )

        # Get response
        response = qa_chain({"query": query.question})
        logger.info("Successfully generated response")
        
        return {
            "answer": response["result"],
            "sources": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in response["source_documents"]
            ]
        }

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 