# Changelog

## v1.2.7 — 2026-04-04

### 🚀 EXE 本地自动保存与 Zero-Disk 闭环 (EXE Auto-Save & Zero-Disk Finalized)

**EXE 本地体验优化 (EXE Mode Experience)**
- **本地自动存盘**：实现了在导出批注文件和修复文件时，自动在 `.exe` 同级目录的 `output/` 文件夹下生成物理备份。这解决了打包环境下由于浏览器下载目录不明确导致的“找不到文件”问题。
- **路径自适应**：在 `frozen` 模式下智能识别当前运行目录。

**全链路内存流 (True Zero-Disk IO)**
- **重构 AnnotationReporter**：彻底支持 `io.BytesIO` 内存流输入，不再需要通过磁盘临时文件传递原始 Docx 数据。
- **接口逻辑收缩**：完全移除了 `src/main.py` 导出逻辑中的 `tempfile.gettempdir()` 模块引用，实现了真正的 Zero-Disk 解析与回报流程。

**稳定性与代码质量 (Stability & Code Quality)**
- **崩溃风险预防**：修复了 `api/fix` 接口在之前的重构中因代码偏移导致的 `out_name` 未定义 `NameError`。
- **清除静默异常**：修复了 `DocxParser` 中残留的一处 `except: pass` 块，确保解析逻辑出现属性缺失时会被 `debug` 日志捕获而不再“无声消失”。
- **架构瘦身**：移除冗余的 `DocumentFixer` 类，将格式修复逻辑完全统一到 `DocxFixer` 架构中。

## v1.2.6 — 2026-04-04

### 🛡️ 全局异常处理与稳定性加固 (Global Exception Handling & Stability)

**异常拦截与反馈 (Global Sanitization)**
- **全局拦截拦截器**：在 `src/main.py` 中实现了 `setup_exception_handlers`，捕获所有未捕获的 `Exception` 与 `HTTPException`，将 500 错误转化为结构化 JSON 反馈，拒绝前端由于后端崩溃导致的白屏。
- **抗灾故障隔离**：在 `ValidatorPipeline` 的段落校验循环中增加了分片 `try-except`，确保单个插件的崩溃仅会记录错误日志，不再导致整个文档校验流程中断。
- **清除静默错误**：彻底清理了全项目中所有的 `except: pass` 块，确保所有系统异常均有迹可循。

**核心组件性能与鲁棒性 (Core Robustness)**
- **日志系统加固**：升级 `AppLogger` 支持 `exc_info` 全量堆栈记录，并在日志文件不可写时具备自动退避至 `sys.stderr` 的自愈能力。
- **测试环境隔离**：修正了 `test_p0_refactor.py` 和 `test_p1_fixer.py` 中由于全局 `sys.modules` 污染导致的集成测试 Mock 泄露问题，确保测试套件运行的独立性。


## v1.2.5 — 2026-04-04

### 🚑 依赖补丁 (Dependency Hotfix)
- **修复依赖缺失**：补齐了 `requirements.txt` 中缺失的 `httpx` 依赖，解决了 v1.2.4 在纯净环境下由于缺少 `httpx` 导致无法启动的问题。

## v1.2.4 — 2026-04-04

### 🛠️ 校验引擎稳定性与 SSE 状态修复 (Engine Stability & SSE State Fixes)

**状态流转修复 (SSE State Recovery)**
- **修复状态消失 BUG**：解决了 `ValidatorPipeline` 流式返回的事件字段 (`type` vs `event_type`) 与前端不匹配的问题。
- **对齐完成信号**：将后端 `complete` 事件重命名为前端预期的 `done`，确保校验完成后“引擎运行中”状态能正确切换至结果面板。
- **流式 Issue 结构补全**：为流式返回的 Issue 对象补齐了 `type` (severity) 和 `fixable` 字段，确保实时渲染的卡片样式正确且显示修复建议。

**传输编码固化 (Encoding Stability)**
- **文件名编码修复**：解决了在导出带中文文件名的 docx 时由于 `attachment; filename` 导致的 `UnicodeEncodeError` (ordinal not in range(128))。统一使用 `RFC 5987 (filename*)` 标准进行 URL 编码传输。

## v1.2.3 — 2026-04-03

### 🔧 规则管理中心稳定性修复 (Rule Management Stability Fix)

**后端接口补全 (API Integrity)**
- **修复 RuleLoader 缺失方法**：补足了 `import_from_json` 方法，解决了可视化编辑器无法正常保存规则的 BUG。
- **RuleConfig 属性鲁棒化**：通过显式实例默认值（Explicit Instance Defaults）修复了某些环境下缺省 `font` 属性导致的校验中断。

**渲染与可观测性 (UI & Observability)**
- **渲染容错化**：修复了前端加载摘要时的 `TypeError`。
- **配置审计增强**：增强了配置接口的日志记录能力。

## v1.2.1 — 2026-04-03

### 🔧 稳定性增强与架构固化 (Stability & Architecture Fixes)

