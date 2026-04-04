# 项目全景概览 (Project Process)

## 进行中任务

| 任务标识 | 任务描述 | 开始日期 | 结束日期 | 进度 | 传送门 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 20260404_Fix_Dependency_Missing | 紧急修复：补齐 requirements.txt 中缺失的 httpx 依赖 | 2026-04-04 | 2026-04-04 | 100% | [📂 查看](./Workstream_System/20260404_Fix_Dependency_Missing/) |
| 20260404_Ship_v1.2.4 | 打包到 GitHub 并发布 v1.2.4：完成引擎稳定性修复与在线更新上线 | 2026-04-04 | 2026-04-04 | 100% | [📂 查看](./Workstream_System/20260404_Ship_v1.2.4/) |
| 20260404_RealGitHubUpdateCheck | 实现在线 GitHub 检查更新机制：从随机模拟升级为真实 API 比对 | 2026-04-04 | 2026-04-04 | 100% | [📂 查看](./Workstream_FormatCheck/20260404_RealGitHubUpdateCheck/) |
| 20260404_FixEngineDisappearing | 修复引擎运行中状态消失问题：后端稳定性与 WebSocket 中断处理 | 2026-04-04 | 2026-04-04 | 100% | [📂 查看](./Workstream_FormatCheck/20260404_FixEngineDisappearing/) |
| 20260404_DeepValidationEngine_P1 | 校验引擎深度重构：公式/表格语义、视觉特征聚类与自动 UI | 2026-04-03 | - | 0% | [📂 查看](./Workstream_FormatCheck/20260404_DeepValidationEngine_P1/) |
| 20260403_AlgorithmPrecision | 算法精度提升：UNICODE 字符集探测与 UnitConverter 物理换算 | 2026-04-03 | 2026-04-03 | 100% | [📂 查看](./Workstream_FormatCheck/20260403_AlgorithmPrecision/) |
| 20260403_PaginationFeatures | Word 高级排版特性检测：孤行控制/与下段同页 + 修订模式清理 | 2026-04-03 | 2026-04-03 | 100% | [📂 查看](./Workstream_FormatCheck/20260403_PaginationFeatures/) |
| 20260403_SettingsUnifiedUI_P0 | 系统设置界面统一：侧边栏主 Tab 整合与全插件显式开关中心 | 2026-04-03 | 2026-04-03 | 100% | [📂 查看](./Workstream_Frontend/20260403_SettingsUnifiedUI_P0/) |


## 已完成任务

| 任务标识 | 任务描述 | 开始日期 | 结束日期 | 进度 | 传送门 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 20260403_FixRuleManagementCrash_P0 | 修复规则管理功能：解决前端崩溃（页面纯色）与后端日志缺失问题 | 2026-04-03 | 2026-04-03 | 100% | [📂 查看](./Workstream_Frontend/20260403_FixRuleManagementCrash_P0/) |
| 20260404_ImproveExceptionCapturing | 完善整个项目的异常捕获，建立全局异常处理机制并拒绝静默错误 | 2026-04-04 | 2026-04-04 | 100% | [📂 查看](./Workstream_System/20260404_Improve_Exception_Capturing/) |
| 20260403_PluginDrivenConfig_P1 | 插件驱动配置系统重构：去中心化 Pydantic 模型 & 声明式配置声明 | 2026-04-03 | 2026-04-03 | 100% | [📂 查看](./Workstream_Standardization/20260403_PluginDrivenConfig_P1/) |
| 20260403_AddReDetectButton_P1 | 增加重新检测功能按钮：支持已上传文件一键重校验 | 2026-04-03 | 2026-04-03 | 100% | [📂 查看](./Workstream_FormatCheck/20260403_AddReDetectButton_P1/) |
| 20260403_SetupStandardDirectory | 标准化目录初始化：整合架构、插件及开发规范 | 2026-04-03 | 2026-04-03 | 100% | [📂 查看](./Workstream_Standardization/20260403_SetupStandardDirectory_P1/) |
| 20260403_FixVueBuildError | 修复 Vue 编译错误：补齐 App.vue 缺失的 script 启动标签 | 2026-04-03 | 2026-04-03 | 100% | [📂 查看](./Workstream_Frontend/20260403_FixVueBuildError_P1/) |
| 20260402_PersonalMVP | 针对个人使用精简开发的本地版论文格式校验系统MVP方案 | 2026-04-02 | 2026-04-02 | 100% | [📂 查看](./Workstream_FormatCheck/20260402_PersonalMVP/) |
| 20260403_DocxParserRefactor | 重构DocxParser：接入StyleResolver样式树、表格支持与单位换算解开 | 2026-04-03 | 2026-04-03 | 100% | [📂 查看](./Workstream_FormatCheck/20260403_DocxParserRefactor/) |
| 20260403_ValidatorStateMachine | 引入文档区域状态机：实现参考文献进出边逻辑与章内题注计数 | 2026-04-03 | 2026-04-03 | 100% | [📂 查看](./Workstream_FormatCheck/20260403_ValidatorStateMachine/) |
| 20260403_FixerPipeline | 打通Validator-Fixer闭环：实现Patch对象标准化与多插件修复建议支持 | 2026-04-03 | 2026-04-03 | 100% | [📂 查看](./Workstream_FormatCheck/20260403_FixerPipeline/) |
| 20260403_IPCProgress | 实效进度条与SSE流：后端逐段 yield + 前端 ReadableStream 渲染 | 2026-04-03 | 2026-04-03 | 100% | [📂 查看](./Workstream_FormatCheck/20260403_IPCProgress/) |
| 20260403_LocalAPISecurity | 本地接口加固：动态 Token 鉴权中间件 + 随机可用端口 + URI 参数注入 UI | 2026-04-03 | 2026-04-03 | 100% | [📂 查看](./Workstream_FormatCheck/20260403_LocalAPISecurity/) |
| 20260403_PluginArchitecture | 插件模式解耦：引入 _init_para_plugins 注册表 + Section 级支持 | 2026-04-03 | 2026-04-03 | 100% | [📂 查看](./Workstream_FormatCheck/20260403_PluginArchitecture/) |
| 20260403_TempFileGC | 垃圾回收与存储优化：全链路 Zero-Disk IO 内存流实现，已废弃所有 tempfile 及落盘逻辑 | 2026-04-03 | 2026-04-03 | 100% | [📂 查看](./Workstream_FormatCheck/20260403_TempFileGC/) |
| 20260403_CopyrightGenerator | 高级工具开发：软著源码前后 3000 行提取算法实现与一键提取 API | 2026-04-03 | 2026-04-03 | 100% | [📂 查看](./Workstream_FormatCheck/20260403_CopyrightGenerator/) |
| 20260403_RemoveCopyrightTools_P1 | 移除软著生成相关代码：API 接口及 CopyrightGenerator 业务逻辑 | 2026-04-03 | 2026-04-03 | 100% | [📂 查看](./Workstream_System/20260403_RemoveCopyrightTools_P1/) |

| 20260403_PerformanceOptimization | 长文档性能优化：正则预编译 + Generator流式校验（含节流机制） + 异常安全封装 | 2026-04-03 | 2026-04-03 | 100% | [📂 查看](./Workstream_FormatCheck/20260403_PerformanceOptimization/) |
