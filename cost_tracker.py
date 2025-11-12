import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

class CostTracker:
    """Track and analyze Claude API costs"""
    
    def __init__(self, storage_path: str = "./logs/cost_tracking.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(exist_ok=True)
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Load existing cost data"""
        if self.storage_path.exists():
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        return {
            'queries': [],
            'daily_totals': {},
            'monthly_totals': {},
            'total_cost': 0.0
        }
    
    def _save_data(self):
        """Save cost data"""
        with open(self.storage_path, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def log_query(
        self,
        question: str,
        input_tokens: int,
        output_tokens: int,
        model: str = "claude-sonnet-4-5-20250929"
    ) -> Dict:
        """Log a query and its cost"""
        
        # Calculate cost based on model
        if "sonnet" in model:
            # Claude Sonnet 3.5, 4.0, and 4.5
            input_cost_per_1k = 0.003
            output_cost_per_1k = 0.015
        elif "opus" in model:
            # Claude Opus 3.0 and 4.0
            input_cost_per_1k = 0.015
            output_cost_per_1k = 0.075
        elif "haiku" in model:
            # Claude Haiku 3.0 and 3.5
            input_cost_per_1k = 0.00025
            output_cost_per_1k = 0.00125
        else:
            # Default to Sonnet pricing if unknown
            input_cost_per_1k = 0.003
            output_cost_per_1k = 0.015
        
        cost = (input_tokens / 1000 * input_cost_per_1k + 
                output_tokens / 1000 * output_cost_per_1k)
        
        # Create query record
        query_record = {
            'timestamp': datetime.now().isoformat(),
            'question': question[:100],  # Truncate for storage
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'model': model,
            'cost': round(cost, 4)
        }
        
        # Update data
        self.data['queries'].append(query_record)
        self.data['total_cost'] += cost
        
        # Update daily total
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in self.data['daily_totals']:
            self.data['daily_totals'][today] = {
                'cost': 0.0,
                'queries': 0,
                'tokens': 0
            }
        
        self.data['daily_totals'][today]['cost'] += cost
        self.data['daily_totals'][today]['queries'] += 1
        self.data['daily_totals'][today]['tokens'] += input_tokens + output_tokens
        
        # Update monthly total
        month = datetime.now().strftime('%Y-%m')
        if month not in self.data['monthly_totals']:
            self.data['monthly_totals'][month] = {
                'cost': 0.0,
                'queries': 0,
                'tokens': 0
            }
        
        self.data['monthly_totals'][month]['cost'] += cost
        self.data['monthly_totals'][month]['queries'] += 1
        self.data['monthly_totals'][month]['tokens'] += input_tokens + output_tokens
        
        # Save data
        self._save_data()
        
        return query_record
    
    def get_statistics(self, period: str = 'all') -> Dict:
        """Get cost statistics for a period"""
        
        if period == 'today':
            today = datetime.now().strftime('%Y-%m-%d')
            daily_data = self.data['daily_totals'].get(today, {})
            return {
                'period': 'today',
                'date': today,
                'total_cost': round(daily_data.get('cost', 0), 4),
                'total_queries': daily_data.get('queries', 0),
                'total_tokens': daily_data.get('tokens', 0),
                'average_cost_per_query': round(
                    daily_data.get('cost', 0) / max(daily_data.get('queries', 1), 1),
                    4
                )
            }
        
        elif period == 'this_month':
            month = datetime.now().strftime('%Y-%m')
            monthly_data = self.data['monthly_totals'].get(month, {})
            return {
                'period': 'this_month',
                'month': month,
                'total_cost': round(monthly_data.get('cost', 0), 4),
                'total_queries': monthly_data.get('queries', 0),
                'total_tokens': monthly_data.get('tokens', 0),
                'average_cost_per_query': round(
                    monthly_data.get('cost', 0) / max(monthly_data.get('queries', 1), 1),
                    4
                ),
                'projected_monthly_cost': self._project_monthly_cost()
            }

        else:  # all time
            return {
                'period': 'all_time',
                'total_cost': round(self.data['total_cost'], 4),
                'total_queries': len(self.data['queries']),
                'daily_totals': self.data['daily_totals'],
                'monthly_totals': self.data['monthly_totals'],
                'average_cost_per_query': round(
                    self.data['total_cost'] / max(len(self.data['queries']), 1),
                    4
                )
            }
    
    def _project_monthly_cost(self) -> float:
        """Project monthly cost based on current usage"""
        month = datetime.now().strftime('%Y-%m')
        monthly_data = self.data['monthly_totals'].get(month, {})
        
        if monthly_data.get('cost', 0) == 0:
            return 0
        
        # Calculate days elapsed in month
        today = datetime.now()
        days_in_month = 30  # Simplified
        days_elapsed = today.day

        # Project based on current rate
        daily_rate = monthly_data['cost'] / days_elapsed
        projected = daily_rate * days_in_month

        return round(projected, 4)
    
    def get_cost_chart_data(self, days: int = 30) -> List[Dict]:
        """Get data for cost visualization"""
        chart_data = []
        cumulative = 0
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=days-i-1)).strftime('%Y-%m-%d')
            daily_data = self.data['daily_totals'].get(date, {})
            daily_cost = daily_data.get('cost', 0)
            cumulative += daily_cost
            
            chart_data.append({
                'date': date,
                'daily_cost': round(daily_cost, 2),
                'cumulative_cost': round(cumulative, 2),
                'queries': daily_data.get('queries', 0)
            })
        
        return chart_data
    
    def export_to_csv(self, filepath: str):
        """Export cost data to CSV"""
        df = pd.DataFrame(self.data['queries'])
        df.to_csv(filepath, index=False)
        return filepath
    
    def get_cost_alerts(self) -> List[str]:
        """Get cost alerts if thresholds are exceeded"""
        alerts = []
        
        # Daily threshold
        today_stats = self.get_statistics('today')
        if today_stats['total_cost'] > 10:
            alerts.append(f"⚠️ Daily cost exceeds $10: ${today_stats['total_cost']}")
        
        # Monthly threshold
        month_stats = self.get_statistics('this_month')
        if month_stats['total_cost'] > 100:
            alerts.append(f"⚠️ Monthly cost exceeds $100: ${month_stats['total_cost']}")
        
        if month_stats.get('projected_monthly_cost', 0) > 200:
            alerts.append(
                f"⚠️ Projected monthly cost high: ${month_stats['projected_monthly_cost']}"
            )
        
        return alerts