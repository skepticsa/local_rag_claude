# app.py
import streamlit as st
import os
from rag_simple import LocalRAGSystem

st.title("Local RAG System with Claude")

# Initialize system
@st.cache_resource
def init_rag():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        st.error("Please set ANTHROPIC_API_KEY environment variable")
        return None
    return LocalRAGSystem(claude_api_key=api_key)

rag = init_rag()

# File upload
uploaded_files = st.file_uploader(
    "Upload PDF files", 
    type=['pdf'], 
    accept_multiple_files=True
)

if uploaded_files and rag:
    for uploaded_file in uploaded_files:
        # Save uploaded file temporarily
        with open(f"temp_{uploaded_file.name}", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Process the PDF
        with st.spinner(f"Processing {uploaded_file.name}..."):
            rag.process_pdf(f"temp_{uploaded_file.name}")
        
        # Clean up
        os.remove(f"temp_{uploaded_file.name}")
    
    st.success("PDFs processed successfully!")

# Query interface
if rag:
    question = st.text_input("Ask a question about your documents:")
    
    if question:
        with st.spinner("Searching and generating answer..."):
            answer, sources = rag.query(question)
        
        st.write("### Answer:")
        st.write(answer)
        
        st.write("### Sources:")
        for source in sources:
            st.write(f"- {source['source']}, Page {source['page']}")

            