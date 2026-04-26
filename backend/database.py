"""
Database connection and session management
Uses SQLAlchemy with PostgreSQL (Supabase)
"""

import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from models import Base
import logging

logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/startup_radar"
)

# Create engine
# NullPool avoids connection pooling issues with Supabase
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency for FastAPI to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize all tables in the database"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables initialized successfully")
        
        # Verify tables were created
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Tables in database: {tables}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {str(e)}")
        return False


def verify_connection():
    """Verify database connection works"""
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            logger.info("✅ Database connection verified")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Verifying database connection...")
    if verify_connection():
        print("Initializing database tables...")
        if init_db():
            print("✅ Database ready!")
        else:
            print("❌ Failed to initialize database")
    else:
        print("❌ Cannot connect to database")
