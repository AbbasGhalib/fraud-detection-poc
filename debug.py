import os
import sys
import logging
import traceback
from typing import Dict, Any

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import project modules
from tax_validators.data_extractor import (
    extract_text_from_pdf, 
    extract_key_fields, 
    extract_tables_from_pdf, 
    get_page_count
)
from tax_validators.gemini_validator import (
    initialize_gemini,
    extract_structured_data_t1,
    extract_structured_data_noa
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(project_root, 'debug.log'))
    ]
)
logger = logging.getLogger(__name__)

def debug_pdf_extraction(pdf_path: str, doc_type: str) -> Dict[str, Any]:
    """
    Comprehensive PDF extraction debugging function
    
    Args:
        pdf_path (str): Path to the PDF file
        doc_type (str): Type of document ('T1' or 'NOA')
    
    Returns:
        Dict containing extraction results and debug information
    """
    debug_info = {
        'pdf_path': pdf_path,
        'doc_type': doc_type,
        'extraction_results': {},
        'errors': []
    }
    
    try:
        # Step 1: Get Page Count
        logger.info(f"Analyzing PDF: {pdf_path}")
        page_count = get_page_count(pdf_path)
        debug_info['page_count'] = page_count
        logger.debug(f"Total pages: {page_count}")
        
        # Step 2: Extract Full Text
        full_text = extract_text_from_pdf(pdf_path)
        debug_info['full_text'] = full_text
        logger.debug(f"Extracted text length: {len(full_text)} characters")
        
        # Step 3: Extract Tables
        # tables = extract_tables_from_pdf(pdf_path)
        # debug_info['tables'] = tables
        # logger.debug(f"Extracted {len(tables)} tables")
        
        # # Step 4: Extract Key Fields
        # extracted_fields = extract_key_fields(full_text, doc_type)
        # debug_info['extraction_results'] = extracted_fields
        
        # # Log extracted fields
        # logger.info("Extracted Fields:")
        # for key, value in extracted_fields.items():
        #     logger.info(f"{key}: {value}")

        # SStep 5: Data Extraction from Gemini (if applicable)
        logger.info("Step 5: Extracting structured data...")
        try:
            if doc_type == 'NOA':
                model = initialize_gemini()
                noa_data = extract_structured_data_noa(full_text, model)
                logger.info(f"Structured Data (NOA): {noa_data}")
            if doc_type == 'T1':
                model = initialize_gemini()
                t1_data = extract_structured_data_t1(full_text, model)
                logger.info(f"Structured Data (T1): {t1_data}")
        except Exception as e:
            logger.error(f"Structured data extraction failed: {e}")
            analysis_ok = False
            raise


        return debug_info
    
    except Exception as e:
        error_details = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'traceback': traceback.format_exc()
        }
        debug_info['errors'].append(error_details)
        logger.error(f"Extraction Error: {error_details}")
        return debug_info

def main():
    """
    Main debugging entry point
    """
    # Sample documents directory
    sample_dir = os.path.join(project_root, 'sample_documents')
    
    # Document types to debug
    doc_types = ['NOA', 'T1']
    
    # Collect debug results
    all_debug_results = {}
    
    # Debug each document type
    for doc_type in doc_types:
        # Find PDF files for this document type
        pdf_files = [
            os.path.join(sample_dir, f) 
            for f in os.listdir(sample_dir) 
            if f.lower().endswith('.pdf') and f.startswith(doc_type)
        ]
        
        # Debug each PDF
        for pdf_path in pdf_files:
            logger.info(f"Starting debug for {pdf_path}")
            debug_result = debug_pdf_extraction(pdf_path, doc_type)
            all_debug_results[pdf_path] = debug_result
    
    # Final summary
    logger.info("Debugging Complete")
    logger.info("=" * 50)
    logger.info("Debug Summary:")
    for path, result in all_debug_results.items():
        logger.info(f"PDF: {path}")
        logger.info(f"Document Type: {result['doc_type']}")
        logger.info(f"Page Count: {result.get('page_count', 'N/A')}")
        logger.info(f"Extracted Fields: {len(result.get('extraction_results', {}))}")
        if result.get('errors'):
            logger.error(f"Errors: {len(result['errors'])}")

if __name__ == '__main__':
    main()
