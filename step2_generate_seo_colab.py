"""
Step 2: Generate SEO Descriptions (Google Colab Version)
Reads CSV with datasheet links and generates SEO content using OpenAI API.

SETUP REQUIRED:
    pip install openai
    Set environment variable: OPENAI_API_KEY
"""

import pandas as pd
import requests
import pdfplumber
from bs4 import BeautifulSoup
from io import BytesIO
from tqdm import tqdm
import json
import time
import re
import os
import urllib3

# For Colab: Use OpenAI instead of Ollama
try:
    import openai
except ImportError:
    print("⚠️  OpenAI library not found. Install with: pip install openai")
    raise

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
OPENAI_MODEL = "gpt-4o-mini"  # Use gpt-3.5-turbo for cheaper alternative
REQUEST_DELAY = 1.0
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("❌ ERROR: OPENAI_API_KEY not set!")
    print("Set it in Colab with:")
    print("  import os")
    print("  os.environ['OPENAI_API_KEY'] = 'your-api-key-here'")
    raise ValueError("OPENAI_API_KEY environment variable not set")

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
            try:
                # Use 'strict_metadata=False' to ignore minor font errors
                with pdfplumber.open(BytesIO(response.content)) as pdf:
                    all_text = []
                    for i, page in enumerate(pdf.pages[:10]):
                        try:
                            # layout=False is faster and less prone to BBox errors
                            text = page.extract_text(layout=False)
                            if text and len(text.strip()) > 50:
                                all_text.append(text)
                        except Exception as e:
                            # If a specific page fails, just skip it instead of crashing
                            continue
                    
                    full_text = "\n\n".join(all_text)
                    if full_text:
                        words = full_text.split()[:5000]
                        return " ".join(words)
                    return None
            except Exception as e:
                # If pdfplumber fails entirely (e.g. encrypted PDF), return None gracefully
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

def generate_seo_content(product_name, datasheet_text):
    """Generate SEO description and specifications using OpenAI."""
    
    if not datasheet_text or len(datasheet_text.strip()) < 100:
        datasheet_text = f"Limited datasheet information for {product_name}."
    
    prompt = f"""Create a structured JSON response for this electronics component.

Product Name: {product_name}

Datasheet Information:
{datasheet_text[:8000]}

Generate a JSON object with these EXACT keys:
{{
    "seo_description": "A compelling 150-200 character SEO-optimized description highlighting key features and applications",
    "long_description": "A detailed 3-4 paragraph technical description covering: what it is, key specifications, typical applications, and why customers should choose this product",
    "technical_specifications": "Bullet-pointed list of key technical specs (voltage, current, frequency, dimensions, etc.)",
    "applications": "Common use cases and applications for this component",
    "features": "Key features and benefits in bullet points"
}}

IMPORTANT:
- Keep seo_description under 200 characters
- Make long_description informative and engaging
- Focus on facts from the datasheet
- Use technical terminology appropriately
- Format specifications as clean bullet points

Return ONLY valid JSON, no additional text."""

    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert electronics technical writer. Generate accurate, SEO-optimized product descriptions from datasheets."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        content = response.choices[0].message.content.strip()
        
        # Try to parse JSON
        if content.startswith("```json"):
            content = content.split("```json")[1].split("```")[0].strip()
        elif content.startswith("```"):
            content = content.split("```")[1].split("```")[0].strip()
        
        result = json.loads(content)
        
        # Validate required keys
        required_keys = ["seo_description", "long_description", "technical_specifications", "applications", "features"]
        for key in required_keys:
            if key not in result:
                result[key] = f"Information not available for {product_name}"
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON parse error for {product_name}: {e}")
        return generate_fallback_content(product_name)
    except Exception as e:
        print(f"⚠️  API error for {product_name}: {e}")
        return generate_fallback_content(product_name)

def generate_fallback_content(product_name):
    """Generate basic content when AI fails."""
    return {
        "seo_description": f"{product_name} - High-quality electronics component for professional and hobbyist use",
        "long_description": f"The {product_name} is a reliable electronics component designed for various applications. This product offers excellent performance and compatibility for your projects. Contact us for detailed specifications and availability.",
        "technical_specifications": "Specifications available upon request",
        "applications": f"Suitable for electronics projects, prototyping, and professional applications",
        "features": f"• Quality {product_name}\n• Industry standard compatibility\n• Reliable performance"
    }

def main():
    print("=" * 60)
    print("Step 2: SEO Content Generation (OpenAI)")
    print("=" * 60)
    
    # Read input from Step 1
    input_file = "temp/after_step1.csv"
    if not os.path.exists(input_file):
        print(f"❌ Error: {input_file} not found")
        print("Run Step 1 first: python step1_scrape_links.py")
        return
    
    df = pd.read_csv(input_file)
    print(f"📊 Processing {len(df)} products...")
    
    # Process each product
    results = []
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Generating SEO"):
        product_name = row['product_name']
        datasheet_link = row.get('datasheet_link', 'Not Found')
        
        # Extract datasheet text
        datasheet_text = extract_text_from_url(datasheet_link) if datasheet_link != 'Not Found' else None
        
        # Generate SEO content
        seo_data = generate_seo_content(product_name, datasheet_text)
        
        # Combine with original data
        result = {
            'sku': row.get('sku', ''),
            'product_name': product_name,
            'price': row.get('price', 0),
            'bin_location': row.get('bin_location', ''),
            'initial_stock': row.get('initial_stock', 0),
            'datasheet_link': datasheet_link,
            'image_link': row.get('image_link', ''),
            'seo_description': seo_data.get('seo_description', ''),
            'long_description': seo_data.get('long_description', ''),
            'technical_specifications': seo_data.get('technical_specifications', ''),
            'applications': seo_data.get('applications', ''),
            'features': seo_data.get('features', '')
        }
        results.append(result)
        
        # Rate limiting
        time.sleep(REQUEST_DELAY)
    
    # Save output
    output_df = pd.DataFrame(results)
    output_file = "temp/after_step2.csv"
    output_df.to_csv(output_file, index=False)
    
    print(f"\n✅ SEO content generated: {output_file}")
    print(f"📊 Products processed: {len(results)}")

if __name__ == "__main__":
    main()
