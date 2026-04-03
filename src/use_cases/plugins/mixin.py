from __future__ import annotations
from typing import Type, Optional
from pydantic import BaseModel

class DeclarativeConfigMixin:
    """
    提供声明式配置支持。
    子类插件通过声明 `config_model` Pydantic 类来暴露其所需的配置项。
    """
    plugin_id: str                      # 插件唯一标识，对应 rules.yaml 中的 key
    config_model: Optional[Type[BaseModel]] = None # 插件的配置模型
