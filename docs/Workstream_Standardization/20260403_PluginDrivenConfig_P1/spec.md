# 插件驱动配置系统技术方案 (Plugin-driven Config Design Spec)

## 背景 (Background)
目前的 `RuleConfig` 类是一个静态 Pydantic 模型，其中手动定义了所有规则字段。这导致在添加新插件时，必须同步修改 `rule_config.py`，违背了开闭原则。

## 目标 (Goals)
1.  **声明化**: 插件通过类属性（如 `plugin_config`）声明其配置 Pydantic 模型。
2.  **去中心化**: 删除 `rule_config.py` 中所有的具体插件配置定义。
3.  **动态性**: `RuleConfig` 作为一个空容器，在启动时动态聚合所有可用插件的模型。

## 核心设计 (Architecture)

### 1. `DeclarativeConfigMixin`
定义在 `src/use_cases/plugins/mixin.py`:
```python
from pydantic import BaseModel
from typing import Type

class DeclarativeConfigMixin:
    """提供声明式配置支持。"""
    config_model: Type[BaseModel] = None # 插件必须声明其配置模型
```

### 2. 动态模型生成 (Dynamic Model Generation)
利用 Pydantic 的 `create_model`:
```python
def create_dynamic_rule_config(plugins: List[Type[BaseRulePlugin]]) -> Type[BaseModel]:
    fields = {}
    for p in plugins:
        if issubclass(p, DeclarativeConfigMixin) and p.config_model:
            # e.g. "pagination": (PaginationConfig, Field(...))
            fields[p.plugin_id] = (p.config_model, ...) 
    return create_model("DynamicRuleConfig", **fields)
```

### 3. 段落级配置的拆解 (Paragraph Rule Sharding)
针对 `ParagraphRule` 这种被多个插件共享的模型，可以使用 **组合 (Composition)** 模式：
- `FontPlugin` 声明其需要的 `FontParams`。
- `SpacingPlugin` 声明其需要的 `SpacingParams`。
- 汇总成 `ParagraphRule = FontParams + SpacingParams + ...`。

## 关键挑战 (Challenges)
- **加载顺序**: 必须确保在 `RuleLoader` 加载 `rules.yaml` 之前，所有插件已经注册。
- **配置层级**: `rules.yaml` 的现有结构（`headings`, `paragraphs`）需要适配这种由插件定义的结构。
  - *方案*: 将 `ParagraphRule` 改为由各插件 `Config` 组合而成。

## 路线图 (Roadmap)
1. 定义 Mixin 并初步支持 `pagination` 等独立顶层配置的动态化。
2. 重构 `ParagraphRule` 为插件子模型的合集。
3. 更新 `RuleLoader` 的加载逻辑。
