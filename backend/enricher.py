"""
Enricher: Add metadata to companies
- Website URL detection
- LinkedIn URL generation
- Hiring signal detection
- Contact information
"""

import logging
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import Company

logger = logging.getLogger(__name__)

# Common tech job titles to look for in careers page
TECH_JOB_KEYWORDS = [
    "engineer", "developer", "data scientist",
    "product manager", "designer", "qa",
    "devops", "infra", "security",
    "frontend", "backend", "fullstack"
]

# Common hiring page paths
HIRING_PATHS = [
    "/careers",
    "/jobs",
    "/hiring",
    "/work-with-us",
    "/join-us",
    "/team",
    "/careers/",
    "/jobs/",
]


class Enricher:
    """Enrich company data with metadata"""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def detect_website_url(self, company_name: str) -> Optional[str]:
        """
        Try to detect company website
        Simple heuristic: search for company domain
        In production, use Clearbit API
        """
        try:
            # Try variations of domain
            domain_name = company_name.lower().replace(" ", "").replace(".", "")
            
            # Try common TLDs
            for tld in [".com", ".io", ".ai", ".co", ".app"]:
                url = f"https://{domain_name}{tld}"
                
                try:
                    response = requests.head(url, timeout=3, allow_redirects=True)
                    if response.status_code < 400:
                        logger.debug(f"✅ Found website: {url}")
                        return url
                except:
                    pass

            return None

        except Exception as e:
            logger.debug(f"Website detection error: {str(e)}")
            return None

    def generate_linkedin_url(self, company_name: str) -> str:
        """Generate likely LinkedIn company URL"""
        # Convert to URL slug
        slug = company_name.lower().replace(" ", "-").replace(".", "")
        # Remove non-alphanumeric except hyphens
        slug = re.sub(r"[^a-z0-9\-]", "", slug)
        return f"https://linkedin.com/company/{slug}"

    def detect_hiring_signals(self, website_url: Optional[str]) -> Dict[str, Any]:
        """
        Detect if company is hiring
        - Check for careers/jobs page
        - Look for job postings
        """
        result = {
            "is_hiring": False,
            "careers_page_found": False,
            "job_titles": [],
            "open_roles_count": 0,
        }

        if not website_url:
            return result

        try:
            # Check main domain first
            response = requests.get(website_url, timeout=self.timeout, allow_redirects=True)
            if response.status_code == 200:
                # Look for hiring keywords on main page
                content = response.text.lower()
                if any(keyword in content for keyword in ["careers", "hiring", "join us"]):
                    result["is_hiring"] = True

            # Check common hiring paths
            base_url = website_url.rstrip("/")
            for path in HIRING_PATHS:
                careers_url = f"{base_url}{path}"
                
                try:
                    response = requests.get(careers_url, timeout=3)
                    if response.status_code == 200:
                        result["careers_page_found"] = True
                        result["is_hiring"] = True

                        # Parse page for job titles
                        soup = BeautifulSoup(response.content, "html.parser")
                        text = soup.get_text().lower()

                        found_jobs = []
                        for keyword in TECH_JOB_KEYWORDS:
                            if keyword in text:
                                found_jobs.append(keyword)
                                result["open_roles_count"] += 1

                        result["job_titles"] = list(set(found_jobs))[:5]  # Top 5
                        
                        logger.info(f"✅ Hiring page found: {careers_url}")
                        logger.info(f"  Found roles: {', '.join(result['job_titles'])}")
                        break

                except:
                    continue

            return result

        except Exception as e:
            logger.debug(f"Error detecting hiring signals: {str(e)}")
            return result

    def enrich_company(self, company: Company) -> bool:
        """
        Enrich a single company record
        
        Returns:
            True if enrichment succeeded
        """
        try:
            logger.info(f"🔍 Enriching: {company.company_name}")

            # Detect website
            if not company.website_url:
                website = self.detect_website_url(company.company_name)
                if website:
                    company.website_url = website

            # Generate LinkedIn URL
            if not company.linkedin_url:
                company.linkedin_url = self.generate_linkedin_url(company.company_name)

            # Detect hiring signals
            if company.website_url:
                hiring_data = self.detect_hiring_signals(company.website_url)
                company.is_hiring = hiring_data["is_hiring"]
                company.careers_page_found = hiring_data["careers_page_found"]
                company.job_titles = hiring_data["job_titles"]
                company.open_roles_count = hiring_data["open_roles_count"]

            company.last_enriched = datetime.utcnow()
            
            logger.info(f"✅ Enriched: {company.company_name} (Hiring: {company.is_hiring})")
            return True

        except Exception as e:
            logger.error(f"❌ Enrichment error for {company.company_name}: {str(e)}")
            return False

    def enrich_batch(self, db: Session, limit: int = 50) -> Dict[str, int]:
        """
        Enrich companies that haven't been enriched yet
        
        Args:
            db: Database session
            limit: Max companies to enrich
            
        Returns:
            Stats: {enriched: N, failed: N}
        """
        stats = {"enriched": 0, "failed": 0}

        try:
            # Get companies not yet enriched
            stmt = select(Company).where(Company.last_enriched == None).limit(limit)
            companies = db.execute(stmt).scalars().all()

            logger.info(f"Enriching {len(companies)} companies...")

            for company in companies:
                if self.enrich_company(company):
                    stats["enriched"] += 1
                else:
                    stats["failed"] += 1

                try:
                    db.commit()
                except Exception as e:
                    logger.error(f"Error committing enrichment: {str(e)}")
                    db.rollback()
                    stats["failed"] += 1

            logger.info(f"📊 Enrichment complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Batch enrichment error: {str(e)}")
            return stats


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    enricher = Enricher()
    
    # Test website detection
    website = enricher.detect_website_url("OpenAI")
    print(f"Website for OpenAI: {website}")
    
    # Test LinkedIn URL
    linkedin = enricher.generate_linkedin_url("TechVision")
    print(f"LinkedIn URL for TechVision: {linkedin}")
