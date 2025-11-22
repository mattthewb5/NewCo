# Loudoun County UI - Quick Start Guide

## 🚀 Run the UI (30 seconds)

```bash
# 1. Install dependencies (first time only)
pip install streamlit requests shapely geopy pandas

# 2. Run the UI
streamlit run loudoun_ui.py

# 3. Opens automatically at: http://localhost:8501
```

## 🎯 Quick Test

1. **Select a test address** from the dropdown:
   - Ashburn (Eastern Loudoun)
   - Sterling (Northern Loudoun)
   - Leesburg (Downtown)
   - Purcellville (Western Loudoun)
   - Developer's test address

2. **Click Search** 🔎

3. **View results** in tabs:
   - **Zoning Tab**: ✅ Real Loudoun County GIS data
   - **Schools Tab**: ⏳ Infrastructure ready, API pending
   - **Crime Tab**: ⏳ Infrastructure ready, API pending

## 📊 What You'll See

### Working Now ✅
- **Real zoning data** from Loudoun County GIS
  - Current zoning code
  - Detailed descriptions
  - Zoning authority
  - Data source attribution

### Coming Soon ⏳
- **School assignments** (pending LCPS API)
- **Crime analysis** (pending LCSO API)

## 🧪 Backend Validation

Test the backend services directly:

```bash
python test_loudoun_backend.py
```

Expected output:
```
✅ Configuration: Working
✅ Jurisdiction Detection: Working
✅ Zoning (Real GIS): Working
⏳ Schools: Infrastructure ready, API pending
⏳ Crime: Infrastructure ready, API pending
```

## 📖 Full Documentation

See `docs/loudoun_demo.md` for:
- Detailed test results for 5 addresses
- Technical architecture
- API integration status
- Known issues and solutions
- Next steps

## 💡 Tips

- **Try your own address!** Enter any Loudoun County address
- **Check zoning** - See what your property is zoned for
- **Explore different areas** - Compare Eastern vs Western Loudoun
- **Test incorporated towns** - Leesburg, Purcellville, etc.

## 🐛 Troubleshooting

**UI won't start:**
```bash
pip install --upgrade streamlit
streamlit run loudoun_ui.py
```

**Import errors:**
```bash
cd /home/user/NewCo
python -c "import sys; sys.path.insert(0, 'multi-county-real-estate-research'); from config import get_county_config; print('✅ OK')"
```

**Zoning data not loading:**
- Check internet connection (accesses Loudoun GIS API)
- Try backend test: `python test_loudoun_backend.py`

## 📧 Questions?

- Technical issues: Check `docs/loudoun_demo.md`
- API access: Contact LCPS (schools) or LCSO (crime)
- Feature requests: Note in documentation

---

**Ready to test!** 🎉

Run: `streamlit run loudoun_ui.py`
