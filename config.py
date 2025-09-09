"""
Configuration module for Phara AI chatbot
Handles AI model selection and API key management
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional

class AIProvider(Enum):
    """Supported AI providers"""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"

@dataclass
class ModelConfig:
    """Configuration for a specific AI model"""
    provider: AIProvider
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    additional_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}

class Config:
    """Main configuration class for Phara"""
    
    # Current active model - CHANGE THIS TO SWITCH MODELS
    ACTIVE_MODEL = AIProvider.OPENAI
    
    # API Keys - Add your keys here for quick programming
    API_KEYS = {
        AIProvider.GEMINI: "your-gemini-api-key-here",
        AIProvider.OPENAI: "your-openai-api-key-here",
        AIProvider.ANTHROPIC: "your-anthropic-api-key-here",
        AIProvider.OLLAMA: None,  # Ollama doesn't need API key for local models
    }
    
    # Model configurations
    MODEL_CONFIGS = {
        AIProvider.GEMINI: ModelConfig(
            provider=AIProvider.GEMINI,
            model_name="gemini-pro",
            api_key=API_KEYS[AIProvider.GEMINI],
            temperature=0.7,
            max_tokens=2048
        ),
        AIProvider.OPENAI: ModelConfig(
            provider=AIProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            api_key=API_KEYS[AIProvider.OPENAI],
            temperature=0.7,
            max_tokens=2048
        ),
        AIProvider.ANTHROPIC: ModelConfig(
            provider=AIProvider.ANTHROPIC,
            model_name="claude-3-sonnet-20240229",
            api_key=API_KEYS[AIProvider.ANTHROPIC],
            temperature=0.7,
            max_tokens=2048
        ),
        AIProvider.OLLAMA: ModelConfig(
            provider=AIProvider.OLLAMA,
            model_name="llama2",
            base_url="http://localhost:11434",
            temperature=0.7,
            max_tokens=2048
        )
    }
    
    @classmethod
    def get_active_config(cls) -> ModelConfig:
        """Get the configuration for the currently active model"""
        return cls.MODEL_CONFIGS[cls.ACTIVE_MODEL]
    
    @classmethod
    def switch_model(cls, provider: AIProvider) -> None:
        """Switch to a different AI model"""
        if provider not in cls.MODEL_CONFIGS:
            raise ValueError(f"Unsupported AI provider: {provider}")
        cls.ACTIVE_MODEL = provider
    
    @classmethod
    def update_api_key(cls, provider: AIProvider, api_key: str) -> None:
        """Update API key for a specific provider"""
        cls.API_KEYS[provider] = api_key
        cls.MODEL_CONFIGS[provider].api_key = api_key
    
    # General settings
    CONVERSATION_HISTORY_LIMIT = 20
    THINKING_ANIMATION_DURATION = 1
    MULTILINE_THRESHOLD = 100
