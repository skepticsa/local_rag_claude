# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a local Retrieval-Augmented Generation (RAG) system optimized for macOS (Apple Silicon M1/M2). It combines local vector embeddings with Claude AI for intelligent document Q&A. The system uses a simplified in-memory vector storage approach rather than ChromaDB.

## Key Commands

### Environment Setup
```bash
# First-time setup
chmod +x setup.sh
./setup.sh

# Activate virtual environment
source rag_env/bin/activate
```

### Running the Application
```bash
# Web interface (Streamlit)
streamlit run app.py

# CLI commands
python cli.py process /path/to/document.pdf     # Process single PDF
python cli.py batch /path/to/pdf/directory      # Process directory
python cli.py query "Your question here"        # Query documents
python cli.py stats                             # View statistics
```

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Note: No test suite currently exists in this codebase
```

## Architecture

### Core Components

**rag_simple.py** (`SimpleRAGSystem` class)
- The main RAG implementation using in-memory storage
- Uses PyTorch tensors for vector storage and cosine similarity search
- Persists data to disk as JSON (documents/metadata) and PyTorch tensors (embeddings)
- Key methods:
  - `process_pdf(pdf_path, force=False)`: Extracts text from PDFs, chunks it, generates embeddings. Set `force=True` to reprocess already-processed files
  - `process_directory(directory)`: Batch processes all PDFs in a directory, returns detailed results including file list
  - `query(question, n_results=5)`: Performs semantic search and generates answers via Claude API. Reads model from `CLAUDE_MODEL` env var
  - `get_statistics()`: Returns comprehensive stats including total_files, total_chunks, storage_size_mb, and files array
  - `clear_database()`: Clears all in-memory data and deletes persisted files
  - `_save_data()/_load_data()`: Persist/restore state from `./vectors/` directory (uses `weights_only=False` for PyTorch 2.6+ compatibility)

**app.py** (Streamlit Web UI)
- Full-featured web interface with 5 tabs: Upload, Query, Analytics, Manage Data, Settings
- Uses Streamlit session state to maintain RAG system instance and query results (auto-refreshes sidebar costs)
- Integrates with `CostTracker` for real-time cost monitoring
- Default batch processing directory: `./uploaded_pdfs`
- Uses modern Streamlit API (`width='stretch'` instead of deprecated `use_container_width`)
- Note: There are two `app.py` files - the larger one (app.py) is the production version

**cli.py** (Command-line Interface)
- Click-based CLI for headless operations
- Imports `SimpleRAGSystem` from `rag_simple.py` (aliased as `M1OptimizedRAGSystem`)
- Commands: process, batch, query, stats

**cost_tracker.py** (`CostTracker` class)
- Tracks Claude API usage and costs per query
- Stores data in `./logs/cost_tracking.json`
- Provides cost projections, daily/monthly statistics, and alerts
- Supports multiple Claude model pricing tiers (detects sonnet/opus/haiku in model name)
- Uses 4 decimal place precision for cost display (prevents small costs showing as $0.00)
- Pricing:
  - Sonnet (3.5, 4.0, 4.5): $0.003/$0.015 per 1K tokens (input/output)
  - Opus (3.0, 4.0): $0.015/$0.075 per 1K tokens (input/output)
  - Haiku (3.0, 3.5): $0.00025/$0.00125 per 1K tokens (input/output)

**utils.py**
- Utility functions for file formatting, export, visualization
- `get_system_info()`: Detects M1/M2 chip and Metal Performance Shaders availability
- `create_cost_visualization()`: Generates Plotly charts for cost tracking

### Data Flow

1. **Document Processing**: PDF → PyPDF2 text extraction → chunk into 500-char segments with 50-char overlap → SentenceTransformer embeddings → store in-memory + persist to disk
2. **Query Flow**: Question → embed with SentenceTransformer → cosine similarity search → retrieve top-k chunks → construct prompt with context → Claude API → answer + sources + cost stats
3. **Storage**:
   - Vector data: `./vectors/embeddings.pt` (PyTorch tensor file)
   - Metadata: `./vectors/data.json` (documents array, metadata array)
   - Cost logs: `./logs/cost_tracking.json`

### Apple Silicon Optimization

The system detects and uses Metal Performance Shaders (MPS) when available:
```python
if torch.backends.mps.is_available():
    self.device = "mps"  # Uses Apple's Neural Engine
