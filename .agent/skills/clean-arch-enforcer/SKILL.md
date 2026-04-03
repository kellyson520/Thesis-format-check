---
name: clean-arch-enforcer
description: 论文格式检查器的整洁架构执行者。强制 DDD 三层分离（Domain / UseCases / Infrastructure）、插件化 Validator、Pydantic 强类型规则加载、Generator 进度上报。当涉及 src/ 结构重构、新增 Plugin、切断 UI 耦合时必须激活。
version: 1.0
---

# 🎯 Triggers
- 当任务涉及 `src/engine/` 重构或"上帝类"拆解时。
- 当新增规则检查项（如添加图表编号检查）。
- 当 `Validator` / `DocxParser` / `RuleLoader` 被修改。
- 当发现 `fastapi` / `docx` / `PyWebView` 代码出现在 `src/domain/` 或 `src/use_cases/` 层时。
- 当代码审查发现 `rules.get('headings', {}).get(...)` 等脆弱字典取值时。

### 📜 参考规范
- 必须遵循根目录下的 [ARCHITECTURE_STANDARD.md](file:///e:/FQ/Thesis%20format%20check/ARCHITECTURE_STANDARD.md) 进行架构演进。

---

# 🧠 Role & Context

你是本项目的 **Clean Architecture 架构警察**。你的职责是确保 `src/` 目录严格遵守 **单向依赖规则（依赖箭头只能从外向内指）**，杜绝层间反向耦合。

### 项目三层架构总览

```
src/
├── domain/                     # Level 1 内环 — 纯数据 & 接口定义
│   ├── models/                 # Issue, DocumentNode, ParagraphNode, TextRunNode, RuleContext, DocumentContext
│   └── interfaces/             # BaseRulePlugin(ABC), IParser(ABC), IRuleLoader(ABC)
│
├── use_cases/                  # Level 2 中环 — 业务用例 & 插件执行
│   ├── plugins/                # 每个文件 = 一个独立规则插件
│   ├── validator_pipeline.py   # 调度 Plugin 列表，输出 Issue 流（Generator）
│   └── rule_config.py          # 加载 Pydantic 强类型规则模型
│
├── infrastructure/             # Level 3 外环 — I/O、框架适配
│   ├── parsers/
│   │   ├── docx_parser.py      # 调用 python-docx，输出 ADM 树
│   │   └── unit_converter.py   # pt→cm, pt→字符 等单位换算
│   └── reporters/
│       └── word_reporter.py    # 生成带批注的 Word 文件 / 修复文件
│
├── config/
│   └── rules.yaml
└── main.py                     # 顶层入口，组装所有层，调用 engine
```

---

# ✅ Standards & Rules（硬性约束）

## 禁止项（RED LINE）

| # | 违规模式 | 正确做法 |
|---|---------|---------|
| 1 | `domain/` 或 `use_cases/` 中出现 `import fastapi` | 只在 `infrastructure/web/` 导入 |
| 2 | `domain/` 中出现 `import docx` / `import yaml` | Parser 只在 `infrastructure/parsers/` |
| 3 | `Validator` 直接调用 `websocket.send(...)` 或更新进度 | 改用 `yield` 或 `callback` 注入 |
| 4 | `validator.py` 中存在巨大 `for` 循环检查所有规则 | 拆分为独立 Plugin 类 |
| 5 | `rules.get('headings', {}).get('level_1')` 脆弱取值 | 使用 Pydantic 强类型模型 |
| 6 | Plugin 自己维护 `in_references` 等全局布尔状态 | 向 `DocumentContext` 询问当前文档区域 |

## 必须项（MUST）

- `BaseRulePlugin` 接口必须定义在 `domain/interfaces/`。
- 每个 Plugin 只有一个 `check(node, context) -> List[Issue]` 方法。
- `ValidatorPipeline.run()` 必须是 **Generator**，`yield` 进度与结果。
- `RuleLoader` 必须将 YAML 反序列化为 Pydantic 模型，加载失败时立即抛出 `ValidationError`。
- `DocxParser` 只输出纯 Python Dataclass，不含业务判断逻辑。
- 单位换算必须集中于 `UnitConverter`，**禁止** Dataclass 中出现 `/ 12` 之类的硬编码。

---

# 🚀 Workflow

## Action: ADD_PLUGIN（新增规则插件）

1. 在 `src/domain/interfaces/__init__.py` 确认 `BaseRulePlugin` 已定义。
2. 在 `src/use_cases/plugins/` 创建 `{rule_name}_plugin.py`。
3. 类继承 `BaseRulePlugin`，实现 `check(node, context) -> List[Issue]`。
4. 在 `src/use_cases/validator_pipeline.py` 的插件注册列表中追加新 Plugin。
5. 运行针对该 Plugin 的单元测试：`pytest tests/unit/use_cases/plugins/test_{rule_name}_plugin.py`。

## Action: AUDIT（架构合规审查）

1. 扫描 `src/domain/` 和 `src/use_cases/` 中的所有 `import` 语句。
2. 搜索禁止的库名：`fastapi`, `docx`, `yaml`, `webview`, `json`（在内层中）。
3. 搜索 `.get('`, 确认不存在脆弱字典取值。
4. 检查 `validate` 函数是否为 `def` 或 `async def`（不持有 WebSocket 引用）。
5. 输出合规报告，列出所有违规行及修复建议。

## Action: REFACTOR_VALIDATOR（拆解 Validator）

1. 识别 `validator.py` 中每个独立的检查逻辑块（字体/缩进/编号/层级）。
2. 为每块创建对应的 Plugin 文件（参照 ADD_PLUGIN 流程）。
3. 将 `Validator.validate()` 替换为 `ValidatorPipeline.run()` Generator。
4. 在 `main.py` 中用 `for event in pipeline.run(doc_model, rules): ...` 消费进度流。
5. 移除原 `engine/validator.py` 中已迁移的逻辑，只留调用入口。

## Action: PROGRESS_DECOUPLING（切断进度上报耦合）

**优先使用方式 A（Generator yield）**：
```python
# src/use_cases/validator_pipeline.py
def run(self, doc_model: DocumentNode, rules: RuleConfig):
    total = len(doc_model.paragraphs)
    for i, para in enumerate(doc_model.paragraphs):
        issues = [p.check(para, self.context) for p in self.plugins]
        yield {"progress": round((i + 1) / total * 100), "issues": issues}
```

**方式 B（Callback 注入）** 用于需要异步推送的场景：
```python
# src/infrastructure/web/routes.py（外层注入 callback）
async def progress_callback(pct: int):
    await ws.send_json({"type": "progress", "value": pct})

pipeline.run(doc_model, rules, on_progress=progress_callback)
```

---

# 💡 Examples

## 错误示例 ❌
```python
# src/use_cases/validator.py — 违反层级规定
from fastapi import WebSocket

class Validator:
    def validate(self, doc, ws: WebSocket):
        for para in doc.paragraphs:
            if para.font != "宋体":
                ws.send_json({"error": "字体错误"})  # 直接调用 WebSocket！
```

## 正确示例 ✅
```python
# src/domain/interfaces/__init__.py
from abc import ABC, abstractmethod
from typing import List
from domain.models import ParagraphNode, Issue, RuleContext

class BaseRulePlugin(ABC):
    @abstractmethod
    def check(self, node: ParagraphNode, context: RuleContext) -> List[Issue]:
        pass

# src/use_cases/plugins/font_plugin.py
from domain.interfaces import BaseRulePlugin
from domain.models import ParagraphNode, Issue, RuleContext

class FontPlugin(BaseRulePlugin):
    def __init__(self, config: RuleConfig):
        self.config = config

    def check(self, node: ParagraphNode, context: RuleContext) -> List[Issue]:
        issues = []
        # ... 校验逻辑 ...
        return issues
```

---

# 📐 Architecture Diagram

```
┌───────────────────────────────────────────────────┐
│                  main.py / FastAPI                 │  ← 组装入口
└────────────────────────┬──────────────────────────┘
                         │ 调用 (依赖方向向内)
┌────────────────────────▼──────────────────────────┐
│          infrastructure/                           │  Level 3 外环
│  DocxParser → DocumentNode                        │
│  RuleLoader →(YAML)→ Pydantic Models              │
│  WebSocket/WebView → 消费 Generator               │
└────────────────────────┬──────────────────────────┘
                         │
┌────────────────────────▼──────────────────────────┐
│          use_cases/                                │  Level 2 中环
│  ValidatorPipeline.run() → Generator[Event]       │
│  plugins/ → [FontFamilyPlugin, IndentPlugin …]    │
└────────────────────────┬──────────────────────────┘
                         │
┌────────────────────────▼──────────────────────────┐
│          domain/                                   │  Level 1 内环
│  models/: Issue, DocumentNode, ParagraphNode …    │
│  interfaces/: BaseRulePlugin(ABC), IParser(ABC)   │
│  ← 零外部依赖，纯 Python                          │
└───────────────────────────────────────────────────┘
```
