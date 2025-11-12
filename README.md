# Local RAG System with Claude AI

A production-ready Retrieval-Augmented Generation (RAG) system that runs locally on macOS (optimized for Apple Silicon) and uses Claude AI for intelligent responses.

## Features

- 🚀 **Fully Local Embeddings**: Vector embeddings run entirely on your Mac
- 🎯 **M1/M2 Optimized**: Uses Metal Performance Shaders for acceleration
- 💾 **Simple Storage**: Lightweight in-memory vector storage with disk persistence
- 🤖 **Claude AI Integration**: Supports latest Claude models (Sonnet 4.5, Opus 4.0, Haiku 3.5)
- 📊 **Cost Tracking**: Real-time monitoring of API usage and costs with automatic model detection
- 🔍 **Semantic Search**: Fast cosine similarity search across your documents
- 🌐 **Web & CLI**: Both Streamlit web interface and command-line tools
- 🧹 **Easy Management**: Clear database, export results, view detailed analytics

## Requirements

- macOS (optimized for Apple Silicon M1/M2)
- Python 3.8+
- Claude API key from Anthropic

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

3. Configure your API key and model:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY and preferred CLAUDE_MODEL
```

Example `.env` configuration:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CLAUDE_MODEL=claude-sonnet-4-5-20250929
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
```python
from rag_simple import SimpleRAGSystem

# Initialize the system
rag = SimpleRAGSystem(claude_api_key="your_key")

# Process a PDF
result = rag.process_pdf("document.pdf")
print(f"Processed {result['chunks']} chunks")

# Query your documents
answer, sources, stats = rag.query("Your question here", n_results=5)
print(f"Answer: {answer}")
print(f"Cost: ${stats['estimated_cost']:.4f}")

# Get statistics
stats = rag.get_statistics()
print(f"Total files: {stats['total_files']}, Total chunks: {stats['total_chunks']}")

# Clear database
rag.clear_database()
```

## Cost

- **Local Components**: FREE (embeddings, storage)
- **Claude API** (pay-as-you-go):
  - Sonnet 4.5: ~$0.0016-0.0069 per query (most balanced)
  - Opus 4.0: ~$0.008-0.035 per query (highest quality)
  - Haiku 3.5: ~$0.0001-0.0006 per query (fastest/cheapest)

The system automatically tracks costs with 4-decimal precision and provides daily/monthly projections.

## Getting a Claude API Key

1. Go to https://console.anthropic.com
2. Create an account (separate from Claude.ai)
3. Add credits (minimum $5)
4. Generate API key in Settings

## Project Structure
```
RAG/
├── rag_simple.py        # Core RAG system (SimpleRAGSystem)
├── app.py               # Streamlit web interface (5 tabs)
├── web_app.py           # Simplified web interface
├── cli.py               # Command-line interface
├── cost_tracker.py      # API cost monitoring
├── utils.py             # Utility functions
├── requirements.txt     # Python dependencies
├── setup.sh             # Setup script
├── .env.example         # Environment template
├── CLAUDE.md            # Developer documentation for Claude Code
├── vectors/             # Persisted embeddings and metadata
├── logs/                # Cost tracking logs
├── exports/             # Exported query results
└── uploaded_pdfs/       # Temporary PDF storage
```

## How It Works

1. **Document Processing**: PDFs are split into 500-character chunks with 50-character overlap
2. **Embeddings**: Each chunk is converted to a vector using `all-MiniLM-L6-v2` (runs locally on M1/M2)
3. **Storage**: Vectors and metadata are stored in memory and persisted to `./vectors/`
4. **Query**: Your question is embedded, top-k similar chunks are retrieved via cosine similarity
5. **Answer**: Retrieved context is sent to Claude AI to generate an intelligent response
6. **Tracking**: All API calls are logged with token counts and costs

## Available Claude Models

Set your preferred model in `.env` using the `CLAUDE_MODEL` variable:

- `claude-sonnet-4-5-20250929` - Latest Sonnet (recommended, best balance)
- `claude-opus-4-1-20250805` - Opus 4.0 (highest quality)
- `claude-3-5-haiku-20241022` - Haiku 3.5 (fastest, cheapest)

The system automatically detects the model and calculates costs accordingly.

## Tips

- **Start Small**: Test with a few PDFs first to understand costs
- **Monitor Costs**: Check the Analytics tab to track spending
- **Batch Processing**: Use the web UI or `cli.py batch` to process multiple PDFs at once
- **Clear Database**: Use the "Manage Data" tab to reset and start fresh
- **Export Results**: Save query results as Markdown for reference
- **Model Selection**: Use Haiku for simple questions, Sonnet for most tasks, Opus for complex analysis

## Troubleshooting

- **"Already processed" messages**: Files are tracked by name. Use "Clear Database" or set `force=True` to reprocess
- **Costs showing $0.00**: Costs are very small and display with 4 decimals (e.g., $0.0017)
- **MPS not available**: System will fallback to CPU, embeddings will be slightly slower
- **Import errors**: Make sure to activate the virtual environment: `source rag_env/bin/activate`

## For Developers

If you're using Claude Code to work on this project, check [`CLAUDE.md`](CLAUDE.md) for detailed architecture and development documentation.

## License

MIT License

## Contributing

Pull requests are welcome! For major changes, please open an issue first.
