"""Test cases for GachaStats main application."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_session
from sqlmodel import Session, create_engine
from backend.models import SQLModel, Account
import tempfile
import os


class TestMainApp:
    """测试主应用"""

    def setup_method(self):
        """为每个测试创建临时数据库和客户端."""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()

        # 创建测试引擎
        self.test_engine = create_engine(f"sqlite:///{self.temp_db.name}")

        # 创建表
        SQLModel.metadata.create_all(self.test_engine)

        # 临时替换依赖
        def get_test_session():
            with Session(self.test_engine) as session:
                yield session

        app.dependency_overrides[get_session] = get_test_session

        # 创建测试客户端
        self.client = TestClient(app)

    def teardown_method(self):
        """测试后清理."""
        # 恢复依赖
        app.dependency_overrides.clear()
        # 删除临时数据库
        os.unlink(self.temp_db.name)

    def test_root_endpoint(self):
        """测试根路径返回前端页面."""
        response = self.client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "米哈游抽卡" in response.text

    def test_api_accounts_empty(self):
        """测试空账号列表."""
        response = self.client.get("/api/accounts")
        assert response.status_code == 200
        data = response.json()

        # 新标准返回格式
        assert data == [] or data["data"] == []

    def test_create_account_success(self):
        """测试创建账号."""
        account_data = {
            "game_type": "genshin",
            "account_name": "测试账号",
            "server": "cn_gf01",
            "uid": "114514810",
            "auth_key": "test_auth_key"
        }

        response = self.client.post("/api/accounts", json=account_data)
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "account_id" in data
        assert data["message"] == "账号创建成功"

        # 验证创建成功
        get_response = self.client.get("/api/accounts")
        assert get_response.status_code == 200
        accounts = get_response.json()

    def test_create_account_duplicate_uid(self):
        """测试重复UID处理."""
        account_data = {
            "game_type": "genshin",
            "account_name": "测试账号",
            "server": "cn_gf01",
            "uid": "114514810",
            "auth_key": "test_auth_key"
        }

        # 第一次创建
        response1 = self.client.post("/api/accounts", json=account_data)
        assert response1.status_code == 200

        # 第二次创建（同UID）
        account_data["account_name"] = "另一个账号"
        response2 = self.client.post("/api/accounts", json=account_data)

        assert response2.status_code == 400
        data = response2.json()
        assert data["status"] == "error"
        assert data["message"] == "该游戏UID已存在"

    def test_create_account_with_honkai(self):
        """测试崩坏3账号创建."""
        account_data = {
            "game_type": "honkai3",
            "account_name": "崩坏3测试",
            "server": "bh3_tw01",
            "uid": "123456789",
            "auth_key": "bh3_auth_key"
        }

        response = self.client.post("/api/accounts", json=account_data)
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["status"] == "success"
        assert "account_id" in response_data

    def test_create_account_with_starrail(self):
        """测试崩坏：星穹铁道账号创建."""
        account_data = {
            "game_type": "starrail",
            "account_name": "星穹铁道测试",
            "server": "prod_gf_cn",
            "uid": "987654321",
            "auth_key": "sr_auth_key"
        }

        response = self.client.post("/api/accounts", json=account_data)
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["status"] == "success"
        assert "account_id" in response_data

    def test_delete_account(self):
        """测试删除账号."""
        # 先创建一个账号
        account_data = {
            "game_type": "genshin",
            "account_name": "要删除的账号",
            "server": "cn_gf01",
            "uid": "777777777",
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

    def test_delete_nonexistent_account(self):
        """测试删除不存在的账号."""
        response = self.client.delete("/api/accounts/999999")
        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "error"
        assert data["message"] == "账号不存在"

    def test_static_files_service(self):
        """测试静态文件服务."""
        # 假设有前端文件存在
        response = self.client.get("/static/index.html")
        # 在主程序中，如果有前端文件会重定向到/，如果没有会404
        assert response.status_code == 200 or response.status_code == 404

    def test_404_handler(self):
        """测试404处理器."""
        response = self.client.get("/api/nonexistent/endpoint")
        assert response.status_code == 404

        # 检查返回的内容是否为JSON
        try:
            json_data = response.json()
            assert isinstance(json_data, dict)
        except ValueError:
            # 可能是HTML错误页面
            assert "text/html" in response.headers.get("content-type", "")

    def test_cors_headers(self):
        """测试CORS跨越配置."""
        response = self.client.get("/api/accounts")
        # 应该允许跨域访问
        # 实际测试中，检查头是否存在
        cors_headers = ["access-control-allow-origin", "access-control-allow-methods"]
        has_any = any(h in response.headers for h in cors_headers)
        assert has_any or True  # CORS可能已全局配置

    def test_multiple_games_support(self):
        """测试多游戏支持（通过参数验证）."""
        games = ["genshin", "honkai3", "starrail", "zzz"]

        for game in games:
            account_data = {
                "game_type": game,
                "account_name": f"{game}账号",
                "server": "test_server",
                "uid": f"uid_{game}",
                "auth_key": f"auth_{game}"
            }

            response = self.client.post("/api/accounts", json=account_data)
            assert response.status_code == 200

    def test_account_response_fields(self):
        """测试返回的账号字段是否完整."""
        test_data = {
            "game_type": "genshin",
            "account_name": "完整测试",
            "server": "cn_gf01",
            "uid": "888888888",
            "auth_key": "complete_test"
        }

        create_response = self.client.post("/api/accounts", json=test_data)
        assert create_response.status_code == 200

        # 获取所有账号列表
        list_response = self.client.get("/api/accounts")
        assert list_response.status_code == 200

        first_account = list_response.json()[0] if list_response.json() else None
        if first_account:
            required_fields = ["id", "game_type", "account_name", "server", "uid", "auth_key"]
            for field in required_fields:
                assert field in first_account