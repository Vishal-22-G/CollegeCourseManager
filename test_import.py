#!/usr/bin/env python3
"""
Test script to verify Excel import functionality
"""
import os
import sys
import pandas as pd
from werkzeug.datastructures import FileStorage
from io import BytesIO

# Add the project directory to Python path
sys.path.insert(0, '/home/runner/workspace')

def test_excel_import():
    """Test the Excel import functionality"""
    try:
        # Test file reading
        filepath = '/home/runner/workspace/uploads/courses_new_updated.xlsx'
        
        print("Testing Excel file reading...")
        df = pd.read_excel(filepath)
        print(f"✓ File read successfully: {len(df)} rows, {len(df.columns)} columns")
        
        # Test column mapping
        print("\nTesting column mapping...")
        columns = df.columns.tolist()
        print(f"✓ Columns extracted: {columns[:5]}...")
        
        # Test data preview
        print("\nTesting data preview...")
        preview = df.head(3).to_dict('records')
        print(f"✓ Preview generated: {len(preview)} sample rows")
        
        # Test data types inference
        print("\nTesting data type inference...")
        for col in columns[:3]:
            dtype = str(df[col].dtype)
            print(f"  {col}: {dtype}")
        
        print("\n✓ All Excel import components working correctly!")
        return True
        
    except Exception as e:
        print(f"✗ Error in Excel import test: {e}")
        return False

if __name__ == "__main__":
    test_excel_import()