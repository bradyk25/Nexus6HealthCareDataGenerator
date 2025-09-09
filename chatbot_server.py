#!/usr/bin/env python3
"""
Flask Web API Server for Phara Chatbot Integration
Provides REST endpoints for the healthcare analytics interface
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from brain import Brain
from config import AIProvider
import os
import json
import traceback
from werkzeug.utils import secure_filename
import tempfile
import shutil

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Initialize Phara Brain
try:
    brain = Brain()
    print("✓ Phara Brain initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize Phara Brain: {e}")
    brain = None

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'brain_initialized': brain is not None,
        'message': 'Phara Chatbot API is running'
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint with context-aware responses"""
    try:
        if not brain:
            return jsonify({
                'error': 'Brain not initialized',
                'response': 'I apologize, but the AI system is not properly initialized. Please check the server configuration.'
            }), 500
        
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Check if we have loaded files to provide context
        loaded_files = brain.get_loaded_files()
        
        # Enhance the user message with context about loaded data
        if loaded_files:
            current_file = loaded_files[0] if loaded_files else None
            context_message = f"""
            Context: The user has uploaded and I am currently analyzing the file '{current_file}'. 
            Please focus your response on this specific dataset and provide insights, analysis, or answers 
            related to this uploaded file. Steer the conversation toward analyzing this data.
            
            User question: {user_message}
            """
        else:
            context_message = f"""
            Context: No data file has been uploaded yet. Encourage the user to upload a healthcare 
            data file so I can provide specific analysis and insights about their data.
            
            User question: {user_message}
            """
        
        # Process the enhanced message through Phara's brain
        response = brain.think(context_message)
        
        return jsonify({
            'response': response,
            'model_info': brain.get_current_model_info(),
            'loaded_file': loaded_files[0] if loaded_files else None,
            'has_data': len(loaded_files) > 0
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        traceback.print_exc()
        return jsonify({
            'error': 'Internal server error',
            'response': 'I encountered an error while processing your request. Please try again.'
        }), 500

@app.route('/api/model/info', methods=['GET'])
def get_model_info():
    """Get current model information"""
    try:
        if not brain:
            return jsonify({'error': 'Brain not initialized'}), 500
        
        info = brain.get_current_model_info()
        return jsonify(info)
        
    except Exception as e:
        print(f"Model info error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/model/switch', methods=['POST'])
def switch_model():
    """Switch AI model"""
    try:
        if not brain:
            return jsonify({'error': 'Brain not initialized'}), 500
        
        data = request.get_json()
        if not data or 'provider' not in data:
            return jsonify({'error': 'No provider specified'}), 400
        
        provider_name = data['provider'].lower()
        try:
            provider = AIProvider(provider_name)
            result = brain.switch_model(provider)
            
            return jsonify({
                'success': True,
                'message': result,
                'model_info': brain.get_current_model_info()
            })
            
        except ValueError:
            return jsonify({
                'error': f'Unknown provider: {provider_name}',
                'available_providers': [p.value for p in AIProvider]
            }), 400
            
    except Exception as e:
        print(f"Model switch error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/model/list', methods=['GET'])
def list_models():
    """List available AI models"""
    try:
        from config import Config
        
        models = []
        for provider in AIProvider:
            config = Config.MODEL_CONFIGS[provider]
            is_configured = (config.api_key and 
                           config.api_key != "your-openai-api-key-here" and 
                           config.api_key != "your-anthropic-api-key-here")
            
            models.append({
                'provider': provider.value,
                'model_name': config.model_name,
                'configured': is_configured,
                'temperature': config.temperature,
                'max_tokens': config.max_tokens
            })
        
        return jsonify({'models': models})
        
    except Exception as e:
        print(f"List models error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/list', methods=['GET'])
def list_files():
    """List available data files"""
    try:
        if not brain:
            return jsonify({'error': 'Brain not initialized'}), 500
        
        available_files = brain.get_available_files()
        loaded_files = brain.get_loaded_files()
        
        files_info = []
        for filename in available_files:
            files_info.append({
                'filename': filename,
                'loaded': filename in loaded_files
            })
        
        return jsonify({
            'files': files_info,
            'total_available': len(available_files),
            'total_loaded': len(loaded_files)
        })
        
    except Exception as e:
        print(f"List files error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/upload', methods=['POST'])
def upload_file():
    """Upload and analyze any file type"""
    try:
        if not brain:
            return jsonify({'error': 'Brain not initialized'}), 500
        
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Secure the filename and save to data directory
        filename = secure_filename(file.filename)
        data_dir = 'data'
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        file_path = os.path.join(data_dir, filename)
        file.save(file_path)
        
        print(f"📁 File uploaded: {filename}")
        
        # Immediately load the file into Phara's brain
        success, message = brain.load_data_file(filename)
        
        if success:
            # Get suggestions for the loaded file
            suggestions = brain.get_data_suggestions()
            
            # Get basic file info
            file_size = os.path.getsize(file_path)
            file_info = {
                'filename': filename,
                'size': file_size,
                'size_mb': round(file_size / (1024 * 1024), 2)
            }
            
            return jsonify({
                'success': True,
                'message': f"Successfully uploaded and analyzed {filename}",
                'file_info': file_info,
                'analysis': message,
                'suggestions': suggestions[:5] if suggestions else [],
                'loaded_file': filename
            })
        else:
            # Remove the file if it couldn't be processed
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({
                'success': False,
                'error': f"Failed to analyze {filename}: {message}"
            }), 400
            
    except Exception as e:
        print(f"Upload file error: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Failed to upload file: {str(e)}'}), 500

@app.route('/api/files/load', methods=['POST'])
def load_file():
    """Load a data file"""
    try:
        if not brain:
            return jsonify({'error': 'Brain not initialized'}), 500
        
        data = request.get_json()
        if not data or 'filename' not in data:
            return jsonify({'error': 'No filename provided'}), 400
        
        filename = data['filename']
        success, message = brain.load_data_file(filename)
        
        if success:
            # Get suggestions for the loaded file
            suggestions = brain.get_data_suggestions()
            
            return jsonify({
                'success': True,
                'message': message,
                'suggestions': suggestions[:5] if suggestions else []
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        print(f"Load file error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/suggestions', methods=['GET'])
def get_suggestions():
    """Get data analysis suggestions"""
    try:
        if not brain:
            return jsonify({'error': 'Brain not initialized'}), 500
        
        suggestions = brain.get_data_suggestions()
        
        return jsonify({
            'suggestions': suggestions if suggestions else [],
            'count': len(suggestions) if suggestions else 0
        })
        
    except Exception as e:
        print(f"Suggestions error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/query', methods=['POST'])
def query_data():
    """Execute a data query"""
    try:
        if not brain:
            return jsonify({'error': 'Brain not initialized'}), 500
        
        data = request.get_json()
        if not data or 'query_type' not in data:
            return jsonify({'error': 'No query type provided'}), 400
        
        query_type = data['query_type']
        kwargs = data.get('params', {})
        
        result = brain.query_data(query_type, **kwargs)
        
        return jsonify({
            'result': result,
            'query_type': query_type
        })
        
    except Exception as e:
        print(f"Data query error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    """Clear conversation history"""
    try:
        if not brain:
            return jsonify({'error': 'Brain not initialized'}), 500
        
        brain.clear_history()
        
        return jsonify({
            'success': True,
            'message': 'Conversation history cleared'
        })
        
    except Exception as e:
        print(f"Clear history error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/get', methods=['GET'])
def get_history():
    """Get conversation history"""
    try:
        if not brain:
            return jsonify({'error': 'Brain not initialized'}), 500
        
        history = brain.get_history()
        
        return jsonify({
            'history': history[-20:] if history else [],  # Last 20 entries
            'total_entries': len(history) if history else 0
        })
        
    except Exception as e:
        print(f"Get history error: {e}")
        return jsonify({'error': str(e)}), 500

# Serve static files (for the frontend)
@app.route('/')
def serve_frontend():
    """Serve the main frontend file"""
    return send_from_directory('.', 'nexus_analytics_integrated.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('.', filename)

def main():
    """Main entry point"""
    print("🚀 Starting Phara Chatbot Web API Server...")
    print("📡 Server will be available at: http://localhost:5001")
    print("🔗 API endpoints:")
    print("   - POST /api/chat - Main chat endpoint")
    print("   - GET  /api/model/info - Get current model info")
    print("   - POST /api/model/switch - Switch AI model")
    print("   - GET  /api/model/list - List available models")
    print("   - GET  /api/files/list - List data files")
    print("   - POST /api/files/load - Load data file")
    print("   - GET  /api/data/suggestions - Get analysis suggestions")
    print("   - POST /api/data/query - Execute data query")
    print("   - POST /api/history/clear - Clear chat history")
    print("   - GET  /api/history/get - Get chat history")
    print("   - GET  /api/health - Health check")
    print()
    
    if not brain:
        print("⚠️  Warning: Brain not initialized. Check your API keys and configuration.")
        print("   The server will start but chat functionality may not work properly.")
        print()
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5001, debug=True)

if __name__ == "__main__":
    main()
