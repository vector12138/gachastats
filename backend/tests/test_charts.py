"""Test charts routes for GachaStats."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from backend.main import app
from backend.models import Account, GachaRecord
from backend.database import get_session

client = TestClient(app)


def create_test_account(session: Session, **kwargs):
    """Helper to create a test account"""
    account = Account(
        game_type=kwargs.get("game_type", "genshin"),
        account_name=kwargs.get("account_name", "测试图表账号"),
        server=kwargs.get("server", "cn_gf01"),
        uid=kwargs.get("uid", "987654321"),
        auth_key=kwargs.get("auth_key", "test_key")
    )
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


def create_test_records(session: Session, account_id: int, records_data: list):
    """Helper to create test gacha records"""
    for data in records_data:
        record = GachaRecord(
            account_id=account_id,
            gacha_type=data.get("gacha_type", "301"),
            gacha_name=data.get("gacha_name", "活动祈愿"),
            item_name=data.get("item_name", "测试物品"),
            item_type=data.get("item_type", "角色"),
            rarity=data.get("rarity", 3),
            time=data.get("time", "2024-01-01 12:00:00"),
            pity=data.get("pity", 0),
            is_new=data.get("is_new", False)
        )
        session.add(record)
    session.commit()


def test_get_trend_chart_without_account():
    """Test getting trend chart for non-existent account"""
    response = client.get("/api/charts/99999/trend")
    assert response.status_code == 404


def test_get_trend_chart_empty(db_session):
    """Test getting trend chart with no records"""
    account = create_test_account(db_session)

    response = client.get(f"/api/charts/{account.id}/trend")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["categories"] == []
    assert data["series"] == []


def test_get_trend_chart_with_records(db_session):
    """Test getting trend chart with actual records"""
    account = create_test_account(db_session)

    # Create records spread over different days
    records = []
    for i in range(50):
        records.append({
            "item_name": f"物品{i}",
            "item_type": "角色" if i == 25 else "武器",
            "rarity": 5 if i == 25 else 3,
            "time": f"2024-01-{(i % 10) + 1:02d} 12:00:00",
            "gacha_type": "301"
        })

    create_test_records(db_session, account.id, records)

    response = client.get(f"/api/charts/{account.id}/trend?days=30")
    assert response.status_code == 200
    data = response.json()["data"]

    assert len(data["categories"]) == 30
    assert len(data["series"]) == 3
    assert data["series"][0]["name"] == "总抽数"
    assert data["series"][1]["name"] == "五星"


def test_get_pity_distribution_without_account():
    """Test getting pity distribution for non-existent account"""
    response = client.get("/api/charts/99999/pity-distribution")
    assert response.status_code == 404


def test_get_pity_distribution(db_session):
    """Test getting pity distribution"""
    account = create_test_account(db_session)

    # Create records with 5-stars at different pity levels
    records = []
    pity_levels = [20, 35, 45, 78, 82]
    five_star_index = 0
    current_pity = 0

    for i in range(150):
        current_pity += 1
        if five_star_index < len(pity_levels) and current_pity == pity_levels[five_star_index]:
            records.append({
                "item_name": f"五星{five_star_index}",
                "item_type": "角色",
                "rarity": 5,
                "time": f"2024-01-{(i % 30) + 1:02d} 12:00:00",
                "gacha_type": "301"
            })
            five_star_index += 1
            current_pity = 0
        else:
            records.append({
                "item_name": f"三星{i}",
                "item_type": "武器",
                "rarity": 3,
                "time": f"2024-01-{(i % 30) + 1:02d} 12:00:00",
                "gacha_type": "301"
            })

    create_test_records(db_session, account.id, records)

    response = client.get(f"/api/charts/{account.id}/pity-distribution")
    assert response.status_code == 200
    data = response.json()["data"]

    assert len(data["categories"]) == 8
    assert len(data["data"]) == 8
    assert data["avg_pity"] > 0
    assert data["min_pity"] == min(pity_levels)
    assert data["max_pity"] == max(pity_levels)


def test_get_item_types_without_account():
    """Test getting item types for non-existent account"""
    response = client.get("/api/charts/99999/item-types")
    assert response.status_code == 404


def test_get_item_types(db_session):
    """Test getting item types distribution"""
    account = create_test_account(db_session)

    # Create mixed records
    records = [
        {"item_name": "五星角色1", "item_type": "角色", "rarity": 5},
        {"item_name": "五星角色2", "item_type": "角色", "rarity": 5},
        {"item_name": "五星武器", "item_type": "武器", "rarity": 5},
        {"item_name": "四星角色", "item_type": "角色", "rarity": 4},
        {"item_name": "四星武器", "item_type": "武器", "rarity": 4},
        {"item_name": "三星武器1", "item_type": "武器", "rarity": 3},
        {"item_name": "三星武器2", "item_type": "武器", "rarity": 3},
    ]

    for i, r in enumerate(records):
        r["time"] = f"2024-01-{i+1:02d} 12:00:00"
        r["gacha_type"] = "301"

    create_test_records(db_session, account.id, records)

    response = client.get(f"/api/charts/{account.id}/item-types")
    assert response.status_code == 200
    data = response.json()["data"]

    assert len(data) > 0
    # Should have 5星角色, 5星武器, 4星角色, 4星武器, 3星武器
    type_names = [item["name"] for item in data]
    assert "5星角色" in type_names
    assert "3星武器" in type_names


def test_get_monthly_stats(db_session):
    """Test getting monthly stats"""
    account = create_test_account(db_session)

    # Create records across multiple months
    records = []
    for month in range(1, 4):
        for day in range(1, 11):
            records.append({
                "item_name": f"物品{month}-{day}",
                "item_type": "武器",
                "rarity": 5 if day == 1 else 3,
                "time": f"2024-{month:02d}-{day:02d} 12:00:00",
                "gacha_type": "301"
            })

    create_test_records(db_session, account.id, records)

    response = client.get(f"/api/charts/{account.id}/monthly?months=3")
    assert response.status_code == 200
    data = response.json()["data"]

    assert len(data["categories"]) == 3
    assert "2024-01" in data["categories"]
    assert "2024-02" in data["categories"]
    assert "2024-03" in data["categories"]


def test_get_all_radar_no_accounts():
    """Test radar chart with no accounts"""
    response = client.get("/api/charts/all/radar")
    assert response.status_code == 200
    data = response.json()["data"]

    assert data["indicators"] is not None
    assert len(data["series"]) == 0  # No accounts


def test_get_all_radar_with_accounts(db_session):
    """Test radar chart with multiple accounts"""
    # Create multiple accounts
    account1 = create_test_account(db_session, account_name="账号1", uid="111111111")
    account2 = create_test_account(db_session, account_name="账号2", uid="222222222")

    # Add records to both
    for acc in [account1, account2]:
        records = []
        for i in range(100):
            records.append({
                "item_name": f"物品{i}",
                "item_type": "角色" if i % 10 == 0 else "武器",
                "rarity": 5 if i % 10 == 0 else 3,
                "time": f"2024-01-{(i % 30) + 1:02d} 12:00:00",
                "gacha_type": "301"
            })
        create_test_records(db_session, acc.id, records)

    response = client.get("/api/charts/all/radar")
    assert response.status_code == 200
    data = response.json()["data"]

    assert len(data["series"]) == 2
    account_names = [s["name"] for s in data["series"]]
    assert "账号1" in account_names
    assert "账号2" in account_names
    assert len(data["series"][0]["value"]) == 5
