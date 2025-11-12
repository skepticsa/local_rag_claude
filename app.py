import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
from datetime import datetime

from rag_simple import M1OptimizedRAGSystem
from cost_tracker import CostTracker
from utils import (
    format_file_size, 
    export_results_to_markdown,
    create_cost_visualization,
    get_system_info
)

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="RAG System - M1 Pro Optimized",
    page_icon="🚀",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.stAlert {
    background-color: #f0f2f6;
    border-radius: 5px;
}
.metric-card {
    background-color: #ffffff;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'rag_system' not in st.session_state:
    llm_provider = os.getenv("LLM_PROVIDER", "claude").lower()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:70b-instruct-q4_K_M")

    try:
        if llm_provider == "ollama":
            st.session_state.rag_system = M1OptimizedRAGSystem(
                llm_provider="ollama",
                ollama_model=ollama_model
            )
            st.session_state.cost_tracker = CostTracker()
        elif api_key:
            st.session_state.rag_system = M1OptimizedRAGSystem(
                claude_api_key=api_key,
                llm_provider="claude"
            )
            st.session_state.cost_tracker = CostTracker()
        else:
            st.session_state.rag_system = None
            st.session_state.cost_tracker = None
    except Exception as e:
        st.error(f"Failed to initialize RAG system: {e}")
        st.session_state.rag_system = None
        st.session_state.cost_tracker = None

# Sidebar
with st.sidebar:
    st.title("🚀 RAG System Control")

    # LLM Provider Info
    st.markdown("### 🤖 LLM Provider")
    if st.session_state.rag_system:
        provider = st.session_state.rag_system.llm_provider
        if provider == "claude":
            st.info("📡 Using Claude API")
            model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
            st.text(f"Model: {model}")
        elif provider == "ollama":
            st.success("🖥️ Using Local LLM (Ollama)")
            st.text(f"Model: {st.session_state.rag_system.ollama_model}")
            st.caption("✅ Free & Private!")
    else:
        st.warning("No LLM configured")

    # API Key setup (only if using Claude)
    llm_provider = os.getenv("LLM_PROVIDER", "claude").lower()
    if llm_provider == "claude":
        st.markdown("### 🔑 Claude API Key")
        if not os.getenv("ANTHROPIC_API_KEY"):
            api_key = st.text_input("Claude API Key", type="password")
            if st.button("Set API Key"):
                if api_key:
                    os.environ["ANTHROPIC_API_KEY"] = api_key
                    st.session_state.rag_system = M1OptimizedRAGSystem(
                        claude_api_key=api_key,
                        llm_provider="claude"
                    )
                    st.session_state.cost_tracker = CostTracker()
                    st.success("API Key set successfully!")
                    st.rerun()
        else:
            st.success("✅ API Key configured")

    # System info
    st.markdown("### 💻 System Info")
    sys_info = get_system_info()
    st.text(f"CPU: {sys_info.get('cpu', 'Unknown')}")
    st.text(f"Memory: {sys_info.get('memory_gb', 'Unknown')} GB")
    st.text(f"MPS: {'✅' if sys_info.get('mps_available') else '❌'}")
    
    # Statistics
    if st.session_state.rag_system:
        st.markdown("### 📊 Database Statistics")
        stats = st.session_state.rag_system.get_statistics()
        st.metric("Total PDFs", stats['total_files'])
        st.metric("Total Chunks", stats['total_chunks'])
        st.metric("Storage Size", f"{stats['storage_size_mb']} MB")
        st.metric("Total Queries", stats['total_queries'])
    
    # Cost tracking (only for Claude API)
    if st.session_state.cost_tracker and st.session_state.rag_system:
        if st.session_state.rag_system.llm_provider == "claude":
            st.markdown("### 💰 Cost Tracking")
            cost_stats = st.session_state.cost_tracker.get_statistics('today')
            st.metric("Today's Cost", f"${cost_stats['total_cost']}")

            month_stats = st.session_state.cost_tracker.get_statistics('this_month')
            st.metric("Month's Cost", f"${month_stats['total_cost']}")

            if month_stats.get('projected_monthly_cost'):
                st.metric(
                    "Projected Monthly",
                    f"${month_stats['projected_monthly_cost']}"
                )

            # Alerts
            alerts = st.session_state.cost_tracker.get_cost_alerts()
            for alert in alerts:
                st.warning(alert)
        else:
            st.markdown("### 💰 Cost")
            st.success("✅ Free (Local LLM)")
            st.caption("No API costs when using Ollama!")

# Main content
st.title("🤖 Local RAG System - M1 Pro Optimized")
if st.session_state.rag_system:
    provider = st.session_state.rag_system.llm_provider
    if provider == "ollama":
        st.markdown("### Powered by Local LLM (Ollama) | 100% Free & Private")
    else:
        st.markdown("### Powered by Claude AI | M1 Optimized")

# Check if system is initialized
if not st.session_state.rag_system:
    st.error("Please set your Claude API key in the sidebar")
    st.stop()

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📁 Upload & Process",
    "🔍 Query",
    "📊 Analytics",
    "💾 Manage Data",
    "⚙️ Settings"
])

