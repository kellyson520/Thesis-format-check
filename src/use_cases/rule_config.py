"""
Use Cases Layer — 强类型规则配置模型（Pydantic）
规则：此模块只依赖 domain 层，禁止导入 docx / fastapi 等外部库。
RuleLoader 在此层完成 YAML → Pydantic 的反序列化。
"""
from __future__ import annotations
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator
import yaml
import json
import os
import copy


# ─── 子规则模型 ───────────────────────────────────────────────────────────────

class ParagraphRule(BaseModel):
    """单个样式的格式规则，所有字段均有合理默认值。"""
    name: str = ""
    font_east_asia: Optional[str] = None
    font_ascii: Optional[str] = None
    font_size: Optional[float] = None          # 单位：pt
    bold: Optional[bool] = None
    alignment: Optional[str] = None            # "left" / "center" / "right" / "justify"
    first_line_indent: Optional[float] = None  # 单位：字符数
    line_spacing: Optional[float] = None       # 倍数 (e.g. 1.5) 或 pt
    space_before: Optional[float] = None       # 单位：pt
    space_after: Optional[float] = None        # 单位：pt


class HeadingsConfig(BaseModel):
    level_1: Optional[ParagraphRule] = None
    level_2: Optional[ParagraphRule] = None
    level_3: Optional[ParagraphRule] = None


class ParagraphsConfig(BaseModel):
    body_text: Optional[ParagraphRule] = None


class CaptionsConfig(BaseModel):
    figure_caption: Optional[ParagraphRule] = None
    table_caption: Optional[ParagraphRule] = None


class DocumentDefaults(BaseModel):
    default_font_east_asia: str = "宋体"
    default_font_ascii: str = "Times New Roman"
    default_font_size: float = 12.0
    default_line_spacing: float = 1.5


class PageSetupConfig(BaseModel):
    top_margin_cm: Optional[float] = None
    bottom_margin_cm: Optional[float] = None
    left_margin_cm: Optional[float] = None
    right_margin_cm: Optional[float] = None


class ValidatorsConfig(BaseModel):
    check_hierarchy: bool = True
    check_gb7714: bool = True


# ─── 顶层规则配置（根节点） ───────────────────────────────────────────────────

class RuleConfig(BaseModel):
    """
    完整的规则配置对象。
    加载失败时 Pydantic 会抛出 ValidationError，不会静默通过。
    替代原来的脆弱字典取值，提供 IDE 类型安全与自动补全。
    """
    document: DocumentDefaults = Field(default_factory=DocumentDefaults)
    headings: HeadingsConfig = Field(default_factory=HeadingsConfig)
    paragraphs: ParagraphsConfig = Field(default_factory=ParagraphsConfig)
    captions: CaptionsConfig = Field(default_factory=CaptionsConfig)
    page_setup: PageSetupConfig = Field(default_factory=PageSetupConfig)
    validators: ValidatorsConfig = Field(default_factory=ValidatorsConfig)
    # P0 新增：自定义样式映射 {"我的标题1": "level_1", "我的图注": "figure_caption"}
    style_mapping: Dict[str, str] = Field(default_factory=dict)

    def get_paragraph_rule(self, style_name: str) -> Optional[ParagraphRule]:
        """
        根据 Word 样式名称查找对应的格式规则。
        使用 StyleMapper (逻辑上) 或配置的 style_mapping 进行解耦。
        """
        # 1. 检查自定义映射
        mapped_key = self.style_mapping.get(style_name)
        if mapped_key:
            return self._get_rule_by_key(mapped_key)

        # 2. 回退到内置启发式逻辑 (解耦后使用 StyleMapper 相似逻辑)
        from use_cases.style_mapper import StyleMapper
        mapper = StyleMapper() # 使用默认内置规则
        
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
        """通过 key (如 'level_1', 'body_text') 获取对应规则对象。"""
        if key == "level_1": return self.headings.level_1
        if key == "level_2": return self.headings.level_2
        if key == "level_3": return self.headings.level_3
        if key == "body_text": return self.paragraphs.body_text
        if key == "figure_caption": return self.captions.figure_caption
        if key == "table_caption": return self.captions.table_caption
        return None


# ─── 规则加载器 ───────────────────────────────────────────────────────────────

class RuleLoader:
    """
    规则加载与管理器（Use Cases 层）。
    输出：强类型的 RuleConfig（Pydantic），不再返回裸字典。
    支持热重载、YAML/JSON 导入导出。
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self._config: RuleConfig = self._load()

    def _load(self) -> RuleConfig:
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"规则文件未找到: {self.filepath}")
        with open(self.filepath, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        # Pydantic 自动校验：格式错误时立即抛出 ValidationError
        return RuleConfig.model_validate(raw)

    def reload(self) -> None:
        """从当前 filepath 重新加载规则文件。"""
        self._config = self._load()

    def get_rules(self) -> RuleConfig:
        """返回强类型规则配置对象。"""
        return self._config

    def import_from_yaml(self, yaml_content: str) -> dict:
        """从 YAML 字符串导入规则（用于 API 文件上传）。"""
        try:
            raw = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML 解析失败: {e}")
        config = RuleConfig.model_validate(raw)  # 校验
        with open(self.filepath, "w", encoding="utf-8") as f:
            yaml.dump(raw, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        self._config = config
        return {"status": "ok", "message": f"规则已更新，共 {len(raw)} 个顶层节点"}

    def import_from_json(self, json_content: str) -> dict:
        """从 JSON 字符串导入规则。"""
        try:
            raw = json.loads(json_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 解析失败: {e}")
        config = RuleConfig.model_validate(raw)
        with open(self.filepath, "w", encoding="utf-8") as f:
            yaml.dump(raw, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        self._config = config
        return {"status": "ok", "message": "规则已从 JSON 格式更新"}

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
            "default_font_ascii": doc.default_font_ascii,
            "default_font_size": doc.default_font_size,
            "default_line_spacing": doc.default_line_spacing,
            "heading_levels": [
                k for k, v in self._config.headings.model_dump().items() if v
            ],
            "paragraph_styles": [
                k for k, v in self._config.paragraphs.model_dump().items() if v
            ],
            "caption_styles": [
                k for k, v in self._config.captions.model_dump().items() if v
            ],
        }
