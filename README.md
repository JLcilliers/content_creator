# SEO Content Pipeline

Automated SEO content generation system that crawls websites, performs keyword research, and generates content briefs and drafts with full Excel indexing.

## Features

✅ **Implemented**
- Respectful web crawling with robots.txt compliance
- Business understanding and entity extraction
- Pydantic data models with validation
- Excel export with clickable hyperlinks
- FastAPI REST endpoints
- CLI interface with progress tracking
- Organized folder structure for exports

🚧 **To Be Implemented**
- Google Ads API keyword research
- Search Console integration
- Keyword clustering with embeddings
- Competitor gap analysis
- Content brief generator with template
- AI content writer
- Grammar and UK English QA
- NLI-based fact verification

## Installation

### Prerequisites
- Python 3.11+
- Poetry (for dependency management)

### Setup

1. Clone the repository:
```bash
cd seo-content-pipeline
```

2. Install dependencies with Poetry:
```bash
poetry install
```

3. Download spaCy language model:
```bash
poetry run python -m spacy download en_core_web_sm
```

4. Install Playwright browsers (for JS-rendered pages):
```bash
poetry run playwright install chromium
```

## Usage

### CLI Interface

#### Basic crawl and analysis:
```bash
poetry run seo-pipeline run --url https://example.com --max-pages 50
```

#### With custom configuration:
```bash
# Generate config file
poetry run seo-pipeline init

# Edit pipeline-config.json as needed

# Run with config
poetry run seo-pipeline run --url https://example.com --config pipeline-config.json
```

### API Server

#### Start the server:
```bash
poetry run seo-pipeline serve
```

#### Create a job via API:
```bash
curl -X POST "http://localhost:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "locale": "en-GB"}'
```

#### Check job status:
```bash
curl "http://localhost:8000/jobs/{job_id}"
```

### Python Script

```python
import asyncio
from src.crawler import RespectfulCrawler
from src.business.understanding import BusinessAnalyzer
from src.models import PipelineConfig

async def main():
    config = PipelineConfig()
    
    # Crawl website
    async with RespectfulCrawler(config) as crawler:
        results = await crawler.crawl_site("https://example.com")
    
    # Analyze business
    analyzer = BusinessAnalyzer()
    business = analyzer.analyze(results, "Example Co", "https://example.com")
    
    print(f"Found {len(business.services)} services")
    print(f"Found {len(business.products)} products")

asyncio.run(main())
```

## Output Structure

```
exports/
└── client-name_20240101_120000/
    ├── briefs/
    │   ├── 001-topic-name-brief.md
    │   ├── 002-topic-name-brief.md
    │   └── ...
    ├── drafts/
    │   ├── 001-topic-name-draft.md
    │   ├── 002-topic-name-draft.md
    │   └── ...
    ├── data/
    │   ├── crawl-report.json
    │   ├── business-analysis.json
    │   ├── keywords.csv
    │   └── clusters.json
    ├── assets/
    └── content-calendar-index.xlsx  # With clickable hyperlinks
```

## Configuration

The `PipelineConfig` supports:

- **Crawling**: max_pages, crawl_delay, respect_robots
- **Keywords**: min_search_volume, max_ads_competition
- **Clustering**: method (hdbscan/agglomerative/bertopic)
- **Calendar**: weeks, content_mix
- **Language**: locale, readability_target
- **Export**: format, include_drafts, include_briefs

## API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /jobs` - Create new job
- `GET /jobs/{job_id}` - Get job status
- `GET /jobs` - List all jobs

## Next Steps for Full Implementation

1. **Google Ads Integration**
   - Set up Google Ads API credentials
   - Implement KeywordPlannerService client
   - Add historical metrics fetching

2. **Keyword Clustering**
   - Implement sentence-transformers embeddings
   - Add HDBSCAN clustering
   - Create cluster naming with c-TF-IDF

3. **Content Generation**
   - Implement brief template matching your format
   - Add OpenAI/Anthropic integration for writing
   - Implement UK English validation with LanguageTool

4. **Verification System**
   - Add NLI model for fact-checking
   - Implement claim-evidence alignment
   - Add "cannot verify" fallback

5. **Production Deployment**
   - Replace in-memory storage with PostgreSQL
   - Add Redis for job queuing
   - Implement Celery workers for background tasks
   - Add monitoring and logging

## Environment Variables

Create a `.env` file:

```env
# Google APIs (when implemented)
GOOGLE_ADS_DEVELOPER_TOKEN=
GOOGLE_ADS_CLIENT_ID=
GOOGLE_ADS_CLIENT_SECRET=
GOOGLE_ADS_REFRESH_TOKEN=
GOOGLE_ADS_CUSTOMER_ID=

# Search Console API (when implemented)
SEARCH_CONSOLE_CREDENTIALS_PATH=

# OpenAI (for content generation - when implemented)
OPENAI_API_KEY=

# Database (for production)
DATABASE_URL=postgresql://user:pass@localhost/seo_pipeline
REDIS_URL=redis://localhost:6379

# Export settings
EXPORT_BASE_PATH=./exports
```

## License

MIT

## Support

For issues or questions, please create an issue in the repository.