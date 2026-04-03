# 论文格式智能校验系统 - 阶段四进化 (Phase 4 Evolution)

## 背景 (Context)
在上一个版本个人 MVP (20260402_PersonalMVP) 中，我们成功实现了文件的本地流式解析、三级格式校验基础规则以及直观美观的 GUI 和批注式返回功能。
为进一步提升使用体验和核心价值，我们将启动 Phase 4 工作流，全面覆盖“一键修复修改”、“多维度深度校验”、“可视化规则开发”及“核心引擎性能升级”等进阶功能。

## 策略 (Strategy)
以增量迭代的方式，分阶段实现各个功能点，保持应用稳定性。优先实现一键 Auto-Fix 修正式校验以形成业务闭环，再扩展更多深层规则，接着优化交互及打包链路。

## 待办清单 (Checklist)

### Phase 1: 核心进化 - "一键修复"机制 (Auto-Correction)
- [x] 后端支持: 扩展 `Validator` 或新建 `Fixer` 模块，直接在解析内存态中覆盖错乱字号、字体等属性。
- [x] 新增接口: `POST /api/fix`，接收 DOCX 返回完全修改后无错的新版下载流，无需用户手动改。
- [x] 前端联动: 渲染层增加“一键全部修复”按钮并挂载 API 响应。

### Phase 2: 深度规则体系 (Advanced Validation)
- [x] 规则扩展: `rules.yaml` 补充页面级别规则（页眉页脚、页边距等）。
- [x] 功能新增: 校验机制支持表格标题与图片题注的位置和编号连续性验证。
- [x] 国标检测: `GB/T 7714` 参考文献正则校验集成。
- [x] 结构校验: 侦测多层标题降级错误 (如 H1 后直接跟 H3)。

### Phase 3: GUI 工程深化 - 可视化编辑器 (Visual Rule Editor)
- [x] 前端页面: 增加 Vue 表单级规则配置器面板 (Settings Configurator)。
- [x] API 打通: 通过 JSON/表单提交直接覆写后端规则文件并进行内存热重载。
- [x] 交互打磨: 去除必须改文件的体验掣肘。

### Phase 4: 性能与工程化兜底 (Performance & QA)
- [x] SSE 流式上报: 实现前后端实时进度条通信（替代 WebSocket 以获得更好的稳定性与 Zero-Disk 适配性）。
- [x] 单元及集成测试: 在 `tests/` 目录下提供自动化 TestCase（覆盖 Fixer 与 SSE 链路）。
- [x] 包管理及交叉编译: 对 macOS 和 Linux 添加 PyInstaller 处理，扩展云端的 release Actions 范畴（已于 CI 代码中预置）。
