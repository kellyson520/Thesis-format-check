# Changelog

## v1.0.0 — 2026-04-03

### 🏗️ 架构大革命 (Clean Architecture Revolution)

**核心架构 (Core Architecture)**
- **DDD 分层重构**：从单体“上帝类”演进为严格的 Domain / Use Cases / Infrastructure 三层模型。通过物理路径隔离强制执行业务与 I/O 的彻底解耦。
- **ADM (Abstract Document Model)**：引入抽象文档模型，使校验插件面向 ADM 编程，不再依赖具体的 python-docx 库。
- **生成器管道 (ValidatorPipeline)**：基于 Generator 驱动校验任务，原生支持非阻塞式实时进度上报，解耦了业务逻辑与 UI 推送。
- **单一职责插件化 (SRP)**：原 `Validator` 拆解为 `FontPlugin`, `SpacingPlugin`, `HierarchyPlugin`, `CaptionSeqPlugin`, `PageMarginPlugin` 等独立可插拔插件。
- **依赖倒置 (DIP)**：通过 `domain/interfaces` 建立接口契约，实现核心层由于对外部库（fastapi, docx）的零引用。

**配置与规则管理 (Rule Engine)**
- **Pydantic 强类型接入**：使用 `RuleConfig` 代替脆弱的嵌套字典，支持规则热加载、默认值自动填充及 Schema 级联合法性校验。
- **深度校验能力**：新增图表题注编号连续性校验、跨级标题（H1 直接到 H3）侦测、以及页面边距合规性验证。

**工程化与标准化 (Engineering & Standards)**
- **架构标准**：建立根目录 [ARCHITECTURE_STANDARD.md](file:///ARCHITECTURE_STANDARD.md)，固化分层原则与插件开发 SOP。
- **架构卫士 (Skill Enforcement)**：同步更新 `clean-arch-enforcer` 技能与其配套审计 SOP。
- **环境隔离验证**：通过 `validate_arch.py` 等脚本验证了内层代码的纯净度。

---

## v0.1.4 — 2026-04-03

### 🐛 Bug Fixes
- 修复 `src/main.py` 中 `base_dir` 未定义导致静态资源加载失败及测试目录报错的问题。

---

## v0.1.3 — 2026-04-02

### 🐛 Bug Fixes
- 修复 `src/main.py` 意外丢失 `from pydantic import BaseModel` 导致的启动崩溃问题。

---

## v0.1.2 — 2026-04-02

### 🐛 Bug Fixes
- 修复了 PyInstaller 打包后的文件路径解析问题。
- `frozen` 模式下现在将读取独立外置的 `config/rules.yaml`（在 EXE 同级目录），修复了无法正常读取压缩包内部配置的 BUG，现允许用户直接修改。
- 日志目录也同步在 EXE 同级生成。

---

## v0.1.1 — 2026-04-02

### 🔧 CI 修复与工程固化

**CI/CD Pipeline**
- Fixed `actions/setup-node@v4` 缓存失败错误：移除不存在的 `frontend/package-lock.json` 引用，`npm ci` 改为 `npm install`，消除 lockfile 缺失报错。
- Expanded GitHub Actions 触发策略：新增 `push branches: master` 与 `pull_request` 触发器，每次代码提交自动执行前端构建与 Windows 打包验证。
- Guarded `create-release` job with `if: startsWith(github.ref, 'refs/tags/v')`，确保普通 push 不触发 Release 发布。

**Engineering Persistence**
- Centralized `git-manager` 技能文件：写入仓库注册表（URL / 账号 / 本地路径）、PowerShell 分号规则、exit code 误报说明及版本历史表格，永久固化。
- Added `src/version.py`、`CHANGELOG.md`、`README.md`、`.gitignore` 项目基础设施文件。

---

## v0.1.0 — 2026-04-02

### 🚀 初始版本发布（三阶段 MVP 基础代码架构）

**Core Engine**
- Architected `DocxParser`：通过直接解析 `<w:rFonts>` XML 节点精准提取中文 (`eastAsia`) 与英文 (`ascii`) 字体，支持样式继承链的向上 Fallback。
- Architected `Validator`：分层规则匹配（标题级别/正文段落/图表注释），支持 Unicode 分块检测中英文字号、粗细和首行缩进多维度校验。
- Implemented `RuleLoader`：YAML规则文件热重载，支持 `import_from_yaml` / `import_from_json` / `export_as_yaml` / `export_as_json`，含 Schema 完整性校验防御。
- Implemented `AppLogger`：统一双轨日志（控制台 + 旋转文件），结构化 JSONL 格式供 API 查询，支持级别过滤与手动清空。

**REST API (FastAPI)**
- `POST /api/check`：异步接收 docx，驱动全量三层校验引擎，返回结构化问题清单。
- `POST /api/export/annotated`：将校验结果以 Word 红字批注形式注入副本文档并返回下载流。
- `GET/POST /api/rules/*`：规则摘要查看、YAML/JSON 双格式导入导出、在线热重载。
- `GET/DELETE /api/logs`：结构化日志查询与清空端点。

**Frontend (Vue 3 + Vite + Vanilla CSS)**
- 三栏式侧边栏 PC 客户端（格式校验 / 规则管理 / 系统日志）。
- 毛玻璃 Glassmorphism 暗系设计系统，含微动画拖拽区、流式加载指示器。
- 统计卡片行（严重错误/警告/总计/校验时间），问题卡片左色条分类显示。
- 一键复制纯文本报告（Clipboard API）与导出批注 Docx 文件下载。
- 规则管理面板：摘要卡片展示 + 导出/导入/热重载操作。
- 系统日志面板：级别过滤、刷新、清空，Toast 全局通知反馈。

**Config & Distribution**
- `src/config/rules.yaml`：标注了中英文字体、字号、行距、首行缩进、段间距的完整规则基准。
- `requirements.txt`：完整 Python 依赖声明（fastapi, uvicorn, python-docx, PyYAML, pywebview）。
- `pywebview` + `PyInstaller` 分发策略：最终打包为单一 `.exe` 桌面客户端。