**核心循环引用修复 (Circular Import Fix)**
- **加载链路重构**：通过 `TYPE_CHECKING` 块与字符串延迟引用彻底解决了 `rule_config` 在动态构建模型时由于导入具体插件而引发的循环依赖（ImportError）。
- **属性访问鲁棒化**：确保插件在 `__init__` 和 `check` 阶段即使在部分初始化状态下也能通过传入的 `config` 实例正常工作。

**插件系统小计 (Plugin System Hygiene)**
- **页边距插件加固**：补齐了 `PageMarginPlugin` 中缺失的 `RuleConfig` 类型标注，消除了静态分析告警。

## v1.2.0 — 2026-04-03

### 📑 高级排版特性、系统设置与 UI 大革新 (Pagination & System Control)

**系统设置与插件总控 (System Settings & Plugin Control)**
- **插件驱动型配置系统**：彻底解耦 `RuleConfig` 与具体插件逻辑，所有插件通过 `DeclarativeConfigMixin` 显式声明配置模型，支持细粒度的“即开即用”式开关。
- **Settings API 集群**：新增 `/api/settings` 接口，支持获取版本信息、动态切换插件状态、一键清理临时缓存及日志。
- **真实更新巡检**：接入 **GitHub Releases API**，实现真实的版本巡检、变更日志拉取与下载地址分发，支持语义化版本号 (SemVer) 智能对比。

**UI/UX 交互体验重塑 (UI Redesign)**
- **设置抽屉面板 (Settings Drawer)**：引入右侧滑出的“设置中心”，采用半透明磨砂玻璃设计，集成了模块总控开关与系统维护工具。
- **侧边栏导航升级**：增加底部常驻“系统设置”入口，优化了导航项的微动画与激活态视觉反馈。
- **可视化规则编辑**：优化了规则管理页面的 sub-tabs 布局，提升了大批量配置项下的操作效率。

**高级分页排版控制 (Advanced Pagination)**
- **PaginationPlugin 深度感知**：新增 `Widow Control` (孤行控制) 与 `Keep with Next` (与下段同页) 属性的全量校验支持。
- **标题跨页保护**：强制所有符合规范的标题开启“与下段同页”，预防论文排版中常见的“孤立标题”问题。

**修订模式与协作净化 (Revision & Hygiene)**
- **RevisionCleaner 物理剥离**：引入 `lxml.etree.XPath` 在解析前“接受所有修订”，剥离 `w:del` 内容，防止残留修订痕迹干扰校验。
- **隐藏文字过滤**：自动预处理并移除 `run.font.hidden` 标记的内容。

**工程验证 (Stability)**
- **集成验证套件**：交付 `tests/integration/test_pagination_e2e.py`，覆盖了含修订记录、跨页属性异常的边缘场景校验。
- **版本号规范**：规范化 `src/version.py` 格式，支持 SemVer 与 BUILD_DATE 自动注入。


## v1.1.0 — 2026-04-03

### 🛠️ 深度进化：从“校验”到“修复”的跨越 (The Evolution to Fixer-Loop)

**主动修复与闭环 (Fixer-Loop)**
- **Validator-Fixer 闭环**：不仅发现问题，更能解决问题。引入 `Patch` 对象标准化修复指令，实现了字号、字体（含中英文字体）、加粗、间距、缩进的一键自动修复。
- **DocxFixer 物理引擎**：底层通过 XML 命名空间直接改写 Word 结构，解决了 `python-docx` 无法设置中文字体的顽念，并支持段落级排版属性覆盖。
- **一键排版修复 (Auto-Fix)**：前端新增“一键修复”按钮，实现“上传-修复-下载”全自动流水线。

**性能与实时性 (Speed & Streaming)**
- **SSE 实时进度流**：引入 Server-Sent Events (SSE) 协议，后端校验结果“发现即推送”，配合前端 `ReadableStream` 渲染真实百分比进度条，消除了大文档校验的黑盒等待感。
- **Zero-Disk IO 革命**：全链路采用 `io.BytesIO` 内存流处理，彻底移除 `tempfile` 物理落盘，IO 效率显著提升且无临时文件残留隐患。
- **自适应节流 (Throttling)**：优化上报机制，显著降低了超长文档在 SSE 链路上的网络与前端负载。

**安全与隔离 (Security & Isolation)**
- **动态 Token 鉴权**：后端 API 强制校验随机生成的 `X-Token`，确保本地服务仅能被合法的 UI 实例访问，防止局域网端口劫持。
- **随机端口分配**：启动时自动寻找可用空闲端口，彻底解决本地环境下的端口占用冲突。
- **插件化进阶**：ValidatorPipeline 采用插件注册表模式，并扩展了 `ISectionPlugin` 以支持页边距等全局节属性校验。

**高级工具箱 (Advanced Tools)**
- **软著源码提取器**：内置符合申报标准的源码合规提取算法，一键生成合并后的前后各 3000 行申报文本。
- **多校规则库一键切换**：前端支持从多种 YAML 预设模板中快速切换，满足不同院校或期刊的格式差异。

---

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
