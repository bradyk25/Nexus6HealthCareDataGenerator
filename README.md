# Nexus6 Health Data & Multi-AI Chatbot

## Mission
Provide a flexible, chatbot-style service for exploring and generating synthetic healthcare datasets. The system combines multi-model AI support with privacy-safe data synthesis, enabling experimentation across different providers while ensuring sensitive data is protected.

## Project Overview
Nexus6 is designed to:
- Ingest messy, inconsistent healthcare data
- Infer schema and distributions
- Detect and mask PII/PHI
- Generate trustworthy synthetic datasets
- Allow users to interact via a chatbot powered by multiple AI providers

The result: a development-friendly tool to simulate realistic healthcare datasets without compromising privacy.

---

## Core Features

### Synthetic Data Pipeline
- Zip file upload/download
- Schema inference with JSON output
- PII/PHI detection and masking
- Distribution-matching synthetic generation
- Statistical validation suite
- Deterministic reproducibility

### Chatbot Capabilities
- Multi-AI support: Google Gemini, OpenAI GPT, Anthropic Claude, Ollama (local)
- Simple runtime model switching (`model switch openai`, etc.)
- Conversation history and context management
- Built-in commands for model and session management
- Modular architecture for adding new providers

### Stretch Capabilities (Planned)
- Differential privacy integration
- Anomaly simulation
- Synthetic free-text generation
- Active schema editor

---

## Tech Stack
- **Frontend**: React.js with TypeScript (chat UI, file upload, report view)  
- **Backend**: Node.js with Express (API routes, file handling, session management)  
- **Data Pipeline**: Python with pandas, numpy (schema inference, privacy detection, synthesis)  
- **Synthetic Data Generation**: dbtwin API  
- **Chatbot Framework**: Modular system supporting multiple AI providers  
- **Database**: SQLite (session management)  
- **File Handling**: multer (uploads/downloads)  

---

## Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend       │    │  Data Pipeline  │
│   (React)       │◄──►│   (Node.js)      │◄──►│   (Python)      │
│                 │    │                  │    │                 │
│ - Chat Interface│    │ - API Routes     │    │ - Schema Infer  │
│ - File Upload   │    │ - File Handling  │    │ - PII Detection │
│ - Reports View  │    │ - Session Mgmt   │    │ - Synthesis     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  External APIs   │
                       │                  │
                       │ - Listening Post │
                       │ - dbtwin API     │
                       └──────────────────┘
```

---

## Getting Started

### Prerequisites
- Node.js 18+  
- Python 3.9+  
- npm or yarn  
- API keys for AI providers (optional for Ollama/local)  

### Installation
```
# Clone repository
git clone <repository-url>
cd nexus6

# Install dependencies
npm install
pip install -r requirements.txt

# Configure API keys
cp config.example.py config.py
# edit config.py with your keys

# Start dev servers
npm run dev
```

## API Documentation
See `docs/API.md` for endpoint specifications.

## Contributing
This is a hackathon project. See `CONTRIBUTING.md` for development guidelines.

## License
MIT License - see LICENSE file for details.

## Contributors
- [Thang Hua](https://www.linkedin.com/in/thanghua20/) – Full-stack/System Design  
- [Aidan Martin](https://www.linkedin.com/in/aidanjmartin/) – Algorithmic Architect  
- [Hernan Hernandez](https://www.linkedin.com/in/hernan-hernandez-4a796328a/) – UX  
- [Gabrielle Miller](https://www.linkedin.com/in/gabrielle-miller-mtsu/) – Frontend Styling  
- [Carol Li](https://www.linkedin.com/in/carol-li-217664326/) – Machine Learning Theory  
- [Brady Reed](https://www.linkedin.com/in/brady-reed/) – Prompt/Framework Engineering
