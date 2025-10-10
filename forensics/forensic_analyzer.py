from .checks import (
    check_text_alignment,
    check_font_consistency,
    check_metadata,
    check_number_patterns,
    check_image_quality
)

def analyze_document_forensics(pdf_file, pdf_bytes=None):
    """
    Complete forensic analysis of a PDF document
    
    Args:
        pdf_file: File path or uploaded file object
        pdf_bytes: Optional bytes for image analysis
        
    Returns:
        dict with all forensic results and overall score
    """
    
    results = {
        'alignment': None,
        'fonts': None,
        'metadata': None,
        'numbers': None,
        'image': None,
        'overall_score': 0,
        'risk_level': 'LOW'
    }
    
    # Run all checks
    try:
        results['alignment'] = check_text_alignment(pdf_file)
    except Exception as e:
        results['alignment'] = {'risk_score': 0, 'error': str(e)}
    
    try:
        results['fonts'] = check_font_consistency(pdf_file)
    except Exception as e:
        results['fonts'] = {'risk_score': 0, 'error': str(e)}
    
    try:
        results['metadata'] = check_metadata(pdf_file)
    except Exception as e:
        results['metadata'] = {'risk_score': 0, 'error': str(e)}
    
    try:
        results['numbers'] = check_number_patterns(pdf_file)
    except Exception as e:
        results['numbers'] = {'risk_score': 0, 'error': str(e)}
    
    try:
        if pdf_bytes:
            results['image'] = check_image_quality(pdf_bytes)
        else:
            results['image'] = {'risk_score': 0, 'flags': ['Image analysis skipped']}
    except Exception as e:
        results['image'] = {'risk_score': 0, 'error': str(e)}
    
    # Calculate overall score
    scores = [
        results['alignment'].get('risk_score', 0),
        results['fonts'].get('risk_score', 0),
        results['metadata'].get('risk_score', 0),
        results['numbers'].get('risk_score', 0),
        results['image'].get('risk_score', 0)
    ]
    
    results['overall_score'] = sum(scores) / len(scores)
    
    if results['overall_score'] < 30:
        results['risk_level'] = 'LOW'
    elif results['overall_score'] < 60:
        results['risk_level'] = 'MEDIUM'
    else:
        results['risk_level'] = 'HIGH'
    
    return results