```

Embedding model (`all-MiniLM-L6-v2`) runs locally on the Mac. Only Claude API calls incur costs.

## Environment Variables

Required in `.env` file (use `.env.example` as template):
```
ANTHROPIC_API_KEY=sk-...           # Required for Claude API
CLAUDE_MODEL=claude-sonnet-4-5-20250929  # Optional, defaults handled in code
MAX_TOKENS=2000                    # Optional
TEMPERATURE=0.7                    # Optional
TOKENIZERS_PARALLELISM=true        # Suppresses warnings
```

## Important Notes

- **Two App Files**: There are two different app implementations - `app.py` (full Streamlit app) and `web_app.py` (simplified version). The main app is `app.py`.
- **No ChromaDB**: Despite references in comments/README, the CLI uses `rag_simple.py` which implements simple in-memory vector storage, not ChromaDB.
- **Persistence**: The SimpleRAGSystem persists data between sessions via `./vectors/data.json` and `./vectors/embeddings.pt`.
- **Cost Tracking**:
  - Every Claude API call is automatically logged via `CostTracker.log_query()` in the web app
  - Costs are calculated dynamically based on the actual model used (sonnet/opus/haiku detection)
  - Both `rag_simple.py` query method and `cost_tracker.py` use identical pricing logic
  - Sidebar costs auto-update after each query via session state
- **Chunking Strategy**: Fixed 500-character chunks with 50-character overlap. Page numbers are tracked in metadata.
- **Search**: Currently uses cosine similarity search only (basic semantic search, no hybrid BM25 or reranking).
- **Model Configuration**: Claude model is configured via `CLAUDE_MODEL` environment variable in `.env` file. The system reads this at query time, allowing dynamic model switching without code changes.
- **Clear Database**: The `clear_database()` method properly removes all in-memory data and deletes persisted files, then reinitializes the system.

## File Structure
```
.
├── rag_simple.py       # Core RAG engine (SimpleRAGSystem)
├── app.py              # Main Streamlit web interface
├── web_app.py          # Simplified web interface
├── cli.py              # Command-line interface
├── cost_tracker.py     # API cost monitoring
├── utils.py            # Utility functions
├── setup.sh            # Environment setup script
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── vectors/            # Persisted embeddings and metadata
├── logs/               # Cost tracking logs
├── exports/            # Exported query results
└── uploaded_pdfs/      # Temporary PDF storage
```

## Common Gotchas

1. **Model Configuration**: Ensure `CLAUDE_MODEL` is set in your `.env` file. If not set, defaults to `claude-sonnet-4-5-20250929`. Update the `.env` file to switch models without code changes.
2. **Virtual Environment**: Always activate `rag_env` before running commands.
3. **API Key**: The system gracefully handles missing API keys but won't function without one.
4. **Duplicate Processing**: PDFs are tracked by filename only - processing the same filename from different paths will skip reprocessing. Use `force=True` parameter to reprocess.
5. **Memory**: All embeddings are held in memory, so very large document collections may require architecture changes.
6. **PyTorch Version**: PyTorch 2.6+ requires `weights_only=False` when loading embeddings (already implemented in the code).
7. **Cost Display**: Small query costs (< $0.01) display with 4 decimal places to prevent showing as $0.00.
8. **Model Pricing**: The system automatically detects model type (sonnet/opus/haiku) for correct pricing - no need to update pricing logic when using different models.

## Recent Fixes & Improvements

- ✅ Fixed cost calculation to recognize all Claude model variants (4.0, 4.5, etc.)
- ✅ Fixed sidebar cost tracking to auto-update after queries
- ✅ Added `clear_database()` method with proper cleanup and reinitialization
- ✅ Fixed `process_directory()` to return detailed file information
- ✅ Fixed `get_statistics()` to include all required fields
- ✅ Updated to modern Streamlit API (deprecated warnings resolved)
- ✅ Dynamic cost calculation based on actual model used
- ✅ Query results persist in session state for better UX
