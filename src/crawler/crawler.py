"""
Web crawler with robots.txt respect and intelligent extraction
"""
import asyncio
import logging
import sys
import io

# Fix Unicode issues on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
from typing import List, Optional, Set, Dict, Any
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import httpx
from bs4 import BeautifulSoup
import trafilatura
from playwright.async_api import async_playwright, Browser, Page
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import CrawlResult, PipelineConfig

logger = logging.getLogger(__name__)


class RespectfulCrawler:
    """Polite web crawler that respects robots.txt and rate limits"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.visited_urls: Set[str] = set()
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.browser: Optional[Browser] = None
        self.client: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'SEOContentPipeline/1.0 (Compatible; Respectful Crawler)'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
        if self.browser:
            await self.browser.close()
            
    async def _get_robots(self, url: str) -> RobotFileParser:
        """Fetch and cache robots.txt for a domain"""
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        
        if domain not in self.robots_cache:
            robots_url = urljoin(domain, '/robots.txt')
            rp = RobotFileParser()
            rp.set_url(robots_url)
            
            try:
                response = await self.client.get(robots_url)
                if response.status_code == 200:
                    rp.parse(response.text.splitlines())
                else:
                    rp.allow_all = True
            except Exception as e:
                logger.warning(f"Failed to fetch robots.txt from {domain}: {e}")
                rp.allow_all = True
                
            self.robots_cache[domain] = rp
            
        return self.robots_cache[domain]
        
    async def _can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt"""
        if not self.config.respect_robots:
            return True
            
        robots = await self._get_robots(url)
        return robots.can_fetch("*", url)
        
    async def _extract_sitemap_urls(self, base_url: str) -> List[str]:
        """Extract URLs from sitemap if available"""
        sitemap_urls = []
        parsed = urlparse(base_url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        
        # Check robots.txt for sitemap location
        robots = await self._get_robots(base_url)
        if hasattr(robots, 'site_maps') and robots.site_maps():
            for sitemap_url in robots.site_maps():
                sitemap_urls.extend(await self._parse_sitemap(sitemap_url))
        
        # Also check default location
        default_sitemap = urljoin(domain, '/sitemap.xml')
        try:
            response = await self.client.get(default_sitemap)
            if response.status_code == 200:
                sitemap_urls.extend(await self._parse_sitemap(default_sitemap))
        except:
            pass
            
        return list(set(sitemap_urls))
        
    async def _parse_sitemap(self, sitemap_url: str) -> List[str]:
        """Parse sitemap XML and extract URLs"""
        urls = []
        try:
            response = await self.client.get(sitemap_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'xml')
                for loc in soup.find_all('loc'):
                    urls.append(loc.text.strip())
        except Exception as e:
            logger.warning(f"Failed to parse sitemap {sitemap_url}: {e}")
            
        return urls
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _fetch_page(self, url: str, use_js: bool = False) -> Optional[str]:
        """Fetch page content with retry logic"""
        if use_js and not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
            
        try:
            if use_js:
                page = await self.browser.new_page()
                await page.goto(url, wait_until='networkidle')
                content = await page.content()
                await page.close()
                return content
            else:
                response = await self.client.get(url)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
            
    def _extract_text_and_metadata(self, html: str, url: str) -> CrawlResult:
        """Extract text and metadata from HTML"""
        # Try trafilatura first for clean text extraction
        text_content = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            deduplicate=True,
            target_language='en'
        )
        
        # Fallback to BeautifulSoup for structured data
        soup = BeautifulSoup(html, 'html.parser')
        
        if not text_content:
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            text_content = soup.get_text(separator=' ', strip=True)
            
        # Extract metadata
        title = None
        if soup.title:
            title = soup.title.string
            
        meta_description = None
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            meta_description = meta_desc.get('content')
            
        # Extract headings
        h1 = None
        h1_tag = soup.find('h1')
        if h1_tag:
            h1 = h1_tag.get_text(strip=True)
            
        headings = {}
        for level in ['h2', 'h3', 'h4']:
            headings[level] = [h.get_text(strip=True) for h in soup.find_all(level)]
            
        # Extract links
        internal_links = []
        external_links = []
        parsed_url = urlparse(url)
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href)
            parsed_href = urlparse(full_url)
            
            if parsed_href.netloc == parsed_url.netloc:
                internal_links.append(full_url)
            elif parsed_href.scheme in ['http', 'https']:
                external_links.append(full_url)
                
        # Extract images
        images = [urljoin(url, img['src']) for img in soup.find_all('img', src=True)]
        
        return CrawlResult(
            url=url,
            status_code=200,
            title=title,
            meta_description=meta_description,
            h1=h1,
            headings=headings,
            text_content=text_content or "",
            internal_links=internal_links,
            external_links=external_links,
            images=images,
            word_count=len(text_content.split()) if text_content else 0
        )
        
    async def crawl_site(
        self,
        start_url: str,
        max_pages: Optional[int] = None
    ) -> List[CrawlResult]:
        """Crawl website starting from given URL"""
        max_pages = max_pages or self.config.max_pages
        results = []
        
        # Initialize with sitemap URLs if available
        urls_to_visit = set([start_url])
        sitemap_urls = await self._extract_sitemap_urls(start_url)
        urls_to_visit.update(sitemap_urls[:max_pages])
        
        parsed_start = urlparse(start_url)
        domain = parsed_start.netloc
        
        semaphore = asyncio.Semaphore(self.config.max_concurrent_crawls)
        
        async def process_url(url: str):
            async with semaphore:
                if url in self.visited_urls or len(results) >= max_pages:
                    return
                    
                self.visited_urls.add(url)
                
                # Check robots.txt
                if not await self._can_fetch(url):
                    logger.info(f"Skipping {url} due to robots.txt")
                    return
                    
                # Rate limiting
                await asyncio.sleep(self.config.crawl_delay)
                
                # Fetch and process page
                html = await self._fetch_page(url)
                if html:
                    result = self._extract_text_and_metadata(html, url)
                    results.append(result)
                    
                    # Add internal links to queue
                    for link in result.internal_links[:10]:  # Limit to avoid explosion
                        parsed_link = urlparse(link)
                        if parsed_link.netloc == domain and link not in self.visited_urls:
                            urls_to_visit.add(link)
                            
        while urls_to_visit and len(results) < max_pages:
            batch = list(urls_to_visit)[:10]
            urls_to_visit = urls_to_visit - set(batch)
            
            await asyncio.gather(*[process_url(url) for url in batch])
            
        logger.info(f"Crawled {len(results)} pages from {start_url}")
        return results