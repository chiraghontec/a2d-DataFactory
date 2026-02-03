"""
Step 1: Scrape Datasheet and Image Links
Reads input CSV and searches Google for datasheets and product images.
"""

import pandas as pd
import os
import time
import re
import random
from googleapiclient.discovery import build
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("GOOGLE_API_KEY")
CSE_ID = os.getenv("CUSTOM_SEARCH_ENGINE_ID")

def generate_sku(product_name):
    """Generate SKU from product name with random 4-digit suffix."""
    # Convert to uppercase and replace spaces with hyphens
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', str(product_name).upper()).strip('-')
    # Generate random 4-digit suffix
    suffix = random.randint(1000, 9999)
    return f"{slug}-{suffix}"

def clean_search_term(text):
    """Clean the text to remove noise that confuses Google."""
    text = str(text).replace('nan', '').strip()
    
    # Remove text inside parentheses if it looks like a person's name or bin code
    # But KEEP valid specs like (12V) or (3.90A)
    def keep_specs(match):
        content = match.group(1)
        if any(char.isdigit() for char in content):
            return f"({content})" 
        return "" 

    text = re.sub(r'\((.*?)\)', keep_specs, text)
    text = re.sub(r'Bin \d+|F\d+', '', text, flags=re.IGNORECASE)
    text = text.replace("Rev 3", "").replace("REV 4.0", "")
    
    return text.strip()

def google_search(query, search_type=None):
    """Performs the search and returns the first link found."""
    try:
        service = build("customsearch", "v1", developerKey=API_KEY)
        res = service.cse().list(
            q=query,
            cx=CSE_ID,
            searchType=search_type,
            num=1
        ).execute()
        return res['items'][0]['link'] if 'items' in res else None
    except Exception as e:
        return None

def smart_search_with_fallback(item, context):
    """Tries multiple search strategies until a result is found."""
    clean_item = clean_search_term(item)
    clean_context = clean_search_term(context)
    base_query = f"{clean_item} {clean_context}".strip()
    
    # Strategy 1: Strict PDF Datasheet
    link = google_search(f"{base_query} datasheet filetype:pdf")
    if link: return link

    # Strategy 2: Distributor/Manufacturer Sites
    link = google_search(f"{base_query} datasheet site:mouser.com OR site:digikey.com OR site:ti.com OR site:st.com")
    if link: return link

    # Strategy 3: General Specs
    link = google_search(f"{base_query} specifications")
    if link: return link

    return "Not Found"

def scrape_links(input_csv, output_csv):
    """Main function to scrape links from input CSV."""
    print("=" * 60)
    print("STEP 1: SCRAPING DATASHEET AND IMAGE LINKS")
    print("=" * 60)
    
    if not os.path.exists(input_csv):
        print(f"❌ Error: Input file not found: {input_csv}")
        return False
    
    # Check for API credentials
    if not API_KEY or not CSE_ID:
        print("❌ Error: Google API credentials not found!")
        print("Please set GOOGLE_API_KEY and CUSTOM_SEARCH_ENGINE_ID in .env file")
        return False
    
    # Read input CSV
    print(f"📖 Reading input: {input_csv}")
    df = pd.read_csv(input_csv)
    
    # Initialize new columns
    df['sku'] = ""
    df['Datasheet_Links'] = ""
    df['Image_Links'] = ""
    
    # Process each row with progress bar
    print(f"🔍 Processing {len(df)} products...")
    
    for index in tqdm(range(len(df)), desc="Scraping"):
        row = df.iloc[index]
        
        product_name = str(row.get('product_name', '')).strip()
        
        if not product_name or product_name == 'nan' or len(product_name) < 2:
            continue
        
        # Generate SKU
        sku = generate_sku(product_name)
        df.at[index, 'sku'] = sku
        
        # Search for datasheet using product_name
        ds_link = google_search(f"{clean_search_term(product_name)} datasheet")
        df.at[index, 'Datasheet_Links'] = ds_link if ds_link else "Not Found"
        
        # Search for product photo
        img_link = google_search(f"{clean_search_term(product_name)} product photo", search_type="image")
        df.at[index, 'Image_Links'] = img_link if img_link else "Not Found"
        
        time.sleep(0.5)  # Rate limiting
    
    # Save output
    print(f"💾 Saving to: {output_csv}")
    df.to_csv(output_csv, index=False)
    
    success_count = df[df['Datasheet_Links'] != 'Not Found'].shape[0]
    print(f"✅ Step 1 Complete! Found datasheets for {success_count}/{len(df)} products")
    
    return True

if __name__ == "__main__":
    import sys
    
    # Get paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(script_dir, "product_input_template.csv")
    output_file = os.path.join(script_dir, "temp", "stage1_with_links.csv")
    
    # Create temp directory
    os.makedirs(os.path.join(script_dir, "temp"), exist_ok=True)
    
    # Run scraping
    success = scrape_links(input_file, output_file)
    
    if not success:
        sys.exit(1)
