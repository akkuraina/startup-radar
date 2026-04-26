"""
SQLAlchemy Models for Startup Radar
Database: PostgreSQL (Supabase)
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import TIMESTAMP

Base = declarative_base()


class Company(Base):
    """Represents a funded startup"""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    
    # Core funding information
    company_name = Column(String(255), unique=True, nullable=False, index=True)
    amount_usd = Column(Float, nullable=True)  # In USD
    round_type = Column(String(50), nullable=True)  # Series A, Seed, etc.
    investors = Column(JSON, nullable=True)  # List of investor names
    country = Column(String(100), nullable=True)
    announcement_date = Column(DateTime, nullable=True, index=True)
    
    # Source information
    source_url = Column(Text, nullable=True)  # URL where we found it
    source = Column(String(50), nullable=True)  # 'tavily', 'rss', etc.
    
    # Enrichment data
    website_url = Column(String(255), nullable=True)
    linkedin_url = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Hiring signals
    is_hiring = Column(Boolean, default=False, index=True)
    open_roles_count = Column(Integer, nullable=True)
    job_titles = Column(JSON, nullable=True)  # List of job titles found
    careers_page_found = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_enriched = Column(TIMESTAMP, nullable=True)
    last_alert_sent = Column(TIMESTAMP, nullable=True)

    # Indexes for common queries
    __table_args__ = (
        Index('idx_company_name_date', 'company_name', 'announcement_date'),
        Index('idx_country', 'country'),
        Index('idx_round_type', 'round_type'),
        Index('idx_is_hiring', 'is_hiring'),
    )


class DedupLog(Base):
    """Tracks deduplication decisions"""
    __tablename__ = "dedup_logs"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    announcement_date = Column(DateTime, nullable=False)
    hash_key = Column(String(255), unique=True, nullable=False)
    
    # Reference to the company record this was merged into
    company_id = Column(Integer, nullable=True)
    duplicate_of_id = Column(Integer, nullable=True)
    
    action = Column(String(50), nullable=False)  # 'inserted', 'updated', 'skipped'
    reason = Column(Text, nullable=True)  # Why this decision was made
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)


class FetchLog(Base):
    """Tracks each fetch operation"""
    __tablename__ = "fetch_logs"

    id = Column(Integer, primary_key=True, index=True)
    fetch_source = Column(String(50), nullable=False)  # 'tavily', 'rss_techcrunch', etc.
    articles_found = Column(Integer, default=0)
    companies_extracted = Column(Integer, default=0)
    errors_encountered = Column(Integer, default=0)
    error_details = Column(JSON, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    status = Column(String(20), nullable=False)  # 'success', 'partial', 'failed'
    message = Column(Text, nullable=True)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)


class Alert(Base):
    """Tracks alerts sent to users"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    
    alert_type = Column(String(50), nullable=False)  # 'new_funding', 'hiring_detected'
    message = Column(Text, nullable=False)
    recipient_email = Column(String(255), nullable=True)
    
    sent = Column(Boolean, default=False, index=True)
    sent_at = Column(TIMESTAMP, nullable=True)
    status = Column(String(20), nullable=True)  # 'sent', 'failed', 'pending'
    error_message = Column(Text, nullable=True)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)


if __name__ == "__main__":
    print("Models defined. Use database.py to initialize tables.")
