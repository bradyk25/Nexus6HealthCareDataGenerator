# Phara - Multi-AI Chatbot

Phara is a flexible AI-powered chatbot that supports multiple AI providers, making it easy to switch between different chat AI models.

## Features

- **Multi-AI Support**: Switch between Gemini, OpenAI, Anthropic Claude, and Ollama
- **Easy Model Switching**: Change AI models with simple commands
- **Hardcoded API Keys**: Quick setup for development and testing
- **Conversation History**: Maintains context across conversations
- **Command System**: Built-in commands for model management

## Supported AI Providers

- **Google Gemini** (gemini-pro) - Default
- **OpenAI** (gpt-3.5-turbo)
- **Anthropic Claude** (claude-3-sonnet-20240229)
- **Ollama** (llama2) - Local AI models

## Quick Setup

### 1. Install Dependencies

```bash
pip install -e .
```

### 2. Configure API Keys

Edit `config.py` and add your API keys:

```python
API_KEYS = {
    AIProvider.GEMINI: "your-gemini-api-key-here",
    AIProvider.OPENAI: "your-openai-api-key-here",
    AIProvider.ANTHROPIC: "your-anthropic-api-key-here",
    AIProvider.OLLAMA: None,  # No API key needed for local Ollama
}
```

### 3. Switch Default Model (Optional)

In `config.py`, change the active model:

```python
# Change this line to switch default model
ACTIVE_MODEL = AIProvider.OPENAI  # or ANTHROPIC, OLLAMA
```

### 4. Run Phara

```bash
python main.py
```

## Usage

### Basic Chat
Just type your message and press Enter:
```
You: Hello, how are you?
Phara: Hello! I'm doing well, thank you for asking...
```

### Model Commands

- `model` - Show current AI model information
- `model list` - Show all available AI models
- `model switch gemini` - Switch to Gemini AI
- `model switch openai` - Switch to OpenAI GPT
- `model switch anthropic` - Switch to Anthropic Claude
- `model switch ollama` - Switch to Ollama (local)

### Other Commands

- `help` - Show all available commands
- `clear` - Clear conversation history
- `history` - Show recent conversation history
- `quit` - Exit the chatbot

## Architecture

The new modular architecture consists of:

### Core Files

- `main.py` - Main application orchestrator
- `brain.py` - AI processing logic (now provider-agnostic)
- `config.py` - Configuration and API key management
- `ai_providers.py` - AI provider implementations
- `read.py` - User input handling
- `voice.py` - Output formatting and display

### Configuration System

The `Config` class in `config.py` manages:
- Active AI model selection
- API key storage
- Model-specific parameters (temperature, max_tokens, etc.)
- Easy model switching

### AI Provider System

The `ai_providers.py` module provides:
- Abstract base class for all AI providers
- Unified interface for different AI services
- Factory pattern for provider creation
- Individual implementations for each AI service

## Adding New AI Providers

To add a new AI provider:

1. Create a new provider class in `ai_providers.py` inheriting from `BaseAIProvider`
2. Implement the required methods: `initialize()` and `generate_response()`
3. Add the provider to the `AIProvider` enum in `config.py`
4. Add configuration in `Config.MODEL_CONFIGS`
5. Register the provider in `AIProviderFactory._providers`

## Model Switching Examples

### Runtime Switching
```
You: model list
ℹ️  Available AI Models:
ℹ️    ✓ gemini: gemini-pro
ℹ️    ✗ openai: gpt-3.5-turbo
ℹ️    ✗ anthropic: claude-3-sonnet-20240229
ℹ️    ✗ ollama: llama2

You: model switch openai
✅ Switched to openai model: gpt-3.5-turbo
```

### Configuration-based Switching
Edit `config.py`:
```python
# Switch default model
ACTIVE_MODEL = AIProvider.ANTHROPIC
```

## API Key Management

### Method 1: Hardcoded (Quick Development)
Edit `config.py`:
```python
API_KEYS = {
    AIProvider.GEMINI: "AIzaSyByf5QsEjWIPK3-xOfI9kIBSQUTvdiCGVs",
    AIProvider.OPENAI: "sk-your-openai-key-here",
    # ...
}
```

### Method 2: Environment Variables (Production)
The system still supports `.env` files, but the hardcoded approach in `config.py` takes precedence for quick programming.

## Dependencies

- `google-generativeai>=0.3.0` - For Gemini AI
- `openai>=1.0.0` - For OpenAI GPT models
- `anthropic>=0.7.0` - For Anthropic Claude
- `requests>=2.28.0` - For Ollama HTTP API
- `python-dotenv>=1.0.0` - For environment variables

## Error Handling

The system gracefully handles:
- Missing API keys
- Network connectivity issues
- Invalid model configurations
- Provider-specific errors

Each provider includes proper error handling and fallback messages.

## Local AI with Ollama

To use Ollama (local AI):

1. Install Ollama: https://ollama.ai/
2. Pull a model: `ollama pull llama2`
3. Switch to Ollama: `model switch ollama`

No API key required for local models!
# Nexus6HealthCareDataGenerator
