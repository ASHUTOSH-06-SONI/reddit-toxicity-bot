from flask import Flask, render_template, request, jsonify
import os
import praw
from securedm.model import classify_dm
from datetime import datetime

app = Flask(__name__)

# Reddit credentials
REDDIT_CONFIG = {
    "client_id": os.getenv("REDDIT_CLIENT_ID", "8GP0nJUPDOfiht-FUS7Cig"),
    "client_secret": os.getenv("REDDIT_CLIENT_SECRET", "6wzYEv5IZJFTJjh-o3iW5mRZ-GT-gw"),
    "user_agent": "ToxicityAnalyzer/1.0"
}

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Reddit Toxicity Analyzer</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
            .container { text-align: center; }
            input[type="text"] { padding: 10px; width: 300px; margin: 10px; }
            button { padding: 10px 20px; background: #ff4500; color: white; border: none; cursor: pointer; }
            .results { margin-top: 30px; text-align: left; }
            .toxic { color: red; }
            .clean { color: green; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Reddit Toxicity Analyzer</h1>
            <p>Enter a Reddit username to analyze their recent posts for toxicity</p>
            
            <form id="analyzeForm">
                <input type="text" id="username" placeholder="Enter Reddit username" required>
                <br>
                <button type="submit">Analyze User</button>
            </form>
            
            <div id="loading" style="display:none;">
                <p>🔄 Analyzing user... Please wait</p>
            </div>
            
            <div id="results"></div>
        </div>

        <script>
            document.getElementById('analyzeForm').onsubmit = function(e) {
                e.preventDefault();
                const username = document.getElementById('username').value;
                const loading = document.getElementById('loading');
                const results = document.getElementById('results');
                
                loading.style.display = 'block';
                results.innerHTML = '';
                
                fetch('/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username: username})
                })
                .then(response => response.json())
                .then(data => {
                    loading.style.display = 'none';
                    if (data.error) {
                        results.innerHTML = '<p style="color:red;">❌ ' + data.error + '</p>';
                    } else {
                        displayResults(data);
                    }
                });
            };
            
            function displayResults(data) {
                const results = document.getElementById('results');
                const toxicRate = ((data.toxic_count / data.total_count) * 100).toFixed(1);
                
                let html = '<div class="results">';
                html += '<h2>📊 Analysis Results for u/' + data.username + '</h2>';
                html += '<p><strong>Total Posts Analyzed:</strong> ' + data.total_count + '</p>';
                html += '<p><strong>Toxic Posts:</strong> ' + data.toxic_count + '</p>';
                html += '<p><strong>Toxicity Rate:</strong> <span class="' + (data.toxic_count > 0 ? 'toxic' : 'clean') + '">' + toxicRate + '%</span></p>';
                
                if (data.toxic_items.length > 0) {
                    html += '<h3>🚨 Toxic Content Examples:</h3>';
                    data.toxic_items.slice(0, 3).forEach(item => {
                        html += '<div style="border-left: 3px solid red; padding-left: 10px; margin: 10px 0;">';
                        html += '<p><strong>' + item.type + ':</strong> ' + item.content + '</p>';
                        html += '<p><small>Score: ' + item.toxicity_score.toFixed(3) + '</small></p>';
                        html += '</div>';
                    });
                }
                
                html += '</div>';
                results.innerHTML = html;
            }
        </script>
    </body>
    </html>
    '''

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({'error': 'Username required'})
        
        # Initialize Reddit (read-only)
        reddit = praw.Reddit(**REDDIT_CONFIG)
        
        # Analyze user
        result = analyze_user(reddit, username)
        
        if not result:
            return jsonify({'error': 'User not found or no recent posts'})
        
        toxic_count, total_count, details, toxic_items = result
        
        return jsonify({
            'username': username,
            'toxic_count': toxic_count,
            'total_count': total_count,
            'toxic_items': toxic_items[:5]  # Top 5 toxic items
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

def analyze_user(reddit, username, max_posts=10):
    try:
        user = reddit.redditor(username)
        texts = []
        analysis_details = []

        # Fetch recent comments
        for comment in user.comments.new(limit=max_posts):
            if comment.body and comment.body != "[deleted]":
                texts.append(comment.body)
                analysis_details.append({
                    'type': 'comment',
                    'content': comment.body[:100] + "..." if len(comment.body) > 100 else comment.body,
                    'subreddit': str(comment.subreddit),
                    'created': datetime.fromtimestamp(comment.created_utc)
                })

        # Fetch recent submissions
        for submission in user.submissions.new(limit=max_posts):
            content = submission.title
            if submission.selftext:
                content += " " + submission.selftext
            
            texts.append(content)
            analysis_details.append({
                'type': 'submission',
                'content': content[:100] + "..." if len(content) > 100 else content,
                'subreddit': str(submission.subreddit),
                'created': datetime.fromtimestamp(submission.created_utc)
            })

        if not texts:
            return None

        # Analyze each text for toxicity
        toxic_count = 0
        toxic_items = []
        
        for i, text in enumerate(texts):
            try:
                label, score = classify_dm(text)
                analysis_details[i]['toxicity_label'] = label
                analysis_details[i]['toxicity_score'] = score
                
                if label and label.upper() == "TOXIC":
                    toxic_count += 1
                    toxic_items.append(analysis_details[i])
                    
            except Exception as e:
                analysis_details[i]['toxicity_label'] = "ERROR"
                analysis_details[i]['toxicity_score'] = 0.0

        return toxic_count, len(texts), analysis_details, toxic_items

    except Exception as e:
        return None

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
