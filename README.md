# Reddit Toxicity Detection System

A comprehensive Reddit toxicity detection system with ML model, available as bot, web app, and MCP server.

## Features

- 🤖 **ML-powered toxicity detection** using BERT model
- 📊 **Reddit user analysis** - analyze recent posts/comments
- 🔧 **Multiple interfaces**: Bot, Web App, MCP Server
- 🚀 **Real-time classification** of text content

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export REDDIT_CLIENT_ID=your_client_id
export REDDIT_CLIENT_SECRET=your_client_secret
export REDDIT_USERNAME=your_username  # For bot only
export REDDIT_PASSWORD=your_password   # For bot only
```

## Usage

### MCP Server (Model Context Protocol)
```bash
python simple_mcp_server.py
```

**Available Tools:**
- `analyze_reddit_user` - Analyze user's recent posts for toxicity
- `classify_text` - Classify single text for toxicity

### Web App
```bash
python webapp.py
```
Visit `http://localhost:5000` to use the web interface.

### Bot (Auto-message processing)
```bash
python bot.py
```

## MCP Server Integration

The MCP server provides Reddit toxicity detection as tools that other applications can use:

```json
{"method": "tools/call", "params": {"name": "analyze_reddit_user", "arguments": {"username": "someuser"}}}
```
