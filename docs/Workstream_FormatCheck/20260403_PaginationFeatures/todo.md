# Word 高级排版特性检测 (v1.2.0) [COMPLETED]

## 背景 (Context)
当前引擎完全忽略学术论文中极度重要的"流式排版控制"：孤行控制、与下段同页、隐藏文字与修订模式。这些是学校审核常见的高级格式要求。

## 策略 (Strategy)
扩展解析器提取 `paragraph_format` 的分页属性；在 Validator 中新增相应的校验规则；在解析前清理修订模式内容防止误报。

## 待办清单 (Checklist)

### Phase 1: 解析器扩展 [DONE]
- [x] 提取 `para.paragraph_format.widow_control` 孤行控制属性
- [x] 提取 `para.paragraph_format.keep_with_next` 与下段同页属性
- [x] 提取 `para.paragraph_format.keep_together` 段落内不分页属性
- [x] 将以上属性加入 `ParagraphNode` 模型字段与 ADM

### Phase 2: 修订模式清理 [DONE]
- [x] 实现 `RevisionCleaner.accept_all_revisions` (基于 lxml.etree.XPath)
- [x] 在解析前屏蔽 `w:del` 内容并平铺 `w:ins` 内容
- [x] 过滤隐藏文字 `run.font.hidden`
- [x] 在 `DocxParser` 中集成 RevisionCleaner。

### Phase 3: 新增校验规则 [DONE]
- [x] `rules.yaml` 新增 `pagination` 规则区块
- [x] 实现 `PaginationPlugin` (E009/E010)
- [x] 标题必须开启 `keep_with_next`，正文应开启 `widow_control`
- [x] 实现 `PaginationPlugin` 的 Patch 建议生成

### Phase 4: 验证 [DONE]
- [x] 编写 `tests/integration/test_pagination_e2e.py`
- [x] 验证通过：检测输出包含预期代码且消息准确
- [x] 代码已合并并准备发布 v1.2.0

## 归档 (Archive)
任务执行日期：2026-04-03
执行人：Antigravity
状态：已完成并验证
