"""
Step 1: Scrape Datasheet and Image Links
Reads input CSV and searches Google for datasheets and product images.
Optimized with domain curation and smart filtering.
"""

import pandas as pd
import os
import time
import re
import random
from urllib.parse import urlparse
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("GOOGLE_API_KEY")
CSE_ID = os.getenv("CUSTOM_SEARCH_ENGINE_ID")

# --- SOURCE CURATION ---
# Known official domains for brands found in the inventory
OFFICIAL_DOMAINS = {
    "meanwell": "meanwell.com",
    "delta": "deltaww.com",
    "wacom": "wacom.com",
    "pelco": "pelco.com",
    "hid": "hidglobal.com",
    "hikvision": "hikvision.com",
    "ge": "ge.com",
    "arduino": "arduino.cc",
    "xp power": "xppower.com",
    "tdk": "tdk-lambda.com",
    "emerson": "emerson.com",
    "march networks": "marchnetworks.com",
    "stm": "st.com",
    "ti": "ti.com",
    "microchip": "microchip.com",
    "invensense": "invensense.tdk.com", # for mpu-6050
    "analog": "analog.com", # for adxl345
    "espressif": "espressif.com", # for esp32
    "u-blox": "u-blox.com", # for gps m8n
    "amphenol": "amphenol.com",
    "vishay": "vishay.com",
    "te": "te.com",
    "renesas": "renesas.com",
    "omron": "omron.com",
    "honeywell": "honeywell.com",
    "nxp": "nxp.com",
    "onsemi": "onsemi.com",
    "infineon": "infineon.com",
    "bosch": "bosch.com",
    "panasonic": "panasonic.com",
    "sony": "sony.com",
    "samsung": "samsung.com",
    "burr-brown": "ti.com",
    "national semiconductor": "ti.com",
    "dallas": "analog.com",
    "maxim": "analog.com",
    "intersil": "renesas.com",
    "fairchild": "onsemi.com",
    "signetics": "nxp.com",
    "binder": "binder-connector.com",
    "positronic": "connectpositronic.com",
    "raychem": "te.com",
    "schaffner": "schaffner.com",
    "exxelia": "exxelia.com",
    "souriau": "souriau.com", # now Eaton/Souriau-Sunbank
    "eaton": "eaton.com",
    "hubersuhner": "hubersuhner.com",
    "huber+suhner": "hubersuhner.com",
    "huber suhner": "hubersuhner.com",
    "apem": "apem.com"
}

TRUSTED_DISTRIBUTORS = [
    "mouser.com", "digikey.com", "newark.com", "farnell.com", 
    "rs-online.com", "arrow.com", "avnet.com", "futureelectronics.com",
    "adafruit.com", "sparkfun.com", "seeedstudio.com", "robu.in", 
    "element14.com", "onlinecomponents.com", "masterelectronics.com", "biscoind.com"
]

ABBREVIATIONS = {
    r"\(MOT\)": "Motorola",
    r"\(BB\)": "Burr-Brown",
    r"\(ADC\)": "Analog Devices",
    r"\(BEL\)": "Bel Fuse", # or Bharat Electronics, context dependent but likely components
    r"\(AMI\)": "AMI Semiconductor",
    r"\(TI\)": "Texas Instruments",
    r"\(NS\)": "National Semiconductor",
    r"\(ST\)": "STMicroelectronics"
}

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
    
    # Expand abbreviations first
    for abbr, full_name in ABBREVIATIONS.items():
        text = re.sub(abbr, full_name, text, flags=re.IGNORECASE)

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

def get_domain(url):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith("www."):
            return domain[4:]
        return domain
    except:
        return ""

def is_official(url, brand_name):
    domain = get_domain(url)
    if not domain: return False
    
    # Check explicitly mapped domains
    for brand, official_domain in OFFICIAL_DOMAINS.items():
        if brand.lower() in brand_name.lower() and official_domain in domain:
            return True
            
    # Heuristic: Check if brand name is part of the domain (e.g. brand "Foobar", domain "foobar.com")
    # This is risky but useful for unmapped brands.
    clean_brand = re.sub(r'[^a-zA-Z0-9]', '', brand_name.lower())
    if len(clean_brand) > 3 and clean_brand in domain.replace(".", ""):
        return True
        
    return False

def is_trusted_distributor(url):
    domain = get_domain(url)
    for dist in TRUSTED_DISTRIBUTORS:
        if dist in domain:
            return True
    return False

