"""
Performance Monitor Component

This module provides performance monitoring and metrics display
for the credit card optimizer application.
"""

import streamlit as st
import time
import psutil
import pandas as pd
import sys
from typing import Dict, Any, Optional


class PerformanceMonitor:
    """Monitor and display application performance metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics = {}
    
    def start_timer(self, operation: str):
        """Start timing an operation"""
        self.metrics[operation] = {'start': time.time()}
    
    def end_timer(self, operation: str):
        """End timing an operation and calculate duration"""
        if operation in self.metrics:
            self.metrics[operation]['end'] = time.time()
            self.metrics[operation]['duration'] = (
                self.metrics[operation]['end'] - self.metrics[operation]['start']
            )
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get Streamlit cache statistics"""
        try:
            # This is a simplified version - actual cache stats would require
            # accessing Streamlit's internal cache manager
            return {
                'data_loading_cache_hits': 'N/A',
                'calculation_cache_entries': 'N/A',
                'combination_cache_entries': 'N/A'
            }
        except Exception:
            return {
                'data_loading_cache_hits': 'N/A',
                'calculation_cache_entries': 'N/A',
                'combination_cache_entries': 'N/A'
            }
    
    def display_performance_metrics(self, show_detailed: bool = False):
        """Display performance metrics in the UI"""
        st.subheader("📊 Performance Metrics")
        
        # Basic metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            memory_mb = self.get_memory_usage()
            st.metric("Memory Usage", f"{memory_mb:.1f} MB")
        
        with col2:
            total_time = time.time() - self.start_time
            st.metric("Total Runtime", f"{total_time:.1f}s")
        
        with col3:
            cache_stats = self.get_cache_stats()
            st.metric("Cache Status", "Active")
        
        # Detailed metrics if requested
        if show_detailed:
            st.write("**Detailed Performance Breakdown:**")
            
            # Operation timings
            if self.metrics:
                timing_data = []
                for operation, data in self.metrics.items():
                    if 'duration' in data:
                        timing_data.append({
                            'Operation': operation,
                            'Duration (s)': f"{data['duration']:.3f}"
                        })
                
                if timing_data:
                    timing_df = pd.DataFrame(timing_data)
                    st.dataframe(timing_df, use_container_width=True)
            
            # Cache statistics
            st.write("**Cache Statistics:**")
            cache_stats = self.get_cache_stats()
            for key, value in cache_stats.items():
                st.write(f"- {key}: {value}")
            
            # System information
            st.write("**System Information:**")
            st.write(f"- CPU Usage: {psutil.cpu_percent()}%")
            st.write(f"- Available Memory: {psutil.virtual_memory().available / 1024 / 1024 / 1024:.1f} GB")
            st.write(f"- Python Version: {sys.version}")


def create_performance_monitor() -> PerformanceMonitor:
    """Create a performance monitor instance"""
    return PerformanceMonitor()


def display_performance_toggle():
    """Display a toggle for showing performance metrics"""
    return st.checkbox("Show Performance Metrics", value=False)


def monitor_operation(monitor: PerformanceMonitor, operation: str):
    """Context manager for monitoring operations"""
    class OperationMonitor:
        def __init__(self, monitor, operation):
            self.monitor = monitor
            self.operation = operation
        
        def __enter__(self):
            self.monitor.start_timer(self.operation)
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.monitor.end_timer(self.operation)
    
    return OperationMonitor(monitor, operation) 