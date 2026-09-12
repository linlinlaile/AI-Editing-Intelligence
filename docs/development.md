[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "aei"
version = "0.1.0"
description = "AI Editing Intelligence semantic timeline"
requires-python = ">=3.10,<3.13"

[project.optional-dependencies]
dev = [
  "pytest>=8.0,<9",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = ["-ra"]
"@ | Set-Content pyproject.toml
@'
# 开发环境与测试

## 安装

需要 Python 3.10–3.12。建议在仓库根目录创建虚拟环境并安装开发依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## 本地测试

```powershell
python -m pytest
```

只运行契约测试：

```powershell
python -m pytest tests/test_contract.py tests/test_contract_hardening.py
```

## CI

CI 只需要执行同一个入口，确保本地与 CI 行为一致：

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

pytest 配置位于 `pyproject.toml`，测试目录固定为 `tests/`，源码目录自动加入 `pythonpath`。