def google_search(query, search_type=None, num_results=1):
    """Performs the search and returns list of items with exponential backoff."""
    max_retries = 5
    base_delay = 5  # Start with 5 seconds delay if rate limited
    
    for attempt in range(max_retries):
        try:
            service = build("customsearch", "v1", developerKey=API_KEY)
            res = service.cse().list(
                q=query,
                cx=CSE_ID,
                searchType=search_type,
                num=min(num_results, 10)  # API max is 10
            ).execute()
            return res.get('items', [])
            
        except HttpError as e:
            if e.resp.status == 429:
                wait_time = base_delay * (2 ** attempt)
                print(f"\n⚠️ Rate limit exceeded (429). Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"\nError searching for {query}: {e}")
                return []
                
        except Exception as e:
            print(f"\nError searching for {query}: {e}")
            return []
            
    print(f"\n❌ Failed to get results for '{query}' after {max_retries} attempts.")
    return []

def find_best_link(product_name, context, search_type=None, num_results=1):
    """
    Finds the best link (Official > Distributor > General)
    """
    clean_item = clean_search_term(product_name)
    clean_context = clean_search_term(context)
    
    if search_type == "image":
        query = f"{clean_item} {clean_context} product photo"
    else:
        query = f"{clean_item} {clean_context} datasheet"
        
    results = google_search(query, search_type=search_type, num_results=10) # Fetch more to filter
    
    if not results:
        # Fallback for datasheets if strict search fails
        if not search_type:
             query = f"{clean_item} {clean_context} specifications"
             results = google_search(query, num_results=5)
             if not results: return [] if num_results > 1 else None

    # Sort/Filter logic
    official_links = []
    distributor_links = []
    general_links = []
    
    for res in results:
        link = res['link']
        if is_official(link, product_name) or is_official(link, context):
            official_links.append(link)
        elif is_trusted_distributor(link):
            distributor_links.append(link)
        else:
            general_links.append(link)
            
    # Prioritize: Official -> Distributor -> General
    all_links = official_links + distributor_links + general_links
    
    if num_results == 1:
        return all_links[0] if all_links else None
    else:
        return all_links[:num_results]

def scrape_links(input_csv, output_csv):
    """Main function to scrape links from input CSV."""
    print("=" * 60)
    print("STEP 1: SCRAPING DATASHEET AND IMAGE LINKS (OPTIMIZED)")
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
    if 'sku' not in df.columns: df['sku'] = ""
    df['Datasheet_Links'] = ""
    df['Image_Links'] = ""
    
    # Process each row with progress bar
    print(f"🔍 Processing {len(df)} products...")
    
    for index in tqdm(range(len(df)), desc="Scraping"):
        row = df.iloc[index]
        
        # Robust column detection
        product_name = ""
        context = ""
        
        if 'product_name' in df.columns:
            product_name = str(row['product_name'])
            # Try to find context columns
            for col in ['Description / Text Details', 'Details', 'description', 'desc', 'initial_stock']:
                if col in df.columns and col != 'product_name':
                    context = str(row[col])
                    break
        elif 'Part Number / Model' in df.columns:
            product_name = str(row['Part Number / Model'])
            context = str(row.get('Description / Text Details', ''))
        elif 'Part Number / Brand / Specs' in df.columns:
             product_name = str(row['Part Number / Brand / Specs'])
             context = str(row.get('Voltage / Type', ''))
        else:
             # Fallback: take first column
             product_name = str(row.iloc[0])

        if not product_name or product_name == 'nan' or len(product_name) < 2:
            continue
            
        # Generate SKU if missing
        if not row.get('sku'):
            df.at[index, 'sku'] = generate_sku(product_name)
        
        # 1. Search for Datasheet (Priority: Official > Distributor)
        ds_link = find_best_link(product_name, context, search_type=None, num_results=1)
        df.at[index, 'Datasheet_Links'] = ds_link if ds_link else "Not Found"
        
        # 2. Search for Images (Priority: Official > Distributor)
        # We fetch up to 3 images to give options
        img_links = find_best_link(product_name, context, search_type="image", num_results=3)
        
        if img_links and len(img_links) > 0:
            df.at[index, 'Image_Links'] = " | ".join(img_links)
        else:
            df.at[index, 'Image_Links'] = "Not Found"
        
        time.sleep(1.5)  # Increased rate limiting to avoid 429 errors
    
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
