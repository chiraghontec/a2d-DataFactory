# DataFactory - Google Colab Setup Guide

## ✅ Code Validation Summary

The DataFactory code has been pulled from the remote repository and validated for Google Colab compatibility.

### Changes Pulled
- Updated from: `https://github.com/chiraghontec/a2d-DataFactory`
- Latest commit: `2c410c8`
- All 10 files synchronized successfully

### Compatibility Status

| Component | Status | Notes |
|-----------|--------|-------|
| File Paths | ✅ Compatible | Uses `pathlib.Path` which works in Colab |
| Dependencies | ✅ Compatible | All packages available via pip |
| Environment Variables | ⚠️ Requires Setup | Need to configure Google API keys |
| Ollama Integration | ⚠️ Alternative Needed | Ollama won't run in Colab - needs API alternative |
| File I/O | ✅ Compatible | Standard Python file operations |
| Network Requests | ✅ Compatible | Uses `requests` library |

## 🚀 Google Colab Setup Instructions

### 1. Upload Files to Colab

```python
# In Colab, upload these files:
# - run_pipeline.py
# - step1_scrape_links.py
# - step2_generate_seo.py (NEEDS MODIFICATION - see below)
# - step3_download_images.py
# - step4_package_bundle.py
# - product_input.csv
# - requirements.txt
```

### 2. Install Dependencies

```python
# Run in Colab cell
!pip install pandas google-api-python-client python-dotenv tqdm requests pdfplumber beautifulsoup4 lxml urllib3
```

### 3. Configure Environment Variables

```python
# Run in Colab cell
import os

# Set your Google API credentials
os.environ['GOOGLE_API_KEY'] = 'YOUR_GOOGLE_API_KEY_HERE'
os.environ['CUSTOM_SEARCH_ENGINE_ID'] = 'YOUR_SEARCH_ENGINE_ID_HERE'
```

### 4. **IMPORTANT**: Ollama Alternative for Step 2

Since Ollama doesn't run in Google Colab, you have TWO options:

#### Option A: Use OpenAI API (Recommended)
Modify `step2_generate_seo.py` to use OpenAI instead:

```python
# Replace ollama import with:
import openai

# Replace generate_seo_content function with:
def generate_seo_content(product_name, datasheet_text):
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # ... rest of the prompt remains same
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # or gpt-3.5-turbo for cheaper
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    
    return response.choices[0].message.content
```

Then set API key in Colab:
```python
os.environ['OPENAI_API_KEY'] = 'your-openai-api-key'
```

#### Option B: Skip SEO Generation
Run only steps 1, 3, and 4:

```python
# Manually run steps
!python step1_scrape_links.py product_input.csv
# Skip step2 - manually add descriptions later
!python step3_download_images.py
!python step4_package_bundle.py
```

### 5. Run the Pipeline

```python
# Full pipeline (if you modified step2 for OpenAI)
!python run_pipeline.py product_input.csv

# OR individual steps
!python step1_scrape_links.py product_input.csv
!python step2_generate_seo.py  # Only if modified for OpenAI
!python step3_download_images.py
!python step4_package_bundle.py
```

### 6. Download Output

```python
# Download the generated bundle
from google.colab import files
files.download('output/product_import_bundle.zip')
```

## 📋 Input File Created

A new input CSV has been created: **`product_input.csv`**

Contains 15 sample products:
- Arduino Uno R3
- Raspberry Pi 4 Model B 8GB
- ESP32-DevKitC V4
- STM32 Nucleo-64 F401RE
- Texas Instruments MSP430G2553
- Adafruit Metro M4 Express
- NodeMCU ESP8266
- Arduino Mega 2560 R3
- BeagleBone Black
- Teensy 4.0
- STM32F103C8T6 Blue Pill
- Seeed Studio XIAO ESP32C3
- Adafruit Feather M0
- BBC micro:bit V2
- Particle Photon

## ⚠️ Critical Considerations for Colab

1. **Session Timeout**: Colab sessions timeout after 12 hours or 90 minutes of inactivity
   - Save intermediate results frequently
   - Consider breaking into smaller batches

2. **Rate Limits**: Google Custom Search API has limits
   - Free tier: 100 queries/day
   - Add delays between requests (already implemented in code)

3. **Memory**: Large PDF processing can use significant RAM
   - Monitor with: `!free -h`
   - Restart runtime if needed

4. **File Persistence**: Files are deleted when runtime disconnects
   - Download important outputs immediately
   - Or mount Google Drive for persistence

## 🔧 Mounting Google Drive (Optional but Recommended)

```python
from google.colab import drive
drive.mount('/content/drive')

# Change working directory to Drive
%cd /content/drive/MyDrive/DataFactory

# Now files persist even after session ends
```

## 📊 Expected Output

After successful execution:
- `output/product_import_bundle.zip` - Ready to upload to Django Admin
- Contains:
  - `Master_Inventory_ready.csv` - Enriched product data
  - `images/` - Downloaded product images

## 🐛 Troubleshooting

### Error: "Ollama not found"
→ You need to modify step2 to use OpenAI API (see Option A above)

### Error: "Google API key invalid"
→ Check your `.env` or environment variable setup

### Error: "Rate limit exceeded"
→ Wait 24 hours or upgrade to paid Google Custom Search API

### Error: "PDF extraction failed"
→ Some PDFs are protected or malformed - this is normal, script continues

## ✨ Next Steps After Generation

1. Download `product_import_bundle.zip` from Colab
2. Go to your Django Admin: `http://localhost:8000/admin/products/csvimport/`
3. Upload the ZIP file
4. Products will be imported with SEO descriptions and images

---

**Files Location**: `/Volumes/LocalDrive/A2d Circuits/tools/DataFactory/`

**Remote Repo**: https://github.com/chiraghontec/a2d-DataFactory

**Last Sync**: February 3, 2026
