# ContractIQ - AI-Powered Contract Analysis

ContractIQ is an intelligent contract analysis platform that uses AI to help you understand, analyze, and interact with your legal documents through natural language conversations.

## 🚀 Quick Start

### Start the Application

```bash
# Start ContractIQ
./start.sh
```

Then open your browser to: `http://localhost:8501`

### Manual Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run streamlit_app.py --server.port 8501
```

## ✨ Features

- 📄 **Smart Document Upload**: Process PDF, DOCX, and TXT contracts
- 🤖 **AI-Powered Analysis**: Advanced contract understanding using Novita AI
- 🔍 **Vector Search**: Semantic clause matching with Zilliz database
- 💬 **Natural Language Chat**: Ask questions about your contracts in plain English
- ⚡ **Fast Performance**: Direct function calls for optimal speed
- 🎨 **Modern UI**: Beautiful, responsive Streamlit interface

## 📦 Dependencies

The application uses the following key technologies:
- **Streamlit**: Modern web UI framework
- **PyPDF2**: PDF document processing
- **python-docx**: Word document processing
- **pymilvus**: Vector database operations
- **openai**: AI model integration
- **requests**: HTTP client
- **python-dotenv**: Environment variable management

## 📁 Project Structure

```
contractiq/
├── streamlit_app.py            # Main application
├── start.sh                    # Startup script
├── requirements.txt            # Dependencies
├── utils.py                    # AI and vector database utilities
├── document.py                 # Document processing engine
├── .env                        # Environment variables
├── uploads/                    # File upload directory
└── venv/                       # Virtual environment
```

## 🛠️ Setup Instructions

1. **Clone the repository**
   ```bash
   git clone git@github.com:hariscoder3/ContractIQ.git
   cd contractiq
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   Create a `.env` file with your API keys:
   ```
   NOVITA_API_KEY=your_novita_api_key
   ZILLIZ_URI=your_zilliz_endpoint
   ZILLIZ_TOKEN=your_zilliz_token
   ```

4. **Start the application**
   ```bash
   ./start.sh
   ```

## 🎯 How to Use

1. **Upload Contract**: Upload your PDF, DOCX, or TXT contract file
2. **Wait for Processing**: The system will extract and analyze contract clauses
3. **Start Chatting**: Ask questions about your contract in natural language
4. **Get Insights**: Receive AI-powered analysis and answers

### Sample Questions
- "What are the payment terms?"
- "What is the contract duration?"
- "Are there any termination clauses?"
- "What are the key obligations?"
- "Are there any penalties mentioned?"

## 🔧 Technical Architecture

- **Frontend**: Streamlit web application
- **AI Engine**: Novita AI for natural language processing
- **Vector Database**: Zilliz for semantic search
- **Document Processing**: Custom extraction pipeline
- **Deployment**: Single-service architecture

## 🐛 Troubleshooting

1. **Import Errors**: Ensure all dependencies from `requirements.txt` are installed
2. **Port Issues**: Make sure port 8501 is available
3. **File Upload Issues**: Verify the `uploads/` directory exists and is writable
4. **API Errors**: Check your `.env` file has valid API keys

## 🔐 Environment Variables

Required environment variables in `.env`:

```bash
# Novita AI Configuration
NOVITA_API_KEY=your_novita_api_key

# Zilliz Vector Database Configuration
ZILLIZ_URI=your_zilliz_endpoint
ZILLIZ_TOKEN=your_zilliz_token
```

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 
