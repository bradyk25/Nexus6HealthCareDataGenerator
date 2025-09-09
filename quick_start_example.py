#!/usr/bin/env python3
"""
Quick Start Example - Demonstrates how easy it is to switch AI models
"""

from config import Config, AIProvider

def main():
    print("PHARA AI CHATBOT - QUICK MODEL SWITCHING DEMO")
    print("=" * 55)
    print()
    
    print("STEP 1: Current Configuration")
    print("-" * 30)
    current_config = Config.get_active_config()
    print(f"Active Model: {current_config.provider.value}")
    print(f"Model Name: {current_config.model_name}")
    print(f"API Key: {'✓ Configured' if current_config.api_key and not current_config.api_key.startswith('your-') else '✗ Not configured'}")
    print()
    
    print("STEP 2: How to Switch Models")
    print("-" * 30)
    print("Method 1 - Edit config.py:")
    print("   Change: ACTIVE_MODEL = AIProvider.GEMINI")
    print("   To:     ACTIVE_MODEL = AIProvider.OPENAI")
    print()
    print("Method 2 - Runtime switching in chat:")
    print("   Type: model switch openai")
    print("   Type: model switch anthropic")
    print("   Type: model switch ollama")
    print()
    
    print("STEP 3: API Key Management")
    print("-" * 30)
    print("Edit config.py and update API_KEYS:")
    print()
    print("API_KEYS = {")
    for provider in AIProvider:
        config = Config.MODEL_CONFIGS[provider]
        status = "✓" if config.api_key and not config.api_key.startswith("your-") else "✗"
        if provider == AIProvider.OLLAMA:
            print(f"    AIProvider.{provider.name}: None,  # {status} Local model")
        else:
            print(f"    AIProvider.{provider.name}: \"your-{provider.value}-api-key\",  # {status}")
    print("}")
    print()
    
    print("STEP 4: Available Models")
    print("-" * 30)
    for provider in AIProvider:
        config = Config.MODEL_CONFIGS[provider]
        status = "🟢" if config.api_key and not config.api_key.startswith("your-") else "🔴"
        print(f"{status} {provider.value.upper()}: {config.model_name}")
    print()
    
    print("STEP 5: Start Chatting")
    print("-" * 30)
    print("Run: python main.py")
    print()
    print("Try these commands:")
    print("• model list          - See all available models")
    print("• model               - Show current model info")
    print("• model switch gemini - Switch to Google Gemini")
    print("• help                - Show all commands")
    print()
    
    print("PRO TIPS:")
    print("-" * 30)
    print("• Ollama runs locally (no API key needed)")
    print("• Each model has different strengths")
    print("• Conversation history is maintained when switching")
    print("• API keys are hardcoded for quick development")
    print()

if __name__ == "__main__":
    main()
