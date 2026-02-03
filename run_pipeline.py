"""
Master Pipeline Orchestrator
Runs all 4 steps of the Data Factory pipeline in sequence.

Usage:
    python run_pipeline.py input.csv
    python run_pipeline.py  # Uses template
"""

import sys
import os
import subprocess
from pathlib import Path

def run_step(step_name, script_path, args=None):
    """Run a pipeline step and handle errors."""
    print(f"\n{'=' * 60}")
    print(f"Running: {step_name}")
    print(f"{'=' * 60}\n")
    
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode != 0:
        print(f"\n❌ {step_name} failed with error code {result.returncode}")
        return False
    
    return True

def main():
    print("=" * 60)
    print("A2D CIRCUITS - DATA FACTORY PIPELINE")
    print("=" * 60)
    print("This pipeline will:")
    print("  1. Scrape datasheet and image links from Google")
    print("  2. Generate SEO descriptions using AI")
    print("  3. Download product images")
    print("  4. Package everything into an import bundle")
    print("=" * 60)
    
    # Get script directory
    script_dir = Path(__file__).parent
    
    # Get input file from command line or use template
    if len(sys.argv) > 1:
        input_csv = sys.argv[1]
        if not os.path.exists(input_csv):
            print(f"❌ Error: Input file not found: {input_csv}")
            sys.exit(1)
    else:
        input_csv = script_dir / "product_input_template.csv"
        if not os.path.exists(input_csv):
            print(f"❌ Error: Template file not found: {input_csv}")
            print("Please create product_input_template.csv or specify an input file")
            sys.exit(1)
    
    print(f"\n📄 Input file: {input_csv}")
    
    # Create directories
    (script_dir / "temp").mkdir(exist_ok=True)
    (script_dir / "output").mkdir(exist_ok=True)
    (script_dir / "output" / "images").mkdir(exist_ok=True)
    
    # Define steps
    steps = [
        ("Step 1: Scrape Links", script_dir / "step1_scrape_links.py", [str(input_csv)]),
        ("Step 2: Generate SEO", script_dir / "step2_generate_seo.py", None),
        ("Step 3: Download Images", script_dir / "step3_download_images.py", None),
        ("Step 4: Package Bundle", script_dir / "step4_package_bundle.py", None),
    ]
    
    # Run all steps
    for step_name, script_path, args in steps:
        if not run_step(step_name, script_path, args):
            print(f"\n❌ Pipeline failed at: {step_name}")
            print("Fix the error and run again, or run individual steps")
            sys.exit(1)
    
    # Success!
    print("\n" + "=" * 60)
    print("🎉 PIPELINE COMPLETE!")
    print("=" * 60)
    print(f"✅ Output: {script_dir / 'output' / 'product_import_bundle.zip'}")
    print("\nNext steps:")
    print("1. Go to Admin Dashboard → Products → Product List")
    print("2. Click 'Import from CSV'")
    print("3. Upload the product_import_bundle.zip file")
    print("=" * 60)

if __name__ == "__main__":
    main()
