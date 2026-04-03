# Validator-Fixer 闭环打通

## 背景 (Context)
MVP 阶段"查而不改"是最大遗憾。Validator 发现错误仅生成 Issue，无法直接修复文档。需要建立 Patch Object 标准和 Fixer/Reporter 类，实现"一键查改结合"。

## 策略 (Strategy)
Validator 在生成 `issue` 时同时生成标准化 `Patch Object`；实现 `Fixer` 类接收 Patches 并调用 `python-docx` 覆写属性；最后 `doc.save('checked.docx')` 输出。

## 待办清单 (Checklist)

### Phase 1: Patch Object 标准化
- [ ] 定义 `Patch` 数据类（`dataclass` 或 `TypedDict`）
  ```python
  @dataclass
  class Patch:
      action: str        # "set_font" | "set_size" | "set_indent" | ...
      target_id: str     # paragraph/run 的唯一标识符
      attribute: str     # 要修改的属性名
      value: Any         # 目标值
      issue_ref: str     # 关联的 Issue ID
  ```
- [ ] 为每个 Validator 规则实现对应的 Patch 生成逻辑
- [ ] 在 `parsed_data` 中为每个 para/run 添加唯一 `id` 字段
- [ ] 编写单元测试 `tests/unit/engine/test_patch_generation.py`

### Phase 2: Fixer 类实现
- [ ] 实现 `Fixer` 类接收 `list[Patch]` 和原始 `Document` 对象
- [ ] 实现 `apply(patches) -> Document` 方法
- [ ] 覆盖优先级最高的 action：`set_font`, `set_size`, `set_bold`, `set_indent`
- [ ] 实现 `doc.save()` 输出到用户指定路径（Zero-Disk IO：仅在用户导出时落盘）

### Phase 3: Reporter 类（可选增强）
- [ ] 实现 `Reporter` 类，生成 HTML/PDF 格式的详细差异报告
- [ ] 报告格式：原文 vs 修正后，标注每处修改的规则依据

### Phase 4: API 集成
- [ ] 在 FastAPI 路由中新增 `/api/fix` 端点
- [ ] 接收 `job_id`，返回修复后的文件流（`StreamingResponse`）
- [ ] 编写 API 集成测试
