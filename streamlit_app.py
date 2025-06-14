import streamlit as st
import os
import shutil
import uuid
import logging
from typing import Optional, List
from dotenv import load_dotenv
import sys

# Import backend functionality (now in root directory)
from utils import init_zilliz, store_clauses, search_similar_clauses, generate_response
from document import extract_clauses_from_file

# Load environment variables
load_dotenv()

# Initialize logging with reduced verbosity
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Reduce verbosity of specific loggers
logging.getLogger('watchdog').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('pymilvus').setLevel(logging.WARNING)
logging.getLogger('streamlit').setLevel(logging.WARNING)

# Page configuration
st.set_page_config(
    page_title="ContractIQ - AI Contract Analysis",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: #1f2937;
        text-align: center;
        margin-bottom: 0.5rem;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .sub-header {
        font-size: 1.2rem;
        color: #6b7280;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .upload-section {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 2rem;
        border-radius: 1rem;
        border: 2px dashed #cbd5e1;
        margin: 1rem 0;
    }
    
    .chat-container {
        background: white;
        padding: 1.5rem;
        border-radius: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    
    .user-message {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white;
        padding: 1rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
        margin-left: 2rem;
    }
    
    .ai-message {
        background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
        color: #1f2937;
        padding: 1rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
        margin-right: 2rem;
        border-left: 4px solid #3b82f6;
    }
    
    .success-message {
        background: linear-gradient(135deg, #dcfce7, #bbf7d0);
        color: #166534;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #22c55e;
        margin: 1rem 0;
    }
    
    .info-card {
        background: linear-gradient(135deg, #dbeafe, #bfdbfe);
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
        margin: 0.5rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Initialize Zilliz connection
@st.cache_resource
def initialize_backend():
    """Initialize the backend services"""
    try:
        init_zilliz()
        # Create uploads directory if it doesn't exist
        os.makedirs("uploads", exist_ok=True)
        logger.info("Backend initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing backend: {str(e)}")
        st.error(f"Backend initialization failed: {str(e)}")
        return False

def upload_document(file) -> Optional[dict]:
    """Upload and process document using backend functionality"""
    try:
        logger.info(f"Processing file upload: {file.name}")
        
        # Generate a unique ID for the contract
        contract_id = str(uuid.uuid4())
        logger.info(f"Generated contract ID: {contract_id}")
        
        # Save the uploaded file
        file_path = f"uploads/{contract_id}_{file.name}"
        logger.info(f"Saving file to: {file_path}")
        
        with open(file_path, "wb") as buffer:
            buffer.write(file.getvalue())
        logger.info("File saved successfully")
        
        # Extract clauses from the document
        logger.info("Extracting clauses from document")
        clauses = extract_clauses_from_file(file_path)
        logger.info(f"Extracted {len(clauses)} clauses")
        
        # Store clauses in Zilliz
        logger.info("Storing clauses in database")
        store_clauses(contract_id, clauses)
        logger.info("Clauses stored successfully")
        
        return {
            "message": "File uploaded and processed successfully",
            "filename": file.name,
            "contract_id": contract_id,
            "clauses_count": len(clauses)
        }
    except Exception as e:
        logger.error(f"Error in upload_document: {str(e)}", exc_info=True)
        st.error(f"Error uploading file: {str(e)}")
        return None

def chat_with_contract(query: str, contract_id: Optional[str] = None) -> Optional[dict]:
    """Process chat query using backend functionality"""
    try:
        logger.info(f"Processing chat query: '{query}'")
        
        # Search for relevant clauses
        logger.info("Searching for similar clauses...")
        similar_clauses = search_similar_clauses(query, top_k=10)
        logger.info(f"Found {len(similar_clauses)} similar clauses")
        
        # Extract context and filter by relevance
        context = []
        for clause, distance in similar_clauses:
            if distance < 1.5:  # Similarity threshold
                context.append(clause)
                logger.debug(f"Including clause with distance {distance:.4f}")
            else:
                logger.debug(f"Excluding clause with distance {distance:.4f}")
        
        logger.info(f"Context after filtering: {len(context)} clauses")
        
        if not context:
            logger.warning("No relevant context found for the query")
        
        # Generate response
        logger.info("Generating response...")
        response = generate_response(query, context)
        logger.info(f"Generated response preview: {response[:100]}...")
        
        return {
            "response": response,
            "query": query,
            "context": context,
            "found_clauses": len(similar_clauses),
            "relevant_clauses": len(context)
        }
    except Exception as e:
        logger.error(f"Error in chat_with_contract: {str(e)}", exc_info=True)
        return {
            "response": "I apologize, but I'm experiencing technical difficulties. Please try your question again.",
            "query": query,
            "context": [],
            "error": str(e)
        }

def main():
    # Initialize backend
    if not initialize_backend():
        st.error("Failed to initialize backend services. Please check your configuration.")
        return
    
    # Header
    st.markdown('<h1 class="main-header">📄 ContractIQ</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Contract Analysis & Intelligence</p>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'contract_uploaded' not in st.session_state:
        st.session_state.contract_uploaded = False
    if 'contract_id' not in st.session_state:
        st.session_state.contract_id = None
    if 'contract_filename' not in st.session_state:
        st.session_state.contract_filename = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🚀 Features")
        st.markdown("""
        - **Smart Upload**: PDF contract processing
        - **AI Analysis**: Powered by Novita AI
        - **Vector Search**: Semantic clause matching
        - **Natural Chat**: Conversational interface
        - **All-in-One**: Complete Streamlit deployment
        """)
        
        if st.session_state.contract_uploaded:
            st.markdown("### 📋 Current Contract")
            st.success(f"✅ {st.session_state.contract_filename}")
            st.info(f"Contract ID: `{st.session_state.contract_id[:8]}...`")
            
            if st.button("🗑️ Clear Contract", type="secondary"):
                st.session_state.contract_uploaded = False
                st.session_state.contract_id = None
                st.session_state.contract_filename = None
                st.session_state.chat_history = []
                st.rerun()
        
        st.markdown("### 💡 Sample Questions")
        sample_questions = [
            "What are the payment terms?",
            "What is the contract duration?",
            "Are there any termination clauses?",
            "What are the key obligations?",
            "Are there any penalties mentioned?"
        ]
        
        for i, question in enumerate(sample_questions):
            if st.button(f"💬 {question}", key=f"sample_{i}", use_container_width=True):
                if st.session_state.contract_uploaded:
                    # Process the question directly
                    with st.spinner("🤔 Analyzing contract..."):
                        response_data = chat_with_contract(
                            question, 
                            st.session_state.contract_id
                        )
                        
                        if response_data:
                            # Add to chat history
                            st.session_state.chat_history.append({
                                "query": question,
                                "response": response_data["response"]
                            })
                            
                            # Show success message
                            st.success(f"✅ Processed: {question}")
                            if response_data.get("relevant_clauses", 0) > 0:
                                st.info(f"🎯 Found {response_data['relevant_clauses']} relevant clauses")
                            
                            st.rerun()
                else:
                    st.warning("Please upload a contract first!")
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Upload section
        st.markdown("### 📤 Upload Contract")
        
        with st.container():
            st.markdown('<div class="upload-section">', unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader(
                "Choose a contract file",
                type=["pdf", "txt", "docx"],
                help="Upload a PDF, TXT, or DOCX contract file for analysis"
            )
            
            if uploaded_file is not None and not st.session_state.contract_uploaded:
                with st.spinner("🔄 Processing document..."):
                    result = upload_document(uploaded_file)
                    
                    if result:
                        st.session_state.contract_uploaded = True
                        st.session_state.contract_id = result["contract_id"]
                        st.session_state.contract_filename = result["filename"]
                        
                        st.markdown(f"""
                        <div class="success-message">
                            <h4>✅ Upload Successful!</h4>
                            <p><strong>File:</strong> {result['filename']}</p>
                            <p><strong>Clauses Processed:</strong> {result['clauses_count']}</p>
                            <p><strong>Contract ID:</strong> {result['contract_id'][:8]}...</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.balloons()
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Chat section
        st.markdown("### 💬 Chat with Contract")
        
        if st.session_state.contract_uploaded:
            # Chat history
            chat_container = st.container(height=400)
            with chat_container:
                for chat in st.session_state.chat_history:
                    st.markdown(f"""
                    <div class="user-message">
                        <strong>You:</strong> {chat['query']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class="ai-message">
                        <strong>ContractIQ:</strong> {chat['response']}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Chat input
            query = st.text_input(
                "Ask a question about your contract:",
                placeholder="e.g., What are the payment terms?",
                key="chat_input"
            )
            
            if st.button("🚀 Send", type="primary") and query:
                with st.spinner("🤔 Analyzing contract..."):
                    response_data = chat_with_contract(
                        query, 
                        st.session_state.contract_id
                    )
                    
                    if response_data:
                        # Add to chat history
                        st.session_state.chat_history.append({
                            "query": query,
                            "response": response_data["response"]
                        })
                        
                        # Show additional info
                        if response_data.get("relevant_clauses", 0) > 0:
                            st.info(f"🎯 Found {response_data['relevant_clauses']} relevant clauses")
                        
                        # Rerun to refresh the chat history
                        st.rerun()
        else:
            st.markdown("""
            <div class="info-card">
                <h4>📋 Getting Started</h4>
                <p>Upload a contract document to start chatting with ContractIQ!</p>
                <ul>
                    <li>Upload your PDF, TXT, or DOCX contract</li>
                    <li>Wait for processing to complete</li>
                    <li>Start asking questions about your contract</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # Simple footer with just stats
    st.markdown("---")
    if st.session_state.contract_uploaded:
        st.markdown(f"### 📊 Current Session: {len(st.session_state.chat_history)} conversations")
    else:
        st.markdown("### 📊 Ready to analyze your contracts!")

if __name__ == "__main__":
    main() 