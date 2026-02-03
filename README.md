# A2D Circuits - Data Factory Pipeline

Complete automated pipeline for processing product data from simple input to import-ready bundle.

## 🎯 Overview

This pipeline transforms a simple CSV with part numbers into a complete product import bundle with:
- ✅ Datasheet links (from Google Search)
- ✅ Product images (downloaded locally)
- ✅ AI-generated SEO descriptions
- ✅ Technical specifications (JSON format)
- ✅ Ready-to-import zip bundle

## 📁 Folder Structure

```
DataFactory/
├── product_input_template.csv  # Your starting point
├── run_pipeline.py             # Master orchestrator (run this!)
├── step1_scrape_links.py       # Google search for datasheets/images
├── step2_generate_seo.py       # AI-powered SEO generation
├── step3_download_images.py    # Batch image downloader
├── step4_package_bundle.py     # Creates final zip bundle
├── README.md                   # This file
├── .env                        # API keys (you create this)
├── output/                     # Final bundle appears here
│   ├── product_import_bundle.zip
│   └── images/
└── temp/                       # Intermediate files
    ├── stage1_with_links.csv
    ├── stage2_with_seo.csv
    └── stage3_final.csv
```

## 🚀 Quick Start

### 1. Install Requirements

```bash
pip install pandas google-api-python-client python-dotenv tqdm requests pdfplumber beautifulsoup4 ollama lxml
```

### 2. Set Up API Keys

Create a `.env` file in the `DataFactory/` directory:

```env
GOOGLE_API_KEY=your_google_api_key_here
CUSTOM_SEARCH_ENGINE_ID=your_cse_id_here
```

**Get API keys:**
- Google API Key: https://console.cloud.google.com/apis/credentials
- Custom Search Engine: https://programmablesearchengine.google.com/

### 3. Install Ollama (for SEO generation)

**Mac/Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:7b
```

**Windows:**
Download from https://ollama.com/download

### 4. Prepare Your Input

Edit `product_input_template.csv`:

```csv
Part Number / Model,Description / Text Details,Quantity / Bin,Source
TPS54360DDAR,High-Efficiency Step-Down Converter,50,Distributor
LM2596S-5.0,5V Switching Regulator,100,Manufacturer
ESP32-WROOM,WiFi/Bluetooth Module,25,Espressif
```

**Columns:**
- `Part Number / Model` (required) - The product identifier
- `Description / Text Details` (optional) - Additional context for search
- `Quantity / Bin` (optional) - Inventory info
- `Source` (optional) - Where you got it

### 5. Run the Pipeline

**Full pipeline:**
```bash
cd Backend/Inventory/DataFactory
python run_pipeline.py
```

**Or with custom input:**
```bash
python run_pipeline.py path/to/your_products.csv
```

**Or run individual steps:**
```bash
python step1_scrape_links.py your_input.csv
python step2_generate_seo.py
python step3_download_images.py
python step4_package_bundle.py
```

## 📊 What Each Step Does

### Step 1: Scrape Links (2-5 min for 50 products)
- Searches Google for datasheets using multiple strategies
- Finds product images
- Adds `Datasheet_Links` and `Image_Links` columns
- **Output:** `temp/stage1_with_links.csv`

### Step 2: Generate SEO (10-20 min for 50 products)
- Downloads and extracts text from datasheets
- Uses AI to generate product descriptions
- Extracts technical specifications
- Adds `seo_description` and `technical_specifications` columns
- **Output:** `temp/stage2_with_seo.csv`

### Step 3: Download Images (1-3 min for 50 products)
- Downloads all product images in parallel
- Saves with sanitized filenames
- Adds `image_filename` column
- **Output:** `temp/stage3_final.csv` + `output/images/`

### Step 4: Package Bundle (< 1 min)
- Creates zip file with CSV + images
- **Output:** `output/product_import_bundle.zip`

## 🎓 Google Colab Support

The pipeline works in Google Colab! Just:

1. Upload to Colab
2. Install requirements in a cell:
   ```python
   !pip install -q pandas google-api-python-client python-dotenv tqdm requests pdfplumber beautifulsoup4 lxml
   !pip install ollama
   
   # Set up Ollama
   !curl -fsSL https://ollama.com/install.sh | sh
   !nohup ollama serve &
   import time
   time.sleep(5)
   !ollama pull qwen2.5:7b
   ```
3. Set environment variables:
   ```python
   import os
   os.environ['GOOGLE_API_KEY'] = 'your_key'
   os.environ['CUSTOM_SEARCH_ENGINE_ID'] = 'your_cse_id'
   ```
4. Run the pipeline

## ⚙️ Configuration

Edit these variables in the scripts:

**step1_scrape_links.py:**
- `time.sleep(0.5)` - API rate limiting

**step2_generate_seo.py:**
- `OLLAMA_MODEL` - Change AI model
- `REQUEST_DELAY` - Adjust processing speed

**step3_download_images.py:**
- `max_workers=10` - Concurrent downloads

## 🐛 Troubleshooting

**"Google API credentials not found"**
- Make sure `.env` file is in `DataFactory/`
- Check that API key and CSE ID are correct

**"Ollama is not running"**
- Run `ollama serve` in terminal
- Make sure model is downloaded: `ollama pull qwen2.5:7b`

**"Few datasheets found"**
- Check your Google API quota (100 queries/day free)
- Try more specific part numbers
- Verify CSE is configured for web search

**"Images not downloading"**
- Some sites block bots - this is normal
- Check internet connection
- Images marked "Not Found" will be skipped

## 📈 Performance Tips

- **Small batches:** Start with 10-20 products to test
- **API limits:** Google CSE has 100 queries/day on free tier
- **Ollama speed:** Uses local AI, faster on better hardware
- **Parallel processing:** Images download in parallel (10 at a time)

## 🔄 Resume Failed Runs

If a step fails:

1. Fix the issue (API keys, network, etc.)
2. Run just that step: `python step2_generate_seo.py`
3. Continue with remaining steps

The pipeline saves progress at each stage in `temp/`.

## 📝 Output Format

**Final CSV columns:**
- Original input columns (Part Number, Description, etc.)
- `Datasheet_Links` - URL to product datasheet
- `Image_Links` - URL to product image
- `seo_description` - 120-150 word marketing description
- `technical_specifications` - JSON with detailed specs
- `image_filename` - Local image file name

**Zip bundle structure:**
```
product_import_bundle.zip
├── Master_Inventory_ready.csv
└── images/
    ├── TPS54360DDAR.jpg
    ├── LM2596S_5_0.jpg
    └── ...
```

## 🎯 Next Steps

After running the pipeline:

1. Extract `product_import_bundle.zip` to inspect
2. Review `Master_Inventory_ready.csv`
3. Upload to Admin Dashboard → Products → Import from CSV
4. Bulk import complete!

---

Made with ❤️ for A2D Circuits
