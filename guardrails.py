"""
Guardrails system for Phara AI chatbot
Ensures conversations stay focused on data analysis and file content
"""

import re
from typing import List, Tuple, Optional
from file_processor import FileProcessor

class DataGuardrails:
    """Implements guardrails to keep conversations focused on data analysis"""
    
    def __init__(self, file_processor: FileProcessor):
        self.file_processor = file_processor
        
        # Keywords that indicate data-related queries
        self.data_keywords = [
            'data', 'column', 'row', 'table', 'csv', 'excel', 'file',
            'analyze', 'analysis', 'statistics', 'stats', 'summary',
            'count', 'sum', 'average', 'mean', 'median', 'max', 'min',
            'trend', 'pattern', 'correlation', 'distribution',
            'filter', 'sort', 'group', 'aggregate', 'pivot',
            'chart', 'graph', 'plot', 'visualization',
            'missing', 'null', 'duplicate', 'unique',
            'sales', 'revenue', 'product', 'customer', 'region'  # Domain-specific
        ]
        
        # Topics to redirect away from
        self.off_topic_patterns = [
            r'\b(weather|news|politics|sports|entertainment|movies|music)\b',
            r'\b(recipe|cooking|food|restaurant)\b',
            r'\b(travel|vacation|hotel|flight)\b',
            r'\b(health|medical|doctor|medicine)\b',
            r'\b(programming|code|software|development)\b(?!.*data)',
            r'\b(personal|family|relationship|dating)\b',
            r'\b(joke|funny|humor|meme)\b'
        ]
        
        # Responses for different scenarios
        self.redirect_responses = [
            "I'm here to help you analyze and understand your data files. Let's focus on the data you've loaded.",
            "I specialize in data analysis. Would you like to explore the information in your files instead?",
            "Let's keep our conversation focused on your data. What would you like to know about the loaded files?",
            "I'm designed to help with data analysis and file exploration. How can I assist you with your data?"
        ]
        
        self.no_data_responses = [
            "I don't see any data files loaded yet. Would you like to load a file from the data folder?",
            "To get started, please load a data file using the 'load' command. I can then help you analyze it.",
            "No data files are currently loaded. Use 'files' to see available files or 'load <filename>' to load one."
        ]
    
    def check_query_relevance(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """
        Check if the user query is relevant to data analysis
        
        Returns:
            Tuple of (is_relevant, redirect_message)
        """
        user_input_lower = user_input.lower()
        
        # Check if any data files are loaded
        loaded_files = self.file_processor.list_loaded_files()
        
        # If no files loaded and user isn't trying to load files
        if not loaded_files and not any(keyword in user_input_lower for keyword in ['load', 'file', 'data']):
            import random
            return False, random.choice(self.no_data_responses)
        
        # Check for off-topic patterns
        for pattern in self.off_topic_patterns:
            if re.search(pattern, user_input_lower, re.IGNORECASE):
                import random
                return False, random.choice(self.redirect_responses)
        
        # Check for data-related keywords
        has_data_keywords = any(keyword in user_input_lower for keyword in self.data_keywords)
        
        # If it has data keywords or files are loaded, it's probably relevant
        if has_data_keywords or loaded_files:
            return True, None
        
        # For ambiguous cases, redirect to data focus
        import random
        return False, random.choice(self.redirect_responses)
    
    def enhance_prompt_with_context(self, user_input: str) -> str:
        """
        Enhance the user prompt with data context and guardrails
        """
        enhanced_prompt_parts = []
        
        # Add system context
        enhanced_prompt_parts.append("You are a data analysis assistant. Your role is to help users understand and analyze their data files.")
        
        # Add current file context
        current_file = self.file_processor.get_current_context()
        loaded_files = self.file_processor.list_loaded_files()
        
        if loaded_files:
            enhanced_prompt_parts.append(f"\nCurrently loaded files: {', '.join(loaded_files)}")
            
            if current_file:
                file_info = self.file_processor.get_file_info(current_file)
                if file_info:
                    enhanced_prompt_parts.append(f"Active file: {current_file}")
                    enhanced_prompt_parts.append(f"Columns: {', '.join(file_info['columns'])}")
                    enhanced_prompt_parts.append(f"Shape: {file_info['shape'][0]} rows × {file_info['shape'][1]} columns")
        
        # Add guardrails
        enhanced_prompt_parts.append("\nGuidelines:")
        enhanced_prompt_parts.append("- Focus only on data analysis, statistics, and insights from the loaded files")
        enhanced_prompt_parts.append("- Provide specific, actionable insights about the data")
        enhanced_prompt_parts.append("- If asked about non-data topics, politely redirect to data analysis")
        enhanced_prompt_parts.append("- Use the actual column names and data when providing examples")
        
        # Add the user's actual question
        enhanced_prompt_parts.append(f"\nUser question: {user_input}")
        
        return "\n".join(enhanced_prompt_parts)
    
    def suggest_data_questions(self, filename: Optional[str] = None) -> List[str]:
        """Generate suggested questions based on loaded data"""
        if not filename:
            filename = self.file_processor.get_current_context()
        
        if not filename:
            return [
                "Load a data file to get started",
                "Use 'files' to see available data files",
                "Try 'load sales_data.csv' to load the sample file"
            ]
        
        file_info = self.file_processor.get_file_info(filename)
        if not file_info:
            return ["File information not available"]
        
        suggestions = []
        columns = file_info['columns']
        
        # Generic suggestions
        suggestions.extend([
            f"What are the main insights from {filename}?",
            "Show me a summary of the data",
            "What columns have missing values?",
            "Describe the data distribution"
        ])
        
        # Column-specific suggestions
        if len(columns) > 0:
            suggestions.append(f"Tell me about the '{columns[0]}' column")
            
        # Domain-specific suggestions based on column names
        if any('sales' in col.lower() or 'amount' in col.lower() or 'revenue' in col.lower() for col in columns):
            suggestions.extend([
                "What are the total sales?",
                "Which products sell the most?",
                "Show sales trends over time"
            ])
        
        if any('date' in col.lower() or 'time' in col.lower() for col in columns):
            suggestions.append("Show me data trends over time")
        
        if any('category' in col.lower() or 'type' in col.lower() for col in columns):
            suggestions.append("Break down the data by category")
        
        return suggestions[:6]  # Return top 6 suggestions
    
    def is_data_command(self, user_input: str) -> bool:
        """Check if the input is a data-related command"""
        data_commands = [
            'load', 'files', 'describe', 'summary', 'head', 'tail',
            'columns', 'info', 'stats', 'analyze'
        ]
        
        first_word = user_input.strip().split()[0].lower()
        return first_word in data_commands
