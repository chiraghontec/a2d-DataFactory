"""
Step 4: Package Bundle
Creates a zip file with the final CSV and all downloaded images.
"""

import os
import pandas as pd
from zipfile import ZipFile

def package_bundle(input_csv, image_dir, output_zip):
    """Create a zip bundle for product import."""
    print("=" * 60)
    print("STEP 4: PACKAGING IMPORT BUNDLE")
    print("=" * 60)
    
    if not os.path.exists(input_csv):
        print(f"❌ Error: Input file not found: {input_csv}")
        return False
    
    if not os.path.exists(image_dir):
        print(f"⚠️  Warning: Image directory not found: {image_dir}")
        print("Creating bundle without images...")
    
    print(f"📦 Creating import bundle...")
    
    # Create output directory
    os.makedirs(os.path.dirname(output_zip), exist_ok=True)
    
    # Read CSV and select required columns
    df = pd.read_csv(input_csv)
    
    # Ensure all required columns are present in the final CSV
    required_columns = [
        'sku', 'product_name', 'price', 'initial_stock', 'bin_location',
        'seo_title', 'meta_description', 'long_description_html', 
        'specs_json', 'image_filename_1', 'image_filename_2', 'image_filename_3'
    ]
    
    # Filter to only include required columns that exist
    available_columns = [col for col in required_columns if col in df.columns]
    df_final = df[available_columns]
    
    # Create temporary CSV with final structure
    import tempfile
    temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
    df_final.to_csv(temp_csv.name, index=False)
    temp_csv.close()
    
    # Create zip file
    with ZipFile(output_zip, 'w') as zipf:
        # Add CSV as Master_Inventory_ready.csv
        zipf.write(temp_csv.name, 'Master_Inventory_ready.csv')
        print(f"  ✓ Added CSV: Master_Inventory_ready.csv ({len(df_final)} products)")
        print(f"  ✓ Columns: {', '.join(available_columns)}")
        
        # Add all images
        if os.path.exists(image_dir):
            image_count = 0
            for img_file in os.listdir(image_dir):
                if img_file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    img_path = os.path.join(image_dir, img_file)
                    zipf.write(img_path, f'images/{img_file}')
                    image_count += 1
            print(f"  ✓ Added {image_count} images")
    
    # Clean up temp file
    os.unlink(temp_csv.name)
    
    # Get file size
    size_mb = os.path.getsize(output_zip) / (1024 * 1024)
    
    print(f"\n✅ Step 4 Complete!")
    print(f"📦 Bundle created: {output_zip}")
    print(f"📊 Contains: {len(df_final)} products")
    print(f"💾 File size: {size_mb:.2f} MB")
    print(f"\n🎉 PIPELINE COMPLETE! Ready to import.")
    
    return True

if __name__ == "__main__":
    import sys
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "temp", "stage3_final.csv")
    image_directory = os.path.join(script_dir, "output", "images")
    output_bundle = os.path.join(script_dir, "output", "product_import_bundle.zip")
    
    success = package_bundle(input_file, image_directory, output_bundle)
    
    if not success:
        sys.exit(1)
