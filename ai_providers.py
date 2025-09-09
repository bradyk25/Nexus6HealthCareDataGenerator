"""
AI Provider implementations for different chat AI models
Provides a unified interface for various AI services
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from config import ModelConfig, AIProvider
import json

class BaseAIProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.conversation_history = []
    
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        """Generate a response from the AI model"""
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the AI provider"""
        pass
    
    def add_to_history(self, user_input: str, ai_response: str) -> None:
        """Add conversation to history"""
        self.conversation_history.append(f"User: {user_input}")
        self.conversation_history.append(f"Assistant: {ai_response}")
    
    def clear_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_history(self) -> List[str]:
        """Get conversation history"""
        return self.conversation_history.copy()
    
    def get_context(self, limit: int = 20) -> str:
        """Get recent conversation context"""
        return "\n".join(self.conversation_history[-limit:]) if self.conversation_history else ""

class GeminiProvider(BaseAIProvider):
    """Google Gemini AI provider"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.model = None
    
    def initialize(self) -> None:
        """Initialize Gemini AI"""
        try:
            import google.generativeai as genai
            
            if not self.config.api_key:
                raise ValueError("Gemini API key is required")
            
            genai.configure(api_key=self.config.api_key)
            self.model = genai.GenerativeModel(self.config.model_name)
            
        except ImportError:
            raise ImportError("google-generativeai package is required for Gemini provider")
    
    def generate_response(self, prompt: str) -> str:
        """Generate response using Gemini"""
        try:
            context = self.get_context()
            
            if context:
                full_prompt = f"Previous conversation:\n{context}\n\nCurrent user input: {prompt}\n\nPlease respond naturally and helpfully:"
            else:
                full_prompt = prompt
            
            response = self.model.generate_content(full_prompt)
            ai_response = response.text if response.text else "I'm sorry, I couldn't generate a response."
            
            self.add_to_history(prompt, ai_response)
            return ai_response
            
        except Exception as e:
            error_msg = f"Error with Gemini: {str(e)}"
            return f"I'm sorry, I encountered an error: {error_msg}"

class OpenAIProvider(BaseAIProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.client = None
    
    def initialize(self) -> None:
        """Initialize OpenAI client"""
        try:
            import openai
            
            if not self.config.api_key:
                raise ValueError("OpenAI API key is required")
            
            self.client = openai.OpenAI(api_key=self.config.api_key)
            
        except ImportError:
            raise ImportError("openai package is required for OpenAI provider")
    
    def generate_response(self, prompt: str) -> str:
        """Generate response using OpenAI"""
        try:
            messages = [{"role": "system", "content": "You are a helpful AI assistant."}]
            
            # Add conversation history
            for i in range(0, len(self.conversation_history), 2):
                if i + 1 < len(self.conversation_history):
                    user_msg = self.conversation_history[i].replace("User: ", "")
                    assistant_msg = self.conversation_history[i + 1].replace("Assistant: ", "")
                    messages.append({"role": "user", "content": user_msg})
                    messages.append({"role": "assistant", "content": assistant_msg})
            
            # Add current prompt
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            ai_response = response.choices[0].message.content
            self.add_to_history(prompt, ai_response)
            return ai_response
            
        except Exception as e:
            error_msg = f"Error with OpenAI: {str(e)}"
            return f"I'm sorry, I encountered an error: {error_msg}"

class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude provider"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.client = None
    
    def initialize(self) -> None:
        """Initialize Anthropic client"""
        try:
            import anthropic
            
            if not self.config.api_key:
                raise ValueError("Anthropic API key is required")
            
            self.client = anthropic.Anthropic(api_key=self.config.api_key)
            
        except ImportError:
            raise ImportError("anthropic package is required for Anthropic provider")
    
    def generate_response(self, prompt: str) -> str:
        """Generate response using Anthropic Claude"""
        try:
            context = self.get_context()
            
            if context:
                full_prompt = f"Previous conversation:\n{context}\n\nCurrent user input: {prompt}\n\nPlease respond naturally and helpfully:"
            else:
                full_prompt = prompt
            
            response = self.client.messages.create(
                model=self.config.model_name,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[{"role": "user", "content": full_prompt}]
            )
            
            ai_response = response.content[0].text
            self.add_to_history(prompt, ai_response)
            return ai_response
            
        except Exception as e:
            error_msg = f"Error with Anthropic: {str(e)}"
            return f"I'm sorry, I encountered an error: {error_msg}"

class OllamaProvider(BaseAIProvider):
    """Ollama local AI provider"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"
    
    def initialize(self) -> None:
        """Initialize Ollama connection"""
        try:
            import requests
            # Test connection to Ollama
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise ConnectionError("Cannot connect to Ollama server")
        except ImportError:
            raise ImportError("requests package is required for Ollama provider")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Ollama: {str(e)}")
    
    def generate_response(self, prompt: str) -> str:
        """Generate response using Ollama"""
        try:
            import requests
            
            context = self.get_context()
            
            if context:
                full_prompt = f"Previous conversation:\n{context}\n\nCurrent user input: {prompt}\n\nPlease respond naturally and helpfully:"
            else:
                full_prompt = prompt
            
            payload = {
                "model": self.config.model_name,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "No response generated")
                self.add_to_history(prompt, ai_response)
                return ai_response
            else:
                return f"Error: Ollama server returned status {response.status_code}"
                
        except Exception as e:
            error_msg = f"Error with Ollama: {str(e)}"
            return f"I'm sorry, I encountered an error: {error_msg}"

class AIProviderFactory:
    """Factory class to create AI providers"""
    
    _providers = {
        AIProvider.GEMINI: GeminiProvider,
        AIProvider.OPENAI: OpenAIProvider,
        AIProvider.ANTHROPIC: AnthropicProvider,
        AIProvider.OLLAMA: OllamaProvider,
    }
    
    @classmethod
    def create_provider(cls, config: ModelConfig) -> BaseAIProvider:
        """Create an AI provider instance"""
        if config.provider not in cls._providers:
            raise ValueError(f"Unsupported AI provider: {config.provider}")
        
        provider_class = cls._providers[config.provider]
        provider = provider_class(config)
        provider.initialize()
        return provider
    
    @classmethod
    def get_supported_providers(cls) -> List[AIProvider]:
        """Get list of supported providers"""
        return list(cls._providers.keys())
