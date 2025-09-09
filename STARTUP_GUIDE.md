# Nexus6 Healthcare Data Generator - Startup Guide

## Quick Start

This project includes automated startup scripts that handle dependency installation and launch the web interface automatically.

### For Linux/macOS/WSL Users

```bash
./start.sh
```

### For Windows Users

**Option 1: Using the batch file (recommended)**
```cmd
start.bat
```

**Option 2: Using bash (if you have Git Bash, WSL, or Cygwin)**
```bash
./start.sh
```

## What the Scripts Do

Both scripts automatically:

1. ✅ **Check System Requirements**
   - Verify Python 3.9+ is installed
   - Verify pip is available
   - Display helpful error messages if requirements are missing

2. ✅ **Install Dependencies**
   - Install all required Python packages from `requirements.txt`
   - Try multiple installation methods if needed (with `--user` flag as fallback)

3. ✅ **Launch Web Server**
   - Start the Flask web server (`integrated_chatbot_server.py`)
   - Wait for server to be ready
   - Automatically open your default browser to `http://localhost:5000`

4. ✅ **Cross-Platform Browser Opening**
   - **Linux**: Uses `xdg-open`
   - **macOS**: Uses `open`
   - **Windows**: Uses `start` command

## Manual Installation (Alternative)

If you prefer to set up manually:

```bash
# Install dependencies
pip install -r requirements.txt

# Start the web server
python integrated_chatbot_server.py

# Open browser manually
# Navigate to: http://localhost:5000
```

## Troubleshooting

### Python Not Found
- **Linux/macOS**: Install Python 3.9+ using your package manager or from [python.org](https://python.org)
- **Windows**: Download and install Python from [python.org](https://python.org), make sure to check "Add to PATH"

### Permission Denied (Linux/macOS)
```bash
chmod +x start.sh
./start.sh
```

### Dependencies Installation Failed
Try upgrading pip first:
```bash
pip install --upgrade pip
```

Then run the startup script again.

### Server Won't Start
1. Check if port 5000 is already in use
2. Make sure `integrated_chatbot_server.py` exists in the project directory
3. Verify all dependencies are installed correctly

### Browser Doesn't Open Automatically
The scripts will display the URL. Manually open your browser and navigate to:
```
http://localhost:5000
```

## API Keys Configuration

Before using the AI features, you'll need to configure API keys in `config.py`:

1. Open `config.py`
2. Replace placeholder keys with your actual API keys:
   ```python
   API_KEYS = {
       AIProvider.GEMINI: "your-actual-gemini-api-key",
       AIProvider.OPENAI: "your-actual-openai-api-key",
       AIProvider.ANTHROPIC: "your-actual-anthropic-api-key",
       AIProvider.OLLAMA: None,  # Local model, no key needed
   }
   ```

## Features Available After Startup

Once the web interface is running, you can:

- 📊 **Upload Healthcare Data**: CSV or Excel files
- 🤖 **Chat with AI Models**: Switch between Gemini, OpenAI, Claude, or Ollama
- 📈 **Analyze Data**: Get insights, summaries, and visualizations
- 🔒 **Privacy Protection**: Automatic PII/PHI detection and masking
- 📋 **Generate Synthetic Data**: Create privacy-safe datasets

## Stopping the Server

### Linux/macOS (start.sh)
Press `Ctrl+C` in the terminal where the script is running.

### Windows (start.bat)
Press any key in the command prompt window to stop the server.

## Development Mode

For development, you can also run individual components:

```bash
# Command-line chatbot interface
python main.py

# Quick configuration demo
python quick_start_example.py

# Web server only
python integrated_chatbot_server.py
```

## System Requirements

- **Python**: 3.9 or higher
- **Operating System**: Windows 10+, macOS 10.14+, or Linux
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Storage**: 1GB free space
- **Network**: Internet connection for AI API calls (except Ollama)

## Support

If you encounter issues:

1. Check this troubleshooting guide
2. Verify system requirements
3. Try manual installation steps
4. Check the project's GitHub issues page
