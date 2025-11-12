# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a local Retrieval-Augmented Generation (RAG) system optimized for macOS (Apple Silicon M1/M2). It supports **hybrid LLM operation**: you can use either Claude API (fast, costs money) or local LLMs via Ollama (slower, completely free and private). The system uses a lightweight in-memory vector storage with PyTorch tensors for optimal M1/M2 performance.

**Key Feature**: Embeddings always run locally (free), and you choose the LLM provider for answer generation.

## Key Commands

### Environment Setup
```bash
# First-time setup
chmod +x setup.sh
./setup.sh

# Activate virtual environment
source rag_env/bin/activate

# For Ollama (local LLM) - install and start
brew install ollama
ollama serve  # Run in separate terminal

# Download model based on your RAM:
# For 32GB RAM:
ollama pull llama3.1:8b  # Fast and efficient (~8GB RAM)

# For 64GB+ RAM only:
# ollama pull llama3.1:70b-instruct-q4_K_M  # Best quality (~42GB RAM)
# ollama pull llama3.2:90b  # Very high quality (~50GB RAM)
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
- **Hybrid LLM Support**: Supports both Claude API and Ollama (local LLMs)
- Uses PyTorch tensors for vector storage and cosine similarity search
- Persists data to disk as JSON (documents/metadata) and PyTorch tensors (embeddings)
- Key initialization parameters:
  - `llm_provider`: "claude" or "ollama" (reads from `LLM_PROVIDER` env var)
  - `claude_api_key`: Required if using Claude
  - `ollama_model`: Model name for Ollama (e.g., "llama3.1:70b-instruct-q4_K_M")
  - `ollama_base_url`: Ollama server URL (default: "http://localhost:11434")
- Key methods:
  - `process_pdf(pdf_path, force=False)`: Extracts text from PDFs, chunks it, generates embeddings. Set `force=True` to reprocess already-processed files
  - `process_directory(directory)`: Batch processes all PDFs in a directory, returns detailed results including file list
  - `query(question, n_results=5)`: Performs semantic search and generates answers via configured LLM provider
  - `_query_claude(prompt, sources)`: Claude API query implementation (returns answer, sources, stats with cost)
  - `_query_ollama(prompt, sources)`: Ollama query implementation (returns answer, sources, stats with cost=0.0)
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
- Tracks LLM usage: costs for Claude API, token counts for local LLMs
- Stores data in `./logs/cost_tracking.json`
- Provides cost projections, daily/monthly statistics, and alerts
- **Hybrid Support**: Accepts `provider` parameter ("claude" or "ollama")
  - Claude API: Calculates costs based on model pricing
  - Ollama/Local LLMs: Sets cost to $0.00, tracks tokens only
- Supports multiple Claude model pricing tiers (detects sonnet/opus/haiku in model name)
- Auto-detects local LLMs by provider or model name (llama, qwen, mistral)
- Uses 4 decimal place precision for cost display (prevents small costs showing as $0.00)
- Claude API Pricing:
  - Sonnet (3.5, 4.0, 4.5): $0.003/$0.015 per 1K tokens (input/output)
  - Opus (3.0, 4.0): $0.015/$0.075 per 1K tokens (input/output)
  - Haiku (3.0, 3.5): $0.00025/$0.00125 per 1K tokens (input/output)
- Local LLM Pricing: $0.00 (completely free!)

**utils.py**
- Utility functions for file formatting, export, visualization
- `get_system_info()`: Detects M1/M2 chip and Metal Performance Shaders availability
- `create_cost_visualization()`: Generates Plotly charts for cost tracking

### Data Flow

1. **Document Processing**: PDF → PyPDF2 text extraction → chunk into 500-char segments with 50-char overlap → SentenceTransformer embeddings (always local) → store in-memory + persist to disk
2. **Query Flow**:
   - Question → embed with SentenceTransformer (local) → cosine similarity search → retrieve top-k chunks → construct prompt with context
   - **Claude API Path**: prompt → Anthropic API → answer + sources + cost stats
   - **Ollama Path**: prompt → local Ollama server → answer + sources + stats (cost=0.0)
3. **Storage**:
   - Vector data: `./vectors/embeddings.pt` (PyTorch tensor file)
   - Metadata: `./vectors/data.json` (documents array, metadata array)
   - Cost/token logs: `./logs/cost_tracking.json` (works for both providers)

### Apple Silicon Optimization

The system detects and uses Metal Performance Shaders (MPS) when available for embeddings:
```python
if torch.backends.mps.is_available():
    self.device = "mps"  # Uses Apple's Neural Engine for embeddings
