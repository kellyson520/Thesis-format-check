# 插件化校验器架构

## 背景 (Context)
当前 `Validator.validate` 是一个巨大单体函数，违反开闭原则（OCP）。随着不同学校格式要求增加，该函数会膨胀到无法维护。需要引入策略模式与插件化架构。

## 策略 (Strategy)
将每个校验点抽象为独立类（Strategy），在初始化时根据 `rules.yaml` 动态加载校验器链（Validator Chain）。新增规则只需新增一个文件，无需修改核心引擎。

## 待办清单 (Checklist)

### Phase 1: 插件基类设计
- [ ] 定义 `BaseValidator` 抽象基类（ABC）
  ```python
  class BaseValidator(ABC):
      @abstractmethod
      def validate(self, element: dict, context: ValidationContext) -> list[Issue]:
          ...
  ```
- [ ] 定义 `ValidationContext` 上下文对象（当前区域、章节号、前一元素等）
- [ ] 定义 `Issue` 标准数据类（含 severity、rule_id、patch_hint 字段）

### Phase 2: 核心插件迁移
- [ ] 实现 `FontValidator(BaseValidator)` - 字体/字号/字重校验
- [ ] 实现 `IndentValidator(BaseValidator)` - 首行缩进/段落间距校验
- [ ] 实现 `HierarchyValidator(BaseValidator)` - 标题层级连续性校验
- [ ] 实现 `CaptionValidator(BaseValidator)` - 图表题注序号校验
- [ ] 实现 `ReferenceValidator(BaseValidator)` - 参考文献格式校验

### Phase 3: 插件加载机制
- [ ] 实现 `PluginLoader` 类，根据 `rules.yaml` 的 `enabled_checks` 动态加载插件
- [ ] 实现 `ValidatorChain.run(elements, context) -> list[Issue]` 编排执行
- [ ] 确保插件顺序可配置（某些校验依赖前置校验结果）

### Phase 4: 验证与文档
- [ ] 编写所有新插件的单元测试
- [ ] 编写插件开发指南 `docs/plugin_development_guide.md`
- [ ] 运行性能对比：链式执行 vs 原始单体函数
