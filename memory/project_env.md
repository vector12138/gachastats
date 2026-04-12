---
name: project_env
description: 项目开发环境使用规范 - 所有操作必须使用虚拟环境
type: project
---

**规则**: 在测试、修复bug、安装包等需要启动项目时，都必须使用项目内的虚拟环境进行操作。

**为什么**: 确保依赖隔离，避免环境冲突，保证项目稳定性。

**如何应用**: 
- 执行 Python 命令时使用 `source venv/bin/activate && python` 
- 安装包时使用 `source venv/bin/activate && pip install`
- 运行服务时使用 `source venv/bin/activate && python -m backend.main`
- 测试时使用 `source venv/bin/activate && pytest`