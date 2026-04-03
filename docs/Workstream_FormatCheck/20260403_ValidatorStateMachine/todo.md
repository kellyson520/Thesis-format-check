# Validator 状态机重构

## 背景 (Context)
当前 `Validator.validate` 是一个无状态的线性 `for` 循环，导致"参考文献状态泄露"（进入参考文献区域后永不退出）和"图表题注正则灾难"（跨章节序号计数错误）。需要引入状态机感知文档上下文结构。

## 策略 (Strategy)
定义文档区域枚举 `DocRegion`，实现状态进出机制；引入章节上下文感知的正则校验；将硬编码样式名改为 `rules.yaml` 的 `mapping` 驱动。

## 待办清单 (Checklist)

### Phase 1: 文档区域状态机
- [ ] 定义 `DocRegion` 枚举 (`COVER`, `ABSTRACT`, `TOC`, `BODY`, `REFERENCES`, `APPENDIX`)
- [ ] 实现状态转移逻辑：遇"参考文献"标题 → `REFERENCES`；遇下一个一级标题 → 退出
- [ ] 在 Validator 中注入 `self.current_region` 状态属性
- [ ] 编写状态机单元测试 `tests/unit/engine/test_validator_state_machine.py`

### Phase 2: 上下文感知校验
- [ ] 实现章节计数器 `ChapterCounter`，跟踪当前所在章节号
- [ ] 图表题注校验改为：先获取当前章节号，再在该章节内校验序号
- [ ] 跨章时重置图表序号计数器
- [ ] 编写题注序号校验的单元测试

### Phase 3: 样式映射解耦
- [ ] 在 `rules.yaml` 中新增 `style_mapping` 区域（`"heading 1" → level_1`）
- [ ] 实现 `StyleMapper` 类，加载映射并提供 `normalize(style_name) → StyleEnum` 方法
- [ ] 替换 Validator 中所有 `style_name.startswith("Heading 1")` 类型的硬编码
- [ ] 验证：自定义样式名通过 mapping 正确识别

### Phase 4: 集成验证
- [ ] 在已有测试文档上运行重构后的 Validator
- [ ] 确认"参考文献状态泄露"Bug已消除
- [ ] 确认跨章节图表序号误报已消除
