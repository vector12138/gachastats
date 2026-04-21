# CLAUDE.md
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
GachaStats is a local web-based analysis tool for miHoYo gacha/loot box data. It supports Genshin Impact, Honkai Impact 3rd, Honkai: Star Rail, and Zenless Zone Zero. The tool provides gacha data import, analysis, and visualization features with all data stored locally.

## Critical Rule
**MUST operate within venv virtual environment** - all development tasks require environment isolation

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment from project root
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install all dependencies (with OCR support)
pip install -r requirements.txt

# Optional: Minimal installation without OCR
pip install fastapi uvicorn requests pydantic python-multipart loguru sqlmodel
```

### Backend Setup and Run (in venv)
```bash
# Ensure venv is activated first
source venv/bin/activate

# Run the FastAPI server (from project root)
python run.py
# Server runs on port 8777 by default (configurable in config.json)
```

### Testing (in venv)
```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-fastapi httpx

# Run tests from venv (from project root)
source venv/bin/activate
python -m pytest backend/tests/ -v
# Run specific test file
python -m pytest backend/tests/test_accounts.py -v
```

### Frontend
No build process needed. Frontend is served directly from the backend via FastAPI's StaticFiles at `/static` path.

## Architecture Overview

### Backend Structure
The backend uses FastAPI with SQLModel for database operations. Core modules:

| 模块 | 路径 | 功能描述 |
|------|------|----------|
| FastAPI App | `backend/main.py` | 应用初始化、静态文件、路由注册 |
| 账号管理 | `backend/accounts.py` | 账号CRUD操作 |
| 数据导入 | `backend/imports.py` | 游戏API/手动导入 |
| 数据分析 | `backend/analysis.py` | 统计计算与分析 |
| 数据模型 | `backend/models.py` | SQLModel数据库模型 |
| 数据库连接 | `backend/database.py` | 连接与会话管理 |
| 工具函数 | `backend/utils.py` | 工具函数与常量 |
| 浏览器登录 | `backend/browser_login.py` | Playwright自动登录 |
| OCR模块 | `backend/ocr/` | 截图解析（可选） |
| 分析路由 | `backend/analysis_routes.py` | 分析API端点 |
| 图表路由 | `backend/charts_routes.py` | 图表API端点 |
| 导出路由 | `backend/export_routes.py` | 数据导出API |
| 规划路由 | `backend/planning_routes.py` | 抽卡规划API |

### Frontend Structure
Single-page application in frontend/index.html using Vue 3, Element Plus UI, and ECharts. Static assets are served directly by the backend.

### Data Storage
SQLite database stored in `data/gachastats.db` with SQLModel ORM. Database tables:
- Account: Game account info (uid unique per game_type)
- GachaRecord: Individual gacha pulls with pity tracking
- GameData: Game item metadata

### Key Configurations
- `config.json`: 完整配置（服务器、数据库、日志、浏览器、导入等）
- `config.example.json`: 配置模板（带所有可配置项注释）
- `backend/config_loader.py`: 配置加载模块（支持默认值、缓存、深度合并）
- `backend/logging_config.py`: 统一日志配置（使用loguru，支持配置化）
- `backend/database.py`: 数据库配置（支持自定义路径）
- `run.py`: 启动脚本

### Route Modules
后端路由已按功能分离到独立模块：
- `backend/accounts.py` - `/api/accounts/*` 账号管理
- `backend/imports.py` - `/api/imports/*` 数据导入
- `backend/analysis_routes.py` - `/api/analysis/*` 数据分析
- `backend/charts_routes.py` - `/api/charts/*` 图表数据
- `backend/export_routes.py` - `/api/exports/*` 数据导出
- `backend/planning_routes.py` - `/api/planning/*` 抽卡规划

默认端口: 8777（可在 config.json 中修改）

## Development Notes
- Use SQLModel for all database operations - it provides Pydantic models with SQLAlchemy
- All UX text should be in Chinese as this targets Chinese-speaking users
- FastAPI app is mounted at backend/main.py - use `run.py` to start, not direct uvicorn
- Static files served from `/frontend` directory via mount at `/static` route
## 前端文件分离要求
前端代码必须按功能模块分离，避免单文件过大：

### 当前结构（过渡期）
```
frontend/
├── index.html              # 主页面
├── js/
│   ├── app-full.js       # 主应用（所有功能，注意控制大小）
│   └── modules/            # 未来拆分目录
└── css/
    └── base.css            # 基础样式 + 暗黑模式变量
```

### 未来拆分规划
当 app-full.js 超过 500 行时，按以下结构拆分：
```
frontend/js/modules/
├── accounts.js      # 账号管理
├── import.js        # 数据导入
├── analysis.js      # 数据分析
├── charts.js        # 图表功能
├── planning.js      # 抽卡规划
├── export.js        # 数据导出
└── settings.js      # 系统设置
```

拆分原则：
1. 单文件不超过 300 行代码
2. 按功能模块独立
3. 使用 ES6 模块导出/导入
4. 保持与 Element Plus 和 Vue 3 兼容
