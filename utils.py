import os
import json
from pathlib import Path
from typing import List, Dict
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def export_results_to_json(results: Dict, filepath: str):
    """Export query results to JSON"""
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)

def export_results_to_markdown(
    question: str,
    answer: str,
    sources: List[Dict],
    filepath: str
):
    """Export results to Markdown"""
    content = f"""# Query Results

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Question
{question}

## Answer
{answer}

## Sources
"""
    
    for source in sources:
        content += f"- {source['source']}, Page {source['page']}\n"
    
    with open(filepath, 'w') as f:
        f.write(content)

def create_cost_visualization(cost_data: List[Dict]) -> go.Figure:
    """Create cost visualization chart"""
    if not cost_data:
        return go.Figure()
    
    df = pd.DataFrame(cost_data)
    
    fig = go.Figure()
    
    # Add daily cost line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['daily_cost'],
        mode='lines+markers',
        name='Daily Cost',
        line=dict(color='blue', width=2)
    ))
    
    # Add cumulative cost line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['cumulative_cost'],
        mode='lines+markers',
        name='Cumulative Cost',
        line=dict(color='red', width=2),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title='Claude API Cost Tracking',
        xaxis_title='Date',
        yaxis=dict(
            title='Daily Cost ($)',
            side='left'
        ),
        yaxis2=dict(
            title='Cumulative Cost ($)',
            side='right',
            overlaying='y'
        ),
        hovermode='x unified'
    )
    
    return fig

def validate_pdf(filepath: str) -> bool:
    """Validate if file is a valid PDF"""
    try:
        with open(filepath, 'rb') as f:
            header = f.read(4)
            return header == b'%PDF'
    except:
        return False

def batch_process_pdfs(
    pdf_files: List[str],
    max_workers: int = 4
) -> Dict[str, bool]:
    """Process multiple PDFs in parallel"""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(validate_pdf, pdf): pdf 
            for pdf in pdf_files
        }
        
        for future in as_completed(future_to_file):
            pdf = future_to_file[future]
            try:
                results[pdf] = future.result()
            except Exception as e:
                results[pdf] = False
    
    return results

def get_system_info() -> Dict:
    """Get system information for M1 Mac"""
    import platform
    import subprocess
    import torch
    
    info = {
        'platform': platform.platform(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'torch_version': torch.__version__,
        'mps_available': torch.backends.mps.is_available(),
    }
    
    # Get M1 specific info
    try:
        result = subprocess.run(
            ['sysctl', '-n', 'machdep.cpu.brand_string'],
            capture_output=True,
            text=True
        )
        info['cpu'] = result.stdout.strip()
    except:
        info['cpu'] = 'Unknown'
    
    # Get memory info
    try:
        result = subprocess.run(
            ['sysctl', '-n', 'hw.memsize'],
            capture_output=True,
            text=True
        )
        mem_bytes = int(result.stdout.strip())
        info['memory_gb'] = round(mem_bytes / (1024**3), 1)
    except:
        info['memory_gb'] = 'Unknown'
    
    return info
