# 🚀 Quick Start: Document Forensics

## Test in 3 Steps

### 1️⃣ Start the App
```bash
streamlit run app.py
```

### 2️⃣ Scroll Down
Find the **"🔍 Document Forensic Analysis"** section (below the main T1/NOA validation)

### 3️⃣ Upload & Analyze
1. Click "Upload PDF for Forensic Analysis"
2. Select any PDF (try `sample_documents/T1 2024.pdf`)
3. View instant results!

## What You'll See

### Overall Risk Dashboard
```
┌─────────────────────────────────┐
│ Overall Forensic Risk Score     │
│         7/100                   │
│   🟢 Risk Level: LOW            │
└─────────────────────────────────┘
```

### Individual Scores
```
Text Alignment  Font Consistency  Metadata  Numbers  Image Quality
     0/100           0/100         15/100   20/100      0/100
      🟢              🟢             🟢       🟢          🟢
```

### Expandable Details
- 📏 Text Alignment Analysis
- 🔤 Font Consistency Analysis  
- 📋 Metadata Analysis
- 🔢 Number Pattern Analysis
- 🖼️ Image Quality Analysis

### Visual Annotations
4-panel image showing:
- Original document
- Font issues (red)
- Number patterns (colored)
- Alignment problems (yellow)

## Sample Results

### T1 2024.pdf (Government Document)
```
✅ Overall: 7/100 - LOW RISK
- Alignment: 0 (Perfect)
- Fonts: 0 (Consistent)
- Metadata: 15 (Minor flags)
- Numbers: 20 (Slight variation)
- Image: 0 (Good quality)
```

### Typical Forged Document
```
🔴 Overall: 65/100 - HIGH RISK
- Alignment: 50 (Multiple issues)
- Fonts: 80 (Too many fonts)
- Metadata: 70 (Consumer tools detected)
- Numbers: 40 (Inconsistent formatting)
- Image: 30 (Low quality/blur)
```

## Quick Tips

✅ **DO:**
- Upload any PDF document
- Use scores as screening signals
- Review visual annotations
- Compare multiple documents

❌ **DON'T:**
- Treat scores as definitive proof
- Ignore context (some legit docs score medium)
- Skip the detailed findings
- Forget human review

## Keyboard Shortcuts

While in Streamlit:
- `R` - Rerun app
- `C` - Clear cache
- `Ctrl+S` - Screenshot
- `F11` - Fullscreen

## Next Steps

1. ✅ Test with sample documents
2. ✅ Upload your own PDFs
3. ✅ Review visual annotations
4. ✅ Check existing T1/NOA validation still works
5. ✅ Read `FORENSICS_IMPLEMENTATION.md` for details

## Troubleshooting

**Can't see forensics section?**
→ Scroll down below the T1/NOA analysis

**Upload fails?**
→ Ensure PDF is not password-protected

**High score on legit document?**
→ Normal - see detailed findings for context

**Need help?**
→ See `forensics/README.md` for full documentation

---

**Ready to catch document fraud! 🕵️**

