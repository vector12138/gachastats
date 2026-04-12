"""Database models for GachaStats."""
from sqlalchemy import UniqueConstraint
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class Account(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    game_type: str
    account_name: str
    server: str
    uid: str
    auth_key: Optional[str] = None
    last_sync_time: Optional[str] = None
    create_time: Optional[str] = None
    __table_args__ = (UniqueConstraint("game_type", "uid"),)
    gacha_records: List["GachaRecord"] = Relationship(back_populates="account")

class GachaRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: Optional[int] = Field(foreign_key="account.id")
    gacha_type: str
    gacha_name: str
    item_name: str
    item_type: str
    rarity: int
    time: str
    pity: int = 0
    is_new: bool = False
    __table_args__ = (UniqueConstraint("account_id", "gacha_type", "time", "item_name"),)
    account: Optional[Account] = Relationship(back_populates="gacha_records")

class GameData(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    game_type: str
    item_type: str
    item_name: str
    rarity: int
    icon_url: Optional[str] = None
    __table_args__ = (UniqueConstraint("game_type", "item_name"),)
