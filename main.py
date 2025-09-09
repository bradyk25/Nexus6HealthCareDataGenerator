#!/usr/bin/env python3
"""
Phara - AI-powered chatbot using Gemini AI
Main orchestration module that brings together all components
"""

from brain import Brain
from read import Reader
from voice import Voice
from config import Config, AIProvider
import sys

class Phara:
    """Main chatbot class that orchestrates all components"""
    
    def __init__(self):
        try:
            self.brain = Brain()
            self.reader = Reader()
            self.voice = Voice()
            self.running = False
        except Exception as e:
            print(f"Failed to initialize Phara: {e}")
            print("Please check your API key and dependencies.")
            sys.exit(1)
    
    def start(self):
        """Start the chatbot"""
        self.running = True
        self.voice.display_welcome()
        
        # Auto-load first data file if available
        self.auto_load_first_file()
        
        try:
            while self.running:
                self.chat_loop()
        except KeyboardInterrupt:
            self.voice.speak_info("Goodbye! Thanks for chatting with Phara!")
            sys.exit(0)
    
    def chat_loop(self):
        """Main chat loop"""
        try:
            # Get user input and check for commands
            command_type, user_input = self.reader.get_command_input()
            
            if command_type == 'empty':
                return
            elif command_type == 'quit':
                self.handle_quit()
            elif command_type == 'clear':
                self.handle_clear()
            elif command_type == 'history':
                self.handle_history()
            elif command_type == 'help':
                self.handle_help()
            elif command_type == 'model':
                self.handle_model_command(user_input)
            elif command_type == 'load':
                self.handle_load_command(user_input)
            elif command_type == 'files':
                self.handle_files_command()
            elif command_type == 'data_query':
                self.handle_data_query_command(user_input)
            elif command_type == 'suggestions':
                self.handle_suggestions_command()
            elif command_type == 'normal':
                self.handle_normal_input(user_input)
            
        except Exception as e:
            self.voice.speak_error(f"error: {e}")
    
    def handle_normal_input(self, user_input):
        """Handle normal chat input"""
        # Validate input
        if not self.reader.validate_input(user_input):
            self.voice.speak_error("Invalid input. Please try again.")
            return
        
        # Show thinking animation
        self.voice.show_thinking(1)
        
        # Process with AI brain
        try:
            response = self.brain.think(user_input)
            
            # Output response
            if len(response) > 100:
                self.voice.speak_multiline(response)
            else:
                self.voice.speak(response)
                
        except Exception as e:
            self.voice.speak_error(f"Failed to process your message: {e}")
    
    def handle_quit(self):
        """Handle quit command"""
        self.voice.speak_info("Goodbye! Thanks for chatting with Phara!")
        self.running = False
        sys.exit(0)
    
    def handle_clear(self):
        """Handle clear command"""
        self.brain.clear_history()
        self.reader.clear_history()
        self.voice.clear_history()
        self.voice.speak_success("Conversation history cleared!")
    
    def handle_history(self):
        """Handle history command"""
        history = self.brain.get_history()
        
        if not history:
            self.voice.speak_info("No conversation history yet.")
            return
        
        self.voice.speak_info("Conversation History:")
        for entry in history[-10:]:  # Show last 10 entries
            print(f"  {entry}")
        print()
    
    def handle_help(self):
        """Handle help command"""
        self.voice.display_help()
    
    def handle_model_command(self, command):
        """Handle model-related commands"""
        parts = command.strip().split()
        
        if len(parts) == 1:  # Just 'model' - show current model info
            info = self.brain.get_current_model_info()
            self.voice.speak_info(f"Current AI Model:")
            self.voice.speak_info(f"  Provider: {info['provider']}")
            self.voice.speak_info(f"  Model: {info['model_name']}")
            self.voice.speak_info(f"  Temperature: {info['temperature']}")
            self.voice.speak_info(f"  Max Tokens: {info['max_tokens']}")
            
        elif len(parts) == 2 and parts[1] == 'list':  # 'model list' - show available models
            self.voice.speak_info("Available AI Models:")
            for provider in AIProvider:
                config = Config.MODEL_CONFIGS[provider]
                status = "OK" if config.api_key and config.api_key != "your-openai-api-key-here" and config.api_key != "your-anthropic-api-key-here" else "X"
                self.voice.speak_info(f"  {status} {provider.value}: {config.model_name}")
            self.voice.speak_info("\nTo switch models, use: model switch <provider>")
            self.voice.speak_info("Available providers: gemini, openai, anthropic, ollama")
            
        elif len(parts) == 3 and parts[1] == 'switch':  # 'model switch <provider>'
            provider_name = parts[2].lower()
            try:
                provider = AIProvider(provider_name)
                result = self.brain.switch_model(provider)
                self.voice.speak_success(result)
            except ValueError:
                self.voice.speak_error(f"Unknown provider: {provider_name}")
                self.voice.speak_info("Available providers: gemini, openai, anthropic, ollama")
            except Exception as e:
                self.voice.speak_error(f"Failed to switch model: {e}")
        else:
            self.voice.speak_error("Invalid model command. Use:")
            self.voice.speak_info("  model - Show current model info")
            self.voice.speak_info("  model list - Show available models")
            self.voice.speak_info("  model switch <provider> - Switch to different model")
    
    def handle_load_command(self, command):
        """Handle file loading command"""
        parts = command.strip().split(maxsplit=1)
        
        if len(parts) < 2:
            self.voice.speak_error("Please specify a filename. Usage: load <filename>")
            return
        
        filename = parts[1]
        self.voice.speak_info(f"Loading file: {filename}")
        
        try:
            success, message = self.brain.load_data_file(filename)
            
            if success:
                self.voice.speak_success("File loaded successfully!")
                self.voice.speak_multiline(message)
                
                # Show suggestions
                suggestions = self.brain.get_data_suggestions()
                if suggestions:
                    self.voice.speak_info("Try asking:")
                    for suggestion in suggestions[:3]:
                        self.voice.speak_info(f"  - {suggestion}")
            else:
                self.voice.speak_error(message)
                
        except Exception as e:
            self.voice.speak_error(f"Failed to load file: {e}")
    
    def handle_files_command(self):
        """Handle files listing command"""
        try:
            available_files = self.brain.get_available_files()
            loaded_files = self.brain.get_loaded_files()
            
            if not available_files:
                self.voice.speak_info("No data files found in the 'data' folder.")
                self.voice.speak_info("Add CSV or Excel files to the 'data' folder to get started.")
                return
            
            self.voice.speak_info("Available Data Files:")
            for filename in available_files:
                status = "Loaded" if filename in loaded_files else "Available"
                self.voice.speak_info(f"  {status} {filename}")
            
            if not loaded_files:
                self.voice.speak_info("\nUse 'load <filename>' to load a file")
            
        except Exception as e:
            self.voice.speak_error(f"Failed to list files: {e}")
    
    def handle_data_query_command(self, command):
        """Handle data query commands"""
        query_type = command.strip().lower()
        
        try:
            if query_type in ['describe', 'summary']:
                result = self.brain.query_data('describe')
            elif query_type == 'info':
                result = self.brain.query_data('info')
            elif query_type.startswith('head'):
                parts = query_type.split()
                n = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 5
                result = self.brain.query_data('head', n=n)
            elif query_type.startswith('tail'):
                parts = query_type.split()
                n = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 5
                result = self.brain.query_data('tail', n=n)
            elif query_type == 'columns':
                result = self.brain.query_data('columns')
            else:
                result = self.brain.query_data('describe')
            
            if result:
                self.voice.speak_multiline(result)
            else:
                self.voice.speak_error("No data available. Load a file first.")
                
        except Exception as e:
            self.voice.speak_error(f"Failed to execute query: {e}")
    
    def handle_suggestions_command(self):
        """Handle suggestions command"""
        try:
            suggestions = self.brain.get_data_suggestions()
            
            if suggestions:
                self.voice.speak_info("Suggested questions for your data:")
                for i, suggestion in enumerate(suggestions, 1):
                    self.voice.speak_info(f"  {i}. {suggestion}")
            else:
                self.voice.speak_info("Load a data file first to get suggestions.")
                
        except Exception as e:
            self.voice.speak_error(f"Failed to get suggestions: {e}")
    
    def auto_load_first_file(self):
        """Automatically load the first available data file and show data folder contents"""
        try:
            available_files = self.brain.get_available_files()
            
            if not available_files:
                self.voice.speak_info("Data folder is empty.")
                self.voice.speak_info("Add CSV or Excel files to the 'data' folder to get started with data analysis.")
                return
            
            # Show what's in the data folder
            self.voice.speak_info("Data folder contents:")
            for i, filename in enumerate(available_files, 1):
                self.voice.speak_info(f"  {i}. {filename}")
            
            # Auto-load the first file
            first_file = available_files[0]
            self.voice.speak_info(f"Auto-loading first file: {first_file}")
            
            success, message = self.brain.load_data_file(first_file)
            
            if success:
                self.voice.speak_success("File loaded successfully!")
                self.voice.speak_multiline(message)
                
                # Show file switching instructions if there are multiple files
                if len(available_files) > 1:
                    self.voice.speak_info("Multiple data files detected!")
                    self.voice.speak_info("To switch to a different file, use: load <filename>")
                    self.voice.speak_info("Available files:")
                    for filename in available_files:
                        status = "Currently loaded" if filename == first_file else "Available"
                        self.voice.speak_info(f"  {status}: {filename}")
                    self.voice.speak_info("Type 'files' anytime to see all available data files.")
                
                # Show suggestions
                suggestions = self.brain.get_data_suggestions()
                if suggestions:
                    self.voice.speak_info("Try asking:")
                    for suggestion in suggestions[:3]:
                        self.voice.speak_info(f"  - {suggestion}")
            else:
                self.voice.speak_error(f"Failed to auto-load {first_file}: {message}")
                self.voice.speak_info("You can manually load files using: load <filename>")
                
        except Exception as e:
            self.voice.speak_error(f"Error during auto-load: {e}")

def main():
    """Main entry point"""
    try:
        phara = Phara()
        phara.start()
    except Exception as e:
        print(f"Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
