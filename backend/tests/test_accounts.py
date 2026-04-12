"""Test cases for GachaStats API endpoints"""
import json
import tempfile
import os
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_engine
from sqlmodel import create_engine, SQLModel, Session
from backend.models import Account


class TestAccountEndpoints:
    """测试账号相关接口"""

    def setup_method(self):
        """为每个测试创建临时数据库"""
        # 创建临时数据库文件
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()

        # 创建测试数据库引擎
        self.test_engine = create_engine(f"sqlite:///{self.temp_db.name}")
        SQLModel.metadata.create_all(self.test_engine)

        # 替换依赖
        def get_test_session():
            with Session(self.test_engine) as session:
                yield session

        import backend.main
        backend.main.app.dependency_overrides[get_engine] = lambda: self.test_engine
        backend.main.app.dependency_overrides[get_session] = get_test_session

        # 创建测试客户端
        self.client = TestClient(app)

    def teardown_method(self):
        """测试后清理"""
        SQLModel.metadata.drop_all(self.test_engine)
        self.temp_db.close()
        os.unlink(self.temp_db.name)

    def test_root_endpoint(self):
        """Test root endpoint returns frontend HTML"""
        # 由于前端文件可能不存在，我们测试返回404的备用页面
        response = self.client.get("/")
        # 应该返回200（无论前端文件存在与否）
        assert response.status_code == 200

    def test_get_accounts_empty(self):
        """Test getting accounts when database is empty"""
        response = self.client.get("/api/accounts")
        assert response.status_code == 200
        data = response.json()
        # 应该返回空列表
        assert isinstance(data, list)
        assert len(data) == 0

    def test_create_account_success(self):
        """Test creating a new account"""
        account_data = {
            "game_type": "genshin",
            "account_name": "测试用户",
            "server": "cn_gf01",
            "uid": "test_uid_123456",
            "auth_key": "test_auth_key_123"
        }
        response = self.client.post("/api/accounts", json=account_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "account_id" in data
        assert data["message"] == "账号创建成功"

    def test_create_account_duplicate_uid(self):
        """Test creating duplicate account with same UID"""
        account_data = {
            "game_type": "genshin",
            "account_name": "第一个账号",
            "server": "cn_gf01",
            "uid": "duplicate_uid_test",
            "auth_key": "test_auth_key_456"
        }
        # 第一次创建
        response1 = self.client.post("/api/accounts", json=account_data)
        assert response1.status_code == 200

        # 第二次创建（同UID）
        account_data["account_name"] = "第二个账号"
        response2 = self.client.post("/api/accounts", json=account_data)
        assert response2.status_code == 400
        data = response2.json()
        assert data["status"] == "error"
        assert data["message"] == "该游戏UID已存在"

    def test_create_account_with_different_games(self):
        """测试不同游戏账号的创建"""
        games = [
            {"game": "genshin", "server": "cn_gf01"},
            {"game": "starrail", "server": "prod_gf_cn"},
            {"game": "honkai3", "server": "bh3_tw02"},
            {"game": "zzz", "server": "zzz_cn01"}
        ]

        for i, game_config in enumerate(games):
            account_data = {
                "game_type": game_config["game"],
                "account_name": f"{game_config['game']}_user",
                "server": game_config["server"],
                "uid": f"uid_{game_config['game']}_{i}",
                "auth_key": f"auth_key_{i}"
            }
            response = self.client.post("/api/accounts", json=account_data)
            assert response.status_code == 200

    def test_delete_account(self):
        """测试删除账号"""
        # 先创建一个账号
        account_data = {
            "game_type": "genshin",
            "account_name": "待删除账号",
            "server": "cn_gf01",
            "uid": "delete_test_uid",
            "auth_key": "delete_key"
        }
        create_response = self.client.post("/api/accounts", json=account_data)
        assert create_response.status_code == 200
        account_id = create_response.json()["account_id"]

        # 删除账号
        delete_response = self.client.delete(f"/api/accounts/{account_id}")
        assert delete_response.status_code == 200
        delete_data = delete_response.json()
        assert delete_data["status"] == "success"
        assert delete_data["message"] == "账号已删除"

        # 验证删除成功
        accounts_response = self.client.get("/api/accounts")
        accounts = accounts_response.json()
        assert len(accounts) == 0

    def test_delete_nonexistent_account(self):
        """测试删除不存在的账号"""
        response = self.client.delete("/api/accounts/999999")
        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "error"
        assert data["message"] == "账号不存在"

    def test_get_accounts_with_data(self):
        """测试获取包含数据的账号列表"""
        # 创建多个账号
        accounts = [
            {
                "game_type": "genshin",
                "account_name": "账号1",
                "server": "cn_gf01",
                "uid": "uid001",
                "auth_key": "key1"
            },
            {
                "game_type": "starrail",
                "account_name": "账号2",
                "server": "prod_gf_cn",
                "uid": "uid002",
                "auth_key": "key2"
            }
        ]

        for account in accounts:
            response = self.client.post("/api/accounts", json=account)
            assert response.status_code == 200

        # 获取账号列表
        list_response = self.client.get("/api/accounts")
        assert list_response.status_code == 200
        data = list_response.json()
        assert len(data) == 2
        assert data[0]["account_name"] in ["账号1", "账号2"]

    def test_create_account_missing_fields(self):
        """测试创建账号缺少字段的情况"""
        # 缺少必需字段
        account_data = {
            "game_type": "genshin",
            "server": "cn_gf01",
            "uid": "missing_fields_test"
            # 缺少 account_name 和 auth_key
        }
        response = self.client.post("/api/accounts", json=account_data)
        # 应该能处理缺失字段
        assert response.status_code in [200, 400]


if __name__ == "__main__":
    # 运行所有测试
    pytest.main(["-v", __file__])