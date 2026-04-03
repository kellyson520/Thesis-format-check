# 校验引擎深度重构与学术化能力提升 (Deep Validation Engine)

## 🎯 1. 目标 (Objectives)
将校验引擎从「属性匹配」提升至「语义感知」级别，重点解决公式、嵌套表格、参考文献关联性等高阶排版痛点。

## 🏗️ 2. 技术策略 (Technical Strategy)
1. **高保真解析**: 接入 `oMath` (Office Math) 与 `w:tbl` (Structure Table) 深度树遍历。
2. **状态机扩展**: 引入 `ContextCollector` 收集全文引文/图表 ID 映射。
3. **视觉特征聚类**: 引入基于视觉属性而非样式名的 Outlier 检测算法。
4. **自动化 UI**: 基于 Pydantic Schema 自动渲染前端配置面板。

## 📋 3. 待办事项 (Checklist)

### Phase 1: 复杂结构解析增强 (Structure Parsing)
- [ ] **公式支持**: 在 `DocxParser` 中支持 `w:math` 元素文本提取与字体校验。
- [ ] **表格语义化**: 解析表格的合并单元格（vMerge/gridSpan）信息，区分表头与表体。
- [ ] **分节符深度解析**: 支持不同 Section 的页码格式（Roman vs Arabic）独立校验。

### Phase 2: 语义一致性关联 (Semantic Consistency)
- [ ] **引文链路检查**: 校验正文 `[n]` 引用与文末参考文献表的编号完整性与排序。
- [ ] **图表位置约束**: 实现“图下表上”位置限制检查插件。
- [ ] **交叉引用有效性**: 检查文档内的 Hyperlinks 与 Bookmark 引用是否断链。

### Phase 3: 智能化与自动化 (Intelligence & Automation)
- [ ] **视觉特征聚类**: 实现基于字体/字号/居中特征的一级标题“伪样式”识别。
- [ ] **Schema-to-UI**: 重构 `App.vue` 设置页，通过后端 JSON Schema 动态渲染插件开关。
- [ ] **样本逆向生成**: 实现根据「标杆文档」自动推导 `rules.yaml` 参数的功能。

### Phase 4: 性能与工程化 (Performance & Engineering)
- [ ] **增量校验 (Incremental)**：实现基于段落指纹（Fingerprint）的局部重计算。
- [ ] **可视化 Diff**: 实现修复前后的格式差异对比预览模式。
- [ ] **CI 规则回归**: 建立一套「黄金范文」测试库，防止插件升级导致精度退化。

---
> 更新至：2026-04-03
