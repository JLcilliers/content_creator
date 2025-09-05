"""
Pydantic data models for the SEO content pipeline
"""
from pydantic import BaseModel, HttpUrl, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Tuple, Literal
from datetime import datetime
from enum import Enum


class ContentType(str, Enum):
    BLOG = "blog"
    SERVICE = "service"
    PRODUCT = "product"
    LANDING = "landing"
    COMPARISON = "comparison"


class Intent(str, Enum):
    INFORMATIONAL = "informational"
    COMMERCIAL = "commercial"
    TRANSACTIONAL = "transactional"
    NAVIGATIONAL = "navigational"


class JobStatus(str, Enum):
    PENDING = "pending"
    CRAWLING = "crawling"
    ANALYZING = "analyzing"
    RESEARCHING = "researching"
    CLUSTERING = "clustering"
    GENERATING = "generating"
    WRITING = "writing"
    REVIEWING = "reviewing"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    FAILED = "failed"


class BusinessEntity(BaseModel):
    """Represents the business being analyzed"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    name: str
    homepage: HttpUrl
    services: List[str] = Field(default_factory=list)
    products: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    industries: List[str] = Field(default_factory=list)
    target_audiences: List[str] = Field(default_factory=list)
    exclusions: List[str] = Field(default_factory=list, description="Things the business does not do")
    brand_terms: List[str] = Field(default_factory=list)
    unique_value_props: List[str] = Field(default_factory=list)


class KeywordItem(BaseModel):
    """Individual keyword with metrics and verification status"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    term: str
    volume: int = Field(ge=0)
    ads_competition: float = Field(ge=0, le=1, default=0.0)
    cpc: Optional[float] = Field(ge=0, default=None)
    intent: Intent
    serp_features: List[str] = Field(default_factory=list)
    verified_against_site: bool = False
    cannot_verify_note: Optional[str] = None
    score: float = Field(ge=0, default=0.0)
    cluster_id: Optional[str] = None
    is_primary: bool = False
    difficulty_proxy: float = Field(ge=0, le=100, default=50.0)


class Cluster(BaseModel):
    """Keyword cluster with pillar designation"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: str
    label: str
    primary_terms: List[str] = Field(min_length=1)
    members: List[KeywordItem]
    pillar: str
    avg_volume: float = Field(ge=0)
    total_volume: int = Field(ge=0)
    dominant_intent: Intent
    content_type_suggestion: ContentType


class CompetitorGap(BaseModel):
    """Gap analysis result for a keyword"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    keyword: str
    volume: int = Field(ge=0)
    competitors_ranking: Dict[str, int]  # domain -> position
    client_position: Optional[int] = None
    gap_score: float = Field(ge=0)
    opportunity_type: Literal["missing", "underperforming"]


class CalendarItem(BaseModel):
    """Content calendar entry"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    week: int = Field(ge=1, le=52)
    topic: str
    content_type: ContentType
    primary_keyword: str
    secondary_keywords: List[str] = Field(max_length=6)
    cluster_id: str
    target_url: Optional[str] = None
    estimated_effort_hours: float = Field(ge=0)
    priority: Literal["high", "medium", "low"]
    
    @field_validator('secondary_keywords')
    @classmethod
    def validate_secondary_keywords(cls, v):
        if len(v) < 3:
            raise ValueError('Must have at least 3 secondary keywords')
        return v


class InternalLink(BaseModel):
    """Internal linking suggestion"""
    url: HttpUrl
    anchor_text: str
    relevance_score: float = Field(ge=0, le=1)


class FAQ(BaseModel):
    """FAQ item"""
    question: str
    answer: str
    
    @field_validator('answer')
    @classmethod
    def validate_answer_length(cls, v):
        if len(v.split()) < 30:
            raise ValueError('FAQ answer must be at least 30 words')
        return v


class Brief(BaseModel):
    """SEO content brief matching the template structure"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    # Core metadata
    topic: str
    primary_keyword: str
    secondary_keywords: List[str] = Field(min_length=3, max_length=6)
    content_type: ContentType
    
    # Web page structure
    target_url: str
    h1: str
    page_title: str = Field(max_length=60)
    meta_description: str = Field(min_length=120, max_length=160)
    
    # AI Optimisation sections
    key_takeaways: List[str] = Field(min_length=3, max_length=5)
    definitions: List[str] = Field(default_factory=list)
    key_stats: List[str] = Field(default_factory=list)
    decision_tips: List[str] = Field(default_factory=list)
    
    # Internal linking
    internal_links: List[InternalLink] = Field(min_length=3)
    
    # Writing guidelines
    audience: str
    tone: Literal["professional", "conversational", "academic", "friendly"]
    pov: Literal["first_person", "second_person", "third_person"]
    word_count_min: int = Field(default=800)
    word_count_max: int = Field(default=1200)
    
    # Sources and competition
    sources: List[Tuple[str, str]] = Field(default_factory=list)  # (Competitor Name, URL)
    
    # CTA
    cta: str
    
    # Restrictions and requirements
    restrictions: List[str] = Field(default_factory=list)
    requirements: List[str] = Field(default_factory=list)
    
    # Content structure
    headings_outline: List[Tuple[str, str]]  # (level, text) e.g., ("h2", "What is X?")
    
    # FAQs - exactly 4 required
    faqs: List[FAQ] = Field(min_length=4, max_length=4)
    
    @field_validator('faqs')
    @classmethod
    def validate_faqs(cls, v):
        if len(v) != 4:
            raise ValueError('Brief must contain exactly 4 FAQs as last section')
        return v


