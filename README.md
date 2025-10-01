# Canadian Tax Document Fraud Detection – POC

A Streamlit-based proof of concept to validate consistency between Canadian T1 (Income Tax Return) and NOA (Notice of Assessment) documents using PDF text extraction, Google Gemini LLM, and basic image quality analysis.

## 1) Setup Instructions

### Prerequisites
- Python 3.9+
- Poppler (required for `pdf2image`)
- Internet access for Gemini API

### Create and activate a virtual environment

PowerShell (Windows):
```powershell
cd "C:\Users\qaboo\source\repos\Tax Docs Forensic Analysis\fraud-detection-poc"
python -m venv venv
.\nvenv\Scripts\Activate.ps1
```
If activation is blocked:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\nvenv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
cd "fraud-detection-poc"
python3 -m venv venv
source venv/bin/activate
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Install Poppler
- Windows: Download Poppler for Windows and add its `bin` folder to PATH (e.g., `C:\poppler\Library\bin`).
- macOS: `brew install poppler`
- Ubuntu/Debian: `sudo apt-get install poppler-utils`

## 2) Get a Gemini API Key
1. Open the Google AI Studio page: [Get a Gemini API key](https://makersuite.google.com/app/apikey)
2. Create an API key and copy it.
3. Provide the key to the app by either:
   - Entering it in the app sidebar when prompted, or
   - Creating a `.env` file from `env.example` and setting `GEMINI_API_KEY=your_key_here`.

## 3) Run the Application
```bash
streamlit run app.py
```
Then open the displayed local URL in your browser (default: `http://localhost:8501`).

## 4) How to Use
1. In the app, paste your Gemini API key in the sidebar (or use the key from `.env`).
2. Upload two PDFs:
   - T1 Income Tax Return (PDF)
   - Notice of Assessment (PDF)
3. Click "Analyze Documents".
4. Review results across tabs: Validation Checks, Extracted Data, Quality Analysis, Raw Results.
5. Optional: Download all results as JSON.

## 5) What Each Validation Check Does
The app orchestrates three analyzers and consolidates results.

### A. PDF Text Extraction (validators/data_extractor.py)
- Extracts plain text and tables from PDFs.
- Parses key fields per document type.
- Utility checks like page count to help confirm expected structure.

### B. LLM Extraction & Cross-Validation (validators/gemini_validator.py)
- Uses Gemini to extract structured fields from raw text.
- Performs cross-document checks and returns a risk rating with detailed checks.

Checks returned in "Validation Checks" tab include:
- SIN Match: Compares SIN/last 4 digits across T1 and NOA.
- Name Match: Exact or minor variations.
- Address Match: Exact or minor variations.
- Refund Amount Match: T1 refund/balance vs NOA summary.
- Income Matches: Total, Net, and Taxable income alignment.
- Tax Deducted Match: Line 43700 related deductions.
- Date Logic: Filing date (T1) must be before assessment date (NOA).
- High Installment Payment: Flags if instalments ≥ $10,000 for review.

Additional accountant validation:
- Checks accountant name presence and formats phone to a standard if valid (Canadian 10-digit format).

### C. Image Quality (validators/image_analyzer.py)
- Converts PDFs to images and computes a Laplacian variance blur score per page.
- Flags pages with blur score < 100 as potentially blurry.
- Returns average blur score and a list of blurry pages.

## 6) Known Limitations (POC)
- LLM outputs can vary; prompts are tuned with temperature=0 but may still produce inconsistent JSON. The app attempts robust parsing.
- PDF parsing depends on document quality; scanned/image-only PDFs with poor OCR won’t extract reliable text.
- Image analysis is limited to blur detection in this POC; contrast/compression/tampering analysis is not included yet.
- Address/name matching tolerates only minor variations.
- Cross-document mapping assumes standard CRA formats and line numbers; non-standard layouts may reduce accuracy.
- Poppler must be installed and on PATH for `pdf2image` conversions to work.

## 7) Troubleshooting
- "Poppler not found": Ensure Poppler is installed and its `bin` folder is on PATH.
- "Gemini API key not configured": Add the key in the sidebar or set `GEMINI_API_KEY` in `.env`.
- PowerShell script activation blocked: Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.
- pdf2image errors: Confirm Poppler is present and that your PDFs are not password-protected.
- LLM JSON parsing errors: Re-run analysis; if persistent, verify the uploaded documents are correct and readable.

## 8) Tech Stack
- Streamlit 1.x for UI
- pdfplumber for text extraction
- google-generativeai (Gemini) for LLM-based extraction and validation
- pdf2image + Pillow for PDF→image conversion
- OpenCV for blur detection
- python-dotenv for `.env` loading

---
POC Demo – Tax Document Fraud Detection System v0.1
