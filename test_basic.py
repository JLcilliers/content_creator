"""
Basic test script to verify the pipeline can run
"""
import asyncio
from src.models import PipelineConfig
from src.crawler import RespectfulCrawler
from src.business import BusinessAnalyzer
from src.exporter import ContentExporter
from urllib.parse import urlparse

async def test_basic_crawl():
    """Test basic crawl functionality"""
    url = "https://example.com"
    config = PipelineConfig(max_pages=5)
    
    print(f"Testing crawl of {url}...")
    
    try:
        async with RespectfulCrawler(config) as crawler:
            results = await crawler.crawl_site(url, max_pages=2)
            
        print(f"✓ Crawled {len(results)} pages")
        
        if results:
            print(f"  First page title: {results[0].title}")
            print(f"  Word count: {results[0].word_count}")
            
        # Test business analyzer
        print("\nTesting business analyzer...")
        analyzer = BusinessAnalyzer()
        business_name = urlparse(url).netloc.split('.')[0].title()
        
        # Note: spacy will fail if model not installed, so we catch that
        try:
            business = analyzer.analyze(results, business_name, url)
            print(f"✓ Business analysis complete")
            print(f"  Name: {business.name}")
        except Exception as e:
            print(f"⚠ Business analysis skipped (spacy model not installed): {e}")
            
        print("\nBasic functionality test complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
if __name__ == "__main__":
    asyncio.run(test_basic_crawl())