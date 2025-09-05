# Quick Start Guide

## Installation Status

✅ **Core dependencies installed:**
- FastAPI, Pydantic (API and data models)
- Trafilatura, BeautifulSoup (Web scraping)
- httpx (HTTP client)
- Rich, Click (CLI interface)

⚠️ **Optional dependencies (install as needed):**
- `pandas` - Required for Excel export functionality
- `spacy` - Required for advanced NLP business analysis
- `numpy`, `scikit-learn` - Required for keyword clustering

## Running the Basic System

### 1. Test Basic Functionality
```bash
python test_simple.py
```

### 2. Start the API Server
```bash
python -m uvicorn src.api.main:app --reload
```
Then visit: http://localhost:8000

### 3. Create a Job via API
```bash
curl -X POST "http://localhost:8000/jobs" -H "Content-Type: application/json" -d "{\"url\": \"https://example.com\"}"
```

## Installing Additional Components

### For Excel Export
```bash
# Install pandas (may need Visual Studio Build Tools on Windows)
pip install pandas openpyxl
```

### For NLP Analysis
```bash
pip install spacy
python -m spacy download en_core_web_sm
```

### For Keyword Clustering
```bash
# Requires C++ compiler
pip install numpy scikit-learn sentence-transformers
```

## Simplified Usage (Without Heavy Dependencies)

The system can still:
1. ✅ Crawl websites respectfully
2. ✅ Extract text and metadata
3. ✅ Basic business understanding
4. ✅ API endpoints work
5. ⚠️ Excel export (needs pandas)
6. ⚠️ Advanced NLP (needs spacy)
7. ⚠️ Keyword clustering (needs ML libraries)

## Next Steps

1. **For Windows users without C++ compiler:**
   - Install Visual Studio Build Tools: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
   - OR use WSL2/Docker for easier dependency management

2. **For production use:**
   - Set up PostgreSQL database
   - Configure Redis for job queuing
   - Deploy with Docker

3. **To add Google APIs:**
   - Get Google Ads API credentials
   - Get Search Console API access
   - Add credentials to `.env` file

## Troubleshooting

### "No module named pandas"
The Excel export functionality requires pandas. Either:
- Install it: `pip install pandas openpyxl`
- Or use JSON export instead (modify the code)

### "spacy model not found"
The NLP analysis is optional. The system will fall back to basic text analysis.

### Unicode errors on Windows
The code uses UTF-8 encoding. If you see encoding errors, set:
```bash
set PYTHONIOENCODING=utf-8
```

## Working Components

You can use these parts immediately:
- Web crawler with robots.txt respect
- Text extraction with Trafilatura
- FastAPI server
- Pydantic data models
- Basic business analysis (without spacy)