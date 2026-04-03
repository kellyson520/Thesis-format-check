# Word 高级排版特性检测

## 背景 (Context)
当前引擎完全忽略学术论文中极度重要的"流式排版控制"：孤行控制、与下段同页、隐藏文字与修订模式。这些是学校审核常见的高级格式要求。

## 策略 (Strategy)
扩展解析器提取 `paragraph_format` 的分页属性；在 Validator 中新增相应的校验规则；在解析前清理修订模式内容防止误报。

## 待办清单 (Checklist)

### Phase 1: 解析器扩展
- [ ] 提取 `para.paragraph_format.widow_control` 孤行控制属性
- [ ] 提取 `para.paragraph_format.keep_with_next` 与下段同页属性
- [ ] 提取 `para.paragraph_format.keep_together` 段落内不分页属性
- [ ] 将以上属性加入 `parsed_data` 字典

### Phase 2: 修订模式清理
- [ ] 研究 `python-docx` 对 `w:del` / `w:ins` 修订标记的处理方式
- [ ] 实现 `RevisionCleaner.filter(doc) -> Document` 在解析前屏蔽修订内容
- [ ] 处理隐藏文字 `run.font.hidden = True` 的过滤
- [ ] 编写测试：含修订记录的文档不产生误报

### Phase 3: 新增校验规则
- [ ] `rules.yaml` 新增 `pagination` 规则区块
- [ ] 实现 `PaginationValidator`：标题必须开启 `keep_with_next`
- [ ] 实现孤行控制校验：正文段落应开启 `widow_control`
- [ ] 实现 `PaginationValidator` 的单元测试

### Phase 4: 验证
- [ ] 使用包含标题孤页、修订记录的测试文档验证准确率
- [ ] 更新 `rules.yaml` 文档注释
