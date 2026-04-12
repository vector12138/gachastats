#!/usr/bin/env python3
"""浏览器自动登录模块 - 自动检测图形界面环境
通过Playwright实现浏览器自动登录，捕获网络请求获取Cookie和authkey
"""

import os
import asyncio
import json
import re
from typing import Dict, Optional, Tuple
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
import logging
from loguru import logger

from .database import get_session
from .models import Account

def has_display() -> bool:
    """检测是否有图形界面环境"""
    # 检查DISPLAY环境变量（Linux）
    if os.environ.get('DISPLAY'):
        return True
    # 检查Wayland
    if os.environ.get('WAYLAND_DISPLAY'):
        return True
    # Windows/macOS默认有图形界面
    if os.name == 'nt' or os.name == 'posix' and os.uname().sysname == 'Darwin':
        return True
    # 检查常见的No GUI标记
    if os.environ.get('NO_GUI') or os.environ.get('HEADLESS'):
        return False
    return False

def is_playwright_available() -> bool:
    """检测Playwright是否可用"""
    try:
        from playwright.async_api import async_playwright
        return True
    except ImportError:
        return False

# 条件导入Playwright
if is_playwright_available():
    from playwright.async_api import async_playwright, Browser, Cookie
else:
    async_playwright = None
    Browser = None
    Cookie = None

router = APIRouter()
HAS_DISPLAY = has_display()
IS_BROWSER_AVAILABLE = is_playwright_available()


class LoginRequest(BaseModel):
    game_type: str  # genshin, zzz, starrail
    save_account: bool = True  # 是否自动保存账号信息


