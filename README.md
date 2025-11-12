# Local RAG System with Hybrid LLM Support

A production-ready Retrieval-Augmented Generation (RAG) system that runs locally on macOS (optimized for Apple Silicon) with support for both Claude API and local LLMs via Ollama.

## Features

- 🚀 **Fully Local Embeddings**: Vector embeddings run entirely on your Mac
- 🎯 **M1/M2 Optimized**: Uses Metal Performance Shaders for acceleration
- 💾 **Simple Storage**: Lightweight in-memory vector storage with disk persistence
- 🔄 **Hybrid LLM Support**: Choose between Claude API or local LLMs (Ollama)
- 🤖 **Claude AI Integration**: Supports latest Claude models (Sonnet 4.5, Opus 4.0, Haiku 3.5)
- 🏠 **Local LLM Support**: Run Llama 3.1 70B (quantized) or other models completely free
- 📊 **Cost Tracking**: Real-time monitoring of API usage and costs (or just tokens for local LLMs)
- 🔍 **Semantic Search**: Fast cosine similarity search across your documents
- 🌐 **Web & CLI**: Both Streamlit web interface and command-line tools
- 🧹 **Easy Management**: Clear database, export results, view detailed analytics

## Requirements

- macOS (optimized for Apple Silicon M1/M2)
- Python 3.8+
- **Option 1 (API)**: Claude API key from Anthropic
- **Option 2 (Local)**: Ollama installed with a local LLM model

## Installation

1. Clone the repository:
```bash
git clone git@github.com:skepticsa/local_rag_claude.git
cd local_rag_claude
```

2. Run the setup script:
```bash
chmod +x setup.sh
./setup.sh
```

3. Choose your LLM provider:

### Option A: Claude API (Fast, Cloud-based, Costs Money)

Configure your API key:
```bash
cp .env.example .env
# Edit .env and set:
# LLM_PROVIDER=claude
# ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# CLAUDE_MODEL=claude-sonnet-4-5-20250929
```

Example `.env` configuration:
```bash
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CLAUDE_MODEL=claude-sonnet-4-5-20250929
MAX_TOKENS=2000
TEMPERATURE=0.7
```

### Option B: Local LLM with Ollama (Slower, Private, FREE)

Install Ollama and download a model:
```bash
# Install Ollama
brew install ollama

# Start Ollama service
ollama serve

# In a new terminal, pull a model that fits your RAM:

# For 32GB RAM (RECOMMENDED):
ollama pull llama3.1:8b           # Fast, ~8GB RAM, good quality

# For 64GB+ RAM only:
# ollama pull llama3.1:70b-instruct-q4_K_M  # Best quality, ~42GB RAM
# ollama pull llama3.2:90b                  # Very high quality, ~50GB RAM
```

Configure your `.env`:
```bash
cp .env.example .env
# Edit .env and set:
# LLM_PROVIDER=ollama
# OLLAMA_MODEL=llama3.1:70b-instruct-q4_K_M
# OLLAMA_BASE_URL=http://localhost:11434
```

Example `.env` configuration:
```bash
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.1:8b
OLLAMA_BASE_URL=http://localhost:11434
MAX_TOKENS=2000
TEMPERATURE=0.7
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

#### Using Claude API:
```python
from rag_simple import SimpleRAGSystem

# Initialize with Claude
rag = SimpleRAGSystem(
    claude_api_key="your_key",
    llm_provider="claude"
)

# Process a PDF
result = rag.process_pdf("document.pdf")
print(f"Processed {result['chunks']} chunks")

# Query your documents
answer, sources, stats = rag.query("Your question here", n_results=5)
print(f"Answer: {answer}")
print(f"Provider: {stats['provider']}")
print(f"Cost: ${stats['estimated_cost']:.4f}")
```

#### Using Local LLM (Ollama):
```python
from rag_simple import SimpleRAGSystem

# Initialize with Ollama
rag = SimpleRAGSystem(
    llm_provider="ollama",
    ollama_model="llama3.1:8b"
)

# Process a PDF
result = rag.process_pdf("document.pdf")
print(f"Processed {result['chunks']} chunks")

# Query your documents
answer, sources, stats = rag.query("Your question here", n_results=5)
print(f"Answer: {answer}")
print(f"Provider: {stats['provider']}")
print(f"Cost: ${stats['estimated_cost']:.4f}")  # Will be 0.0 for local LLM
print(f"Tokens: {stats['total_tokens']}")

# Get statistics
stats = rag.get_statistics()
print(f"Total files: {stats['total_files']}, Total chunks: {stats['total_chunks']}")

