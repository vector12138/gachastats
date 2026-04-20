"""Database initialization for GachaStats using SQLModel."""
import json
from pathlib import Path
from typing import Generator
from sqlmodel import SQLModel, create_engine, Session
import os

PROJECT_ROOT = Path(__file__).parent.parent

# 读取配置文件中的数据库路径
def _get_database_path() -> str:
    """从配置文件读取数据库路径，若无则使用默认本地路径"""
    config_path = PROJECT_ROOT / "config.json"
    if config_path.exists():
        try:
            with config_path.open(encoding="utf-8") as f:
                cfg = json.load(f)
            db_path = cfg.get("database_path")
            if db_path:
                return db_path
        except (json.JSONDecodeError, KeyError, IOError):
            pass  # 配置读取失败时使用默认值
    
    # 默认使用本地目录（避免 CIFS 文件系统限制）
    local_db_dir = Path.home() / ".local" / "gachastats"
    local_db_dir.mkdir(parents=True, exist_ok=True)
    return str(local_db_dir / "gachastats.db")

DATABASE_PATH = _get_database_path()
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