class BrowserController:
    """浏览器控制器类"""

    def __init__(self) -> None:
        self.playwright = None
        self.browser = None
        self.page = None

    async def start_browser(self, headless: bool = False) -> None:
        """启动浏览器"""
        """启动浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        self.page = await self.browser.new_page()

    async def stop_browser(self) -> None:
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def navigate_to_login(self, game_type: str) -> None:
        """导航到对应的登录页面"""
        login_pages = {
            "genshin": "https://hk4e-api.mihoyo.com",
            "zzz": "https://zzz-zero-api.mihoyo.com",
            "starrail": "https://api-takumi.mihoyo.com"
        }

        url = login_pages.get(game_type)
        if not url:
            raise ValueError(f"不支持的游戏类型: {game_type}")

        await self.page.goto(url)
        logger.info(f"已导航到 {game_type} 登录页面: {url}")

    async def extract_authkey_from_url(self, url: str) -> Optional[str]:
        """从URL提取authkey"""
        # 匹配URL中的authkey参数
        match = re.search(r'authkey=([^&]+)', url)
        if match:
            return match.group(1)
        return None

    async def wait_for_login(self, timeout: int = 60) -> Dict:
        """等待用户登录并捕获认证信息"""
        auth_info = {
            "authkey": None,
            "cookies": [],
            "uid": None
        }

        logger.info("等待用户登录...")

        # 监听网络请求
        async def handle_request(request):
            url = request.url

            # 检查是否包含authkey
            if "gacha_info/api/getGachaLog" in url or "gacha_record/api/getGachaLog" in url:
                authkey = await self.extract_authkey_from_url(url)
                if authkey:
                    auth_info["authkey"] = authkey
                    logger.info(f"成功获取 authkey: {authkey[:20]}...")

            # 提取UID
            if "uid=" in url:
                uid_match = re.search(r'uid=(\d+)', url)
                if uid_match:
                    auth_info["uid"] = uid_match.group(1)

        # 监听网络请求
        self.page.on("request", handle_request)

        # 等待登录（监听重定向）
        try:
            # 等待页面加载完成或用户手动登录
            await self.page.wait_for_load_state("networkidle", timeout=timeout*1000)
        except asyncio.TimeoutError:
            logger.warning("登录等待超时，但可能已获取到部分认证信息")

        # 获取Cookie
        try:
            auth_info["cookies"] = await self.browser.cookies()
            logger.info(f"获取到 {len(auth_info['cookies'])} 个 Cookie")
        except Exception as e:
            logger.error(f"获取 Cookie 失败: {e}")

        return auth_info


# 全局浏览器控制器实例
browser_controller = BrowserController()


@router.post("/api/auth/browser-login")
async def start_browser_login(request: LoginRequest, background_tasks: BackgroundTasks):
    """开始浏览器登录流程"""
    game_type = request.game_type

    if game_type not in ["genshin", "zzz", "starrail", "zenless"]:
        raise HTTPException(status_code=400, detail="不支持的游戏类型：仅支持 genshin, zzz, starrail, zenless")

    # 检查是否有图形界面
    if not HAS_DISPLAY:
        raise HTTPException(
            status_code=503,
            detail="当前服务器没有图形界面，无法启动浏览器。请使用【从链接提取AuthKey】功能手动获取。"
        )

    # 检查Playwright是否可用
    if not IS_BROWSER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="浏览器自动化组件未安装。请使用【从链接提取AuthKey】功能手动获取。"
        )

    logger.info(f"开始 {game_type} 浏览器登录流程")

    # 在后台任务中执行登录 - 需要包装async函数
    def run_browser_login():
        import asyncio
        asyncio.run(process_browser_login(game_type, request.save_account))

    background_tasks.add_task(run_browser_login)

    return {
        "status": "success",
        "message": "已启动浏览器登录流程，请在浏览器中完成登录操作",
        "status_url": "/api/auth/login-status"
    }


@router.get("/api/auth/browser-status")
async def get_browser_status():
    """获取浏览器环境状态"""
    return {
        "status": "success",
        "data": {
            "has_display": HAS_DISPLAY,
            "browser_available": IS_BROWSER_AVAILABLE,
            "can_auto_login": HAS_DISPLAY and IS_BROWSER_AVAILABLE
        }
    }


async def process_browser_login(game_type: str, save_account: bool):
    """处理浏览器登录流程"""
    try:
        # 启动浏览器
        await browser_controller.start_browser(headless=False)

        # 导航到登录页面
        await browser_controller.navigate_to_login(game_type)

        # 等待用户登录
        auth_info = await browser_controller.wait_for_login()

        # 获取UID
        uid = auth_info.get("uid")
        authkey = auth_info.get("authkey")
        cookies = auth_info.get("cookies", {})

        if not authkey:
            logger.error("未能获取到有效的 authkey")
            raise Exception("登录失败：未能获取到监听用的authkey")

        logger.info(f"登录成功！获取到 UID: {uid}, Authkey: {authkey[:20]}...")

        # 如果保存账号，存入数据库
        if save_account and uid:
            await save_browser_login_account(game_type, uid, authkey, cookies)

        logger.info("浏览器登录流程完成")

    except Exception as e:
        error_msg = str(e)
        if "Executable doesn't exist" in error_msg or "playwright install" in error_msg:
            logger.error("浏览器登录失败: Playwright 浏览器未安装")
        else:
            logger.error(f"浏览器登录失败: {e}")
    finally:
        # 关闭浏览器
        await browser_controller.stop_browser()


async def save_browser_login_account(game_type: str, uid: str, authkey: str, cookies: list):
    """保存浏览器登录的账号信息"""
    try:
        from sqlmodel import Session, select

        # 获取会话
        session_gen = get_session()
        session = next(session_gen)

        # 检查是否已存在该UID
        existing_account = session.exec(
            select(Account).where(Account.uid == uid)
        ).first()

        cookies_str = json.dumps(cookies)  # 转换Cookie为字符串

        if existing_account:
            # 更新现有账号
            existing_account.auth_key = authkey
            existing_account.last_sync_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"更新账号 {uid} 的认证信息")
        else:
            # 创建新账号
            new_account = Account(
                game_type=game_type,
                account_name=f"浏览器登录-{uid}",
                server="cn_gf01",  # 默认国服
                uid=uid,
                auth_key=authkey,
                create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            session.add(new_account)
            logger.info(f"创建新账号 {uid}")

        session.commit()

        logger.info(f"账号 {uid} 保存成功")

    except Exception as e:
        logger.error(f"保存账号信息失败: {e}")
        raise


# 用于从截取到的URL中获取authkey的简化方法
@router.post("/api/auth/extract-url")
async def extract_authkey_from_user_url(request: dict):
    """从用户提供的URL中提取authkey"""
    url = request.get("url", "")
    if not url:
        raise HTTPException(status_code=400, detail="URL不能为空")

    # 使用正则表达式提取authkey
    authkey_match = re.search(r'authkey=([^&]+)', url)
    if not authkey_match:
        raise HTTPException(status_code=400, detail="URL中未找到authkey参数")

    authkey = authkey_match.group(1)

    # 尝试提取UID
    uid_match = re.search(r'uid=(\d+)', url)
    uid = uid_match.group(1) if uid_match else "未知"

    logger.info(f"成功从URL中提取authkey: {authkey[:20]}...")

    return {
        "status": "success",
        "authkey": authkey,
        "uid": uid,
        "message": f"成功提取 authkey"
    }