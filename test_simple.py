"""
Simple test without heavy dependencies
"""
import asyncio
import httpx
from bs4 import BeautifulSoup
import trafilatura

async def test_basic():
    """Test basic web scraping functionality"""
    url = "https://example.com"
    
    print(f"Testing basic scraping of {url}...\n")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        html = response.text
        
    # Test trafilatura extraction
    text_content = trafilatura.extract(html)
    print(f"[OK] Trafilatura extracted {len(text_content.split())} words")
    
    # Test BeautifulSoup parsing
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.string if soup.title else "No title"
    print(f"[OK] BeautifulSoup found title: {title}")
    
    # Test model imports
    try:
        from src.models import Job, PipelineConfig, BusinessEntity
        print("[OK] Models imported successfully")
        
        # Test creating instances
        config = PipelineConfig()
        print(f"[OK] Created PipelineConfig with max_pages={config.max_pages}")
        
        business = BusinessEntity(
            name="Test Company",
            homepage="https://example.com",
            services=["Web Development", "Consulting"]
        )
        print(f"[OK] Created BusinessEntity: {business.name}")
        
    except Exception as e:
        print(f"[ERROR] Error with models: {e}")
        
    print("\n[SUCCESS] Basic functionality test complete!")
    print("\nTo run the full pipeline, you'll need to install:")
    print("  - pandas (for Excel export)")
    print("  - spacy (for NLP analysis)")
    print("  - numpy/scikit-learn (for clustering)")
    
if __name__ == "__main__":
    asyncio.run(test_basic())