# model.py
from transformers import pipeline
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import torch
import re

# Download NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

# Device setup for Mac M1/MPS or fallback to CPU
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Device set to use {device}")

# Preprocessing function
def clean_text(text):
    if not text or not isinstance(text, str):
        return ""
    
    # Remove URLs, mentions, and special characters
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'@\w+|#\w+', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    
    # Lowercase
    text = text.lower().strip()
    
    if not text:
        return ""
    
    try:
        # Tokenize
        words = nltk.word_tokenize(text)
        # Remove stopwords and non-alphanumeric
        stop_words = set(stopwords.words('english'))
        words = [w for w in words if w.isalnum() and w not in stop_words and len(w) > 2]
        
        # Lemmatize
        lemmatizer = WordNetLemmatizer()
        words = [lemmatizer.lemmatize(w) for w in words]
        
        return " ".join(words)
    except Exception as e:
        print(f"Error processing text: {e}")
        return text

# Load toxicity detection model
device_index = 0 if device.type != "cpu" else -1

try:
    toxic_model = pipeline(
        "text-classification",
        model="unitary/toxic-bert",
        tokenizer="unitary/toxic-bert",
        device=device_index,
        truncation=True,
        max_length=512
    )
    print("✅ Toxicity model loaded successfully")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    toxic_model = None

def classify_dm(message):
    """
    Classify a direct message for toxicity
    Returns: (label, score) tuple
    """
    if not toxic_model:
        return "UNKNOWN", 0.0
    
    if not message or not isinstance(message, str):
        return "NON_TOXIC", 0.0
    
    try:
        cleaned = clean_text(message)
        if not cleaned:
            return "NON_TOXIC", 0.0
            
        result = toxic_model(cleaned, truncation=True, max_length=512)
        
        # Handle both single prediction and batch prediction formats
        if isinstance(result, list) and len(result) > 0:
            result = result[0]
        
        label = result.get('label', 'UNKNOWN')
        score = result.get('score', 0.0)
        
        return label, score
        
    except Exception as e:
        print(f"Error classifying message: {e}")
        return "ERROR", 0.0