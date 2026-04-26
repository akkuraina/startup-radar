"""
Deduplicator: Check if company already exists in DB
Handles insert/update logic
"""

import logging
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import Company, DedupLog

logger = logging.getLogger(__name__)


def generate_hash_key(company_name: str, announcement_date: Optional[str]) -> str:
    """Generate unique hash for deduplication"""
    key = f"{company_name}_{announcement_date}".lower()
    return hashlib.md5(key.encode()).hexdigest()


def normalize_company_name(name: str) -> str:
    """Normalize company name for matching"""
    if not name:
        return ""
    
    # Remove common suffixes
    suffixes = [" inc", " ltd", " llc", " corp", " corporation", " company"]
    normalized = name.lower().strip()
    
    for suffix in suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)].strip()
    
    return normalized


def check_existing_company(
    db: Session,
    company_name: str,
    announcement_date: Optional[datetime] = None
) -> Optional[Company]:
    """
    Check if company already exists in database
    Uses normalized name matching
    """
    if not company_name:
        return None

    try:
        # Try exact match first
        stmt = select(Company).where(Company.company_name == company_name)
        existing = db.execute(stmt).scalar_one_or_none()
        
        if existing:
            return existing

        # Try normalized match
        normalized = normalize_company_name(company_name)
        stmt = select(Company).where(Company.company_name.ilike(f"%{normalized}%"))
        results = db.execute(stmt).scalars().all()
        
        if results:
            # Return exact name match or first result
            for result in results:
                if normalize_company_name(result.company_name) == normalized:
                    return result
            return results[0]
        
        return None

    except Exception as e:
        logger.error(f"Error checking existing company: {str(e)}")
        return None


def upsert_company(db: Session, company_data: Dict[str, Any]) -> tuple[Company, str]:
    """
    Insert or update company record
    
    Args:
        db: Database session
        company_data: Extracted company data with keys:
            company, amount, round, investors, country, date, source_url, source
    
    Returns:
        (company_record, action) where action is 'inserted', 'updated', or 'skipped'
    """
    company_name = company_data.get("company")
    
    if not company_name:
        logger.warning("⚠️  Skipping record with no company name")
        return None, "skipped"

    try:
        # Check if exists
        existing = check_existing_company(db, company_name)

        announcement_date = None
        if company_data.get("date"):
            try:
                announcement_date = datetime.fromisoformat(company_data["date"])
            except:
                pass

        hash_key = generate_hash_key(company_name, company_data.get("date"))

        if existing:
            # Update existing record
            logger.info(f"🔄 Updating existing company: {company_name}")
            
            existing.amount_usd = company_data.get("amount") or existing.amount_usd
            existing.round_type = company_data.get("round") or existing.round_type
            existing.investors = company_data.get("investors") or existing.investors
            existing.country = company_data.get("country") or existing.country
            existing.announcement_date = announcement_date or existing.announcement_date
            existing.source_url = company_data.get("source_url") or existing.source_url
            existing.updated_at = datetime.utcnow()

            db.commit()

            # Log dedup action
            log = DedupLog(
                company_name=company_name,
                announcement_date=announcement_date,
                hash_key=hash_key,
                company_id=existing.id,
                action="updated",
                reason="Duplicate detected and merged"
            )
            db.add(log)
            db.commit()

            return existing, "updated"

        else:
            # Insert new record
            logger.info(f"✨ Inserting new company: {company_name}")
            
            new_company = Company(
                company_name=company_name,
                amount_usd=company_data.get("amount"),
                round_type=company_data.get("round"),
                investors=company_data.get("investors"),
                country=company_data.get("country"),
                announcement_date=announcement_date,
                source_url=company_data.get("source_url"),
                source=company_data.get("source", "unknown")
            )
            
            db.add(new_company)
            db.flush()  # Get the ID
            db.commit()

            # Log dedup action
            log = DedupLog(
                company_name=company_name,
                announcement_date=announcement_date,
                hash_key=hash_key,
                company_id=new_company.id,
                action="inserted",
                reason="New company"
            )
            db.add(log)
            db.commit()

            return new_company, "inserted"

    except Exception as e:
        logger.error(f"❌ Error upserting company: {str(e)}")
        db.rollback()
        return None, "skipped"


def process_extracted_data(db: Session, extracted_companies: list[Dict[str, Any]]) -> Dict[str, int]:
    """
    Process a batch of extracted company records
    
    Returns:
        Summary stats: {inserted: N, updated: N, skipped: N}
    """
    stats = {"inserted": 0, "updated": 0, "skipped": 0}

    for company_data in extracted_companies:
        company, action = upsert_company(db, company_data)
        if action in stats:
            stats[action] += 1

    logger.info(f"📊 Deduplication results: {stats}")
    return stats


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test hash generation
    hash1 = generate_hash_key("OpenAI Inc", "2026-04-10")
    print(f"Hash for 'OpenAI Inc' on 2026-04-10: {hash1}")
