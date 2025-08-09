#!/usr/bin/env python3
"""
Simple Reddit Toxicity Detection MCP Server
"""

import json
import sys
from securedm.model import classify_dm
import praw

# Reddit configuration
REDDIT_CONFIG = {
    "client_id": "8GP0nJUPDOfiht-FUS7Cig",
    "client_secret": "6wzYEv5IZJFTJjh-o3iW5mRZ-GT-gw",
    "user_agent": "ToxicityMCP/1.0"
}

def handle_request(request):
    """Handle MCP requests"""
    method = request.get("method")
    params = request.get("params", {})
    
    if method == "tools/list":
        return {
            "tools": [
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
        
        if tool_name == "analyze_reddit_user":
            return analyze_user(arguments)
        elif tool_name == "classify_text":
            return classify_text(arguments)
    
    return {"error": "Unknown method"}

def analyze_user(args):
    """Analyze Reddit user"""
    username = args.get("username")
    max_posts = args.get("max_posts", 10)
    
    try:
        reddit = praw.Reddit(**REDDIT_CONFIG)
        user = reddit.redditor(username)
        
        texts = []
        # Get recent comments
        for comment in user.comments.new(limit=max_posts):
            if comment.body and comment.body != "[deleted]":
                texts.append(comment.body)
        
        # Analyze toxicity
        toxic_count = 0
        results = []
        
        for text in texts:
            label, score = classify_dm(text)
            if label.upper() == "TOXIC":
                toxic_count += 1
            results.append({"text": text[:100], "label": label, "score": score})
        
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

def main():
    """Main MCP server loop"""
    print("Reddit Toxicity MCP Server started", file=sys.stderr)
    
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except Exception as e:
            error_response = {"error": str(e)}
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    main()

