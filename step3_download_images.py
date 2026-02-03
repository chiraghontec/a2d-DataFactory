"""
Step 3: Download Product Images
Downloads images from URLs and saves them with sanitized filenames.
"""

import os
import pandas as pd
import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from urllib.parse import urlparse

# Configuration
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def sanitize_filename(name):
    """Sanitize the string to be safe for filenames."""
    if pd.isna(name):
        return "unknown_product"
    clean = re.sub(r'[^a-zA-Z0-9_\-]', '_', str(name))
    return clean[:50]  # Limit length

def extract_url(image_link_str):
    """Extracts URL from strings."""
    if pd.isna(image_link_str) or not isinstance(image_link_str, str):
        return None
    
    url_pattern = r'(https?://[^\s]+)'
    match = re.search(url_pattern, image_link_str)
    if match:
        return match.group(1)
    return None

def download_image(row_data, image_dir):
    """Downloads image for a single row."""
    index, sku, image_link_raw = row_data
    
    url = extract_url(image_link_raw)
    if not url or "not found" in str(url).lower():
        return index, None

    try:
        # Use SKU for filename
        filename = f"{sku}.jpg"
        save_path = os.path.join(image_dir, filename)
        
        response = requests.get(url, headers=HEADERS, timeout=15, stream=True)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        return index, filename

    except Exception as e:
        return index, None

def download_images_from_csv(input_csv, output_csv, image_dir):
    """Main function to download images."""
    print("=" * 60)
    print("STEP 3: DOWNLOADING PRODUCT IMAGES")
    print("=" * 60)
    
    if not os.path.exists(input_csv):
        print(f"❌ Error: Input file not found: {input_csv}")
        return False
    
    # Create image directory
    os.makedirs(image_dir, exist_ok=True)
    
    print(f"📖 Reading input: {input_csv}")
    df = pd.read_csv(input_csv)
    
    # Find the right columns
    sku_col = 'sku'
    img_col = 'Image_Links'
    
    if sku_col not in df.columns or img_col not in df.columns:
        print(f"❌ Error: Required columns not found")
        return False
    
    print(f"📥 Downloading images for {len(df)} products...")
    
    # Prepare tasks
    tasks = [(idx, row[sku_col], row[img_col]) for idx, row in df.iterrows()]
    results = {}
    
    # Multithreaded download
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_row = {executor.submit(download_image, task, image_dir): task for task in tasks}
        
        for future in tqdm(as_completed(future_to_row), total=len(tasks), desc="Downloading"):
            idx, filename = future.result()
            results[idx] = filename
    
    # Update DataFrame
    df['image_filename'] = df.index.map(results)
    
    # Save output
    print(f"💾 Saving to: {output_csv}")
    df.to_csv(output_csv, index=False)
    
    success_count = df['image_filename'].notna().sum()
    print(f"✅ Step 3 Complete! Downloaded {success_count}/{len(df)} images")
    
    return True

if __name__ == "__main__":
    import sys
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "temp", "stage2_with_seo.csv")
    output_file = os.path.join(script_dir, "temp", "stage3_final.csv")
    image_directory = os.path.join(script_dir, "output", "images")
    
    success = download_images_from_csv(input_file, output_file, image_directory)
    
    if not success:
        sys.exit(1)
