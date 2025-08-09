import pandas as pd
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from model import clean_text
    print("✅ Model imported successfully")
except ImportError as e:
    print(f"❌ Error importing model: {e}")
    sys.exit(1)

def preprocess_dataset(csv_path="train.csv", output_path="processed_dataset.csv", text_column="comment_text"):
    """
    Preprocess a dataset by cleaning text data
    
    Args:
        csv_path (str): Path to input CSV file
        output_path (str): Path to save processed CSV
        text_column (str): Name of the column containing text data
    """
    
    # Check if input file exists
    if not os.path.exists(csv_path):
        print(f"❌ Error: File '{csv_path}' not found")
        return False
    
    try:
        # Load CSV
        print(f"📂 Loading dataset from {csv_path}...")
        df = pd.read_csv(csv_path)
        print(f"✅ Loaded {len(df)} rows")
        
        # Check if required column exists
        if text_column not in df.columns:
            print(f"❌ Error: Column '{text_column}' not found in CSV")
            print(f"Available columns: {list(df.columns)}")
            return False
        
        # Handle missing values
        initial_count = len(df)
        df = df.dropna(subset=[text_column])
        final_count = len(df)
        
        if initial_count != final_count:
            print(f"⚠️ Removed {initial_count - final_count} rows with missing text")
        
        # Clean text column
        print("🧹 Cleaning text data...")
        df['cleaned_text'] = df[text_column].apply(lambda x: clean_text(str(x)) if pd.notna(x) else "")
        
        # Remove rows where cleaned text is empty
        df = df[df['cleaned_text'].str.len() > 0]
        print(f"✅ Processed {len(df)} rows with valid cleaned text")
        
        # Add text length statistics
        df['original_length'] = df[text_column].str.len()
        df['cleaned_length'] = df['cleaned_text'].str.len()
        
        # Save processed dataset
        df.to_csv(output_path, index=False)
        print(f"💾 Saved processed dataset to {output_path}")
        
        # Print statistics
        print("\n📊 Processing Statistics:")
        print(f"   Original rows: {initial_count}")
        print(f"   Final rows: {len(df)}")
        print(f"   Average original length: {df['original_length'].mean():.1f} characters")
        print(f"   Average cleaned length: {df['cleaned_length'].mean():.1f} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing dataset: {e}")
        return False

def main():
    """Main function for preprocessing"""
    print("🔄 Starting dataset preprocessing...")
    print("="*50)
    
    # Default file paths
    input_file = "train.csv"
    output_file = "processed_dataset.csv"
    
    # Check if custom paths are provided via command line
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    success = preprocess_dataset(input_file, output_file)
    
    if success:
        print("\n✅ Preprocessing completed successfully!")
    else:
        print("\n❌ Preprocessing failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()