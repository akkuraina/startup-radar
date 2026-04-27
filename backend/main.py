"""
FastAPI REST API Server for Startup Radar
Endpoints for dashboard and data access
"""

# Load environment variables from .env file FIRST
from dotenv import load_dotenv
load_dotenv()

import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func

from database import init_db, get_db, verify_connection, SessionLocal
from models import Company, Alert, FetchLog
from fetcher import fetch_all_sources
from parser import parse_articles_batch
from deduplicator import process_extracted_data
from enricher import Enricher
from alerter import Alerter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models for API
from pydantic import BaseModel


class CompanyResponse(BaseModel):
    id: int
    company_name: str
    amount_usd: Optional[float]
    round_type: Optional[str]
    investors: Optional[List[str]]
    country: Optional[str]
    announcement_date: Optional[datetime]
    website_url: Optional[str]
    is_hiring: bool
    open_roles_count: Optional[int]
    job_titles: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_companies: int
    total_funding_usd: float
    hiring_count: int
    latest_announcement: Optional[datetime]
    by_round: dict
    by_country: dict


class PipelineRunResponse(BaseModel):
    status: str
    message: str
    articles_found: int
    companies_extracted: int
    inserted: int
    updated: int
    enriched: int
    timestamp: datetime


# Lifespan handler for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Startup Radar API...")
    if not verify_connection():
        logger.error("❌ Failed to verify database connection")
    else:
        init_db()
    logger.info("✅ API startup complete")
    yield
    # Shutdown
    logger.info("👋 Shutting down Startup Radar API")


