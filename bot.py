import os
import sys
from datetime import datetime
import praw
from praw.exceptions import RedditAPIException, PRAWException
import time
import urllib.parse

# Add the current directory to Python path to import our model
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from securedm.model import classify_dm
    print("✅ Model imported successfully")
except ImportError as e:
    print(f"❌ Error importing model: {e}")
    sys.exit(1)

# Reddit credentials - temporarily hardcoded for Replit
REDDIT_CONFIG = {
    "client_id": os.getenv("REDDIT_CLIENT_ID") or "8GP0nJUPDOfiht-FUS7Cig",
    "client_secret": os.getenv("REDDIT_CLIENT_SECRET") or "6wzYEv5IZJFTJjh-o3iW5mRZ-GT-gw",
    "username": os.getenv("REDDIT_USERNAME") or "Unusual-Pass8282",
    "password": os.getenv("REDDIT_PASSWORD") or "Sadlife_152005",
    "user_agent": "ToxicityBot/1.0 by u/Unusual-Pass8282 and u/Recent_Custard_5092"
}

def initialize_reddit():
    """Initialize Reddit instance with error handling"""
    # Check if all required env vars are set
    required_vars = ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USERNAME', 'REDDIT_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Set them with: export REDDIT_CLIENT_ID=your_id")
        return None
    
    try:
        reddit = praw.Reddit(**REDDIT_CONFIG)
        user = reddit.user.me()
        print(f"✅ Authenticated as: {user}")
        return reddit
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None

def analyze_user(reddit, username, max_posts=10):
    """
    Analyze a user's recent posts and comments for toxicity
    Returns: (toxic_count, total_count, analysis_details)
    """
    try:
        user = reddit.redditor(username)
        texts = []
        analysis_details = []

        print(f"🔍 Analyzing user: {username}")

        # Fetch recent comments
        try:
            for comment in user.comments.new(limit=max_posts):
                if comment.body and comment.body != "[deleted]":
                    texts.append(comment.body)
                    analysis_details.append({
                        'type': 'comment',
                        'content': comment.body[:100] + "..." if len(comment.body) > 100 else comment.body,
                        'subreddit': str(comment.subreddit),
                        'created': datetime.fromtimestamp(comment.created_utc)
                    })
        except Exception as e:
            print(f"⚠️ Error fetching comments: {e}")

        # Fetch recent submissions
        try:
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
        except Exception as e:
            print(f"⚠️ Error fetching submissions: {e}")

        if not texts:
            print(f"📭 No recent posts/comments found for {username}")
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
                print(f"⚠️ Error analyzing text {i+1}: {e}")
                analysis_details[i]['toxicity_label'] = "ERROR"
                analysis_details[i]['toxicity_score'] = 0.0

        return toxic_count, len(texts), analysis_details, toxic_items

    except Exception as e:
        print(f"❌ Error analyzing user {username}: {e}")
        return None

def process_messages(reddit, limit=10):
    """Process unread messages and analyze senders"""
    try:
        messages = list(reddit.inbox.unread(limit=limit))
        
        if not messages:
            print("📬 No unread messages found")
            return
        
        print(f"📨 Processing {len(messages)} unread messages...")
        
        for message in messages:
            try:
                sender = str(message.author) if message.author else "Unknown"
                timestamp = datetime.fromtimestamp(message.created_utc)
                
                print(f"\n" + "="*50)
                print(f"📩 Message from: {sender}")
                print(f"📅 Received: {timestamp}")
                print(f"💬 Preview: {message.body[:100]}{'...' if len(message.body) > 100 else ''}")
                
                if sender != "Unknown":
                    result = analyze_user(reddit, sender)
                    
                    if result:
                        toxic_count, total, details, toxic_items = result
                        
                        if toxic_count > 0:
                            print(f"⚠️  ALERT: {toxic_count}/{total} recent posts flagged as toxic!")
                            print(f"🚨 Toxicity rate: {(toxic_count/total)*100:.1f}%")
                            
                            # Show most toxic items
                            for item in toxic_items[:3]:  # Show top 3 toxic items
                                print(f"   🔴 {item['type']}: {item['content']}")
                                print(f"      Score: {item['toxicity_score']:.3f}")
                        else:
                            print("✅ Sender appears clean based on recent activity")
                            print(f"📊 Analyzed {total} recent posts/comments")
                    else:
                        print("❓ Could not analyze user or no recent activity found")
                
                # Mark message as read
                message.mark_read()
                print("✅ Message marked as read")
                
                # Add small delay to avoid rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error processing message: {e}")
                continue
                
    except Exception as e:
        print(f"❌ Error accessing inbox: {e}")

def main():
    """Main function to run the bot continuously"""
    print("🤖 Starting Reddit Toxicity Detection Bot...")
    print("="*50)
    
    # Initialize Reddit connection
    reddit = initialize_reddit()
    if not reddit:
        print("❌ Cannot proceed without Reddit connection")
        return
    
    print("🔄 Bot running continuously... Press Ctrl+C to stop")
    
    try:
        while True:
            try:
                # Process unread messages
                process_messages(reddit)
                print(f"✅ Check completed at {datetime.now()}")
                
                # Wait 5 minutes before next check
                print("⏰ Waiting 5 minutes before next check...")
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                print("⏰ Waiting 1 minute before retry...")
                time.sleep(60)  # Wait 1 minute before retry
                
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()