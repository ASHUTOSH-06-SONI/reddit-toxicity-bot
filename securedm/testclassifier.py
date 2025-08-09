import pandas as pd
import os
import sys
from datetime import datetime
import time

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from model import toxic_model, clean_text, classify_dm
    print("✅ Model imported successfully")
except ImportError as e:
    print(f"❌ Error importing model: {e}")
    sys.exit(1)

def test_classifier(csv_path="train.csv", output_path="predictions.csv", batch_size=32, text_column="comment_text"):
    """
    Test the toxicity classifier on a dataset
    
    Args:
        csv_path (str): Path to input CSV file
        output_path (str): Path to save predictions
        batch_size (int): Number of texts to process at once
        text_column (str): Name of column containing text data
    """
    
    # Check if input file exists
    if not os.path.exists(csv_path):
        print(f"❌ Error: File '{csv_path}' not found")
        return False
    
    try:
        # Load dataset
        print(f"📂 Loading dataset from {csv_path}...")
        df = pd.read_csv(csv_path)
        print(f"✅ Loaded {len(df)} rows")
        
        # Validate required column
        if text_column not in df.columns:
            print(f"❌ Error: Column '{text_column}' not found")
            print(f"Available columns: {list(df.columns)}")
            return False
        
        # Handle resuming from previous run
        start_index = 0
        if os.path.exists(output_path):
            try:
                existing_df = pd.read_csv(output_path)
                start_index = len(existing_df)
                print(f"📄 Found existing predictions file with {start_index} rows")
                print(f"🔄 Resuming from row {start_index}")
                results_df = existing_df.copy()
            except Exception as e:
                print(f"⚠️ Error reading existing file: {e}")
                print("🆕 Starting fresh...")
                results_df = pd.DataFrame(columns=["original_text", "cleaned_text", "label", "score", "timestamp"])
        else:
            results_df = pd.DataFrame(columns=["original_text", "cleaned_text", "label", "score", "timestamp"])
        
        # Process in batches
        total_rows = len(df)
        processed_count = start_index
        
        print(f"🚀 Starting classification from row {start_index}/{total_rows}")
        print("="*50)
        
        for batch_start in range(start_index, total_rows, batch_size):
            batch_end = min(batch_start + batch_size, total_rows)
            batch_texts = df[text_column].iloc[batch_start:batch_end].tolist()
            
            batch_results = []
            
            for i, original_text in enumerate(batch_texts):
                try:
                    # Skip empty or invalid texts
                    if pd.isna(original_text) or not str(original_text).strip():
                        batch_results.append({
                            "original_text": str(original_text) if not pd.isna(original_text) else "",
                            "cleaned_text": "",
                            "label": "EMPTY",
                            "score": 0.0,
                            "timestamp": datetime.now().isoformat()
                        })
                        continue
                    
                    # Clean and classify text
                    cleaned_text = clean_text(str(original_text))
                    
                    if not cleaned_text:
                        label, score = "EMPTY", 0.0
                    else:
                        label, score = classify_dm(original_text)
                    
                    batch_results.append({
                        "original_text": str(original_text)[:500],  # Limit length for storage
                        "cleaned_text": cleaned_text[:500],
                        "label": label,
                        "score": float(score),
                        "timestamp": datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    print(f"⚠️ Error processing text {batch_start + i}: {e}")
                    batch_results.append({
                        "original_text": str(original_text)[:500] if not pd.isna(original_text) else "",
                        "cleaned_text": "",
                        "label": "ERROR",
                        "score": 0.0,
                        "timestamp": datetime.now().isoformat()
                    })
            
            # Add batch results to main dataframe
            batch_df = pd.DataFrame(batch_results)
            results_df = pd.concat([results_df, batch_df], ignore_index=True)
            
            # Save progress
            results_df.to_csv(output_path, index=False)
            
            processed_count = batch_end
            progress = (processed_count / total_rows) * 100
            
            print(f"✅ Processed batch {batch_start}-{batch_end-1} | Progress: {progress:.1f}% ({processed_count}/{total_rows})")
            
            # Small delay to prevent overwhelming the system
            time.sleep(0.1)
        
        # Final statistics
        print("\n📊 Classification Results:")
        print("="*30)
        
        label_counts = results_df['label'].value_counts()
        for label, count in label_counts.items():
            percentage = (count / len(results_df)) * 100
            print(f"   {label}: {count} ({percentage:.1f}%)")
        
        print(f"\n💾 Final results saved to {output_path}")
        print(f"✅ Successfully processed {len(results_df)} texts")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during classification: {e}")
        return False

def main():
    """Main function for testing classifier"""
    print("🧪 Starting toxicity classifier testing...")
    print("="*50)
    
    # Default parameters
    input_file = "train.csv"
    output_file = "predictions.csv"
    batch_size = 32
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    if len(sys.argv) > 3:
        try:
            batch_size = int(sys.argv[3])
        except ValueError:
            print("⚠️ Invalid batch size, using default: 32")
    
    print(f"📋 Configuration:")
    print(f"   Input file: {input_file}")
    print(f"   Output file: {output_file}")
    print(f"   Batch size: {batch_size}")
    print()
    
    success = test_classifier(input_file, output_file, batch_size)
    
    if success:
        print("\n🎉 Testing completed successfully!")
    else:
        print("\n❌ Testing failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()