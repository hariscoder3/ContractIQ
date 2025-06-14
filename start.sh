#!/bin/bash

echo "🚀 Starting ContractIQ..."

# Try to install dependencies using pip3
echo "📦 Installing/updating dependencies..."
pip install --user -r requirements.txt

# Check if streamlit is available, if not try to install it
if ! command -v streamlit &> /dev/null; then
    echo "🔧 Streamlit not found, installing..."
    pip install --user streamlit>=1.28.0
fi

# Start Streamlit app
echo "🎨 Starting ContractIQ..."
python3 -m streamlit run streamlit_app.py --server.port 8501 --server.headless true

echo "✅ ContractIQ is running!"
echo "🖥️  Access your app at: http://localhost:8501"
echo "🚀 All backend functionality is now available!"
echo "⚡ No more separate backend API - everything runs on Streamlit!"
echo ""
echo "Press Ctrl+C to stop the service" 