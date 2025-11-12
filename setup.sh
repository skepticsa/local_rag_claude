#!/bin/bash

# Setup script for M1 Pro Mac
echo "🚀 Setting up RAG System for M1 Pro Mac..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
echo "📦 Python version: $PYTHON_VERSION"

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv rag_env
source rag_env/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install PyTorch for M1 Mac
echo "🔥 Installing PyTorch for Apple Silicon..."
pip install torch torchvision torchaudio

# Install other requirements
echo "📦 Installing other packages..."
pip install chromadb==0.4.22
pip install sentence-transformers
pip install anthropic
pip install pypdf2
pip install pdfplumber
pip install streamlit
pip install python-dotenv
pip install tqdm
pip install pandas
pip install numpy
pip install click
pip install rich
pip install plotly
pip install rank-bm25
pip install langdetect

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p chroma_db
mkdir -p uploaded_pdfs
mkdir -p logs
mkdir -p exports

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env template..."
    cat > .env << EOL
# Anthropic API Configuration
ANTHROPIC_API_KEY=your_api_key_here
CLAUDE_MODEL=claude-sonnet-4-5-20250929
MAX_TOKENS=2000
TEMPERATURE=0.7
EOL
    echo "✅ Created .env file - Please add your ANTHROPIC_API_KEY"
else
    echo "📝 .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit .env file and add your ANTHROPIC_API_KEY"
echo "2. Activate environment: source rag_env/bin/activate"
echo "3. Run web interface: streamlit run app.py"
echo "   OR"
echo "   Use CLI: python cli.py --help"
