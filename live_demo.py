"""
Live Demo Script - Test the SEO Content Pipeline with a real website
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys

# Add colored output for better visibility
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    console = Console()
    RICH_AVAILABLE = True
except:
    RICH_AVAILABLE = False
    
from src.models import PipelineConfig, Job, JobStatus
from src.crawler import RespectfulCrawler
from src.business import BusinessAnalyzer
from urllib.parse import urlparse


def print_header():
    """Print demo header"""
    if RICH_AVAILABLE:
        console.print("\n[bold cyan]=" * 60)
        console.print("[bold yellow]SEO Content Pipeline - Live Demo")
        console.print("[bold cyan]=" * 60 + "\n")
    else:
        print("\n" + "=" * 60)
        print("SEO Content Pipeline - Live Demo")
        print("=" * 60 + "\n")


def print_section(title):
    """Print section header"""
    if RICH_AVAILABLE:
        console.print(f"\n[bold green]>>> {title}")
        console.print("[dim]" + "-" * 40)
    else:
        print(f"\n>>> {title}")
        print("-" * 40)


async def demo_crawl(url: str, max_pages: int = 10):
    """Demonstrate the crawling capability"""
    print_section("Web Crawling Demo")
    
    config = PipelineConfig(
        max_pages=max_pages,
        crawl_delay=1.0,  # Respectful delay between requests
        respect_robots=True
    )
    
    print(f"Target URL: {url}")
    print(f"Max pages: {max_pages}")
    print(f"Respecting robots.txt: {config.respect_robots}")
    print(f"Crawl delay: {config.crawl_delay}s\n")
    
    try:
        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("[cyan]Crawling website...", total=None)
                
                async with RespectfulCrawler(config) as crawler:
                    results = await crawler.crawl_site(url, max_pages)
                    
                progress.update(task, completed=True)
        else:
            print("Crawling website...")
            async with RespectfulCrawler(config) as crawler:
                results = await crawler.crawl_site(url, max_pages)
        
        # Display results
        print(f"\n[SUCCESS] Crawled {len(results)} pages")
        
        if RICH_AVAILABLE:
            # Create a table for crawl results
            table = Table(title="Crawled Pages")
            table.add_column("URL", style="cyan", no_wrap=False)
            table.add_column("Title", style="magenta")
            table.add_column("Words", style="green")
            
            for page in results[:5]:  # Show first 5 pages
                title = page.title[:40] + "..." if page.title and len(page.title) > 40 else page.title or "No title"
                table.add_row(
                    str(page.url)[:50],
                    title,
                    str(page.word_count)
                )
            
            console.print(table)
        else:
            print("\nCrawled pages:")
            for i, page in enumerate(results[:5], 1):
                print(f"{i}. {page.url}")
                print(f"   Title: {page.title}")
                print(f"   Words: {page.word_count}")
        
        return results
        
    except Exception as e:
        print(f"[ERROR] Crawling failed: {e}")
        return []


async def demo_business_analysis(crawl_results, url):
    """Demonstrate business understanding"""
    print_section("Business Analysis Demo")
    
    if not crawl_results:
        print("[WARNING] No crawl results to analyze")
        return None
    
    print(f"Analyzing {len(crawl_results)} pages for business insights...\n")
    
    try:
        analyzer = BusinessAnalyzer()
        business_name = urlparse(url).netloc.split('.')[0].replace('-', ' ').title()
        
        business = analyzer.analyze(crawl_results, business_name, url)
        
        print(f"[SUCCESS] Business analysis complete\n")
        
        # Display results
        if RICH_AVAILABLE:
            table = Table(title="Business Analysis Results")
            table.add_column("Category", style="cyan")
            table.add_column("Count", style="magenta")
            table.add_column("Examples", style="green")
            
            table.add_row(
                "Services",
                str(len(business.services)),
                ", ".join(business.services[:3]) if business.services else "None found"
            )
            table.add_row(
                "Products",
                str(len(business.products)),
                ", ".join(business.products[:3]) if business.products else "None found"
            )
            table.add_row(
                "Locations",
                str(len(business.locations)),
                ", ".join(business.locations[:3]) if business.locations else "None found"
            )
            table.add_row(
                "Target Audiences",
                str(len(business.target_audiences)),
                ", ".join(business.target_audiences[:3]) if business.target_audiences else "None found"
            )
            
            console.print(table)
        else:
            print("Business Name:", business.name)
            print(f"Services found: {len(business.services)}")
            if business.services:
                print(f"  Examples: {', '.join(business.services[:3])}")
            print(f"Products found: {len(business.products)}")
            if business.products:
                print(f"  Examples: {', '.join(business.products[:3])}")
        
        return business
        
    except Exception as e:
        print(f"[ERROR] Business analysis failed: {e}")
        print("[INFO] This may be because spaCy is not installed")
        return None


def save_demo_results(crawl_results, business, url):
    """Save demo results to JSON"""
    print_section("Saving Results")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    domain = urlparse(url).netloc.replace('.', '_')
    filename = f"demo_results_{domain}_{timestamp}.json"
    
    results = {
        "url": url,
        "timestamp": timestamp,
        "pages_crawled": len(crawl_results),
        "crawl_summary": [
            {
                "url": str(page.url),
                "title": page.title,
                "word_count": page.word_count
            }
            for page in crawl_results[:10]
        ]
    }
    
    if business:
        results["business_analysis"] = {
            "name": business.name,
            "services": business.services[:10],
            "products": business.products[:10],
            "locations": business.locations,
            "target_audiences": business.target_audiences
        }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"[SUCCESS] Results saved to: {filename}")
    return filename


async def main():
    """Main demo function"""
    print_header()
    
    # Get URL from user or use default
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        print("Usage: python live_demo.py <URL> [max_pages]")
        print("Example: python live_demo.py https://example.com 10\n")
        url = input("Enter URL to analyze (or press Enter for https://example.com): ").strip()
        if not url:
            url = "https://example.com"
    
    # Get max pages
    max_pages = 10
    if len(sys.argv) > 2:
        try:
            max_pages = int(sys.argv[2])
        except:
            pass
    
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    print(f"\nStarting demo with: {url}")
    print(f"Maximum pages to crawl: {max_pages}\n")
    
    # Run demo steps
    crawl_results = await demo_crawl(url, max_pages)
    
    if crawl_results:
        business = await demo_business_analysis(crawl_results, url)
        filename = save_demo_results(crawl_results, business, url)
        
        print_section("Demo Complete!")
        print(f"\nCrawled {len(crawl_results)} pages from {url}")
        print(f"Results saved to: {filename}")
        print("\nNext steps:")
        print("1. Install pandas for Excel export functionality")
        print("2. Install spacy for advanced NLP analysis")
        print("3. Configure Google APIs for keyword research")
        print("4. Run the full pipeline with: python -m src.cli.main run --url " + url)
    else:
        print("\n[ERROR] Demo failed - no pages could be crawled")
        print("Please check the URL and your internet connection")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[INFO] Demo interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()