class Draft(BaseModel):
    """Full content draft"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    brief_id: str
    content: str
    word_count: int
    readability_score: float
    grammar_check_passed: bool
    uk_english_verified: bool
    internal_links_validated: bool
    facts_verified: bool
    verification_notes: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class CrawlResult(BaseModel):
    """Result from crawling a single page"""
    url: HttpUrl
    status_code: int
    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1: Optional[str] = None
    headings: Dict[str, List[str]] = Field(default_factory=dict)  # h2, h3, etc.
    text_content: str
    internal_links: List[str] = Field(default_factory=list)
    external_links: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    word_count: int
    crawled_at: datetime = Field(default_factory=datetime.now)


class Job(BaseModel):
    """Main job tracking model"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: str
    url: HttpUrl
    locale: str = Field(default="en-GB")
    status: JobStatus = JobStatus.PENDING
    progress: float = Field(ge=0, le=100, default=0)
    
    # Results
    business_entity: Optional[BusinessEntity] = None
    crawl_results: List[CrawlResult] = Field(default_factory=list)
    keywords: List[KeywordItem] = Field(default_factory=list)
    clusters: List[Cluster] = Field(default_factory=list)
    gaps: List[CompetitorGap] = Field(default_factory=list)
    calendar: List[CalendarItem] = Field(default_factory=list)
    briefs: List[Brief] = Field(default_factory=list)
    drafts: List[Draft] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    # Export paths
    export_folder: Optional[str] = None
    excel_path: Optional[str] = None


class PipelineConfig(BaseModel):
    """Configuration for the pipeline"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    # Crawling
    max_pages: int = Field(default=500, ge=1)
    crawl_delay: float = Field(default=1.0, ge=0.5)
    max_concurrent_crawls: int = Field(default=3, ge=1)
    respect_robots: bool = True
    
    # Keyword research
    min_search_volume: int = Field(default=10, ge=0)
    max_ads_competition: float = Field(default=0.8, ge=0, le=1)
    max_difficulty: float = Field(default=70, ge=0, le=100)
    
    # Clustering
    min_cluster_size: int = Field(default=3, ge=2)
    clustering_method: Literal["hdbscan", "agglomerative", "bertopic"] = "hdbscan"
    
    # Calendar
    calendar_weeks: int = Field(default=36, ge=1)
    content_mix: Dict[ContentType, int] = Field(
        default={
            ContentType.BLOG: 20,
            ContentType.SERVICE: 10,
            ContentType.LANDING: 4,
            ContentType.PRODUCT: 2
        }
    )
    
    # Verification
    nli_threshold: float = Field(default=0.8, ge=0, le=1)
    require_site_evidence: bool = True
    
    # Language
    language: str = Field(default="en-GB")
    readability_target: str = Field(default="university")
    
    # Export
    export_format: Literal["excel", "csv", "json"] = "excel"
    include_drafts: bool = True
    include_briefs: bool = True