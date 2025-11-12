#!/usr/bin/env python3
import click
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the RAG system with in-memory vector storage
from rag_simple import SimpleRAGSystem as M1OptimizedRAGSystem

@click.group()
def cli():
    """RAG System CLI"""
    pass

@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
@click.option('--force', is_flag=True, help='Force reprocess')
def process(pdf_path, force):
    """Process a PDF file"""
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not set in .env")
        return
    
    rag = M1OptimizedRAGSystem(claude_api_key=api_key)
    
    print(f"📄 Processing: {pdf_path}")
    
    result = rag.process_pdf(pdf_path, force=force)
    
    if result['status'] == 'success':
        print(f"✅ Success: {result['chunks']} chunks processed")
    elif result['status'] == 'skipped':
        print("⏭️ Skipped: Already processed")
    else:
        print(f"❌ Failed: {result.get('reason', 'Unknown error')}")

@cli.command()
@click.argument('directory', type=click.Path(exists=True))
def batch(directory):
    """Process all PDFs in a directory"""
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not set in .env")
        return
    
    rag = M1OptimizedRAGSystem(claude_api_key=api_key)
    
    print(f"📁 Processing directory: {directory}")
    
    results = rag.process_directory(directory)
    
    print(f"\n📊 Results:")
    print(f"  ✅ Processed: {results['processed']}")
    print(f"  ⏭️ Skipped: {results['skipped']}")
    print(f"  ❌ Failed: {results['failed']}")

@cli.command()
@click.argument('question')
@click.option('--n-results', default=5, help='Number of results')
def query(question, n_results):
    """Query the RAG system"""
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not set in .env")
        return
    
    rag = M1OptimizedRAGSystem(claude_api_key=api_key)
    
    print(f"❓ Question: {question}\n")
    
    answer, sources, stats = rag.query(question, n_results=n_results)
    
    print("💡 Answer:")
    print(answer)
    
    if sources:
        print("\n📚 Sources:")
        for i, source in enumerate(sources, 1):
            print(f"  {i}. {source['source']} - Page {source['page']}")
    
    if stats:
        print(f"\n💰 Cost: ${stats['estimated_cost']:.4f}")

@cli.command()
def stats():
    """Show statistics"""
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not set in .env")
        return
    
    rag = M1OptimizedRAGSystem(claude_api_key=api_key)
    
    stats = rag.get_statistics()
    
    print("📊 System Statistics:")
    print(f"  Total chunks: {stats['total_chunks']}")

if __name__ == '__main__':
    cli()