# Clear database
rag.clear_database()
```

## Cost Comparison

### Local LLM (Ollama)
- **Cost**: $0.00 - Completely FREE!
- **Hardware**: Uses your Mac's CPU/GPU (M1/M2 recommended)
- **Privacy**: All data stays on your machine
- **Speed**: 2-5 seconds per query (8B model), 10-30 seconds (70B model)
- **RAM Requirements**:
  - Llama 3.1 8B: ~8GB RAM (recommended for 32GB systems)
  - Llama 3.1 70B: ~42GB RAM (requires 64GB+ system)
  - Llama 3.2 90B: ~50GB RAM (requires 64GB+ system)
- **Quality**: Good to excellent depending on model size

### Claude API
- **Local Components**: FREE (embeddings, storage)
- **Claude API** (pay-as-you-go):
  - Sonnet 4.5: ~$0.0016-0.0069 per query (most balanced)
  - Opus 4.0: ~$0.008-0.035 per query (highest quality)
  - Haiku 3.5: ~$0.0001-0.0006 per query (fastest/cheapest)
- **Speed**: Fast (1-3 seconds per query)
- **Quality**: State-of-the-art

The system automatically tracks costs with 4-decimal precision and provides daily/monthly projections.

## Getting a Claude API Key

1. Go to https://console.anthropic.com
2. Create an account (separate from Claude.ai)
3. Add credits (minimum $5)
4. Generate API key in Settings

## Project Structure
```
RAG/
├── rag_simple.py        # Core RAG system with in-memory vector storage
├── app.py               # Streamlit web interface (5 tabs)
├── web_app.py           # Simplified web interface
├── cli.py               # Command-line interface
├── cost_tracker.py      # LLM usage and cost monitoring
├── utils.py             # Utility functions
├── requirements.txt     # Python dependencies
├── setup.sh             # Setup script
├── .env.example         # Environment template
├── .gitignore           # Git ignore rules
├── LICENSE              # MIT License
├── README.md            # User documentation
├── CLAUDE.md            # Developer documentation for Claude Code
├── vectors/             # Persisted embeddings and metadata (ignored)
├── logs/                # Cost tracking logs (ignored)
├── exports/             # Exported query results (ignored)
└── uploaded_pdfs/       # Temporary PDF storage (ignored)
```

## How It Works

1. **Document Processing**: PDFs are split into 500-character chunks with 50-character overlap
2. **Embeddings**: Each chunk is converted to a vector using `all-MiniLM-L6-v2` (runs locally on M1/M2)
3. **Storage**: Vectors and metadata are stored in memory and persisted to `./vectors/`
4. **Query**: Your question is embedded, top-k similar chunks are retrieved via cosine similarity
5. **Answer**: Retrieved context is sent to your chosen LLM (Claude API or Ollama) to generate an intelligent response
6. **Tracking**: All queries are logged with token counts and costs (or just tokens for local LLMs)

## Available Claude Models

Set your preferred model in `.env` using the `CLAUDE_MODEL` variable:

- `claude-sonnet-4-5-20250929` - Latest Sonnet (recommended, best balance)
- `claude-opus-4-1-20250805` - Opus 4.0 (highest quality)
- `claude-3-5-haiku-20241022` - Haiku 3.5 (fastest, cheapest)

The system automatically detects the model and calculates costs accordingly.

## Choosing Between Claude API and Local LLM

**Use Claude API when:**
- You need fast responses (1-3 seconds)
- You want state-of-the-art quality
- You have budget for API calls (~$0.002-0.007 per query)
- You're doing production work

**Use Local LLM (Ollama) when:**
- You want zero cost
- Privacy is critical (sensitive documents)
- You have time for slower responses (10-30 seconds)
- You have 32GB+ RAM and ~40GB disk space
- You're experimenting or learning

**Switching providers**: Just change `LLM_PROVIDER` in `.env` and restart the app!

## Tips

- **Start Small**: Test with a few PDFs first (especially important for local LLMs to gauge speed)
- **Monitor Costs**: Check the Analytics tab to track spending (or token usage for local LLMs)
- **Batch Processing**: Use the web UI or `cli.py batch` to process multiple PDFs at once
- **Clear Database**: Use the "Manage Data" tab to reset and start fresh
- **Export Results**: Save query results as Markdown for reference
- **Model Selection (Claude)**: Use Haiku for simple questions, Sonnet for most tasks, Opus for complex analysis
- **Model Selection (Ollama for 32GB RAM)**: Llama 3.1 8B (fast and efficient)
- **Model Selection (Ollama for 64GB+ RAM)**: Llama 3.1 70B or Llama 3.2 90B for best quality
- **Ollama Performance**: Ensure `ollama serve` is running before starting the app

## Troubleshooting

### General
- **"Already processed" messages**: Files are tracked by name. Use "Clear Database" or set `force=True` to reprocess
- **MPS not available**: System will fallback to CPU, embeddings will be slightly slower
- **Import errors**: Make sure to activate the virtual environment: `source rag_env/bin/activate`

### Claude API
- **Costs showing $0.00**: Costs are very small and display with 4 decimals (e.g., $0.0017)
- **API key errors**: Ensure `ANTHROPIC_API_KEY` in `.env` is correct and has credits
- **Rate limits**: Claude API has rate limits; wait a moment and try again

### Ollama (Local LLM)
- **"Ollama not installed"**: Run `brew install ollama` and restart terminal
- **Connection refused**: Make sure `ollama serve` is running in a separate terminal
- **Model not found**: Pull the model first: `ollama pull llama3.1:70b-instruct-q4_K_M`
- **Very slow responses (minutes)**: Your model is too large for your RAM and swapping to disk. Solutions:
  - 32GB RAM: Use `llama3.1:8b` (NOT the 70B model!)
  - 16GB RAM: Use `llama3.1:8b` only
  - Stop the current query with Ctrl+C and switch models
- **Out of memory**: The 70B+ models need ~42-50GB RAM (64GB+ system). Use `llama3.1:8b` for 32GB systems
- **Poor quality**: The 8B model has limitations. For better quality, consider upgrading RAM to use 70B models or use Claude API

## For Developers

If you're using Claude Code to work on this project, check [`CLAUDE.md`](CLAUDE.md) for detailed architecture and development documentation.

## License

MIT License

## Contributing

Pull requests are welcome! For major changes, please open an issue first.