```

**Important**:
- Embedding model (`all-MiniLM-L6-v2`) runs locally on the Mac using MPS acceleration
- Claude API: Inference happens in the cloud (costs money, fast)
- Ollama: Inference happens locally on CPU/GPU (free, slower, requires RAM)
  - Llama 3.1 70B requires ~32GB RAM, uses significant CPU/GPU resources
  - For M1/M2 Macs: Ollama uses Metal for acceleration automatically

## Environment Variables

Required in `.env` file (use `.env.example` as template):

### Core Configuration
```bash
LLM_PROVIDER=claude                # "claude" or "ollama" (choose your provider)
MAX_TOKENS=2000                    # Optional
TEMPERATURE=0.7                    # Optional
TOKENIZERS_PARALLELISM=true        # Suppresses warnings
```

### Claude API Configuration (if LLM_PROVIDER=claude)
```bash
ANTHROPIC_API_KEY=sk-ant-api03-... # Required for Claude
CLAUDE_MODEL=claude-sonnet-4-5-20250929  # Available models:
                                   # - claude-sonnet-4-5-20250929
                                   # - claude-opus-4-1-20250805
                                   # - claude-3-5-haiku-20241022
```

### Ollama Configuration (if LLM_PROVIDER=ollama)
```bash
OLLAMA_MODEL=llama3.1:8b  # Recommended models by RAM:
                          # For 32GB RAM:
                          # - llama3.1:8b (fast, ~8GB RAM)
                          # - mistral:7b (alternative, ~7GB RAM)
                          # For 64GB+ RAM only:
                          # - llama3.1:70b-instruct-q4_K_M (~42GB RAM)
                          # - llama3.2:90b (~50GB RAM)
