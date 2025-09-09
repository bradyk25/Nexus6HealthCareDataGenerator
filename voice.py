import time
import textwrap

class Voice:
    """Class that the chatbot uses to send responses to the person"""
    
    def __init__(self):
        self.response_history = []
        self.typing_speed = 0.03  # Seconds between characters for typing effect
        self.enable_typing_effect = True
    
    def speak(self, message, prefix="Phara: "):
        """
        Output a message to the user with optional typing effect
        
        Args:
            message (str): The message to output
            prefix (str): Prefix to add before the message
        """
        if not message:
            return
        
        # Store response in history
        self.response_history.append(message)
        
        # Format the message with prefix
        full_message = f"{prefix}{message}"
        
        if self.enable_typing_effect:
            self._type_message(full_message)
        else:
            print(full_message)
        
        print()  # Add a blank line after the message
    
    def _type_message(self, message):
        """
        Display message with typing effect
        
        Args:
            message (str): The message to type out
        """
        for char in message:
            print(char, end='', flush=True)
            time.sleep(self.typing_speed)
        print()  # New line at the end
    
    def speak_multiline(self, message, prefix="Phara: ", wrap_width=80):
        """
        Output a multiline message with proper formatting
        
        Args:
            message (str): The message to output
            prefix (str): Prefix to add before the first line
            wrap_width (int): Width to wrap text at
        """
        if not message:
            return
        
        # Store response in history
        self.response_history.append(message)
        
        # Wrap the text
        wrapped_lines = textwrap.fill(message, width=wrap_width).split('\n')
        
        # Print first line with prefix
        if wrapped_lines:
            first_line = f"{prefix}{wrapped_lines[0]}"
            if self.enable_typing_effect:
                self._type_message(first_line)
            else:
                print(first_line)
            
            # Print remaining lines with proper indentation
            indent = " " * len(prefix)
            for line in wrapped_lines[1:]:
                indented_line = f"{indent}{line}"
                if self.enable_typing_effect:
                    self._type_message(indented_line)
                else:
                    print(indented_line)
        
        print()  # Add a blank line after the message
    
    def speak_error(self, error_message):
        """
        Output an error message
        
        Args:
            error_message (str): The error message to display
        """
        error_text = f"error: {error_message}"
        print(error_text)
        print()
    
    def speak_info(self, info_message):
        """
        Output an informational message
        
        Args:
            info_message (str): The info message to display
        """
        info_text = f"INFO: {info_message}"
        print(info_text)
        print()
    
    def speak_success(self, success_message):
        """
        Output a success message
        
        Args:
            success_message (str): The success message to display
        """
        success_text = f"{success_message}"
        print(success_text)
        print()
    
    def show_thinking(self, duration=2):
        """
        Show a thinking animation
        
        Args:
            duration (int): How long to show the thinking animation in seconds
        """
        thinking_chars = ['-', '\\', '|', '/']
        end_time = time.time() + duration
        
        print("Phara is thinking", end='')
        
        i = 0
        while time.time() < end_time:
            print(f'\r{thinking_chars[i % len(thinking_chars)]} Phara is thinking...', end='', flush=True)
            time.sleep(0.1)
            i += 1
        
        print('\r' + ' ' * 30 + '\r', end='')  # Clear the thinking line
    
    def display_welcome(self):
        """Display welcome message"""
        welcome_msg = """
            Welcome to Phara!
         Your AI-powered chatbot

Type 'help' for commands or just start chatting!
Type 'quit' to exit.
        """
        print(welcome_msg)
    
    def display_help(self):
        """Display help information"""
        help_msg = """
Available commands:
- help, ? - Show this help message
- quit, exit, bye, goodbye - Exit the chatbot
- clear, reset - Clear conversation history
- history - Show conversation history

AI Model Commands:
- model - Show current AI model information
- model list - Show all available AI models
- model switch <provider> - Switch to different AI model
  Available providers: gemini, openai, anthropic, ollama

Data Analysis Commands:
- files - List available data files
- load <filename> - Load a CSV or Excel file
- describe, summary - Show data statistics
- head, tail - Show first/last rows
- columns - Show column names
- suggestions - Get suggested questions for your data

Just type your message and press Enter to chat with Phara about your data!
        """
        print(help_msg)
    
    def set_typing_effect(self, enabled):
        """
        Enable or disable typing effect
        
        Args:
            enabled (bool): Whether to enable typing effect
        """
        self.enable_typing_effect = enabled
    
    def set_typing_speed(self, speed):
        """
        Set the typing speed
        
        Args:
            speed (float): Seconds between characters (lower = faster)
        """
        self.typing_speed = max(0.01, speed)  # Minimum speed limit
    
    def get_response_history(self):
        """
        Get the history of responses
        
        Returns:
            list: List of previous responses
        """
        return self.response_history.copy()
    
    def clear_history(self):
        """Clear the response history"""
        self.response_history = []