# Tab 1: Upload & Process
with tab1:
    st.header("Upload and Process PDFs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # File uploader
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=['pdf'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            if st.button("🔄 Process PDFs", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, uploaded_file in enumerate(uploaded_files):
                    # Save temporarily
                    temp_path = Path("uploaded_pdfs") / uploaded_file.name
                    temp_path.parent.mkdir(exist_ok=True)
                    
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Process
                    status_text.text(f"Processing {uploaded_file.name}...")
                    result = st.session_state.rag_system.process_pdf(str(temp_path))
                    
                    if result['status'] == 'success':
                        st.success(f"✅ {uploaded_file.name}: {result['chunks']} chunks")
                    elif result['status'] == 'skipped':
                        st.info(f"⏭️ {uploaded_file.name}: Already processed")
                    else:
                        st.error(f"❌ {uploaded_file.name}: Failed")
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                status_text.text("Processing complete!")
    
    with col2:
        # Batch processing
        st.subheader("Batch Process Directory")
        
        dir_path = st.text_input("Directory path", value="./uploaded_pdfs")
        
        if st.button("📁 Process Directory"):
            if dir_path and Path(dir_path).exists():
                with st.spinner("Processing directory..."):
                    results = st.session_state.rag_system.process_directory(dir_path)
                    
                    st.success(
                        f"Processed: {results['processed']} | "
                        f"Skipped: {results['skipped']} | "
                        f"Failed: {results['failed']}"
                    )
                    
                    # Show details
                    if results['files']:
                        df = pd.DataFrame(results['files'])
                        st.dataframe(df)
            else:
                st.error("Invalid directory path")

# Tab 2: Query
with tab2:
    st.header("Query Your Documents")
    
    # Query settings
    n_results = st.slider("Number of results", 1, 10, 5)
    
    # Query input
    question = st.text_area(
        "Ask a question about your documents:",
        height=100,
        placeholder="What are the key findings discussed in the documents?"
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        search_button = st.button("🔍 Search", type="primary")
    with col2:
        if st.button("Clear Results"):
            st.session_state.last_query_results = None
            st.rerun()

    if search_button:
        if question:
            with st.spinner("Searching and generating answer..."):
                answer, sources, stats = st.session_state.rag_system.query(
                    question,
                    n_results=n_results
                )

                # Log to cost tracker FIRST
                if stats and st.session_state.cost_tracker:
                    st.session_state.cost_tracker.log_query(
                        question,
                        stats['input_tokens'],
                        stats['output_tokens'],
                        stats['model'],
                        stats['provider']
                    )

                # Store results in session state
                st.session_state.last_query_results = {
                    'question': question,
                    'answer': answer,
                    'sources': sources,
                    'stats': stats
                }

    # Display results if they exist in session state
    if 'last_query_results' in st.session_state and st.session_state.last_query_results:
        results = st.session_state.last_query_results

        # Display answer
        st.markdown("### 💡 Answer")
        st.markdown(results['answer'])

        # Display sources
        st.markdown("### 📚 Sources")
        for i, source in enumerate(results['sources'], 1):
            st.caption(
                f"{i}. {source['source']} - Page {source['page']} "
                f"(Language: {source.get('language', 'en')})"
            )

        # Display stats
        if results['stats']:
            st.markdown("### 📊 Query Statistics")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Input Tokens", results['stats']['input_tokens'])
            with col2:
                st.metric("Output Tokens", results['stats']['output_tokens'])
            with col3:
                st.metric("Total Tokens", results['stats']['total_tokens'])
            with col4:
                st.metric("Cost", f"${results['stats']['estimated_cost']:.4f}")

        # Export options
        st.markdown("### 💾 Export Results")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Export as Markdown"):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filepath = f"exports/query_{timestamp}.md"
                Path("exports").mkdir(exist_ok=True)
                export_results_to_markdown(
                    results['question'], results['answer'], results['sources'], filepath
                )
                st.success(f"Exported to {filepath}")

        with col2:
            if st.button("Copy to Clipboard"):
                result_text = f"Question: {results['question']}\n\nAnswer: {results['answer']}"
                st.code(result_text)

# Tab 3: Analytics
with tab3:
    st.header("Analytics Dashboard")
    
    if st.session_state.cost_tracker:
        # Cost visualization
        st.subheader("💰 Cost Analysis")
        
        days = st.slider("Days to display", 7, 90, 30)
        chart_data = st.session_state.cost_tracker.get_cost_chart_data(days)
        
        if chart_data:
            fig = create_cost_visualization(chart_data)
            st.plotly_chart(fig, width='stretch')
        
        # Statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Today")
            today_stats = st.session_state.cost_tracker.get_statistics('today')
            st.metric("Cost", f"${today_stats['total_cost']}")
            st.metric("Queries", today_stats['total_queries'])
            st.metric("Tokens", today_stats['total_tokens'])
        
        with col2:
            st.subheader("This Month")
            month_stats = st.session_state.cost_tracker.get_statistics('this_month')
            st.metric("Cost", f"${month_stats['total_cost']}")
            st.metric("Queries", month_stats['total_queries'])
            st.metric("Avg Cost/Query", f"${month_stats['average_cost_per_query']}")
        
        with col3:
            st.subheader("All Time")
            all_stats = st.session_state.cost_tracker.get_statistics('all')
            st.metric("Total Cost", f"${all_stats['total_cost']}")
            st.metric("Total Queries", all_stats['total_queries'])
            st.metric("Avg Cost/Query", f"${all_stats['average_cost_per_query']}")
    
    # Document statistics
    st.subheader("📄 Document Statistics")
    
    if st.session_state.rag_system:
        stats = st.session_state.rag_system.get_statistics()
        
        if stats['files']:
            df = pd.DataFrame(stats['files'])
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(
                    df,
                    x='name',
                    y='chunks',
                    title='Chunks per Document'
                )
                st.plotly_chart(fig, width='stretch')

            with col2:
                fig = px.pie(
                    df,
                    values='size_mb',
                    names='name',
                    title='Document Size Distribution'
                )
                st.plotly_chart(fig, width='stretch')
            
            # Table
            st.subheader("Document Details")
            st.dataframe(df)

# Tab 4: Manage Data
with tab4:
    st.header("Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🗑️ Clear Database")

        st.warning(
            "This will permanently delete all processed documents and embeddings."
        )

        # Show checkbox first
        confirm_clear = st.checkbox("I understand this is permanent")

        # Button is only enabled when checkbox is checked
        if st.button("Clear All Data", type="secondary", disabled=not confirm_clear):
            st.session_state.rag_system.clear_database()

            # Reinitialize the RAG system to reflect the cleared state
            llm_provider = os.getenv("LLM_PROVIDER", "claude").lower()
            if llm_provider == "ollama":
                ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:70b-instruct-q4_K_M")
                st.session_state.rag_system = M1OptimizedRAGSystem(
                    llm_provider="ollama",
                    ollama_model=ollama_model
                )
            else:
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if api_key:
                    st.session_state.rag_system = M1OptimizedRAGSystem(
                        claude_api_key=api_key,
                        llm_provider="claude"
                    )

            st.success("Database cleared successfully!")
            st.rerun()
    
    with col2:
        st.subheader("📥 Export Data")
        
        if st.button("Export Cost Data to CSV"):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"exports/costs_{timestamp}.csv"
            Path("exports").mkdir(exist_ok=True)
            
            if st.session_state.cost_tracker:
                exported = st.session_state.cost_tracker.export_to_csv(filepath)
                st.success(f"Exported to {exported}")
        
        if st.button("Export System Statistics"):
            stats = st.session_state.rag_system.get_statistics()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"exports/stats_{timestamp}.json"
            
            Path("exports").mkdir(exist_ok=True)
            with open(filepath, 'w') as f:
                import json
                json.dump(stats, f, indent=2)
            
            st.success(f"Exported to {filepath}")

# Tab 5: Settings
with tab5:
    st.header("System Settings")
    
    # Model settings
    st.subheader("🤖 Model Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Get current model from environment
        current_model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
        available_models = [
            "claude-sonnet-4-5-20250929",
            "claude-opus-4-1-20250805",
            "claude-3-5-haiku-20241022"
        ]

        # Set default index based on current model
        try:
            default_index = available_models.index(current_model)
        except ValueError:
            default_index = 0

        model = st.selectbox(
            "Claude Model",
            available_models,
            index=default_index
        )

        if st.button("Update Model"):
            os.environ["CLAUDE_MODEL"] = model
            st.success(f"Model updated to {model}")
    
    with col2:
        max_tokens = st.number_input("Max Tokens", 100, 4000, 2000)
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7)
        
        if st.button("Update Parameters"):
            os.environ["MAX_TOKENS"] = str(max_tokens)
            os.environ["TEMPERATURE"] = str(temperature)
            st.success("Parameters updated")
    
    # Embedding settings
    st.subheader("🧠 Embedding Settings")
    
    embedding_models = [
        "all-MiniLM-L6-v2",  # Fastest
        "all-mpnet-base-v2",  # Best quality
        "paraphrase-multilingual-MiniLM-L12-v2"  # Multilingual
    ]
    
    selected_model = st.selectbox(
        "Embedding Model",
        embedding_models,
        index=1
    )
    
    if st.button("Change Embedding Model"):
        st.warning("This will require reprocessing all documents")
        if st.checkbox("I understand"):
            # Reinitialize with new model (preserving current LLM provider)
            llm_provider = os.getenv("LLM_PROVIDER", "claude").lower()
            if llm_provider == "ollama":
                ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:70b-instruct-q4_K_M")
                st.session_state.rag_system = M1OptimizedRAGSystem(
                    llm_provider="ollama",
                    ollama_model=ollama_model
                )
            else:
                st.session_state.rag_system = M1OptimizedRAGSystem(
                    claude_api_key=os.getenv("ANTHROPIC_API_KEY"),
                    llm_provider="claude"
                )
            st.success(f"Model changed to {selected_model}")
            st.rerun()
            