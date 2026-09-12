# 开发环境与测试入口

本文件是项目开发环境和测试命令的统一入口。以下信息于 2026-09-12 在仓库实际检测；所有 PowerShell 命令均从仓库根目录执行，不需要激活虚拟环境或修改 PATH。

## Runtime

- 当前 Python：CPython **3.12.14**，Windows AMD64。
- 项目声明支持范围：`>=3.10,<3.13`，见 [pyproject.toml](../../pyproject.toml)。本次仅验证 3.12.14。
- 虚拟环境：仓库根目录 `.venv`；当前绝对路径为 `D:\vibecoding\AI-Editing-Intelligence\.venv`。
- 解释器入口：`.\.venv\Scripts\python.exe`。
- 包管理：虚拟环境内的 **pip 25.0.1**，setuptools 构建；`aei 0.1.0` 以 editable 方式安装到当前仓库。
- 已安装并检测：pytest **8.4.2**、PyAV **14.2.0**、Pillow **11.3.0**、torch **2.8.0+cpu**、torchvision **0.23.0+cpu**；`pip check` 通过。
- 未发现仓库的 uv/Poetry lockfile；该虚拟环境没有 uv/Poetry。本次 session 的 PATH 无 python、py、uv、poetry、pytest、ffmpeg、ffprobe；这不代表整台机器没有安装它们。
- `.venv` 已被 Git 忽略。当前依赖使用版本范围，没有依赖锁文件；上面的版本是实测快照，不保证未来重装解析出完全相同的版本。

## Install

当前 `.venv` 已可用，无需重建。安装或恢复当前项目声明的开发及媒体依赖，使用：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,media]"
.\.venv\Scripts\python.exe -m pip check
```

`dev` 提供 pytest；`media` 提供 PyAV 和 Pillow。完整媒体测试必须安装两组依赖，并检查测试输出没有因缺少依赖而 skipped。安装需要可用的包源或缓存；本次未重新安装依赖。

视觉模型适配器的可选依赖安装命令（CPU wheel）：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[vision]" --index-url https://download.pytorch.org/whl/cpu
```

ResNet18 `IMAGENET1K_V1` 权重必须由操作者显式放置到 `.venv\models\resnet18-f37072fd.pth`；代码会校验 SHA-256，不会自动下载。真实模型测试另需设置 `RUN_REAL_MODEL=1`。

仅当 `.venv` 不存在时才创建，不要覆盖一个正在使用的环境。当前 `pyvenv.cfg` 记录的基础解释器已经检测存在：

```powershell
& 'C:\Users\42748\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,media]"
```

这个基础路径是本机信息，可能随 Codex runtime 更新而失效；其他机器应先确认实际存在且满足版本范围的 Python 绝对路径，再创建 `.venv`。创建之后一律使用项目解释器，不依赖全局 python、临时 PATH 或对话历史。不安装新的全局工具。

## Test

完整测试命令：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

本次实测（不启用真实模型）：**38 passed，1 skipped，0 failed**；跳过项是显式 opt-in 的真实 ResNet18 测试。另行启用 `RUN_REAL_MODEL=1` 时，该测试通过。历史 31 项基线和本阶段新增测试均包含在内。

真实模型 smoke test：

```powershell
$env:RUN_REAL_MODEL = "1"
.\.venv\Scripts\python.exe -m pytest tests/test_vision_adapter.py -m real_model -q
```

pytest 从 `pyproject.toml` 读取配置：`testpaths = ["tests"]`，`pythonpath = ["src"]`，无需设置 PYTHONPATH。

## Development Commands

运行单个测试：

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_observation_phase5.py::test_observation_statuses_and_queries_round_trip -q
```

运行 Observation 验证：

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_observation_phase5.py -q
```

运行现有 migration 测试（包含升级保留数据、重复执行和建表检查）：

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_contract.py tests/test_contract_hardening.py -k migration -q
```

列出测试、检查环境及查看修改：

```powershell
.\.venv\Scripts\python.exe -m pytest --collect-only -q
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip list
.\.venv\Scripts\python.exe -m pip check
git diff --check
git status --short
```

现有完整测试通过 PyAV 本地生成与解码媒体，不需要 PATH 中的 ffmpeg/ffprobe。PySceneDetect 未安装，真实 PySceneDetect adapter 不在此次测试覆盖范围内；Shot 测试使用固定 detector 输出。不要把测试通过解释为已验证所有外部 adapter。

## 与已有文档的关系

旧 [development.md](../development.md) 混入了配置/PowerShell 写文件片段，且命令依赖激活环境后的 `python`。以后以本文件中的显式项目解释器命令为准。

README/AGENTS 中“尚无实现代码”的阶段描述已过时；Phase 0-4 基线参见 [Phase Summary](../phases/PHASE_0_4_SUMMARY.md)，Phase 5.1 状态兼容决策参见 [ADR-0008](../decisions/ADR-0008-observation-contract-phase5.md)。本次只固化环境入口，不改写历史架构基线。
