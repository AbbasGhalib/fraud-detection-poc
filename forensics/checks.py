import pdfplumber
import PyPDF2
import cv2
import numpy as np
from pdf2image import convert_from_bytes
from PIL import Image
from collections import Counter
import re

def check_text_alignment(pdf_path):
    """
    Detect misaligned text rows
    Returns: {
        'risk_score': 0-100,
        'issues': [list of alignment issues],
        'count': int
    }
    """
    alignment_issues = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            words = page.extract_words()
            if not words:
                continue
            
            # Group words by y-coordinate (rows)
            rows = {}
            for word in words:
                y_coord = round(word['top'], 1)
                if y_coord not in rows:
                    rows[y_coord] = []
                rows[y_coord].append(word)
            
            # Check alignment within each row
            for y, words_in_row in rows.items():
                if len(words_in_row) < 2:
                    continue
                
                tops = [w['top'] for w in words_in_row]
                deviation = max(tops) - min(tops)
                
                if deviation > 1.5:  # Misalignment threshold
                    alignment_issues.append({
                        'page': page_num,
                        'row_y': round(y, 1),
                        'deviation': round(deviation, 2),
                        'num_words': len(words_in_row),
                        'words': words_in_row
                    })
    
    # Calculate risk score
    if len(alignment_issues) > 10:
        risk_score = 80
    elif len(alignment_issues) > 5:
        risk_score = 50
    elif len(alignment_issues) > 0:
        risk_score = 20
    else:
        risk_score = 0
    
    return {
        'risk_score': risk_score,
        'issues': alignment_issues,
        'count': len(alignment_issues)
    }


def check_font_consistency(pdf_path):
    """
    Analyze font usage consistency
    Returns: {
        'risk_score': 0-100,
        'total_unique_fonts': int,
        'font_counts': Counter object,
        'flags': [list of issues]
    }
    """
    all_fonts = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            chars = page.chars
            if not chars:
                continue
            
            for char in chars:
                font_name = char.get('fontname', 'Unknown')
                all_fonts.append(font_name)
    
    font_counts = Counter(all_fonts)
    total_unique = len(font_counts)
    
    # Calculate risk
    flags = []
    if total_unique > 15:
        flags.append(f"Very high font variation ({total_unique} fonts)")
        risk_score = 80
    elif total_unique > 10:
        flags.append(f"High font variation ({total_unique} fonts)")
        risk_score = 60
    elif total_unique > 6:
        flags.append(f"Moderate font variation ({total_unique} fonts)")
        risk_score = 30
    else:
        risk_score = 0
    
    return {
        'risk_score': risk_score,
        'total_unique_fonts': total_unique,
        'font_counts': font_counts,
        'flags': flags,
        'dominant_font': font_counts.most_common(1)[0][0] if font_counts else None
    }


def check_metadata(pdf_path):
    """
    Check PDF metadata for suspicious signs
    Returns: {
        'risk_score': 0-100,
        'flags': [list of issues],
        'metadata': dict
    }
    """
    flags = []
    risk_score = 0
    metadata_info = {}
    
    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            metadata = pdf.metadata
            
            if not metadata:
                flags.append("No metadata found")
                risk_score = 30
                return {'risk_score': risk_score, 'flags': flags, 'metadata': {}}
            
            producer = str(metadata.get('/Producer', 'Unknown'))
            creator = str(metadata.get('/Creator', 'Unknown'))
            
            metadata_info = {
                'producer': producer,
                'creator': creator,
                'creation_date': str(metadata.get('/CreationDate', 'Unknown')),
                'mod_date': str(metadata.get('/ModDate', 'Unknown')),
                'pages': len(pdf.pages)
            }
            
            # Check for consumer editing tools
            suspicious_tools = [
                'Word', 'LibreOffice', 'Google Docs', 
                'Smallpdf', 'iLovePDF', 'CorelDRAW',
                'Photoshop', 'Illustrator', 'Canva', 'Inkscape'
            ]
            
            for tool in suspicious_tools:
                if tool.lower() in producer.lower() or tool.lower() in creator.lower():
                    flags.append(f"Created with consumer tool: {tool}")
                    risk_score += 35
            
            # Check modification
            creation = metadata.get('/CreationDate', '')
            modified = metadata.get('/ModDate', '')
            if creation and modified and creation != modified:
                flags.append("Document modified after creation")
                risk_score += 15
    
    except Exception as e:
        flags.append(f"Metadata read error: {str(e)}")
        risk_score = 50
    
    return {
        'risk_score': min(risk_score, 100),
        'flags': flags,
        'metadata': metadata_info
    }


def check_number_patterns(pdf_path):
    """
    Analyze number formatting consistency
    Returns: {
        'risk_score': 0-100,
        'precision_map': dict,
        'flags': [list of issues],
        'total_numbers': int
    }
    """
    with pdfplumber.open(pdf_path) as pdf:
        full_text = '\n'.join([page.extract_text() for page in pdf.pages if page.extract_text()])
    
    decimals = re.findall(r'\d+\.\d+', full_text)
    
    precision_map = {}
    for num in decimals:
        precision = len(num.split('.')[-1])
        if precision not in precision_map:
            precision_map[precision] = []
        precision_map[precision].append(num)
    
    flags = []
    if len(precision_map) > 3:
        flags.append(f"High precision variation ({len(precision_map)} types)")
        risk_score = 40
    elif len(precision_map) > 2:
        flags.append(f"Moderate precision variation ({len(precision_map)} types)")
        risk_score = 20
    else:
        risk_score = 0
    
    return {
        'risk_score': risk_score,
        'precision_map': precision_map,
        'flags': flags,
        'total_numbers': len(decimals)
    }


def check_image_quality(pdf_bytes, max_pages=3):
    """
    Analyze image quality (blur detection)
    Takes pdf_bytes (from uploaded file) instead of path
    Returns: {
        'risk_score': 0-100,
        'blur_scores': [list of scores],
        'avg_blur': float,
        'flags': [list of issues]
    }
    """
    try:
        from pdf2image import convert_from_bytes
        
        images = convert_from_bytes(pdf_bytes, dpi=150)
        blur_scores = []
        
        for idx, img in enumerate(images[:max_pages], 1):
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            blur = cv2.Laplacian(gray, cv2.CV_64F).var()
            blur_scores.append(blur)
        
        avg_blur = np.mean(blur_scores) if blur_scores else 0
        
        flags = []
        risk_score = 0
        
        if avg_blur < 100:
            flags.append(f"Low blur score ({avg_blur:.1f})")
            risk_score = 30
        
        if len(blur_scores) > 1:
            variance = max(blur_scores) / min(blur_scores) if min(blur_scores) > 0 else 1
            if variance > 3:
                flags.append(f"Inconsistent blur ({variance:.1f}x)")
                risk_score += 25
        
        return {
            'risk_score': min(risk_score, 100),
            'blur_scores': blur_scores,
            'avg_blur': avg_blur,
            'flags': flags
        }
        
    except Exception as e:
        return {
            'risk_score': 0,
            'blur_scores': [],
            'avg_blur': 0,
            'flags': [f'Image analysis unavailable: {str(e)}']
        }