app = FastAPI(
    title="Startup Radar API",
    description="Discover funded startups and hiring signals",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    try:
        # Total companies
        total_count = db.query(func.count(Company.id)).scalar() or 0
        
        # Total funding
        total_funding = db.query(func.sum(Company.amount_usd)).scalar() or 0
        
        # Hiring companies
        hiring_count = db.query(func.count(Company.id)).where(Company.is_hiring == True).scalar() or 0
        
        # Latest announcement
        latest = db.query(Company).order_by(desc(Company.announcement_date)).first()
        latest_date = latest.announcement_date if latest else None
        
        # By round type
        by_round = {}
        round_stats = db.query(
            Company.round_type,
            func.count(Company.id).label("count"),
            func.sum(Company.amount_usd).label("total")
        ).group_by(Company.round_type).all()
        
        for round_type, count, total in round_stats:
            if round_type:
                by_round[round_type] = {"count": count, "total": total or 0}
        
        # By country
        by_country = {}
        country_stats = db.query(
            Company.country,
            func.count(Company.id).label("count")
        ).group_by(Company.country).all()
        
        for country, count in country_stats:
            if country:
                by_country[country] = count
        
        return StatsResponse(
            total_companies=total_count,
            total_funding_usd=total_funding or 0,
            hiring_count=hiring_count,
            latest_announcement=latest_date,
            by_round=by_round,
            by_country=by_country,
        )
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# COMPANIES ENDPOINTS
# ============================================================================

@app.get("/api/companies", response_model=List[CompanyResponse])
async def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    country: Optional[str] = None,
    round_type: Optional[str] = None,
    search: Optional[str] = None,
    hiring_only: bool = False,
    db: Session = Depends(get_db)
):
    """List companies with filtering"""
    try:
        query = db.query(Company)
        
        # Apply filters
        if country:
            query = query.filter(Company.country == country)
        
        if round_type:
            query = query.filter(Company.round_type == round_type)
        
        if search:
            query = query.filter(Company.company_name.ilike(f"%{search}%"))
        
        if hiring_only:
            query = query.filter(Company.is_hiring == True)
        
        # Order by latest first
        query = query.order_by(desc(Company.announcement_date))
        
        # Pagination
        companies = query.offset(skip).limit(limit).all()
        
        return companies
    except Exception as e:
        logger.error(f"Companies list error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/companies/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: int, db: Session = Depends(get_db)):
    """Get single company details"""
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return company
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Company detail error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/companies/hiring/active", response_model=List[CompanyResponse])
async def get_hiring_companies(
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all companies that are hiring"""
    try:
        companies = db.query(Company)\
            .filter(Company.is_hiring == True)\
            .order_by(desc(Company.open_roles_count))\
            .limit(limit)\
            .all()
        
        return companies
    except Exception as e:
        logger.error(f"Hiring companies error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EXPORT ENDPOINTS
# ============================================================================

@app.get("/api/export/csv")
async def export_csv(db: Session = Depends(get_db)):
    """Export companies as CSV"""
    try:
        import csv
        from io import StringIO
        from fastapi.responses import StreamingResponse
        
        companies = db.query(Company).all()
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'company_name', 'amount_usd', 'round_type', 'country',
            'announcement_date', 'website_url', 'is_hiring', 'open_roles_count'
        ])
        
        writer.writeheader()
        for company in companies:
            writer.writerow({
                'company_name': company.company_name,
                'amount_usd': company.amount_usd,
                'round_type': company.round_type,
                'country': company.country,
                'announcement_date': company.announcement_date,
                'website_url': company.website_url,
                'is_hiring': company.is_hiring,
                'open_roles_count': company.open_roles_count,
            })
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=companies.csv"}
        )
    except Exception as e:
        logger.error(f"CSV export error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/json")
async def export_json(db: Session = Depends(get_db)):
    """Export companies as JSON"""
    try:
        from fastapi.responses import JSONResponse
        
        companies = db.query(Company).all()
        
        data = []
        for company in companies:
            data.append({
                'id': company.id,
                'company_name': company.company_name,
                'amount_usd': company.amount_usd,
                'round_type': company.round_type,
                'investors': company.investors,
                'country': company.country,
                'announcement_date': company.announcement_date.isoformat() if company.announcement_date else None,
                'website_url': company.website_url,
                'is_hiring': company.is_hiring,
                'open_roles_count': company.open_roles_count,
                'job_titles': company.job_titles,
            })
        
        return JSONResponse(data)
    except Exception as e:
        logger.error(f"JSON export error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PIPELINE ENDPOINTS
# ============================================================================

@app.post("/api/pipeline/run", response_model=PipelineRunResponse)
async def run_pipeline(db: Session = Depends(get_db)):
    """Manually trigger the full pipeline"""
    try:
        logger.info("🚀 Pipeline execution started (manual trigger)")
        start_time = datetime.utcnow()
        
        # Step 1: Fetch
        logger.info("📥 Step 1: Fetching articles...")
        articles = fetch_all_sources(days_back=7)
        articles_found = len(articles)
        
        # Step 2: Parse
        logger.info("🔍 Step 2: Parsing articles with Claude...")
        extracted = parse_articles_batch(articles)
        companies_extracted = len(extracted)
        
        # Step 3: Deduplicate & Store
        logger.info("✨ Step 3: Deduplicating and storing...")
        dedup_stats = process_extracted_data(db, extracted)
        
        # Step 4: Enrich
        logger.info("💾 Step 4: Enriching companies...")
        enricher = Enricher()
        enrich_stats = enricher.enrich_batch(db, limit=100)
        
        # Step 5: Send alerts (for newly hired companies)
        logger.info("📧 Step 5: Sending alerts...")
        alerter = Alerter()
        
        # Check for hiring alerts
        stmt = select(Company).where(
            Company.is_hiring == True,
            Company.last_alert_sent == None
        )
        newly_hiring = db.execute(stmt).scalars().all()
        
        for company in newly_hiring:
            alerter.send_hiring_alert(company)
            company.last_alert_sent = datetime.utcnow()
            db.commit()
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(f"✅ Pipeline complete in {duration:.2f}s")
        
        return PipelineRunResponse(
            status="success",
            message="Pipeline executed successfully",
            articles_found=articles_found,
            companies_extracted=companies_extracted,
            inserted=dedup_stats.get("inserted", 0),
            updated=dedup_stats.get("updated", 0),
            enriched=enrich_stats.get("enriched", 0),
            timestamp=datetime.utcnow(),
        )
    
    except Exception as e:
        logger.error(f"❌ Pipeline error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "name": "Startup Radar API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "stats": "/api/stats",
            "companies": "/api/companies",
            "hiring": "/api/companies/hiring/active",
            "pipeline": "POST /api/pipeline/run",
            "export": "/api/export/csv",
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=True,
    )
