#!/usr/bin/env python3
"""
Test script to verify PDF generation functionality
"""

import sys
import os
from io import BytesIO
import logging

# Add the current directory to the path so we can import from app.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_pdf_generation():
    """Test PDF generation functionality"""
    try:
        # Import the PDF generator from app.py
        from app import GenericPDFGenerator, REPORTLAB_AVAILABLE
        
        if not REPORTLAB_AVAILABLE:
            print("❌ ReportLab is not available. Please install it with: pip install reportlab")
            return False
        
        print("✅ ReportLab is available")
        
        # Create test data
        test_case_data = {
            "case_id": "TEST-001",
            "incident_type": "Test Investigation",
            "location": "Test Location",
            "date_time": "2024-01-01 12:00:00",
            "description": "This is a test case for PDF generation verification"
        }
        
        test_analysis = """
        **Executive Summary**
        This is a test analysis to verify PDF generation functionality.
        
        **Key Findings**
        - PDF generation is working correctly
        - Text formatting is preserved
        - Special characters are handled properly
        
        **Recommendations**
        1. Continue with deployment
        2. Monitor PDF downloads
        3. Verify file integrity
        """
        
        # Create PDF generator
        pdf_generator = GenericPDFGenerator()
        print("✅ PDF generator created successfully")
        
        # Generate PDF
        pdf_buffer = pdf_generator.generate_generic_pdf("test", test_case_data, test_analysis)
        print("✅ PDF generated successfully")
        
        # Validate PDF content
        pdf_content = pdf_buffer.getvalue()
        pdf_size = len(pdf_content)
        
        print(f"📄 PDF size: {pdf_size} bytes")
        
        if pdf_size < 100:
            print("❌ PDF is too small, likely corrupted")
            return False
        
        if not pdf_content.startswith(b'%PDF'):
            print("❌ PDF does not have valid PDF header")
            return False
        
        print("✅ PDF has valid header")
        
        # Save test PDF to file for manual verification
        test_filename = "test_pdf_output.pdf"
        with open(test_filename, 'wb') as f:
            f.write(pdf_content)
        
        print(f"✅ Test PDF saved as: {test_filename}")
        print("📝 Please manually open this file to verify it displays correctly")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during PDF generation test: {e}")
        return False

def main():
    """Main test function"""
    print("🔍 Testing PDF Generation Functionality")
    print("=" * 50)
    
    success = test_pdf_generation()
    
    print("=" * 50)
    if success:
        print("✅ PDF generation test PASSED")
        print("🚀 PDF functionality should work correctly after deployment")
    else:
        print("❌ PDF generation test FAILED")
        print("🔧 Please check the error messages above and fix any issues")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
