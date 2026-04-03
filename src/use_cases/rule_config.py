from __future__ import annotations
from typing import Optional, Dict, Any, List, Type
from pydantic import BaseModel, Field, create_model
import yaml
import json
import os


# ─── 核心元模型 ─────────────────────────────────────────────────────────────

class DocumentDefaults(BaseModel):
    default_font_east_asia: str = "宋体"
    default_font_ascii: str = "Times New Roman"
    default_font_size: float = 12.0
    default_line_spacing: float = 1.5


class ValidatorsConfig(BaseModel):
    """全局验证开关保持集中声明"""
    check_font: bool = True
    check_spacing: bool = True
    check_hierarchy: bool = True
    check_gb7714: bool = True


# ─── 动态生成器 ─────────────────────────────────────────────────────────────

def build_paragraph_rule_class() -> Type[BaseModel]:
    """
    从现有插件及其 Config 类动态组装 ParagraphRule。
    遵循：所有设置均由插件显示声明。
    """
    from use_cases.plugins.font_plugin import FontConfig
    from use_cases.plugins.spacing_plugin import SpacingConfig
    
    # 组合字段（扁平化以兼容现有 rules.yaml）
    fields: Dict[str, Any] = {"name": (str, "")}
    
    for sub_config_cls in [FontConfig, SpacingConfig]:
        for name, field in sub_config_cls.model_fields.items():
            fields[name] = (field.annotation, field.default)
            
    return create_model("ParagraphRule", **fields)


# 实例化动态模型
ParagraphRule = build_paragraph_rule_class()


class HeadingsConfig(BaseModel):
    level_1: Optional[ParagraphRule] = None
    level_2: Optional[ParagraphRule] = None
    level_3: Optional[ParagraphRule] = None


class ParagraphsConfig(BaseModel):
    body_text: Optional[ParagraphRule] = None


class CaptionsConfig(BaseModel):
    figure_caption: Optional[ParagraphRule] = None
    table_caption: Optional[ParagraphRule] = None


# ─── 顶层规则配置（根节点） ───────────────────────────────────────────────────

def build_rule_config_class() -> Type[BaseModel]:
    """
    组装顶层 RuleConfig。
    """
    from use_cases.plugins.pagination_plugin import PaginationConfig
    from use_cases.plugins.page_margin_plugin import PageSetupConfig

    # 基础字段
    base_fields = {
        "document": (DocumentDefaults, Field(default_factory=DocumentDefaults)),
        "headings": (HeadingsConfig, Field(default_factory=HeadingsConfig)),
        "paragraphs": (ParagraphsConfig, Field(default_factory=ParagraphsConfig)),
        "captions": (CaptionsConfig, Field(default_factory=CaptionsConfig)),
        "validators": (ValidatorsConfig, Field(default_factory=ValidatorsConfig)),
        "style_mapping": (Dict[str, str], Field(default_factory=dict)),
    }
    
    # 插件显式声明的顶层字段
    base_fields["pagination"] = (PaginationConfig, Field(default_factory=PaginationConfig))
    base_fields["page_setup"] = (PageSetupConfig, Field(default_factory=PageSetupConfig))

    # 创建顶层类
    DynamicRuleConfig = create_model("RuleConfig", **base_fields)

    # 注入辅助方法（保持兼容性）
    def get_paragraph_rule(self, style_name: str) -> Optional[ParagraphRule]:
        mapped_key = self.style_mapping.get(style_name)
        if mapped_key:
            return self._get_rule_by_key(mapped_key)

        from use_cases.style_mapper import StyleMapper
        mapper = StyleMapper() 
        level = mapper.get_heading_level(style_name)
        if level == 1: return self.headings.level_1
        if level == 2: return self.headings.level_2
        if level == 3: return self.headings.level_3
        if "Caption" in style_name or "题注" in style_name:
            if "Figure" in style_name or "图" in style_name:
                return self.captions.figure_caption
            return self.captions.table_caption
        return self.paragraphs.body_text

    def _get_rule_by_key(self, key: str) -> Optional[ParagraphRule]:
        mapping = {
            "level_1": self.headings.level_1,
            "level_2": self.headings.level_2,
            "level_3": self.headings.level_3,
            "body_text": self.paragraphs.body_text,
            "figure_caption": self.captions.figure_caption,
            "table_caption": self.captions.table_caption,
        }
        return mapping.get(key)
    
    # 绑定方法
    DynamicRuleConfig.get_paragraph_rule = get_paragraph_rule
    DynamicRuleConfig._get_rule_by_key = _get_rule_by_key
    
    return DynamicRuleConfig


# 暴露顶层类
RuleConfig = build_rule_config_class()


class RuleLoader:
    """
    规则加载与管理器。
    """
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._config: RuleConfig = self._load()

    def _load(self) -> RuleConfig:
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"规则文件未找到: {self.filepath}")
        with open(self.filepath, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        return RuleConfig.model_validate(raw)

    def reload(self) -> None:
        self._config = self._load()

    def get_rules(self) -> RuleConfig:
        return self._config

    def import_from_yaml(self, yaml_content: str) -> dict:
        try:
            raw = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML 解析失败: {e}")
        config = RuleConfig.model_validate(raw)
        with open(self.filepath, "w", encoding="utf-8") as f:
            yaml.dump(raw, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        self._config = config
        return {"status": "ok", "message": f"规则已更新"}

    def export_as_yaml(self) -> str:
        return yaml.dump(
            self._config.model_dump(exclude_none=False),
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )

    def export_as_json(self) -> str:
        return self._config.model_dump_json(indent=2)

    def get_summary(self) -> dict:
        doc = self._config.document
        return {
            "default_font_east_asia": doc.default_font_east_asia,
            "default_font_size": doc.default_font_size,
        }

    def set_plugin_enabled(self, plugin_id: str, enabled: bool) -> bool:
        """
        动态更新指定插件的启用状态并持久化。
        """
        if not hasattr(self._config, plugin_id):
            return False
            
        plugin_cfg = getattr(self._config, plugin_id)
        if hasattr(plugin_cfg, "enabled"):
            plugin_cfg.enabled = enabled
            # 持久化到文件
            self.import_from_yaml(self.export_as_yaml())
            return True
        return False
