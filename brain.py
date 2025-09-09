from config import Config
from ai_providers import AIProviderFactory
from file_processor import FileProcessor
from guardrails import DataGuardrails

class Brain:
    """Class where the bot will think and process background prompts using configurable AI models"""
    
    def __init__(self):
        # Get the active configuration
        self.config = Config.get_active_config()
        
        # Initialize the AI provider
        try:
            self.ai_provider = AIProviderFactory.create_provider(self.config)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize AI provider ({self.config.provider.value}): {e}")
        
        # Initialize file processor and guardrails
        self.file_processor = FileProcessor()
        self.guardrails = DataGuardrails(self.file_processor)
    
    def think(self, user_prompt):
        """
        Process the user's prompt and generate a response using the configured AI model
        
        Args:
            user_prompt (str): The user's input prompt
            
        Returns:
            str: The AI-generated response
        """
        try:
            # Check if the query is relevant to data analysis
            is_relevant, redirect_message = self.guardrails.check_query_relevance(user_prompt)
            
            if not is_relevant and redirect_message:
                return redirect_message
            
            # Enhance the prompt with data context and guardrails
            enhanced_prompt = self.guardrails.enhance_prompt_with_context(user_prompt)
            
            # Generate response using the configured AI provider
            return self.ai_provider.generate_response(enhanced_prompt)
            
        except Exception as e:
            error_message = f"Error processing prompt with {self.config.provider.value}: {str(e)}"
            print(f"Brain error: {error_message}")
            return "I'm sorry, I encountered an error while processing your request. Please try again."
    
    def clear_history(self):
        """Clear the conversation history"""
        self.ai_provider.clear_history()
    
    def get_history(self):
        """Get the current conversation history"""
        return self.ai_provider.get_history()
    
    def switch_model(self, provider):
        """Switch to a different AI model"""
        try:
            Config.switch_model(provider)
            self.config = Config.get_active_config()
            self.ai_provider = AIProviderFactory.create_provider(self.config)
            return f"Switched to {provider.value} model: {self.config.model_name}"
        except Exception as e:
            return f"Failed to switch to {provider.value}: {e}"
    
    def get_current_model_info(self):
        """Get information about the current model"""
        return {
            "provider": self.config.provider.value,
            "model_name": self.config.model_name,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }
    
    def load_data_file(self, filename):
        """Load a data file and return summary"""
        success, message, df = self.file_processor.load_file(filename)
        return success, message
    
    def get_available_files(self):
        """Get list of available data files"""
        return self.file_processor.scan_data_folder()
    
    def get_loaded_files(self):
        """Get list of currently loaded files"""
        return self.file_processor.list_loaded_files()
    
    def query_data(self, query_type, **kwargs):
        """Execute a data query"""
        current_file = self.file_processor.get_current_context()
        if not current_file:
            return "No data file is currently loaded. Use 'load <filename>' to load a file first."
        
        result = self.file_processor.query_data(current_file, query_type, **kwargs)
        return result if result else f"Unable to execute query: {query_type}"
    
    def get_data_suggestions(self):
        """Get suggested questions for the current data"""
        return self.guardrails.suggest_data_questions()
