"""
File processor module for Phara AI chatbot
Handles reading and processing CSV/Excel files
"""

import pandas as pd
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

class FileProcessor:
    """Handles file reading and data processing for the chatbot"""
    
    def __init__(self, data_folder: str = "data"):
        self.data_folder = Path(data_folder)
        self.data_folder.mkdir(exist_ok=True)
        self.loaded_files = {}
        self.current_file_context = None
        
    def scan_data_folder(self) -> List[str]:
        """Scan the data folder for CSV and Excel files"""
        supported_extensions = ['.csv', '.xlsx', '.xls']
        files = []
        
        for file_path in self.data_folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                files.append(file_path.name)
        
        return sorted(files)
    
    def load_file(self, filename: str) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """
        Load a CSV or Excel file
        
        Returns:
            Tuple of (success, message, dataframe)
        """
        file_path = self.data_folder / filename
        
        if not file_path.exists():
            return False, f"File '{filename}' not found in data folder", None
        
        try:
            # Determine file type and load accordingly
            if filename.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
            elif filename.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                return False, f"Unsupported file format: {filename}", None
            
            # Store the loaded file
            self.loaded_files[filename] = df
            self.current_file_context = filename
            
            # Generate summary
            summary = self._generate_file_summary(df, filename)
            
            return True, summary, df
            
        except Exception as e:
            return False, f"Error loading file '{filename}': {str(e)}", None
    
    def _generate_file_summary(self, df: pd.DataFrame, filename: str) -> str:
        """Generate a summary of the loaded file"""
        summary_parts = []
        
        summary_parts.append(f"File Loaded: {filename}")
        summary_parts.append(f"Dimensions: {df.shape[0]} rows x {df.shape[1]} columns")
        summary_parts.append("")
        
        # Show column headers
        summary_parts.append("Column Headers:")
        for i, col in enumerate(df.columns[:10]):  # Show first 10 columns
            summary_parts.append(f"  {i+1}. {col}")
        
        if len(df.columns) > 10:
            summary_parts.append(f"  ... and {len(df.columns) - 10} more columns")
        
        summary_parts.append("")
        
        # Show first few rows
        summary_parts.append("First 3 rows preview:")
        try:
            preview = df.head(3).to_string(max_cols=5, max_colwidth=20)
            summary_parts.append(preview)
        except Exception:
            summary_parts.append("  (Preview unavailable)")
        
        summary_parts.append("")
        
        # Basic statistics
        summary_parts.append("Quick Stats:")
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            summary_parts.append(f"  - Numeric columns: {len(numeric_cols)}")
        
        text_cols = df.select_dtypes(include=['object']).columns
        if len(text_cols) > 0:
            summary_parts.append(f"  - Text columns: {len(text_cols)}")
        
        # Check for missing values
        missing_data = df.isnull().sum().sum()
        if missing_data > 0:
            summary_parts.append(f"  - Missing values: {missing_data}")
        
        summary_parts.append("")
        summary_parts.append("Ask me anything about this data!")
        
        return "\n".join(summary_parts)
    
    def get_file_info(self, filename: str) -> Optional[Dict]:
        """Get information about a loaded file"""
        if filename not in self.loaded_files:
            return None
        
        df = self.loaded_files[filename]
        return {
            'filename': filename,
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': df.dtypes.to_dict(),
            'memory_usage': df.memory_usage(deep=True).sum(),
            'has_missing': df.isnull().any().any()
        }
    
    def get_column_info(self, filename: str, column: str) -> Optional[Dict]:
        """Get detailed information about a specific column"""
        if filename not in self.loaded_files:
            return None
        
        df = self.loaded_files[filename]
        if column not in df.columns:
            return None
        
        col_data = df[column]
        info = {
            'column': column,
            'dtype': str(col_data.dtype),
            'non_null_count': col_data.count(),
            'null_count': col_data.isnull().sum(),
            'unique_count': col_data.nunique()
        }
        
        # Add statistics for numeric columns
        if pd.api.types.is_numeric_dtype(col_data):
            info.update({
                'mean': col_data.mean(),
                'median': col_data.median(),
                'std': col_data.std(),
                'min': col_data.min(),
                'max': col_data.max()
            })
        
        # Add value counts for categorical data
        if col_data.nunique() <= 20:  # Only for columns with reasonable number of unique values
            info['value_counts'] = col_data.value_counts().head(10).to_dict()
        
        return info
    
    def query_data(self, filename: str, query_type: str, **kwargs) -> Optional[str]:
        """Execute various queries on the data"""
        if filename not in self.loaded_files:
            return None
        
        df = self.loaded_files[filename]
        
        try:
            if query_type == 'describe':
                return df.describe().to_string()
            elif query_type == 'head':
                n = kwargs.get('n', 5)
                return df.head(n).to_string()
            elif query_type == 'tail':
                n = kwargs.get('n', 5)
                return df.tail(n).to_string()
            elif query_type == 'info':
                import io
                buffer = io.StringIO()
                df.info(buf=buffer)
                return buffer.getvalue()
            elif query_type == 'columns':
                return f"Columns: {', '.join(df.columns)}"
            elif query_type == 'shape':
                return f"Shape: {df.shape[0]} rows x {df.shape[1]} columns"
            else:
                return None
        except Exception as e:
            return f"Error executing query: {str(e)}"
    
    def get_current_context(self) -> Optional[str]:
        """Get the currently loaded file context"""
        return self.current_file_context
    
    def list_loaded_files(self) -> List[str]:
        """Get list of currently loaded files"""
        return list(self.loaded_files.keys())
