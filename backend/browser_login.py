#!/usr/bin/env python3
"""
浏览器自动登录模块
通过Playwright实现浏览器自动登录，捕获网络请求获取Cookie和authkey
"""

import asyncio
import json
import re
from typing import Dict, Optional, Tuple
from playwright.async_api import async_playwright, Browser, Cookie
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
import logging

from .logging_config import logger
from .models import Account
from .database import engine, get_session


router = APIRouter()


class LoginRequest(BaseModel):
    game_type: str  # genshin, zzz, starrail
    save_account: bool = True  # 是否自动保存账号信息


class BrowserController:
    """浏览器控制器类"""

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    async def start_browser(self, headless: bool = False):
        """启动浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        self.page = await self.browser.new_page()

    async def stop_browser(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def navigate_to_login(self, game_type: str):
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

    if game_type not in ["genshin", "zzz", "starrail"]:
        raise HTTPException(status_code=400, detail="不支持的游戏类型")

    logger.info(f"开始 {game_type} 浏览器登录流程")

    # 在后台任务中执行登录
    background_tasks.add_task(process_browser_login, game_type, request.save_account)

    return {
        "status": "success",
        "message": "已启动浏览器登录流程，请在浏览器中完成登录操作",
        "status_url": "/api/auth/login-status"
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
        logger.error(f"浏览器登录失败: {e}")
        raise
    finally:
        # 关闭浏览器
        await browser_controller.stop_browser()


async def save_browser_login_account(game_type: str, uid: str, authkey: str, cookies: list):
    """保存浏览器登录的账号信息"""
    try:
        from sqlmodel import Session, select

        # 获取会话
        session = next(get_session())

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
                server="CN",  # 默认国服
                uid=uid,
                auth_key=authkey,
                create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            session.add(new_account)
            logger.info(f"创建新账号 {uid}")

        session.commit()
        session.close()

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

    logger.info(f"成功从URL中提取authkey: {authkey[:20]}...")

    return {
        "status": "success",
        "authkey": authkey,
        "message": f"成功提取 authkey 到账号 {uid}"
    }