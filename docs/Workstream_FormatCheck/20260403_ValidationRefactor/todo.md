# Validation Engine Refactoring ( Phase 1 & 2 )

## 背景 (Context)
解决当前论文格式校验系统中核心规则“写而不校”（如段前段后间距、行距缺失校验）的漏洞，提升字体与字重的容错能力（处理None继承态），并在修复校验引擎的基础上，打通真正的 Fixer（高亮与一键修复）闭环。

## 待办清单 (Checklist)

### Phase 1: 规则契约对齐与容错兜底 (Validation Engine)
- [x] 在 `validator.py` 中全量实现对 `space_before`、`space_after` 的提取与数值比对。
- [x] 在 `validator.py` 中实现对 `line_spacing`（固定值或倍数）的校验。
- [x] 修复 Bold（字重）校验逻辑，正确处理局部加粗时 Word API 返回 `None` 的继承状态。
- [x] 优化特殊字符的字体校验跳过逻辑，减少常规环境差异引起的误报。

### Phase 2: 反馈闭环打通 (Feedback Loop)
- [x] 构建校验错误对象与 Document 具体 Run/Paragraph 的强绑定（新增 `para_index` 字段）。
- [x] 为全部 13 类错误注入 `issue_code` 分类码（E001~E008、W001~W005），供前端过滤与 Fixer 使用。
- [x] 同步修复 `fixer.py` 的 ASCII 字符检测逻辑，与 validator 保持一致，避免符号/标点触发误修复。
- [ ] (可选) 使用 `watchdog` 实现 `rules.yaml` 的热更新机制。
