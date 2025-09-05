"""
Business understanding module - extracts business context from crawled pages
"""
import re
import logging
from typing import List, Dict, Set, Optional
from collections import Counter
try:
    import spacy
    from spacy.matcher import Matcher
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

from ..models import BusinessEntity, CrawlResult

logger = logging.getLogger(__name__)


class BusinessAnalyzer:
    """Analyzes crawled content to understand the business"""
    
    def __init__(self):
        self.nlp = None
        self.matcher = None
        
        if SPACY_AVAILABLE:
            # Load spaCy model - will need to be installed: python -m spacy download en_core_web_sm
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except:
                logger.warning("spaCy model not found, using blank English model")
                self.nlp = spacy.blank("en")
                
            self.matcher = Matcher(self.nlp.vocab)
            self._setup_patterns()
        else:
            logger.warning("spaCy not installed, using basic text analysis")
        
    def _setup_patterns(self):
        """Setup patterns for extracting business information"""
        # Service patterns
        service_patterns = [
            [{"LOWER": "we"}, {"LOWER": {"IN": ["offer", "provide", "deliver", "specialize"]}},
             {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}],
            [{"LOWER": "our"}, {"LOWER": {"IN": ["services", "solutions", "products"]}},
             {"LOWER": {"IN": ["include", "are"]}, "OP": "?"}, {"OP": "*"}],
        ]
        self.matcher.add("SERVICE", service_patterns)
        
        # Location patterns
        location_patterns = [
            [{"LOWER": {"IN": ["based", "located", "headquartered"]}}, {"LOWER": "in"},
             {"ENT_TYPE": {"IN": ["GPE", "LOC"]}}],
            [{"LOWER": "serving"}, {"ENT_TYPE": {"IN": ["GPE", "LOC"]}, "OP": "+"}],
        ]
        self.matcher.add("LOCATION", location_patterns)
        
    def _extract_from_about_page(self, pages: List[CrawlResult]) -> Dict[str, List[str]]:
        """Extract information specifically from About/Home pages"""
        extracted = {
            "services": [],
            "products": [],
            "locations": [],
            "industries": [],
            "audiences": []
        }
        
        # Identify key pages
        key_pages = []
        for page in pages:
            url_lower = str(page.url).lower()
            if any(keyword in url_lower for keyword in ['about', 'home', 'index', 'who-we-are', 'company']):
                key_pages.append(page)
                
        if not key_pages:
            key_pages = pages[:5]  # Use first 5 pages as fallback
            
        if not self.nlp:
            # Fallback: basic keyword extraction when spaCy not available
            service_keywords = ['service', 'solution', 'consulting', 'development', 'support']
            for page in key_pages:
                text = page.text_content.lower()
                for keyword in service_keywords:
                    if keyword in text:
                        # Extract phrases around the keyword
                        sentences = text.split('.')
                        for sentence in sentences:
                            if keyword in sentence:
                                words = sentence.split()
                                for i, word in enumerate(words):
                                    if keyword in word:
                                        # Get surrounding context
                                        context = ' '.join(words[max(0, i-2):min(len(words), i+3)])
                                        if len(context) > 5:
                                            extracted["services"].append(context.strip())
            return extracted
            
        for page in key_pages:
            doc = self.nlp(page.text_content[:5000])  # Limit processing for performance
            
            # Extract entities
            for ent in doc.ents:
                if ent.label_ in ["ORG", "PRODUCT"]:
                    if "product" in ent.text.lower() or "solution" in ent.text.lower():
                        extracted["products"].append(ent.text)
                    else:
                        extracted["services"].append(ent.text)
                elif ent.label_ in ["GPE", "LOC"]:
                    extracted["locations"].append(ent.text)
                    
            # Extract from patterns
            matches = self.matcher(doc)
            for match_id, start, end in matches:
                span = doc[start:end]
                match_label = self.nlp.vocab.strings[match_id]
                
                if match_label == "SERVICE":
                    service_text = span.text
                    # Extract noun phrases after the verb
                    for token in span:
                        if token.pos_ in ["NOUN", "PROPN"]:
                            extracted["services"].append(token.text)
                elif match_label == "LOCATION":
                    for token in span:
                        if token.ent_type_ in ["GPE", "LOC"]:
                            extracted["locations"].append(token.text)
                            
        return extracted
        
    def _extract_services_from_navigation(self, pages: List[CrawlResult]) -> List[str]:
        """Extract services from navigation menu items"""
        services = []
        
        for page in pages[:10]:  # Check first 10 pages for nav consistency
            # Look for service-related headings
            for h2 in page.headings.get("h2", []):
                if any(keyword in h2.lower() for keyword in ["service", "solution", "product", "offering"]):
                    services.append(h2)
                    
            # Extract from internal link anchors
            service_keywords = ["service", "solution", "product", "consulting", "development", 
                              "support", "training", "implementation", "integration"]
            
            for link in page.internal_links[:50]:
                link_lower = link.lower()
                for keyword in service_keywords:
                    if keyword in link_lower:
                        # Extract the service name from URL
                        parts = link.split('/')
                        if parts:
                            service_name = parts[-1].replace('-', ' ').replace('_', ' ')
                            if service_name:
                                services.append(service_name.title())
                                
        return list(set(services))
        
    def _identify_exclusions(self, pages: List[CrawlResult]) -> List[str]:
        """Identify what the business explicitly does NOT do"""
        exclusions = []
        
        exclusion_phrases = [
            r"we do not (offer|provide|support|work with)",
            r"not (available|offered|supported)",
            r"outside (our|the) scope",
            r"we don't",
            r"we cannot",
            r"not included"
        ]
        
        for page in pages:
            text_lower = page.text_content.lower()
            for pattern in exclusion_phrases:
                matches = re.findall(f"{pattern}[^.]*", text_lower)
                for match in matches:
                    # Extract the excluded item
                    doc = self.nlp(match)
                    for chunk in doc.noun_chunks:
                        exclusions.append(chunk.text)
                        
        return list(set(exclusions))
        
    def _extract_brand_terms(self, pages: List[CrawlResult], business_name: str) -> List[str]:
        """Extract brand-related terms and variations"""
        brand_terms = [business_name]
        
        # Look for copyright notices, trademarks
        for page in pages:
            text = page.text_content
            
            # Copyright patterns
            copyright_match = re.search(r"©\s*\d{4}\s*([^.]+)", text)
            if copyright_match:
                brand_terms.append(copyright_match.group(1).strip())
                
            # Trademark patterns
            tm_matches = re.findall(r"([^\s]+)™", text)
            brand_terms.extend(tm_matches)
            
            # Registered trademark
            r_matches = re.findall(r"([^\s]+)®", text)
            brand_terms.extend(r_matches)
            
        # Clean and deduplicate
        brand_terms = [term.strip() for term in brand_terms if len(term) > 2]
        return list(set(brand_terms))
        
    def _extract_target_audiences(self, pages: List[CrawlResult]) -> List[str]:
        """Extract target audience information"""
        audiences = []
        
        audience_patterns = [
            r"for (businesses|companies|organizations|individuals|professionals|enterprises)",
            r"designed for ([^.]+)",
            r"perfect for ([^.]+)",
            r"ideal for ([^.]+)",
            r"serving ([^.]+)",
            r"we help ([^.]+)",
            r"our clients include ([^.]+)"
        ]
        
        for page in pages:
            text = page.text_content
            for pattern in audience_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                audiences.extend(matches)
                
        # Common audience types to look for
        audience_keywords = {
            "SMB": ["small business", "SME", "small and medium"],
            "Enterprise": ["enterprise", "fortune 500", "large organization"],
            "B2B": ["business to business", "b2b", "companies"],
            "B2C": ["consumers", "individuals", "personal", "b2c"],
            "Startups": ["startup", "early stage", "emerging"],
            "Government": ["government", "public sector", "federal", "municipal"],
            "Non-profit": ["nonprofit", "charity", "ngo", "foundation"],
            "Healthcare": ["healthcare", "medical", "hospital", "clinic"],
            "Education": ["education", "schools", "universities", "academic"],
            "Financial": ["financial", "banking", "insurance", "fintech"]
        }
        
        identified_audiences = set()
        for page in pages:
            text_lower = page.text_content.lower()
            for audience_type, keywords in audience_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    identified_audiences.add(audience_type)
                    
        audiences.extend(list(identified_audiences))
        
        return list(set(audiences))
        
    def _extract_unique_value_props(self, pages: List[CrawlResult]) -> List[str]:
        """Extract unique value propositions"""
        value_props = []
        
        value_patterns = [
            r"what (sets us apart|makes us different|distinguishes us)",
            r"why choose us",
            r"our unique approach",
            r"unlike (our competitors|other)",
            r"the only ([^.]+)",
            r"first to ([^.]+)",
            r"pioneering ([^.]+)",
            r"industry-leading ([^.]+)",
            r"award-winning ([^.]+)"
        ]
        
        for page in pages[:10]:  # Focus on main pages
            text = page.text_content
            for pattern in value_patterns:
                matches = re.findall(f"{pattern}[^.]*", text, re.IGNORECASE)
                for match in matches:
                    if len(match) > 10 and len(match) < 200:
                        value_props.append(match.strip())
                        
        return list(set(value_props))
        
    def analyze(self, crawl_results: List[CrawlResult], business_name: str, 
                homepage_url: str) -> BusinessEntity:
        """Analyze crawled pages to understand the business"""
        
        logger.info(f"Analyzing {len(crawl_results)} pages for business understanding")
        
        # Extract information from different sources
        extracted = self._extract_from_about_page(crawl_results)
        nav_services = self._extract_services_from_navigation(crawl_results)
        extracted["services"].extend(nav_services)
        
        # Additional extraction
        exclusions = self._identify_exclusions(crawl_results)
        brand_terms = self._extract_brand_terms(crawl_results, business_name)
        audiences = self._extract_target_audiences(crawl_results)
        value_props = self._extract_unique_value_props(crawl_results)
        
        # Clean and deduplicate
        def clean_list(items: List[str]) -> List[str]:
            cleaned = []
            for item in items:
                item = item.strip()
                if item and len(item) > 2 and len(item) < 100:
                    cleaned.append(item)
            return list(set(cleaned))
        
        business_entity = BusinessEntity(
            name=business_name,
            homepage=homepage_url,
            services=clean_list(extracted["services"]),
            products=clean_list(extracted["products"]),
            locations=clean_list(extracted["locations"]),
            industries=clean_list(extracted["industries"]),
            target_audiences=clean_list(audiences),
            exclusions=clean_list(exclusions),
            brand_terms=clean_list(brand_terms),
            unique_value_props=clean_list(value_props)
        )
        
        logger.info(f"Business analysis complete: {len(business_entity.services)} services, "
                   f"{len(business_entity.products)} products identified")
        
        return business_entity