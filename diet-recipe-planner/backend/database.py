"""
SQLAlchemy database connection and session management.
Reads DATABASE_URL from environment and creates the engine + session factory.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database URL - defaults to local postgres if not set
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://recipeuser:recipepass@localhost:5432/recipe_db"
)

# Create the SQLAlchemy engine with connection pooling
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Session factory - each request gets its own session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a database session.
    Ensures the session is closed after the request completes.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
