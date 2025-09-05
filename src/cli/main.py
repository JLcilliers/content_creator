"""
CLI interface for the SEO Content Pipeline
"""
import click
import asyncio
import json
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..models import PipelineConfig, JobStatus
from ..crawler import RespectfulCrawler
from ..business.understanding import BusinessAnalyzer
from ..exporter.exporter import ContentExporter

console = Console()


@click.group()
def cli():
    """SEO Content Pipeline - Automated content generation from URL"""
    pass


@cli.command()
@click.option('--url', required=True, help='Website URL to analyze')
@click.option('--locale', default='en-GB', help='Target locale (default: en-GB)')
@click.option('--max-pages', default=100, help='Maximum pages to crawl')
@click.option('--output', default='./exports', help='Output directory')
@click.option('--config', type=click.Path(exists=True), help='Path to config JSON file')
def run(url: str, locale: str, max_pages: int, output: str, config: str):
    """Run the complete SEO content pipeline"""
    
    console.print(f"[bold cyan]SEO Content Pipeline Starting[/bold cyan]")
    console.print(f"URL: {url}")
    console.print(f"Locale: {locale}")
    console.print(f"Max Pages: {max_pages}")
    
    # Load config
    pipeline_config = PipelineConfig()
    if config:
        with open(config) as f:
            config_data = json.load(f)
            pipeline_config = PipelineConfig(**config_data)
    
    pipeline_config.max_pages = max_pages
    
    # Run async pipeline
    asyncio.run(_run_pipeline(url, locale, pipeline_config, output))


async def _run_pipeline(url: str, locale: str, config: PipelineConfig, output_dir: str):
    """Async pipeline execution"""
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Step 1: Crawling
        crawl_task = progress.add_task("[cyan]Crawling website...", total=None)
        
        try:
            async with RespectfulCrawler(config) as crawler:
                crawl_results = await crawler.crawl_site(url, config.max_pages)
                
            progress.update(crawl_task, completed=True)
            console.print(f"[green]✓[/green] Crawled {len(crawl_results)} pages")
            
            # Step 2: Business Understanding
            analysis_task = progress.add_task("[cyan]Analyzing business...", total=None)
            
            analyzer = BusinessAnalyzer()
            from urllib.parse import urlparse
            business_name = urlparse(url).netloc.split('.')[0].title()
            business_entity = analyzer.analyze(crawl_results, business_name, url)
            
            progress.update(analysis_task, completed=True)
            console.print(f"[green]✓[/green] Business analysis complete")
            
            # Display business summary
            table = Table(title="Business Analysis Summary")
            table.add_column("Category", style="cyan")
            table.add_column("Count", style="magenta")
            
            table.add_row("Services", str(len(business_entity.services)))
            table.add_row("Products", str(len(business_entity.products)))
            table.add_row("Locations", str(len(business_entity.locations)))
            table.add_row("Target Audiences", str(len(business_entity.target_audiences)))
            table.add_row("Brand Terms", str(len(business_entity.brand_terms)))
            
            console.print(table)
            
            # Step 3: Export
            export_task = progress.add_task("[cyan]Exporting results...", total=None)
            
            # Create a mock job for export
            from ..models import Job
            from datetime import datetime
            import uuid
            
            job = Job(
                id=str(uuid.uuid4()),
                url=url,
                locale=locale,
                status=JobStatus.COMPLETED,
                business_entity=business_entity,
                crawl_results=crawl_results,
                completed_at=datetime.now()
            )
            
            exporter = ContentExporter(base_export_path=output_dir)
            export_result = exporter.export_job(job)
            
            progress.update(export_task, completed=True)
            console.print(f"[green]✓[/green] Export complete")
            
            # Display results
            console.print("\n[bold green]Pipeline Complete![/bold green]")
            console.print(f"Export folder: [yellow]{export_result['export_folder']}[/yellow]")
            
            if business_entity.services:
                console.print("\n[bold]Top Services Found:[/bold]")
                for service in business_entity.services[:5]:
                    console.print(f"  • {service}")
                    
            if business_entity.unique_value_props:
                console.print("\n[bold]Unique Value Propositions:[/bold]")
                for prop in business_entity.unique_value_props[:3]:
                    console.print(f"  • {prop}")
                    
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            raise


@cli.command()
@click.option('--config-file', type=click.Path(), default='pipeline-config.json', 
              help='Path to save config file')
def init(config_file: str):
    """Initialize a new configuration file"""
    
    config = PipelineConfig()
    config_dict = config.model_dump()
    
    with open(config_file, 'w') as f:
        json.dump(config_dict, f, indent=2, default=str)
        
    console.print(f"[green]✓[/green] Created config file: {config_file}")
    console.print("Edit this file to customize pipeline settings")


@cli.command()
@click.option('--host', default='localhost', help='API host')
@click.option('--port', default=8000, help='API port')
def serve(host: str, port: int):
    """Start the FastAPI server"""
    import uvicorn
    from ..api.main import app
    
    console.print(f"[bold cyan]Starting API server on http://{host}:{port}[/bold cyan]")
    uvicorn.run(app, host=host, port=port)


if __name__ == '__main__':
    cli()