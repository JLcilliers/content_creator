"""
FastAPI application for the SEO Content Pipeline
"""
import uuid
import asyncio
import logging
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from datetime import datetime

from ..models import Job, JobStatus, PipelineConfig
from ..crawler import RespectfulCrawler
from ..business.understanding import BusinessAnalyzer
from ..exporter.exporter import ContentExporter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SEO Content Pipeline",
    description="Automated SEO content generation from URL input",
    version="0.1.0"
)

# In-memory job storage (use Redis or DB in production)
jobs: Dict[str, Job] = {}


class JobRequest(BaseModel):
    url: HttpUrl
    locale: str = "en-GB"
    config: Optional[PipelineConfig] = None


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str


async def process_job(job_id: str, url: str, locale: str, config: PipelineConfig):
    """Background task to process the full pipeline"""
    job = jobs[job_id]
    
    try:
        # Update status
        job.status = JobStatus.CRAWLING
        job.updated_at = datetime.now()
        
        # Step 1: Crawl the website
        logger.info(f"Starting crawl for {url}")
        async with RespectfulCrawler(config) as crawler:
            crawl_results = await crawler.crawl_site(url, config.max_pages)
            job.crawl_results = crawl_results
            job.progress = 20
            
        # Step 2: Business Understanding
        job.status = JobStatus.ANALYZING
        logger.info("Analyzing business from crawled content")
        
        analyzer = BusinessAnalyzer()
        business_name = urlparse(url).netloc.split('.')[0].title()
        business_entity = analyzer.analyze(crawl_results, business_name, url)
        job.business_entity = business_entity
        job.progress = 30
        
        # Step 3: Keyword Research (placeholder for now)
        job.status = JobStatus.RESEARCHING
        job.progress = 40
        logger.info("Keyword research module not yet implemented")
        
        # Step 4: Export what we have
        job.status = JobStatus.EXPORTING
        job.progress = 90
        
        exporter = ContentExporter()
        export_result = exporter.export_job(job)
        
        # Mark complete
        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.completed_at = datetime.now()
        
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        job.status = JobStatus.FAILED
        job.error = str(e)
        job.updated_at = datetime.now()


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "SEO Content Pipeline API",
        "version": "0.1.0",
        "endpoints": {
            "POST /jobs": "Create a new content generation job",
            "GET /jobs/{job_id}": "Get job status and results",
            "GET /health": "Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/jobs", response_model=JobResponse)
async def create_job(request: JobRequest, background_tasks: BackgroundTasks):
    """Create a new content generation job"""
    
    # Create job
    job_id = str(uuid.uuid4())
    config = request.config or PipelineConfig()
    
    job = Job(
        id=job_id,
        url=request.url,
        locale=request.locale,
        status=JobStatus.PENDING
    )
    
    jobs[job_id] = job
    
    # Start processing in background
    background_tasks.add_task(
        process_job,
        job_id,
        str(request.url),
        request.locale,
        config
    )
    
    return JobResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message=f"Job created and processing started for {request.url}"
    )


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Get job status and results"""
    
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job = jobs[job_id]
    
    return {
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress,
        "url": str(job.url),
        "locale": job.locale,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "error": job.error,
        "results": {
            "pages_crawled": len(job.crawl_results),
            "business_name": job.business_entity.name if job.business_entity else None,
            "services_found": len(job.business_entity.services) if job.business_entity else 0,
            "products_found": len(job.business_entity.products) if job.business_entity else 0,
            "keywords_found": len(job.keywords),
            "clusters_created": len(job.clusters),
            "calendar_items": len(job.calendar),
            "briefs_generated": len(job.briefs),
            "drafts_written": len(job.drafts),
            "export_folder": job.export_folder,
            "excel_path": job.excel_path
        }
    }


@app.get("/jobs")
async def list_jobs():
    """List all jobs"""
    return {
        "total": len(jobs),
        "jobs": [
            {
                "job_id": job.id,
                "url": str(job.url),
                "status": job.status,
                "created_at": job.created_at.isoformat(),
                "progress": job.progress
            }
            for job in jobs.values()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    from urllib.parse import urlparse
    uvicorn.run(app, host="0.0.0.0", port=8000)