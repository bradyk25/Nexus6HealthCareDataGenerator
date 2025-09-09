import sys

class Reader:
    """Class that reads the player's prompts and handles input"""
    
    def __init__(self):
        self.input_history = []
    
    def get_user_input(self, prompt_message="You: "):
        """
        Get input from the user
        
        Args:
            prompt_message (str): The message to display when asking for input
            
        Returns:
            str: The user's input
        """
        try:
            user_input = input(prompt_message).strip()
            
            # Store input in history
            if user_input:
                self.input_history.append(user_input)
            
            return user_input
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            sys.exit(0)
        except EOFError:
            print("\nInput ended.")
            return ""
    
    def read_multiline_input(self):
        """
        Read multiple lines of input until user enters 'END' on a new line
        
        Returns:
            str: The complete multiline input
        """
        print("Enter your message (type 'END' on a new line to finish):")
        lines = []
        
        try:
            while True:
                line = input()
                if line.strip().upper() == 'END':
                    break
                lines.append(line)
            
            full_input = '\n'.join(lines).strip()
            
            # Store input in history
            if full_input:
                self.input_history.append(full_input)
            
            return full_input
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            sys.exit(0)
        except EOFError:
            print("\nInput ended.")
            return ""
    
    def get_input_history(self):
        """
        Get the history of user inputs
        
        Returns:
            list: List of previous user inputs
        """
        return self.input_history.copy()
    
    def clear_history(self):
        """Clear the input history"""
        self.input_history = []
    
    def validate_input(self, user_input):
        """
        Validate user input
        
        Args:
            user_input (str): The input to validate
            
        Returns:
            bool: True if input is valid, False otherwise
        """
        # Basic validation - check if input is not empty and not just whitespace
        if not user_input or not user_input.strip():
            return False
        
        # Check for potentially harmful input (basic safety)
        dangerous_patterns = ['<script>', 'javascript:', 'eval(', 'exec(']
        user_input_lower = user_input.lower()
        
        for pattern in dangerous_patterns:
            if pattern in user_input_lower:
                return False
        
        return True
    
    def get_command_input(self):
        """
        Get input and check for special commands
        
        Returns:
            tuple: (command_type, input_text) where command_type is 'quit', 'clear', 'history', or 'normal'
        """
        user_input = self.get_user_input()
        
        if not user_input:
            return 'empty', ''
        
        # Check for special commands
        if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
            return 'quit', user_input
        elif user_input.lower() in ['clear', 'reset']:
            return 'clear', user_input
        elif user_input.lower() in ['history', 'show history']:
            return 'history', user_input
        elif user_input.lower() in ['help', '?']:
            return 'help', user_input
        elif user_input.lower().startswith('model'):
            return 'model', user_input
        elif user_input.lower().startswith('load '):
            return 'load', user_input
        elif user_input.lower() in ['files', 'list files']:
            return 'files', user_input
        elif user_input.lower() in ['describe', 'summary', 'info']:
            return 'data_query', user_input
        elif user_input.lower().startswith(('head', 'tail', 'columns')):
            return 'data_query', user_input
        elif user_input.lower() in ['suggestions', 'suggest']:
            return 'suggestions', user_input
        else:
            return 'normal', user_input
