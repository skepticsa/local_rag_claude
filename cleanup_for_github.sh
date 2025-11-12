#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧹 RAG Project Cleanup for GitHub${NC}"
echo "====================================="
echo ""

# Ask for confirmation
echo -e "${YELLOW}⚠️  This will remove:${NC}"
echo "  - Virtual environments (rag_env/)"
echo "  - Database files (chroma_db/)"
echo "  - Uploaded PDFs (uploaded_pdfs/)"
echo "  - Logs (logs/)"
echo "  - Exported files (exports/)"
echo "  - Cache files (__pycache__, .pyc)"
echo "  - Environment files with secrets (.env)"
echo "  - Processed data and indexes"
echo ""
echo -e "${GREEN}✅ This will keep:${NC}"
echo "  - All Python source code (*.py)"
echo "  - Requirements.txt"
echo "  - Setup scripts (*.sh)"
echo "  - README and documentation"
echo "  - Configuration templates (.env.example)"
echo ""

read -p "Do you want to create a backup first? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Create backup
    BACKUP_DIR="rag_backup_$(date +%Y%m%d_%H%M%S)"
    echo -e "${BLUE}📦 Creating backup in ${BACKUP_DIR}...${NC}"
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup important data
    [ -d "chroma_db" ] && cp -r chroma_db "$BACKUP_DIR/" 2>/dev/null
    [ -d "uploaded_pdfs" ] && cp -r uploaded_pdfs "$BACKUP_DIR/" 2>/dev/null
    [ -d "logs" ] && cp -r logs "$BACKUP_DIR/" 2>/dev/null
    [ -d "exports" ] && cp -r exports "$BACKUP_DIR/" 2>/dev/null
    [ -f ".env" ] && cp .env "$BACKUP_DIR/.env.backup" 2>/dev/null
    
    echo -e "${GREEN}✅ Backup created in ${BACKUP_DIR}${NC}"
    echo ""
fi

read -p "Proceed with cleanup? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}❌ Cleanup cancelled${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Starting cleanup...${NC}"
echo ""

# Function to remove directory/file and report
remove_item() {
    if [ -e "$1" ]; then
        rm -rf "$1"
        echo -e "${GREEN}✓${NC} Removed: $1"
    else
        echo -e "${YELLOW}⊘${NC} Not found: $1"
    fi
}

# 1. Remove virtual environment
echo -e "${BLUE}1. Removing virtual environments...${NC}"
remove_item "rag_env"
remove_item "venv"
remove_item "env"
remove_item ".venv"
echo ""

# 2. Remove database files
echo -e "${BLUE}2. Removing database files...${NC}"
remove_item "chroma_db"
remove_item "*.db"
remove_item "*.sqlite"
remove_item "*.pickle"
remove_item "*.pkl"
echo ""

# 3. Remove uploaded/processed files
echo -e "${BLUE}3. Removing uploaded and processed files...${NC}"
remove_item "uploaded_pdfs"
remove_item "pdfs"
remove_item "temp_*"
remove_item "*.pdf"
echo ""

# 4. Remove logs and exports
echo -e "${BLUE}4. Removing logs and exports...${NC}"
remove_item "logs"
remove_item "exports"
remove_item "*.log"
echo ""

# 5. Remove Python cache files
echo -e "${BLUE}5. Removing Python cache files...${NC}"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null
find . -type f -name "*.pyd" -delete 2>/dev/null
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null
find . -type d -name "*.egg" -exec rm -rf {} + 2>/dev/null
find . -type f -name ".coverage" -delete 2>/dev/null
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".tox" -exec rm -rf {} + 2>/dev/null
echo -e "${GREEN}✓${NC} Removed all Python cache files"
echo ""

# 6. Remove IDE files
echo -e "${BLUE}6. Removing IDE files...${NC}"
remove_item ".idea"
remove_item ".vscode"
remove_item "*.swp"
remove_item "*.swo"
remove_item "*~"
remove_item ".DS_Store"
echo ""

# 7. Handle sensitive files
echo -e "${BLUE}7. Handling sensitive files...${NC}"
if [ -f ".env" ]; then
    # Check if .env.example exists
    if [ ! -f ".env.example" ]; then
        echo -e "${YELLOW}Creating .env.example from .env (without secrets)...${NC}"
        # Create .env.example with keys but no values
        sed 's/=.*/=your_value_here/' .env > .env.example
        echo -e "${GREEN}✓${NC} Created .env.example"
    fi
    remove_item ".env"
fi
remove_item "*.key"
remove_item "*.pem"
remove_item "credentials.json"
echo ""

# 8. Remove results and temporary files
echo -e "${BLUE}8. Removing temporary files...${NC}"
remove_item "*.tmp"
remove_item "*.temp"
remove_item "*.bak"
remove_item "*.backup"
remove_item "claude_models_available.txt"
remove_item "cost_tracking.json"
remove_item "processed.json"
echo ""

# 9. Create/Update .gitignore
echo -e "${BLUE}9. Creating .gitignore...${NC}"
cat > .gitignore << 'EOL'
# Environment
.env
*.env.local
*.env.*.local
venv/
env/
rag_env/
.venv/
ENV/

