import os
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging

import torch
import PyPDF2
from sentence_transformers import SentenceTransformer
from anthropic import Anthropic
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleRAGSystem:
    """Simplified RAG System without ChromaDB"""
    
    def __init__(self, persist_directory: str = "./vectors", claude_api_key: Optional[str] = None):
        """Initialize the RAG system"""
        
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(exist_ok=True)
        
        # Check for M1 optimization
        if torch.backends.mps.is_available():
            self.device = "mps"
            logger.info("🎯 Using M1 Metal Performance Shaders")
        else:
            self.device = "cpu"
            logger.info("💻 Using CPU")
        
        # Initialize embedding model
        logger.info("Loading embedding model...")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize Claude
        self.anthropic = None
        if claude_api_key:
            self.anthropic = Anthropic(api_key=claude_api_key)
            logger.info("✅ Claude API initialized")
        
        # Simple in-memory storage
        self.documents = []
        self.embeddings = []
        self.metadata = []
        
        # Load saved data if exists
        self.data_file = self.persist_directory / "data.json"
        self.embeddings_file = self.persist_directory / "embeddings.pt"
        self._load_data()
    
    def _load_data(self):
        """Load saved data"""
        if self.data_file.exists() and self.embeddings_file.exists():
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.documents = data['documents']
                self.metadata = data['metadata']

            self.embeddings = torch.load(self.embeddings_file, weights_only=False)
            logger.info(f"Loaded {len(self.documents)} documents from storage")
    
    def _save_data(self):
        """Save data to disk"""
        with open(self.data_file, 'w') as f:
            json.dump({
                'documents': self.documents,
                'metadata': self.metadata
            }, f)

        if len(self.embeddings) > 0:
            torch.save(self.embeddings, self.embeddings_file)
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict]:
        """Extract text from PDF"""
        chunks = []
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    
                    # Simple chunking
                    chunk_size = 500
                    overlap = 50
                    
                    for i in range(0, len(text), chunk_size - overlap):
                        chunk_text = text[i:i + chunk_size]
                        if len(chunk_text.strip()) > 50:
                            chunks.append({
                                'text': chunk_text,
                                'metadata': {
                                    'source': Path(pdf_path).name,
                                    'page': page_num + 1,
                                    'chunk_index': len(chunks)
                                }
                            })
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
        
        return chunks
    
    def process_pdf(self, pdf_path: str, force: bool = False) -> Dict:
        """Process a PDF file"""
        pdf_name = Path(pdf_path).name
        
        # Check if already processed
        if not force:
            for meta in self.metadata:
                if meta['source'] == pdf_name:
                    logger.info(f"Already processed: {pdf_name}")
                    return {'status': 'skipped'}
        
        # Extract chunks
        logger.info(f"Extracting text from {pdf_name}")
        chunks = self.extract_text_from_pdf(pdf_path)
        
        if not chunks:
            return {'status': 'failed', 'reason': 'no_text'}
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        texts = [chunk['text'] for chunk in chunks]
        new_embeddings = self.embedder.encode(texts)
        
        # Add to storage
        self.documents.extend(texts)
        self.metadata.extend([chunk['metadata'] for chunk in chunks])
        
        if len(self.embeddings) == 0:
            self.embeddings = new_embeddings
        else:
            self.embeddings = torch.cat([
                torch.tensor(self.embeddings), 
                torch.tensor(new_embeddings)
            ]).numpy()
        
        # Save
        self._save_data()
        
        logger.info(f"✅ Processed {len(chunks)} chunks from {pdf_name}")
        return {'status': 'success', 'chunks': len(chunks)}
    
    def process_directory(self, directory: str) -> Dict:
        """Process all PDFs in a directory"""
        results = {
            'processed': 0,
            'skipped': 0,
            'failed': 0,
            'files': []
        }

        pdf_files = Path(directory).glob("**/*.pdf")
        for pdf_file in pdf_files:
            result = self.process_pdf(str(pdf_file))

            file_info = {
                'name': pdf_file.name,
                'path': str(pdf_file),
                'status': result['status']
            }

            if result['status'] == 'success':
                results['processed'] += 1
                file_info['chunks'] = result.get('chunks', 0)
            elif result['status'] == 'skipped':
                results['skipped'] += 1
            else:
                results['failed'] += 1
                file_info['reason'] = result.get('reason', 'unknown')

            results['files'].append(file_info)

        return results
    
    def query(self, question: str, n_results: int = 5) -> Tuple[str, List, Dict]:
        """Query the RAG system"""
        
        if not self.anthropic:
            return "Please set Claude API key", [], {}
        
        if not self.documents:
            return "No documents processed yet", [], {}
        
        # Generate embedding for question
        query_embedding = self.embedder.encode([question])[0]
        
        # Calculate similarities
        similarities = []
        embeddings_tensor = torch.tensor(self.embeddings)
        query_tensor = torch.tensor(query_embedding)
        
        for i, doc_embedding in enumerate(embeddings_tensor):
            similarity = torch.nn.functional.cosine_similarity(
                query_tensor.unsqueeze(0),
                doc_embedding.unsqueeze(0)
            ).item()
            similarities.append((similarity, i))
        
        # Get top results
        similarities.sort(reverse=True)
        top_indices = [idx for _, idx in similarities[:n_results]]
        
        # Prepare context
        context_parts = []
        sources = []
        
        for idx in top_indices:
            doc = self.documents[idx]
            meta = self.metadata[idx]
            context_parts.append(f"[{meta['source']}, Page {meta['page']}]\n{doc}")
            sources.append(meta)
        
        context = "\n\n".join(context_parts)
        
        # Call Claude
        prompt = f"""Based on the following context, answer the question.
        
Context:
{context}

Question: {question}

Answer:"""
        
        try:
            # Get model from environment variable, with fallback to default
            model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
            max_tokens = int(os.getenv("MAX_TOKENS", "1000"))

            response = self.anthropic.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            answer = response.content[0].text

            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            # Calculate cost based on model
            if "sonnet" in model.lower():
                input_cost_per_1k = 0.003
                output_cost_per_1k = 0.015
            elif "opus" in model.lower():
                input_cost_per_1k = 0.015
                output_cost_per_1k = 0.075
            elif "haiku" in model.lower():
                input_cost_per_1k = 0.00025
                output_cost_per_1k = 0.00125
            else:
                # Default to Sonnet pricing
                input_cost_per_1k = 0.003
                output_cost_per_1k = 0.015

            estimated_cost = (input_tokens / 1000 * input_cost_per_1k +
                            output_tokens / 1000 * output_cost_per_1k)

            stats = {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                'model': model,
                'estimated_cost': estimated_cost
            }
            
            return answer, sources, stats
            
        except Exception as e:
            return f"Error: {e}", sources, {}
    
    def get_statistics(self) -> Dict:
        """Get system statistics"""
        # Calculate unique files
        unique_files = {}
        for meta in self.metadata:
            filename = meta.get('source', 'unknown')
            if filename not in unique_files:
                unique_files[filename] = {
                    'name': filename,
                    'chunks': 0,
                    'pages': set()
                }
            unique_files[filename]['chunks'] += 1
            unique_files[filename]['pages'].add(meta.get('page', 0))

        # Calculate storage size
        storage_size_mb = 0
        if self.embeddings_file.exists():
            storage_size_mb = round(self.embeddings_file.stat().st_size / (1024 * 1024), 2)

        # Prepare files list
        files_list = []
        for filename, info in unique_files.items():
            files_list.append({
                'name': filename,
                'chunks': info['chunks'],
                'pages': len(info['pages']),
                'size_mb': 0  # We don't track individual file sizes
            })

        return {
            'total_files': len(unique_files),
            'total_chunks': len(self.documents),
            'storage_size_mb': storage_size_mb,
            'total_queries': 0,  # Not tracked in SimpleRAGSystem
            'files': files_list
        }

    def clear_database(self):
        """Clear all documents and embeddings from the database"""
        # Clear in-memory storage
        self.documents = []
        self.embeddings = []
        self.metadata = []

        # Delete persisted files
        if self.data_file.exists():
            self.data_file.unlink()
            logger.info(f"Deleted {self.data_file}")

        if self.embeddings_file.exists():
            self.embeddings_file.unlink()
            logger.info(f"Deleted {self.embeddings_file}")

        logger.info("✅ Database cleared successfully")

# Alias for compatibility
M1OptimizedRAGSystem = SimpleRAGSystem