"""Database initialization for GachaStats using SQLModel"""
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session

PROJECT_ROOT = Path(__file__).parent.parent
DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'data' / 'gachastats.db'}"
engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    """Create tables if they do not exist"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """FastAPI dependency that provides a database session"""
    with Session(engine) as session:
        yield session
