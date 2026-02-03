"""
Step 2: Generate SEO Descriptions
Reads CSV with datasheet links and generates SEO content using Ollama.
"""

import pandas as pd
import requests
import pdfplumber
from bs4 import BeautifulSoup
from io import BytesIO
from tqdm import tqdm
import json
import time
import ollama
import re
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
OLLAMA_MODEL = "qwen2.5:7b"
REQUEST_DELAY = 1.0

def extract_text_from_url(url):
    """Extract text from datasheets (PDF or HTML)."""
    if pd.isna(url) or not url or str(url).lower() in ["not found", "nan", ""]:
        return None
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        
        response = requests.get(url, timeout=45, headers=headers, verify=False, allow_redirects=True, stream=True)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '').lower()
        
        # Handle PDFs
        if ".pdf" in url.lower() or "pdf" in content_type:
            with pdfplumber.open(BytesIO(response.content)) as pdf:
                all_text = []
                for i, page in enumerate(pdf.pages[:10]):
                    try:
                        text = page.extract_text()
                        if text and len(text.strip()) > 50:
                            all_text.append(text)
                    except:
                        continue
                
                full_text = "\n\n".join(all_text)
                if full_text:
                    words = full_text.split()[:5000]
                    return " ".join(words)
                return None
        
        # Handle HTML
        else:
            soup = BeautifulSoup(response.content, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            
            text = soup.get_text(separator='\n', strip=True)
            text = re.sub(r'\n\s*\n', '\n', text)
            words = text.split()[:5000]
            return " ".join(words) if words else None
    
    except Exception as e:
        return None

def generate_seo_content(part_number, datasheet_text):
    """Generate SEO description and specifications using Ollama."""
    
    if not datasheet_text or len(datasheet_text.strip()) < 100:
        datasheet_text = f"Limited datasheet information for {part_number}."
    
    prompt = f"""Create a structured JSON response for this electronics component.

Part Number: {part_number}

Datasheet Content:
{datasheet_text[:4000]}

Return ONLY valid JSON with this structure:
{{
  "seo_description": "Professional 120-150 word product description highlighting features, applications, and specifications",
  "technical_specifications": {{
    "Part Number": "{part_number}",
    "Manufacturer": "manufacturer name",
    "Product Type": "category",
    "Operating Voltage": "value with unit",
    "Package Type": "package name",
    "Operating Temperature": "range with unit",
    "Key Features": ["feature 1", "feature 2"],
    "Applications": ["application 1", "application 2"]
  }}
}}

Use actual values from the datasheet. If a field is not available, omit it."""

    try:
        response = ollama.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            format='json',
            options={
                'num_ctx': 6144,
                'temperature': 0.1,
                'num_predict': 2000,
            }
        )
        
        result_text = response['response'].strip()
        
        # Parse JSON
        try:
            data = json.loads(result_text)
        except:
            match = re.search(r'\{[\s\S]*\}', result_text)
            if match:
                data = json.loads(match.group(0))
            else:
                return None
        
        specs_formatted = json.dumps(data.get('technical_specifications', {}), indent=2)
        
        return {
            'seo_description': data.get('seo_description', 'Product information available'),
            'technical_specifications': specs_formatted
        }
    
    except Exception as e:
        print(f"❌ Error generating SEO for {part_number}: {e}")
        return None

def generate_seo_for_csv(input_csv, output_csv):
    """Main function to generate SEO content."""
    print("=" * 60)
    print("STEP 2: GENERATING SEO DESCRIPTIONS")
    print("=" * 60)
    
    if not os.path.exists(input_csv):
        print(f"❌ Error: Input file not found: {input_csv}")
        return False
    
    # Check if Ollama is running
    try:
        ollama.list()
    except:
        print("❌ Error: Ollama is not running!")
        print("Please start Ollama: ollama serve")
        print("And ensure the model is available: ollama pull qwen2.5:7b")
        return False
    
    print(f"📖 Reading input: {input_csv}")
    df = pd.read_csv(input_csv)
    
    # Initialize columns
    df['seo_description'] = ""
    df['technical_specifications'] = ""
    
    print(f"🤖 Generating SEO content for {len(df)} products...")
    
    for index in tqdm(range(len(df)), desc="Generating SEO"):
        row = df.iloc[index]
        
        part_number = str(row.get('Part Number / Model', f'PRODUCT-{index}'))
        datasheet_url = row.get('Datasheet_Links', '')
        
        # Extract datasheet text
        datasheet_text = extract_text_from_url(datasheet_url)
        
        # Generate SEO content
        seo_data = generate_seo_content(part_number, datasheet_text)
        
        if seo_data:
            df.at[index, 'seo_description'] = seo_data['seo_description']
            df.at[index, 'technical_specifications'] = seo_data['technical_specifications']
        
        time.sleep(REQUEST_DELAY)
    
    # Save output
    print(f"💾 Saving to: {output_csv}")
    df.to_csv(output_csv, index=False)
    
    success_count = df[df['seo_description'] != ''].shape[0]
    print(f"✅ Step 2 Complete! Generated SEO for {success_count}/{len(df)} products")
    
    return True

if __name__ == "__main__":
    import sys
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "temp", "stage1_with_links.csv")
    output_file = os.path.join(script_dir, "temp", "stage2_with_seo.csv")
    
    success = generate_seo_for_csv(input_file, output_file)
    
    if not success:
        sys.exit(1)
