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

st.set_page_config(page_title="LendGuard", layout="wide")

st.title("🔍 LendGuard")
st.markdown("Upload T1 Income Tax Return and Notice of Assessment for validation")

# Sidebar for API key input
# with st.sidebar:
# 	st.header("Configuration")
# 	api_key = st.text_input("Gemini API Key", type="password")
# 	if api_key:
# 		os.environ['GEMINI_API_KEY'] = api_key
# 		st.success("API Key configured")

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
				if t1_data.get('accountant_name'):
					accountant_results = validate_accountant_info(
						t1_data.get('accountant_name'),
						t1_data.get('accountant_phone'),
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

# ============================================================================
# FORENSIC ANALYSIS SECTION (Independent Module)
# ============================================================================

st.markdown("---")
st.header("🔍 Document Forensic Analysis")
st.markdown("""
Upload any PDF document for independent forensic analysis.
This checks for visual forgery indicators like font inconsistencies,
text misalignment, suspicious metadata, and image quality issues.
""")

forensic_file = st.file_uploader(
	"Upload PDF for Forensic Analysis",
	type=['pdf'],
	key="forensic_upload",
	help="Upload T1, NOA, or any other PDF document"
)

if forensic_file:
	st.info(f"📄 Analyzing: {forensic_file.name}")
	
	# Save uploaded file temporarily
	import tempfile
	import os
	from forensics import analyze_document_forensics, create_forensic_visualizations
	
	with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
		tmp_file.write(forensic_file.getvalue())
		tmp_path = tmp_file.name
	
	try:
		with st.spinner("Running forensic analysis..."):
			# Get PDF bytes for image analysis
			pdf_bytes = forensic_file.getvalue()
			
			# Run analysis
			results = analyze_document_forensics(tmp_path, pdf_bytes)
			
			# Display overall risk
			risk_colors = {
				'LOW': '🟢',
				'MEDIUM': '🟡',
				'HIGH': '🔴'
			}
			
			col1, col2, col3 = st.columns([1, 2, 1])
			with col2:
				st.metric(
					"Overall Forensic Risk Score",
					f"{results['overall_score']:.0f}/100",
					delta=None
				)
				st.markdown(f"### {risk_colors.get(results['risk_level'], '⚪')} Risk Level: {results['risk_level']}")
			
			# Detailed scores
			st.subheader("📊 Detailed Analysis")
			
			score_cols = st.columns(5)
			checks = [
				('alignment', 'Text Alignment'),
				('fonts', 'Font Consistency'),
				('metadata', 'Metadata'),
				('numbers', 'Number Patterns'),
				('image', 'Image Quality')
			]
			
			for idx, (key, label) in enumerate(checks):
				with score_cols[idx]:
					score = results[key].get('risk_score', 0)
					color = '🟢' if score < 30 else '🟡' if score < 60 else '🔴'
					st.metric(label, f"{score}/100", delta=None)
					st.markdown(f"{color}")
			
			# Expandable details
			st.subheader("🔍 Detailed Findings")
			
			with st.expander("📏 Text Alignment Analysis"):
				align_data = results['alignment']
				if align_data.get('count', 0) > 0:
					st.warning(f"Found {align_data['count']} alignment issues")
					if align_data.get('issues'):
						st.dataframe(align_data['issues'][:10])
				else:
					st.success("✅ All text properly aligned")
			
			with st.expander("🔤 Font Consistency Analysis"):
				font_data = results['fonts']
				st.write(f"**Total unique fonts:** {font_data.get('total_unique_fonts', 0)}")
				if font_data.get('flags'):
					for flag in font_data['flags']:
						st.warning(f"⚠️ {flag}")
				else:
					st.success("✅ Font usage consistent")
			
			with st.expander("📋 Metadata Analysis"):
				meta_data = results['metadata']
				if meta_data.get('metadata'):
					st.json(meta_data['metadata'])
				if meta_data.get('flags'):
					for flag in meta_data['flags']:
						st.warning(f"⚠️ {flag}")
				else:
					st.success("✅ Metadata appears legitimate")
			
			with st.expander("🔢 Number Pattern Analysis"):
				num_data = results['numbers']
				st.write(f"**Total decimal numbers:** {num_data.get('total_numbers', 0)}")
				if num_data.get('precision_map'):
					st.write("**Decimal precision distribution:**")
					for precision, numbers in num_data['precision_map'].items():
						st.write(f"  - {precision} decimal places: {len(numbers)} numbers")
				if num_data.get('flags'):
					for flag in num_data['flags']:
						st.warning(f"⚠️ {flag}")
				else:
					st.success("✅ Number formatting consistent")
			
			with st.expander("🖼️ Image Quality Analysis"):
				img_data = results['image']
				if img_data.get('avg_blur'):
					st.write(f"**Average blur score:** {img_data['avg_blur']:.1f}")
					st.caption("(Higher = Sharper, <100 = Potentially Blurry)")
				if img_data.get('flags'):
					for flag in img_data['flags']:
						st.warning(f"⚠️ {flag}")
				else:
					st.success("✅ Image quality normal")
			
			# Visual annotations
			st.markdown("---")
			create_forensic_visualizations(tmp_path, pdf_bytes, results, max_pages=2)
			
	except Exception as e:
		st.error(f"Error during analysis: {str(e)}")
	
	finally:
		# Clean up temp file
		if os.path.exists(tmp_path):
			os.unlink(tmp_path)

# Footer
st.markdown("---")
st.caption("POC Demo - Tax Document Fraud Detection System v0.1")
