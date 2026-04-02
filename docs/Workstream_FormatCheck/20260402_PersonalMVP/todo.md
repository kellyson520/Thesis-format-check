# 个人版MVP：本地论文格式校验工具 (Personal MVP: Local Thesis Format Checker)

## 背景 (Context)
依据《论文格式智能校验系统技术方案》，为个人使用场景建立精简版 MVP。原方案的微服务、消息队列及分布式存储体系针对高并发商业化环境，而本地个人使用需要轻便、快速的开箱即用体验。核心目标是剔除服务端架构，聚焦于本地 `.docx` 文件的规则校验与直接修正反馈。

## 策略 (Strategy)
以本地 Python 命令行工具或轻便 GUI (如 PyQt / Streamlit) 为主要载体，直接通过 `python-docx` 加载并解析文档内容。由于个人使用无需动态配额设定或多用户管理，规则集固化为本地配置文件（`JSON` 格式或 `YAML` 格式），输出直接体现为控制台日志或原文档批注克隆。

## 待办清单 (Checklist)

### Phase 1: 基础设施与模版设定 (Setup)
- [x] 确定技术栈，搭建本地虚拟环境（如 `venv` / `poetry`）。
- [x] 初始化后端：搭建 FastAPI 本地服务基础。
- [x] 初始化前端：搭建 Vite + Vue 3 基础工程（引入 Glassmorphism 设计系统）。
- [x] 定义配置体系：编写针对本科/硕士论文常用的个人格式约定 `rules.yaml`（含标题各级字号、段落字体、行距等）。

### Phase 2: 文件解析与基础校验 (Core Engine Pipeline)
- [x] 引入 `python-docx` 解析文本流（处理 `paragraphs`, `runs`）。
- [x] 建立规则读取器 (`RuleLoader`)：将 `yaml` 规则结构化加载到内存字典。
- [x] 构建校验引擎 (`Validator`)：以精准比对（语法层）为重点，检查“中文字体”、“英文字体”、“字号”三大核心维度规则冲突。

### Phase 3: GUI 构建与集成 (Premium PC UI Integration)
- [x] 渲染层搭建：编写极其精美、含有拖拽区、毛玻璃动画及暗黑模式支持的 Vue 3 组件。
- [x] API 交互：与 FastAPI 结合，实现文件的本地流式上传、分析和批注响应传输。
- [x] 打包分发：结合 `pywebview` 和 `PyInstaller` 将整个纯 Vue 前端、FastAPI 后端合并成单一的独立桌面 `.exe` 执行文件。