OLLAMA_BASE_URL=http://localhost:11434     # Default Ollama server URL
```

**Switching providers**: Change `LLM_PROVIDER` in `.env` and restart the application. That's it!

## Important Notes

- **Hybrid LLM Architecture**:
  - The system supports both Claude API and Ollama (local LLMs)
  - Provider selection is via `LLM_PROVIDER` env var ("claude" or "ollama")
  - Embeddings always run locally (free), only the answer generation uses the selected provider
  - All query methods return the same format: (answer, sources, stats) regardless of provider
  - Stats dictionary includes 'provider' field to identify which LLM was used
- **Two App Files**: There are two different app implementations - `app.py` (full Streamlit app) and `web_app.py` (simplified version). The main app is `app.py`.
- **In-Memory Vector Storage**: The system uses a lightweight in-memory approach with PyTorch tensors for vector storage and cosine similarity search. This is optimized for M1/M2 and works well for up to ~10,000 documents.
- **Persistence**: The SimpleRAGSystem persists data between sessions via `./vectors/data.json` and `./vectors/embeddings.pt`.
- **Cost/Token Tracking**:
  - Every query (Claude or Ollama) is automatically logged via `CostTracker.log_query()` with provider info
  - Claude API: Costs are calculated dynamically based on the actual model used (sonnet/opus/haiku detection)
  - Ollama: Cost is always $0.00, but token counts are tracked for statistics
  - Both `rag_simple.py` and `cost_tracker.py` use consistent provider-aware logic
  - Sidebar auto-updates after each query via session state
- **Chunking Strategy**: Fixed 500-character chunks with 50-character overlap. Page numbers are tracked in metadata.
- **Search**: Currently uses cosine similarity search only (basic semantic search, no hybrid BM25 or reranking).
- **Model Configuration**: Models are configured via environment variables in `.env` file, allowing switching without code changes.
- **Clear Database**: The `clear_database()` method properly removes all in-memory data and deletes persisted files, then reinitializes the system.

## File Structure
```
.
├── rag_simple.py       # Core RAG engine with in-memory vector storage
├── app.py              # Main Streamlit web interface (5 tabs)
├── web_app.py          # Simplified web interface
├── cli.py              # Command-line interface
├── cost_tracker.py     # LLM usage and cost monitoring
├── utils.py            # Utility functions
├── setup.sh            # Environment setup script
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── .gitignore          # Git ignore rules (excludes sensitive files)
├── LICENSE             # MIT License
├── README.md           # User documentation
├── CLAUDE.md           # Developer documentation (this file)
├── vectors/            # Persisted embeddings and metadata (gitignored)
├── logs/               # Cost tracking logs (gitignored)
├── exports/            # Exported query results (gitignored)
└── uploaded_pdfs/      # Temporary PDF storage (gitignored)
```

## Common Gotchas

### General
1. **Virtual Environment**: Always activate `rag_env` before running commands.
2. **Duplicate Processing**: PDFs are tracked by filename only - processing the same filename from different paths will skip reprocessing. Use `force=True` parameter to reprocess.
3. **Memory**: All embeddings are held in memory, so very large document collections may require architecture changes.
4. **PyTorch Version**: PyTorch 2.6+ requires `weights_only=False` when loading embeddings (already implemented in the code).

### Claude API
5. **Model Configuration**: Ensure `CLAUDE_MODEL` is set in your `.env` file. If not set, defaults to `claude-sonnet-4-5-20250929`.
6. **API Key**: The system gracefully handles missing API keys but won't function without one for Claude provider.
7. **Cost Display**: Small query costs (< $0.01) display with 4 decimal places to prevent showing as $0.00.
8. **Model Pricing**: The system automatically detects model type (sonnet/opus/haiku) for correct pricing - no need to update pricing logic when using different models.

### Ollama (Local LLM)
9. **Ollama Not Running**: Most common issue! Ensure `ollama serve` is running in a separate terminal before starting the app. Connection errors mean Ollama isn't running.
10. **Model Not Downloaded**: Must run `ollama pull <model-name>` before using. The app will fail if the model isn't available locally.
11. **Slow First Query**: Ollama loads the model into memory on first use (10-30 seconds). Subsequent queries are faster.
12. **RAM Requirements** (CRITICAL - models will be extremely slow if swapping to disk):
    - 32GB System RAM: Use `llama3.1:8b` (~8GB) ONLY
    - 64GB+ System RAM: Can use `llama3.1:70b` (~42GB) or `llama3.2:90b` (~50GB)
    - 16GB System RAM: Use `llama3.1:8b` only
    - If queries take many minutes, your model is too large and swapping to disk - switch to `llama3.1:8b` immediately
13. **Import Errors**: If `ollama` module not found, ensure `ollama>=0.1.0` is in requirements.txt and installed in the virtual environment.
14. **Provider Mismatch**: If you set `LLM_PROVIDER=ollama` but Ollama isn't installed, the system will error on initialization. Install Ollama first or switch to Claude.
15. **Response Quality**: Local models (even 70B) are generally less capable than Claude Sonnet/Opus. Set expectations accordingly - they're free but not state-of-the-art.

## Recent Fixes & Improvements

### Hybrid LLM System (Latest)
- ✅ **Hybrid LLM Support**: Added support for both Claude API and Ollama (local LLMs)
- ✅ **Provider Selection**: Configure via `LLM_PROVIDER` env var ("claude" or "ollama")
- ✅ **Ollama Integration**: Full support for local models (Llama 3.1, Qwen, etc.)
- ✅ **Cost Tracker Updates**: Now tracks both API costs and local LLM token usage
- ✅ **Provider-Aware Logic**: All components handle both providers consistently
- ✅ **Documentation**: Updated README.md and CLAUDE.md with hybrid setup instructions

### Previous Improvements
- ✅ Fixed cost calculation to recognize all Claude model variants (4.0, 4.5, etc.)
- ✅ Fixed sidebar cost tracking to auto-update after queries
- ✅ Added `clear_database()` method with proper cleanup and reinitialization
- ✅ Fixed `process_directory()` to return detailed file information
- ✅ Fixed `get_statistics()` to include all required fields
- ✅ Updated to modern Streamlit API (deprecated warnings resolved)
- ✅ Dynamic cost calculation based on actual model used
- ✅ Query results persist in session state for better UX
