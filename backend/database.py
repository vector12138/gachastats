"""Database initialization for GachaStats using SQLModel."""
from pathlib import Path
from typing import Generator
from sqlmodel import SQLModel, create_engine, Session
import os

from .config_loader import get_database_path

# 使用配置加载器获取数据库路径（支持配置覆盖）
DATABASE_PATH = get_database_path()
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
engine = create_engine(DATABASE_URL, echo=False)

print(f"[Database] 使用数据库路径: {DATABASE_PATH}")


def init_db() -> None:
    """Create tables if they do not exist"""
    SQLModel.metadata.create_all(engine)


def get_engine():
    """获取数据库引擎"""
    return engine


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session."""
    with Session(engine) as session:
        yield session
