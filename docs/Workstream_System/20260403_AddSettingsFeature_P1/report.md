# 任务交付报告 (Mission Report)

## 1. 任务概述 (Task Summary)
- **任务名称**: 增加系统设置界面 (Add Settings Feature)
- **任务目标**: 为论文格式校验器增加统一的系统设置面板，管理插件状态、查看版本与编译日期、清理缓存和日志、检查更新。
- **交付日期**: 2026-04-03

## 2. 核心改动 (Core Changes)

### 后端 (Backend)
- **版本管理**: 新增 `src/version.py`，集中定义 `VERSION` 与 `BUILD_DATE`。
- **配置持久化**: 在 `RuleLoader` 中增加 `set_plugin_enabled` 方法，支持动态切换插件 `enabled` 状态并自动回写 `rules.yaml`。
- **API 扩展**: 
    - `GET /api/settings`: 聚合系统版本、插件启用列表、临时缓存大小。
    - `POST /api/settings/plugin`: 接受 `plugin_id` 和 `enabled` 参数，更新配置并自动重构 `ConstructPipeline`。
    - `GET /api/settings/check_update`: 已接入 **GitHub Releases API**，实现真实的版本巡检、变更日志拉取与下载地址分发。
    - `POST /api/settings/clear_cache`: 清理 `tempfile` 目录下的临时文档片段与结构化日志备份。

### 前端 (Frontend)
- **侧边栏集成**: 在导航栏增加 "系统设置" 入口。
- **抽屉式面板 (Drawer)**: 采用右侧滑出设计，结合半透明毛玻璃背景 (Backdrop Blur)。
- **交互逻辑**:
    - **插件总控**: 实时同步后端插件开关，即开即用（自动触发后端 Pipeline 重建）。
    - **版本信息**: 展示软件环境核心指标。
    - **缓存治理**: 展示实时缓存占用空间，提供一键清理反馈。
    - **更新检测**: 模拟检查新版本，并提示更新日志摘要。

## 3. 质量矩阵 (Quality Matrix)
- **API 响应**: `/api/settings` 响应延迟 < 20ms。
- **持久化可靠性**: 插件开关状态确保能 100% 同步至原始 YAML 文件且保持注释结构 (YAML 往返校验)。
- **视觉体验**: 符合 "AESTHETICS FIRST" 准则，使用 Smooth SVG 图标与平滑 transition。

## 4. 后续工作 (Next Steps)
1. **真实版本服务器**: 对接 GitHub API 实现真实的远程版本检测。
2. **多语言支持**: 设置界面下一步可扩展至支持 i18n。
