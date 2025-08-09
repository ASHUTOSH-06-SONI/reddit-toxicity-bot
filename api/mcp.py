from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Mock ML function for deployment
def classify_dm(text):
    """Mock toxicity classifier"""
    # Simple keyword-based detection for demo
    toxic_words = ['hate', 'stupid', 'idiot', 'kill', 'die', 'fuck']
    text_lower = text.lower()
    
    for word in toxic_words:
        if word in text_lower:
            return "TOXIC", 0.8
    
    return "NON_TOXIC", 0.2

import praw

# Reddit configuration
REDDIT_CONFIG = {
    "client_id": "8GP0nJUPDOfiht-FUS7Cig",
    "client_secret": "6wzYEv5IZJFTJjh-o3iW5mRZ-GT-gw",
    "user_agent": "ToxicityMCP/1.0"
}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            request = json.loads(post_data.decode('utf-8'))
            response = handle_request(request)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {"status": "Reddit Toxicity MCP Server", "tools": ["validate", "analyze_reddit_user", "classify_text"]}
        self.wfile.write(json.dumps(response).encode())

def handle_request(request):
    """Handle MCP requests"""
    method = request.get("method")
    params = request.get("params", {})
    
    if method == "tools/list":
        return {
            "tools": [
                {
                    "name": "validate",
                    "description": "Validate bearer token and return phone number",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "token": {"type": "string"}
                        },
                        "required": ["token"]
                    }
                },
                {
                    "name": "analyze_reddit_user",
                    "description": "Analyze Reddit user toxicity",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "username": {"type": "string"},
                            "max_posts": {"type": "integer", "default": 10}
                        },
                        "required": ["username"]
                    }
                },
                {
                    "name": "classify_text",
                    "description": "Classify text toxicity",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"}
                        },
                        "required": ["text"]
                    }
                }
            ]
        }
    
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "validate":
            return validate_token(arguments)
        elif tool_name == "analyze_reddit_user":
            return analyze_user(arguments)
        elif tool_name == "classify_text":
            return classify_text(arguments)
    
    return {"error": "Unknown method"}

def validate_token(args):
    """Validate bearer token - required by PuchAI"""
    token = args.get("token")
    
    # Replace with your actual phone number
    if token == "reddit_toxicity_2024":  # Your bearer token
        return "918147378108"  # Your phone number
    else:
        return {"error": "Invalid token"}

def analyze_user(args):
    """Analyze Reddit user"""
    username = args.get("username")
    max_posts = args.get("max_posts", 10)
    
    try:
        reddit = praw.Reddit(**REDDIT_CONFIG)
        user = reddit.redditor(username)
        
        texts = []
        for comment in user.comments.new(limit=max_posts):
            if comment.body and comment.body != "[deleted]":
                texts.append(comment.body)
        
        toxic_count = 0
        for text in texts:
            label, score = classify_dm(text)
            if label.upper() == "TOXIC":
                toxic_count += 1
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"User: u/{username}\nTotal posts: {len(texts)}\nToxic posts: {toxic_count}\nToxicity rate: {(toxic_count/len(texts)*100):.1f}%"
                }
            ]
        }
        
    except Exception as e:
        return {"error": str(e)}

def classify_text(args):
    """Classify single text"""
    text = args.get("text")
    
    try:
        label, score = classify_dm(text)
        return {
            "content": [
                {
                    "type": "text", 
                    "text": f"Text: {text[:100]}\nClassification: {label}\nScore: {score:.3f}"
                }
            ]
        }
    except Exception as e:
        return {"error": str(e)}