# 论文格式检查引擎 - 架构规范手册 (Standard Whitepaper)

## 🏗️ 1. DDD 分层架构模型 (Layering Model)

遵循 **Clean Architecture** 原则，核心逻辑位于内环，外部实现位于外环。**依赖箭头必须始终由外向内**。

### 📁 目录结构定义
```text
src/
├── domain/            # 【内环】领域层：零外部库依赖，定义核心实体与契约
│   ├── models/        # 抽象文档模型 (ADM: ParagraphNode, Issue)
│   └── interfaces/    # 抽象解析器(IParser)与插件接口(BaseRulePlugin)
├── use_cases/         # 【中环】应用逻辑层：协调领域模型，执行校验业务
│   ├── plugins/       # 分支校验规则：单一职责插件(Font, Spacing, Hierarchy...)
│   ├── pipeline/      # 校验执行引擎：基于 Generator 的流式进度上报
│   └── rule_config.py # Pydantic 强类型规则管理
└── infrastructure/    # 【外环】基础设施层：处理 I/O 与具体库适配
    ├── parsers/       # 具体解析实现：DocxParser (依赖 python-docx)
    ├── reporters/     # 报告生成与自动修复：AnnotatorReporter, DocumentFixer
    └── logger.py      # 日志适配器
```

---

## 🏛️ 2. 核心架构红线 (Red Lines)

1.  **依赖倒置 (DIP)**: `domain/` 与 `use_cases/` 禁止导入任何 `infrastructure/` 中的具体类或装饰器。必须通过 `interfaces/` 进行调用。
2.  **单一职责 (SRP)**:
    *   **Parser** 仅负责将 Word 对象翻译为 ADM 节点，不得包含校验逻辑。
    *   **Plugin** 仅负责特定维度（如字体）的校验，不得涉及 I/O。
3.  **内环纯净性**: `domain/` 目录严禁出现 `docx`, `fastapi`, `uvicorn` 等库的导入。
4.  **无状态引擎**: `ValidatorPipeline` 与 `Plugins` 必须是函数式或无状态的，通过输入 `DocumentModel` 吐出 `Issue` 流。

---

## 🛠️ 3. 校验插件开发流程 (Plugin Development)

新增校验规则时，必须遵循以下步骤：
1.  **定义实体**: 在 `domain/models` 中确认是否有该规则所需的特定属性。
2.  **编写插件**: 在 `use_cases/plugins/` 继承 `BaseRulePlugin` 实现 `check()`。
3.  **注册规则**: 在 `use_cases/rule_config.py` 的 Pydantic 模型中添加对应的配置字段。
4.  **性能上报**: 确保插件不阻塞主进程，通过 `ValidatorPipeline` 的生成器机制上报进度。

---

## ✅ 4. 架构审计与验证

*   **静态验证**: 使用根目录下的 `validate_arch.py` 或由 `clean-arch-enforcer` 技能执行静态依赖扫描。
*   **架构审计**: 任何破坏分层的 PR 将通过自动化 Lint (architecture-auditor) 拦截。

---
> 本规范由 **Antigravity AI** 架构引擎于 2026.04.03 初版修订。
