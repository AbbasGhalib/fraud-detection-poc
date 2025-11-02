"""
Test script for new forensic features
Run this to verify installation and basic functionality
"""

import sys
import os

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import pytesseract
        print("✅ pytesseract imported successfully")
    except ImportError:
        print("❌ pytesseract not found - install with: pip install pytesseract")
        return False
    
    try:
        from reportlab.pdfgen import canvas
        print("✅ reportlab imported successfully")
    except ImportError:
        print("❌ reportlab not found - install with: pip install reportlab")
        return False
    
    try:
        from forensics.database import ForensicDatabase
        print("✅ ForensicDatabase imported successfully")
    except ImportError as e:
        print(f"❌ ForensicDatabase import failed: {e}")
        return False
    
    try:
        from forensics.checks import check_page_numbers, extract_and_check_noa_id
        print("✅ New check functions imported successfully")
    except ImportError as e:
        print(f"❌ Check functions import failed: {e}")
        return False
    
    try:
        from forensics.forensic_analyzer import preprocess_uploaded_file
        print("✅ preprocess_uploaded_file imported successfully")
    except ImportError as e:
        print(f"❌ preprocess_uploaded_file import failed: {e}")
        return False
    
    return True


def test_tesseract():
    """Test that Tesseract OCR is installed and accessible"""
    print("\nTesting Tesseract OCR...")
    
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract version: {version}")
        return True
    except Exception as e:
        print(f"❌ Tesseract not installed or not accessible: {e}")
        print("   Install instructions:")
        print("   - Linux: sudo apt-get install tesseract-ocr")
        print("   - macOS: brew install tesseract")
        print("   - Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        return False


def test_database():
    """Test database creation and basic operations"""
    print("\nTesting database functionality...")
    
    try:
        from forensics.database import ForensicDatabase
        
        # Create test database
        db = ForensicDatabase('test_forensic.db')
        print("✅ Database created successfully")
        
        # Test storing an ID
        stored = db.store_id_number(
            identification_number='TEST12345',
            sin_last_4='6789',
            full_name='Test User',
            date_issued='January 1, 2024',
            file_name='test.pdf'
        )
        
        if stored:
            print("✅ Test ID stored successfully")
        else:
            print("⚠️  ID already exists (expected if test run multiple times)")
        
        # Test duplicate check
        result = db.check_duplicate_id('TEST12345')
        if result['is_duplicate']:
            print("✅ Duplicate check working")
        else:
            print("❌ Duplicate check failed")
            return False
        
        # Test retrieval
        records = db.get_all_records()
        print(f"✅ Database contains {len(records)} record(s)")
        
        # Clean up test database
        if os.path.exists('test_forensic.db'):
            os.unlink('test_forensic.db')
            print("✅ Test database cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def test_check_functions():
    """Test that new check functions work with basic inputs"""
    print("\nTesting check functions...")
    
    try:
        from forensics.checks import check_page_numbers, extract_and_check_noa_id
        
        # Test with non-NOA document (should skip gracefully)
        result = check_page_numbers(b'dummy', doc_type='t1')
        if not result['applicable']:
            print("✅ check_page_numbers skips non-NOA documents correctly")
        else:
            print("❌ check_page_numbers should skip non-NOA documents")
            return False
        
        result = extract_and_check_noa_id(b'dummy', 'test.pdf', doc_type='t1')
        if not result['applicable']:
            print("✅ extract_and_check_noa_id skips non-NOA documents correctly")
        else:
            print("❌ extract_and_check_noa_id should skip non-NOA documents")
            return False
        
        # Test with NOA but no Tesseract (should handle gracefully)
        result = check_page_numbers(b'dummy', doc_type='noa')
        if 'error' in result or result.get('applicable'):
            print("✅ check_page_numbers handles missing/error cases gracefully")
        
        result = extract_and_check_noa_id(b'dummy', 'test.pdf', doc_type='noa')
        if 'error' in result or result.get('applicable'):
            print("✅ extract_and_check_noa_id handles missing/error cases gracefully")
        
        return True
        
    except Exception as e:
        print(f"❌ Check functions test failed: {e}")
        return False


def test_image_preprocessing():
    """Test image preprocessing functionality"""
    print("\nTesting image preprocessing...")
    
    try:
        from PIL import Image
        import io
        
        # Create a simple test image
        img = Image.new('RGB', (800, 600), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Create a mock uploaded file object
        class MockUploadedFile:
            def __init__(self, name, bytes_data):
                self.name = name
                self.bytes_data = bytes_data
            
            def getvalue(self):
                return self.bytes_data.getvalue()
        
        mock_file = MockUploadedFile('test.png', img_bytes)
        
        from forensics.forensic_analyzer import preprocess_uploaded_file
        
        pdf_bytes, file_type, temp_path = preprocess_uploaded_file(mock_file)
        
        if file_type == 'image_converted':
            print("✅ Image conversion successful")
        else:
            print("❌ Image conversion failed")
            return False
        
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
            print("✅ Temporary file cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Image preprocessing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("FORENSIC FEATURES TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Tesseract OCR", test_tesseract()))
    results.append(("Database", test_database()))
    results.append(("Check Functions", test_check_functions()))
    results.append(("Image Preprocessing", test_image_preprocessing()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    print("=" * 60)
    print(f"TOTAL: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Run: streamlit run app.py")
        print("2. Navigate to Tab 3: Document Forensics")
        print("3. Upload a NOA document to test new features")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review errors above.")
        print("\nCommon fixes:")
        print("- Install missing packages: pip install -r requirements.txt")
        print("- Install Tesseract OCR (see FORENSICS_NEW_FEATURES_README.md)")
        return 1


if __name__ == "__main__":
    sys.exit(main())

