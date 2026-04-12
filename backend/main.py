#!/usr/bin/env python3
"""
GachaStats 主服务

已按照规划拆分功能：
- 账号管理 → backend/accounts.py
- 抽卡导入 → backend/imports.py
- 数据分析 → backend/analysis.py

此文件只负责 FastAPI 应用初始化、静态文件挂载以及注册子路由。
端口等运行参数在项目根目录的 ``config.json`` 中配置，由根入口 ``main.py`` 读取。
"""

import logging
import sys
from pathlib import Path
import json

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

# 初始化日志系统
from .logging_config import setup_logging
logger = setup_logging()

# ------------------- 统一所有日志输出到 loguru -------------------

class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        """将标准 logging 的记录转发到 loguru。"""
        try:
            # 获取日志级别
            try:
                level = logger.level(record.levelname).name
            except (ValueError, AttributeError):
                level = record.levelno

            # 跳过 uvicorn.access 日志（我们已经有自定义的访问日志）
            if record.name == "uvicorn.access":
                return

            # 转发日志到 loguru
            logger.opt(depth=6, exception=record.exc_info).log(
                level, f"[{record.name}] {record.getMessage()}"
            )
        except Exception:
            # 静默处理，避免日志拦截器本身出错
            pass

# 配置根 logger
def setup_logging_intercept():
    """设置日志拦截系统"""
    # 移除所有现有的 handler
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 添加我们的拦截器
    root_logger.addHandler(InterceptHandler())

    # 为特定模块设置日志级别，减少冗余输出 , "sqlalchemy", "sqlalchemy.engine", "sqlalchemy.pool"
    for name in ["uvicorn", "uvicorn.error", "fastapi"]:
        logging.getLogger(name).setLevel(logging.INFO)

    logger.info("日志拦截系统已初始化")

# 初始化日志拦截
setup_logging_intercept()

# ------------------- 相对导入 -------------------
from .database import init_db
from .accounts import router as accounts_router
from .imports import router as imports_router
from .analysis_routes import router as analysis_router
from .browser_login import router as browser_login_router
from .export_routes import router as export_router
from .planning_routes import router as planning_router
from .charts_routes import router as charts_router

# 初始化数据库表
init_db()

# ------------------- FastAPI 应用初始化 -------------------
app = FastAPI(
    title="GachaStats API",
    description="米哈游全游戏抽卡数据分析工具",
    version="1.0.0",
)

# 静态文件（前端页面）
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# 注册子路由
app.include_router(accounts_router)
app.include_router(imports_router)
app.include_router(analysis_router)
app.include_router(browser_login_router)
app.include_router(export_router)
app.include_router(planning_router)
app.include_router(charts_router)

@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    """前端首页"""
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    return html

# ------------------- 统一 API 响应格式 -------------------
@app.middleware("http")
async def unify_response(request: Request, call_next) -> JSONResponse:
    """包装成功响应并统一错误结构"""
    response = await call_next(request)
    if 200 <= response.status_code < 300 and isinstance(response, JSONResponse):
        try:
            raw = response.body
            if isinstance(raw, (bytes, bytearray)):
                raw = raw.decode()
            data = json.loads(raw)
        except Exception:
            return response
        wrapped = {"status": "success", "data": data}
        return JSONResponse(content=wrapped, status_code=response.status_code)
    return response

# ------------------- 自定义错误处理 -------------------
from fastapi.exceptions import HTTPException as FastAPIHTTPException

@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request: Request, exc: FastAPIHTTPException) -> JSONResponse:
    """统一 HTTP 错误响应结构"""
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "code": exc.status_code, "message": exc.detail},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """捕获未预料的异常并返回统一结构"""
    logger.exception("Unexpected error")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "code": 500, "message": "Internal server error"},
    )