import os
import sys
import json
import io
import streamlit as st
from typing import Dict, Any


# Ensure the app directory is on sys.path so local packages (e.g., validators) are importable
APP_DIR = os.path.dirname(__file__)
from dotenv import load_dotenv
load_dotenv(os.path.join(APP_DIR, ".env"))
if APP_DIR not in sys.path:
	sys.path.insert(0, APP_DIR)

from tax_validators.data_extractor import (
	extract_text_from_pdf,
	extract_tables_from_pdf,
	get_page_count,
	extract_key_fields,
)
from tax_validators.gemini_validator import (
	initialize_gemini,
	extract_structured_data_t1,
	extract_structured_data_noa,
	validate_cross_document,
	validate_accountant_info,
)
from tax_validators.image_analyzer import (
	analyze_image_quality,
)

st.set_page_config(page_title="Tax Document Fraud Detection", layout="wide")

st.title("🔍 Canadian Tax Document Fraud Detection POC")
st.markdown("Upload T1 Income Tax Return and Notice of Assessment for validation")

# Sidebar for API key input
with st.sidebar:
	st.header("Configuration")
	api_key = st.text_input("Gemini API Key", type="password")
	if api_key:
		os.environ['GEMINI_API_KEY'] = api_key
		st.success("API Key configured")

# File uploaders
col1, col2 = st.columns(2)

with col1:
	st.subheader("📄 T1 Income Tax Return")
	t1_file = st.file_uploader("Upload T1 document", type=['pdf'], key="t1")

with col2:
	st.subheader("📄 Notice of Assessment")
	noa_file = st.file_uploader("Upload NOA document", type=['pdf'], key="noa")

progress = st.empty()
status = st.empty()

if st.button("🚀 Analyze Documents", type="primary", disabled=not (t1_file and noa_file)):
	with st.spinner("Analyzing documents..."):
		analysis_ok = True
		results: Dict[str, Any] = {}
		try:
			# Step 1: Extract text
			status.info("Step 1: Extracting text from PDFs...")
			progress.progress(10)
			try:
				t1_text = extract_text_from_pdf(t1_file)
				noa_text = extract_text_from_pdf(noa_file)
			except Exception as e:
				st.error(f"Failed to extract text: {e}")
				analysis_ok = False
				raise

			# Step 2: Initialize Gemini
			status.info("Step 2: Initializing AI validator...")
			progress.progress(25)
			try:
				model = initialize_gemini()
			except Exception as e:
				st.error(f"Gemini initialization failed: {e}")
				analysis_ok = False
				raise

			# Step 3: Extract structured data
			status.info("Step 3: Extracting structured data...")
			progress.progress(45)
			try:
				t1_data = extract_structured_data_t1(t1_text, model)
				noa_data = extract_structured_data_noa(noa_text, model)
			except Exception as e:
				st.error(f"Structured data extraction failed: {e}")
				analysis_ok = False
				raise

			# Step 4: Cross-document validation
			status.info("Step 4: Validating consistency...")
			progress.progress(65)
			try:
				validation_results = validate_cross_document(t1_data, noa_data, model)
			except Exception as e:
				st.error(f"Validation failed: {e}")
				analysis_ok = False
				raise

			# Step 5: Accountant validation
			status.info("Step 5: Validating accountant information...")
			progress.progress(75)
			try:
				if t1_data.get('AccountantName'):
					accountant_results = validate_accountant_info(
						t1_data.get('AccountantName'),
						t1_data.get('AccountantPhoneNumber'),
						model
					)
				else:
					accountant_results = {"flags": ["No accountant information found - FLAGGED"]}
			except Exception as e:
				st.warning(f"Accountant validation issue: {e}")
				accountant_results = {"flags": [f"Validation error: {e}"]}

			# Step 6: Image quality check
			status.info("Step 6: Analyzing image quality...")
			progress.progress(85)
			try:
				# Reset and read bytes for both files
				t1_file.seek(0)
				noa_file.seek(0)
				t1_bytes = t1_file.read()
				noa_bytes = noa_file.read()
				t1_quality = analyze_image_quality(t1_bytes)
				noa_quality = analyze_image_quality(noa_bytes)
			except Exception as e:
				st.warning(f"Image quality analysis issue: {e}")
				t1_quality, noa_quality = {"quality_flags": [str(e)], "blurry_pages": [], "avg_blur_score": 0}, {"quality_flags": [str(e)], "blurry_pages": [], "avg_blur_score": 0}

			# Step 7: Page count check
			status.info("Step 7: Checking page count...")
			progress.progress(92)
			try:
				noa_file.seek(0)
				noa_pages = get_page_count(noa_file)
				page_check = {"status": "pass" if noa_pages > 2 else "fail", "count": noa_pages}
			except Exception as e:
				st.warning(f"Page count check failed: {e}")
				page_check = {"status": "fail", "count": 0}

			# Aggregate results
			results = {
				"t1_data": t1_data,
				"noa_data": noa_data,
				"validation_results": validation_results,
				"accountant_results": accountant_results,
				"t1_quality": t1_quality,
				"noa_quality": noa_quality,
				"page_check": page_check,
			}

		finally:
			progress.empty()
			status.empty()

		if analysis_ok:
			st.success("✅ Analysis Complete!")
			# Overall Risk Score
			risk_color = {"low": "🟢", "medium": "🟡", "high": "🔴"}
			overall_risk = results["validation_results"].get("overall_risk", "unknown")
			st.header(f"{risk_color.get(overall_risk, '⚪')} Overall Risk: {overall_risk.upper()}")

			# Detailed Results
			tab1, tab2, tab3, tab4 = st.tabs(["Validation Checks", "Extracted Data", "Quality Analysis", "Raw Results"])

			with tab1:
				st.subheader("Validation Results")
				for check in results["validation_results"].get('checks', []):
					status_icon = {"pass": "✅", "fail": "❌", "warning": "⚠️"}
					with st.expander(f"{status_icon.get(check.get('status'))} {check.get('check')} - Confidence: {check.get('confidence')}%"):
						st.write(check.get('details'))

				# Accountant validation
				st.subheader("Accountant Information")
				if results["accountant_results"].get('flags'):
					for flag in results["accountant_results"]['flags']:
						st.warning(flag)
				else:
					st.success("✅ Accountant information validated")

				# Page count
				st.subheader("Document Structure")
				if results["page_check"]['status'] == 'pass':
					st.success(f"✅ NOA has {results['page_check']['count']} pages (required: >2)")
				else:
					st.error(f"❌ NOA has only {results['page_check']['count']} pages (required: >2)")

			with tab2:
				col1, col2 = st.columns(2)
				with col1:
					st.subheader("T1 Data")
					st.json(results["t1_data"]) 
				with col2:
					st.subheader("NOA Data")
					st.json(results["noa_data"]) 

			with tab3:
				col1, col2 = st.columns(2)
				with col1:
					st.subheader("T1 Quality")
					st.json(results["t1_quality"])
				with col2:
					st.subheader("NOA Quality")
					st.json(results["noa_quality"])

			with tab4:
				st.subheader("Raw Results")
				st.json(results)
				st.download_button(
					label="⬇️ Download Results (JSON)",
					data=json.dumps(results, indent=2),
					file_name="fraud_detection_results.json",
					mime="application/json",
				)

# Footer
st.markdown("---")
st.caption("POC Demo - Tax Document Fraud Detection System v0.1")
