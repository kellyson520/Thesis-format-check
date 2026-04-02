# 个人版MVP 技术规范 (Personal MVP Specification)

## 1. 架构精简说明 (Architecture Simplification)
由于使用场景限定于**本地个人级别**，需将原方案的微服务、消息队列及分布式存储体系进行简化压缩：
- **微服务架构模块** -> 本地 Python 包结构。
- **存储集群** -> 依赖本地硬盘读写 (`data/` / `tests/temp/`)。
- **规则引擎（原先用数据库存取）** -> 本地 `.yaml` 文件或 `.json`。
- **UI交互层** -> 放弃重型 Electron，采用 **PyWebView + 本地微Web服务** 的混合渲染架构，打造轻量级且极具现代感（Glassmorphism、平滑动画）的桌面客户端体验。
- **文件解析** -> 初期版本暂缓支持复杂 PDF，只保留纯 `.docx` 的流式解析支持。

## 2. 核心模块简化重组方案 (Core Modules Restructuring)

### 2.1 规则处理器模块 (`Module: rule_loader`)
*   **职责**:
    通过 `PyYAML` 读取 `rules.yaml`（例如设定特定的学校要求规范，比如宋体小四）。
*   **规则分层策略映射**:
    仅保留 "样式级"(Style)、"段落级"(Paragraph)、"文档级默认"(Document default) 三重优先级的比较策略。

### 2.2 本地解析核心 (`Module: docx_parser`)
*   **依赖**: `python-docx`。
*   **职责**:
    遍历文档内容元素（`run`, `paragraph`, `table` 等结构）。
    分析目标为真实的字体状态、字号大小。对于未赋指的元素，按照 Word `styles` 的层次关系找到最终映射字号大小（处理复杂继承关系）。
*   **输入输出**: （文档路径 -> 元信息列表）

### 2.3 验证引擎 (`Module: validator`)
*   **功能**:
    比较 `RuleLoader` 中期望的值，和 `docx_parser` 中扫描出的实际值。收集规则冲突点。
*   **过滤机制**:
    跳过自动插入或者无需校验的特定宏区域。支持英文字体的特定映射。

### 2.4 报告与反馈器 (`Module: reporter`)
*   **输出形式 1 (基础)**: 终端彩页列表：用 `colorama` 以红色显示错误段落及行数。并提示正确样式修复路径。
*   **输出形式 2 (进阶)**: 新建一份 `[原名]_checked_report.docx` 文档副件。
*   原位注入基于 `python-docx` 的文字高亮警告。
*   原位附加文档段落结尾备注。

## 3. 个人PC端技术栈选型 (PC Client Tech Stack)
为了在单机环境下提供**极为出色的用户体验 (Premium UX)** 且保持系统轻量，本项目技术栈设计如下：

### 3.1 表现层 (UI / Frontend)
*   **应用容器**: `pywebview` - 调用 Windows 本地 Edge/Chromium 内核，极低内存消耗，提供完整的桌面应用原生窗口体验。
*   **基础框架**: `Vite` + `Vue.js 3` (或纯 Vanilla JS)。
*   **设计语言 (Aesthetics)**: 放弃臃肿组件库，定制化写 Vanilla CSS。采用**毛玻璃效果 (Glassmorphism)**、深色模式 (Dark Mode)、微动画交互 (Micro-animations) 等前沿 Web 设计规范，确保“惊艳的第一眼感觉”。包含文件拖拽区、流式处理动画等机制。

### 3.2 逻辑控制层 (Backend Local API)
*   **通信路由**: `FastAPI` (搭配 `uvicorn`) - 作为本地常驻微服务通过本地端口（如 `http://127.0.0.1:8000`）提供轻量级 REST API，供前端界面请求与传输文档。
*   **并发模型**: 纯异步接口处理，确保在处理几百页 `.docx` 文件时桌面 GUI 不卡顿。

### 3.3 核心解析层 (Core Engine)
*   `python-docx` (DOM 树与文档操作)
*   `PyYAML` (规则与策略配置加载)

### 3.4 依赖图谱与打包发布
```toml
# pyproject.toml
[tool.poetry.dependencies]
python = "^3.10"
python-docx = ">=0.8.11"
PyYAML = ">=6.0"
fastapi = ">=0.103.0"
uvicorn = ">=0.23.2"
pywebview = ">=4.2.2"
python-multipart = ">=0.0.6" # 用于处理 API 文件上传
```
**发布策略 (Distribution)**: 使用 `PyInstaller` 将本地 Web 资源（HTML/CSS/JS）、Python 解释器以及 `FastAPI` 核心引擎打包到一个独立的 `.exe` 可执行文件中，用户无需预先安装任何 Python 环境即可开箱即用。
