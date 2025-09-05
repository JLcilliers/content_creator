"""
Export module for creating organized folders and Excel index with hyperlinks
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime
import re

from ..models import Job, CalendarItem, Brief, Draft

logger = logging.getLogger(__name__)


class ContentExporter:
    """Exports content to organized folders with Excel index"""
    
    def __init__(self, base_export_path: str = "./exports"):
        self.base_export_path = Path(base_export_path)
        self.base_export_path.mkdir(parents=True, exist_ok=True)
        
    def _sanitize_filename(self, text: str, max_length: int = 50) -> str:
        """Create safe filename from text"""
        # Remove special characters
        text = re.sub(r'[^\w\s-]', '', text)
        # Replace spaces with hyphens
        text = re.sub(r'[-\s]+', '-', text)
        # Truncate and clean
        text = text[:max_length].strip('-').lower()
        return text or "untitled"
        
    def _create_folder_structure(self, job: Job) -> Dict[str, Path]:
        """Create organized folder structure for exports"""
        # Create main export folder with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_slug = self._sanitize_filename(job.business_entity.name if job.business_entity else "client")
        export_folder = self.base_export_path / f"{client_slug}_{timestamp}"
        
        # Create subfolders
        folders = {
            "root": export_folder,
            "briefs": export_folder / "briefs",
            "drafts": export_folder / "drafts",
            "assets": export_folder / "assets",
            "data": export_folder / "data"
        }
        
        for folder in folders.values():
            folder.mkdir(parents=True, exist_ok=True)
            
        return folders
        
    def _export_briefs(self, briefs: List[Brief], folder: Path) -> List[Dict[str, str]]:
        """Export briefs to markdown files"""
        brief_files = []
        
        for idx, brief in enumerate(briefs, 1):
            filename = f"{idx:03d}-{self._sanitize_filename(brief.topic)}-brief.md"
            filepath = folder / filename
            
            # Format brief content
            content = self._format_brief_markdown(brief)
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
            brief_files.append({
                "index": idx,
                "topic": brief.topic,
                "filename": filename,
                "path": str(filepath)
            })
            
        logger.info(f"Exported {len(briefs)} briefs")
        return brief_files
        
    def _format_brief_markdown(self, brief: Brief) -> str:
        """Format brief into structured markdown matching the template"""
        lines = []
        
        # Header
        lines.append(f"# {brief.topic} - Content Brief V2.0")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Web Page Structure
        lines.append("## Web Page Structure")
        lines.append("")
        lines.append(f"**Target URL:** {brief.target_url}")
        lines.append(f"**H1:** {brief.h1}")
        lines.append(f"**Page Title:** {brief.page_title}")
        lines.append(f"**Meta Description:** {brief.meta_description}")
        lines.append("")
        
        # AI Optimisation
        lines.append("## AI Optimisation")
        lines.append("")
        
        # Key Takeaways (must be directly under H1)
        lines.append("### Key Takeaways")
        lines.append("*To appear directly under the H1*")
        lines.append("")
        for takeaway in brief.key_takeaways:
            lines.append(f"- {takeaway}")
        lines.append("")
        
        # Definitions
        if brief.definitions:
            lines.append("### Definitions")
            lines.append("")
            for definition in brief.definitions:
                lines.append(f"- {definition}")
            lines.append("")
            
        # Key Statistics
        if brief.key_stats:
            lines.append("### Key Statistics")
            lines.append("")
            for stat in brief.key_stats:
                lines.append(f"- {stat}")
            lines.append("")
            
        # Decision Tips
        if brief.decision_tips:
            lines.append("### Decision Tips")
            lines.append("")
            for tip in brief.decision_tips:
                lines.append(f"- {tip}")
            lines.append("")
            
        # Keywords
        lines.append("## Keywords")
        lines.append("")
        lines.append(f"**Primary Keyword:** {brief.primary_keyword}")
        lines.append(f"**Secondary Keywords:** {', '.join(brief.secondary_keywords)}")
        lines.append("")
        
        # Internal Linking
        lines.append("## Internal Linking")
        lines.append("")
        lines.append("| URL | Anchor Text | Relevance |")
        lines.append("|-----|-------------|-----------|")
        for link in brief.internal_links:
            lines.append(f"| {link.url} | {link.anchor_text} | {link.relevance_score:.1f} |")
        lines.append("")
        
        # Writing Guidelines
        lines.append("## Writing Guidelines")
        lines.append("")
        lines.append(f"**Target Audience:** {brief.audience}")
        lines.append(f"**Tone:** {brief.tone}")
        lines.append(f"**POV:** {brief.pov}")
        lines.append(f"**Word Count:** {brief.word_count_min}-{brief.word_count_max} words")
        lines.append("")
        
        # Requirements
        if brief.requirements:
            lines.append("### Requirements")
            lines.append("")
            for req in brief.requirements:
                lines.append(f"- {req}")
            lines.append("")
            
        # Restrictions
        if brief.restrictions:
            lines.append("### Restrictions")
            lines.append("")
            for restriction in brief.restrictions:
                lines.append(f"- {restriction}")
            lines.append("")
            
        # Suggested Headings
        lines.append("## Suggested Headings")
        lines.append("")
        for level, heading in brief.headings_outline:
            if level == "h2":
                lines.append(f"## {heading}")
            elif level == "h3":
                lines.append(f"### {heading}")
            elif level == "h4":
                lines.append(f"#### {heading}")
        lines.append("")
        
        # FAQs (exactly 4, last section)
        lines.append("## Frequently Asked Questions")
        lines.append("*Must be the last section with exactly 4 FAQs*")
        lines.append("")
        for faq in brief.faqs:
            lines.append(f"### {faq.question}")
            lines.append("")
            lines.append(faq.answer)
            lines.append("")
            
        # CTA
        lines.append("## Call to Action")
        lines.append("")
        lines.append(brief.cta)
        lines.append("")
        
        return "\n".join(lines)
        
    def _export_drafts(self, drafts: List[Draft], folder: Path) -> List[Dict[str, str]]:
        """Export content drafts to markdown files"""
        draft_files = []
        
        for idx, draft in enumerate(drafts, 1):
            filename = f"{idx:03d}-{self._sanitize_filename(draft.brief_id)}-draft.md"
            filepath = folder / filename
            
            # Add metadata header
            content = f"""---
