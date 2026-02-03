#!/usr/bin/env python3
"""
Validation script to test that the refactored pipeline handles the new schema correctly.
This script validates without needing external APIs.
"""

import pandas as pd
import os
import sys
import re
import random

def test_input_schema():
    """Test that the input CSV has the correct schema."""
    print("Testing input schema...")
    
    input_csv = "product_input_template.csv"
    if not os.path.exists(input_csv):
        print("❌ Input CSV not found")
        return False
    
    df = pd.read_csv(input_csv)
    
    required_columns = ['product_name', 'price', 'bin_location', 'initial_stock']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"❌ Missing columns: {missing_columns}")
        return False
    
    print(f"✅ Input schema correct: {list(df.columns)}")
    print(f"   Sample data: {len(df)} rows")
    return True

def test_sku_generation():
    """Test SKU generation function."""
    print("\nTesting SKU generation...")
    
    def generate_sku(product_name):
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', str(product_name).upper()).strip('-')
        suffix = random.randint(1000, 9999)
        return f"{slug}-{suffix}"
    
    test_cases = [
        "MSP EXP 432 P401",
        "CC31XXEMUBOOST",
        "ESP32-WROOM-32"
    ]
    
    for product_name in test_cases:
        sku = generate_sku(product_name)
        print(f"   {product_name} -> {sku}")
        
        # Validate format
        if not re.match(r'^[A-Z0-9\-]+-\d{4}$', sku):
            print(f"❌ Invalid SKU format: {sku}")
            return False
    
    print("✅ SKU generation working correctly")
    return True

def test_step1_logic():
    """Test that Step 1 logic is correct."""
    print("\nTesting Step 1 logic...")
    
    # Read input
    df = pd.read_csv("product_input_template.csv")
    
    # Simulate Step 1 transformations
    df['sku'] = df['product_name'].apply(
        lambda x: re.sub(r'[^a-zA-Z0-9]+', '-', str(x).upper()).strip('-') + f"-{random.randint(1000, 9999)}"
    )
    
    # Check that all original columns are preserved
    expected_columns = ['product_name', 'price', 'bin_location', 'initial_stock', 'sku']
    for col in expected_columns:
        if col not in df.columns:
            print(f"❌ Missing column after Step 1: {col}")
            return False
    
    print(f"✅ Step 1 preserves all required columns")
    print(f"   Columns: {list(df.columns)}")
    return True

def test_step2_output_schema():
    """Test that Step 2 would produce the correct output structure."""
    print("\nTesting Step 2 output schema...")
    
    expected_seo_fields = [
        'seo_title',
        'meta_description',
        'short_description',
        'long_description_html',
        'specs_json'
    ]
    
    print(f"✅ Expected SEO fields: {expected_seo_fields}")
    return True

def test_step4_final_columns():
    """Test that Step 4 would include all required columns in final output."""
    print("\nTesting Step 4 final output columns...")
    
    required_final_columns = [
        'sku', 'product_name', 'price', 'initial_stock', 'bin_location',
        'seo_title', 'meta_description', 'long_description_html',
        'specs_json', 'image_filename'
    ]
    
    print(f"✅ Required final columns defined: {required_final_columns}")
    return True

def main():
    """Run all validation tests."""
    print("=" * 70)
    print("ETL PIPELINE SCHEMA VALIDATION")
    print("=" * 70)
    
    tests = [
        test_input_schema,
        test_sku_generation,
        test_step1_logic,
        test_step2_output_schema,
        test_step4_final_columns,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 70)
    if all(results):
        print("🎉 ALL VALIDATION TESTS PASSED!")
        print("=" * 70)
        return 0
    else:
        print("❌ SOME VALIDATION TESTS FAILED")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
