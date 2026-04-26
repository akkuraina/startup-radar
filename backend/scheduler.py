"""
Background Job Scheduler using APScheduler
Runs pipeline every 6 hours automatically
"""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from database import SessionLocal
from models import Company, FetchLog
from fetcher import fetch_all_sources
from parser import parse_articles_batch
from deduplicator import process_extracted_data
from enricher import Enricher
from alerter import Alerter

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def run_full_pipeline():
    """Execute the complete pipeline"""
    logger.info("=" * 80)
    logger.info("🔄 [SCHEDULER] Starting scheduled pipeline run")
    logger.info("=" * 80)
    
    db = SessionLocal()
    start_time = datetime.utcnow()
    
    try:
        # Step 1: Fetch
        logger.info("📥 Fetching articles from Tavily and RSS...")
        articles = fetch_all_sources(days_back=7)
        
        if not articles:
            logger.warning("⚠️  No articles found")
            # Log fetch attempt
            log = FetchLog(
                fetch_source="tavily_rss",
                articles_found=0,
                companies_extracted=0,
                status="no_articles",
                message="No articles found in sources",
            )
            db.add(log)
            db.commit()
            return
        
        logger.info(f"✅ Found {len(articles)} articles")
        
        # Step 2: Parse with Claude
        logger.info(f"🤖 Parsing {len(articles)} articles with Claude API...")
        extracted = parse_articles_batch(articles)
        logger.info(f"✅ Extracted {len(extracted)} companies")
        
        # Step 3: Deduplicate & Store
        logger.info("💾 Deduplicating and storing in database...")
        dedup_stats = process_extracted_data(db, extracted)
        logger.info(f"✅ Dedup results: {dedup_stats}")
        
        # Step 4: Enrich
        logger.info("🔍 Enriching company data...")
        enricher = Enricher()
        enrich_stats = enricher.enrich_batch(db, limit=50)
        logger.info(f"✅ Enrichment results: {enrich_stats}")
        
        # Step 5: Check for hiring and send alerts
        logger.info("📧 Checking for hiring signals and sending alerts...")
        alerter = Alerter()
        
        # Get recently updated companies
        recently_updated = db.query(Company)\
            .filter(Company.updated_at >= start_time)\
            .all()
        
        alert_count = 0
        for company in recently_updated:
            if company.is_hiring and not company.last_alert_sent:
                if alerter.send_hiring_alert(company):
                    company.last_alert_sent = datetime.utcnow()
                    db.commit()
                    alert_count += 1
        
        logger.info(f"✅ Sent {alert_count} hiring alerts")
        
        # Log successful execution
        duration = (datetime.utcnow() - start_time).total_seconds()
        log = FetchLog(
            fetch_source="scheduled_pipeline",
            articles_found=len(articles),
            companies_extracted=len(extracted),
            errors_encountered=0,
            duration_seconds=duration,
            status="success",
            message=f"Pipeline executed successfully. Inserted: {dedup_stats.get('inserted', 0)}, Updated: {dedup_stats.get('updated', 0)}",
        )
        db.add(log)
        db.commit()
        
        logger.info("=" * 80)
        logger.info(f"✅ [SCHEDULER] Pipeline complete in {duration:.2f}s")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Pipeline error: {str(e)}", exc_info=True)
        
        # Log error
        try:
            log = FetchLog(
                fetch_source="scheduled_pipeline",
                articles_found=0,
                companies_extracted=0,
                errors_encountered=1,
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                status="failed",
                message=f"Pipeline failed: {str(e)}",
            )
            db.add(log)
            db.commit()
        except:
            pass
    
    finally:
        db.close()


def start_scheduler(interval_hours: int = 6):
    """Start the background scheduler"""
    if scheduler.running:
        logger.warning("Scheduler already running")
        return
    
    logger.info(f"🚀 Starting scheduler - pipeline runs every {interval_hours} hours")
    
    scheduler.add_job(
        run_full_pipeline,
        trigger=IntervalTrigger(hours=interval_hours),
        id="pipeline_job",
        name="Full Pipeline Job",
        replace_existing=True,
    )
    
    # Run once immediately
    logger.info("Running pipeline immediately...")
    run_full_pipeline()
    
    # Start scheduler
    scheduler.start()
    logger.info("✅ Scheduler started successfully")


def stop_scheduler():
    """Stop the background scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("✅ Scheduler stopped")
    else:
        logger.warning("Scheduler not running")


def get_job_status():
    """Get current job status"""
    job = scheduler.get_job("pipeline_job")
    if job:
        return {
            "job_id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "running": scheduler.running,
        }
    return {"running": scheduler.running, "jobs": 0}


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test scheduler
    logger.info("Testing scheduler...")
    start_scheduler(interval_hours=6)
    
    # Keep running
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_scheduler()