# API Keys and Secrets
*.key
*.pem
credentials.json
token.json

# Database
chroma_db/
*.db
*.sqlite
*.sqlite3
*.pkl
*.pickle

# Uploaded/Processed Files
uploaded_pdfs/
pdfs/
*.pdf
temp_*

# Logs and Exports
logs/
exports/
*.log

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Testing
.coverage
.pytest_cache/
.tox/
htmlcov/

# IDEs
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
*.bak
*.backup

# Project specific
processed.json
cost_tracking.json
claude_models_available.txt
rag_backup_*/

# Jupyter
.ipynb_checkpoints/
*.ipynb

# Documentation build
docs/_build/
EOL

echo -e "${GREEN}✓${NC} Created .gitignore"
echo ""

# 10. Create README if it doesn't exist
if [ ! -f "README.md" ]; then
    echo -e "${BLUE}10. Creating README.md...${NC}"
    cat > README.md << 'EOL'
# Local RAG System with Claude AI

A production-ready Retrieval-Augmented Generation (RAG) system that runs locally on macOS (optimized for Apple Silicon) and uses Claude AI for intelligent responses.

## Features

- 🚀 **Fully Local**: Vector database and embeddings run entirely on your Mac
- 🎯 **M1/M2 Optimized**: Uses Metal Performance Shaders for acceleration
- 💾 **Free Storage**: Uses Chroma DB (free forever) for vector storage
- 🤖 **Claude AI Integration**: Leverages Claude's advanced language models
- 📊 **Cost Tracking**: Built-in monitoring of API usage and costs
- 🔍 **Hybrid Search**: Combines vector and keyword search for better results
- 🌐 **Web & CLI**: Both Streamlit web interface and command-line tools

## Requirements

- macOS (optimized for Apple Silicon M1/M2)
- Python 3.8+
- Claude API key from Anthropic

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/rag-system.git
cd rag-system
```

2. Run the setup script:
```bash
chmod +x setup.sh
./setup.sh
```

3. Configure your API key:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Usage

### Web Interface
```bash
source rag_env/bin/activate
streamlit run app.py
```

### Command Line
```bash
source rag_env/bin/activate

# Process PDFs
python cli.py process /path/to/document.pdf
python cli.py batch /path/to/pdf/directory

# Query
python cli.py query "What are the main findings?"

# View statistics
python cli.py stats
```

### Python API
```python
from rag_system import M1OptimizedRAGSystem

rag = M1OptimizedRAGSystem(claude_api_key="your_key")
rag.process_pdf("document.pdf")
answer, sources, stats = rag.query("Your question here")
```

## Cost

- **Local Components**: FREE (Chroma DB, embeddings, storage)
- **Claude API**: ~$0.01-0.05 per query (pay-as-you-go)

## Getting a Claude API Key

1. Go to https://console.anthropic.com
2. Create an account (separate from Claude.ai)
3. Add credits (minimum $5)
4. Generate API key in Settings

## Project Structure
```
rag_system/
├── rag_system.py       # Core RAG system
├── app.py              # Streamlit web interface  
├── cli.py              # Command-line interface
├── cost_tracker.py     # API cost monitoring
├── utils.py            # Utility functions
├── requirements.txt    # Python dependencies
├── setup.sh           # Setup script
└── .env.example       # Environment template
```

## License

MIT License

## Contributing

Pull requests are welcome! For major changes, please open an issue first.
EOL
    echo -e "${GREEN}✓${NC} Created README.md"
else
    echo -e "${YELLOW}⊘${NC} README.md already exists"
fi
echo ""

# 11. Check repository status
echo -e "${BLUE}11. Checking repository status...${NC}"

# Initialize git if needed
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}Git repository not initialized.${NC}"
    read -p "Initialize git repository? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git init
        echo -e "${GREEN}✓${NC} Initialized git repository"
    fi
else
    echo -e "${GREEN}✓${NC} Git repository exists"
fi
echo ""

# 12. Final summary
echo "====================================="
echo -e "${GREEN}✅ Cleanup Complete!${NC}"
echo "====================================="
echo ""
echo -e "${BLUE}📝 Project Status:${NC}"
echo ""

# Count remaining files
PY_FILES=$(find . -name "*.py" -not -path "./rag_env/*" -not -path "./venv/*" 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh . 2>/dev/null | cut -f1)

echo "  Python files: $PY_FILES"
echo "  Total size: $TOTAL_SIZE"
echo ""

echo -e "${BLUE}📋 Next Steps:${NC}"
echo ""
echo "  1. Review the .gitignore file"
echo "  2. Check .env.example has no secrets"
echo "  3. Update README.md with your details"
echo "  4. Add and commit files:"
echo ""
echo "     git add ."
echo "     git commit -m \"Initial commit\""
echo "     git remote add origin https://github.com/yourusername/rag-system.git"
echo "     git push -u origin main"
echo ""

if [ -d "rag_backup_"* ]; then
    echo -e "${YELLOW}⚠️  Backup folder found. Remove it after verifying everything works:${NC}"
    echo "     rm -rf rag_backup_*"
    echo ""
fi

echo -e "${GREEN}✨ Your project is ready for GitHub!${NC}"