brief_id: {draft.brief_id}
word_count: {draft.word_count}
readability_score: {draft.readability_score:.2f}
uk_english_verified: {draft.uk_english_verified}
facts_verified: {draft.facts_verified}
created_at: {draft.created_at.isoformat()}
---

{draft.content}
"""
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
            draft_files.append({
                "index": idx,
                "brief_id": draft.brief_id,
                "filename": filename,
                "path": str(filepath),
                "word_count": draft.word_count
            })
            
        logger.info(f"Exported {len(drafts)} drafts")
        return draft_files
        
    def _create_excel_index(
        self,
        job: Job,
        calendar: List[CalendarItem],
        brief_files: List[Dict[str, str]],
        draft_files: List[Dict[str, str]],
        output_path: Path
    ) -> str:
        """Create Excel index with hyperlinks to all content"""
        
        # Prepare data for DataFrame
        data = []
        
        for idx, item in enumerate(calendar, 1):
            # Find corresponding brief and draft files
            brief_file = next((bf for bf in brief_files if bf["index"] == idx), None)
            draft_file = next((df for df in draft_files if df["index"] == idx), None)
            
            row = {
                "Week": item.week,
                "Topic": item.topic,
                "Content Type": item.content_type,
                "Primary Keyword": item.primary_keyword,
                "Secondary Keywords": ", ".join(item.secondary_keywords),
                "Cluster": item.cluster_id,
                "Priority": item.priority,
                "Brief File": brief_file["filename"] if brief_file else "",
                "Draft File": draft_file["filename"] if draft_file else "",
                "Word Count": draft_file["word_count"] if draft_file else 0
            }
            data.append(row)
            
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Write to Excel with hyperlinks
        excel_path = output_path / "content-calendar-index.xlsx"
        
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Content Calendar', index=False)
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Content Calendar']
            
            # Add hyperlinks
            for idx, row in df.iterrows():
                if row['Brief File']:
                    brief_path = f"briefs/{row['Brief File']}"
                    worksheet.write_url(
                        idx + 1, 7,  # Brief File column (0-indexed + header)
                        brief_path,
                        string=row['Brief File']
                    )
                    
                if row['Draft File']:
                    draft_path = f"drafts/{row['Draft File']}"
                    worksheet.write_url(
                        idx + 1, 8,  # Draft File column
                        draft_path,
                        string=row['Draft File']
                    )
                    
            # Format worksheet
            worksheet.set_column('A:A', 10)  # Week
            worksheet.set_column('B:B', 40)  # Topic
            worksheet.set_column('C:C', 15)  # Content Type
            worksheet.set_column('D:D', 25)  # Primary Keyword
            worksheet.set_column('E:E', 40)  # Secondary Keywords
            worksheet.set_column('F:F', 15)  # Cluster
            worksheet.set_column('G:G', 10)  # Priority
            worksheet.set_column('H:I', 30)  # File columns
            worksheet.set_column('J:J', 12)  # Word Count
            
            # Add header formatting
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D7E4BD',
                'border': 1
            })
            
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
        logger.info(f"Created Excel index at {excel_path}")
        return str(excel_path)
        
    def _export_metadata(self, job: Job, folder: Path):
        """Export job metadata and reports"""
        # Export crawl report
        crawl_report = {
            "pages_crawled": len(job.crawl_results),
            "total_words": sum(cr.word_count for cr in job.crawl_results),
            "pages": [
                {
                    "url": str(cr.url),
                    "title": cr.title,
                    "word_count": cr.word_count
                }
                for cr in job.crawl_results[:50]  # Limit for readability
            ]
        }
        
        with open(folder / "crawl-report.json", 'w', encoding='utf-8') as f:
            json.dump(crawl_report, f, indent=2)
            
        # Export business understanding
        if job.business_entity:
            business_data = job.business_entity.model_dump()
            with open(folder / "business-analysis.json", 'w', encoding='utf-8') as f:
                json.dump(business_data, f, indent=2)
                
        # Export keyword research
        if job.keywords:
            keywords_df = pd.DataFrame([k.model_dump() for k in job.keywords])
            keywords_df.to_csv(folder / "keywords.csv", index=False)
            
        # Export cluster analysis
        if job.clusters:
            clusters_data = [
                {
                    "id": c.id,
                    "label": c.label,
                    "pillar": c.pillar,
                    "total_volume": c.total_volume,
                    "members_count": len(c.members)
                }
                for c in job.clusters
            ]
            with open(folder / "clusters.json", 'w', encoding='utf-8') as f:
                json.dump(clusters_data, f, indent=2)
                
    def export_job(self, job: Job) -> Dict[str, str]:
        """Export complete job results to organized folders with Excel index"""
        
        logger.info(f"Starting export for job {job.id}")
        
        # Create folder structure
        folders = self._create_folder_structure(job)
        
        # Export components
        brief_files = []
        draft_files = []
        
        if job.briefs:
            brief_files = self._export_briefs(job.briefs, folders["briefs"])
            
        if job.drafts:
            draft_files = self._export_drafts(job.drafts, folders["drafts"])
            
        # Create Excel index
        excel_path = ""
        if job.calendar:
            excel_path = self._create_excel_index(
                job, job.calendar, brief_files, draft_files, folders["root"]
            )
            
        # Export metadata
        self._export_metadata(job, folders["data"])
        
        # Update job with export paths
        job.export_folder = str(folders["root"])
        job.excel_path = excel_path
        
        logger.info(f"Export complete: {folders['root']}")
        
        return {
            "export_folder": str(folders["root"]),
            "excel_path": excel_path,
            "briefs_count": len(brief_files),
            "drafts_count": len(draft_files)
        }