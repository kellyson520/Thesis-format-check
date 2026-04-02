import yaml
import json
import os
import copy


class RuleLoader:
    """
    规则加载与管理器：
    - 从本地 YAML 加载规则
    - 支持运行时热更新 (reload)
    - 支持从 JSON/YAML 导入自定义规则并覆盖
    - 支持将当前规则导出为 JSON/YAML 文件
    - 支持规则校验 (validate_schema) 防止非法规则损坏引擎
    """

    REQUIRED_TOP_KEYS = {"document", "headings", "paragraphs", "captions"}

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.rules = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"规则文件未找到: {self.filepath}")
        with open(self.filepath, 'r', encoding='utf-8') as f:
            loaded = yaml.safe_load(f)
        self._validate_schema(loaded)
        self.rules = loaded

    def reload(self):
        """热重载规则文件，不重启服务。"""
        self._load()

    def _validate_schema(self, rules: dict):
        """基础结构校验：确保规则文件完整性。"""
        if not isinstance(rules, dict):
            raise ValueError("规则文件格式非法：根节点必须为字典结构")
        missing = self.REQUIRED_TOP_KEYS - set(rules.keys())
        if missing:
            raise ValueError(f"规则文件缺少必需字段: {missing}")

        doc = rules.get("document", {})
        required_doc_keys = {"default_font_east_asia", "default_font_ascii", "default_font_size"}
        missing_doc = required_doc_keys - set(doc.keys())
        if missing_doc:
            raise ValueError(f"规则文件 document 节点缺少: {missing_doc}")

    def get_rules(self) -> dict:
        return self.rules

    def import_from_yaml(self, yaml_content: str) -> dict:
        """
        从 YAML 字符串导入规则（用于 API 文件上传）。
        成功校验后保存并热重载。
        """
        try:
            new_rules = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML 解析失败: {e}")
        self._validate_schema(new_rules)
        # Persist back to disk
        with open(self.filepath, 'w', encoding='utf-8') as f:
            yaml.dump(new_rules, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        self.rules = new_rules
        return {"status": "ok", "message": f"规则已更新，共 {len(new_rules)} 个顶层节点"}

    def import_from_json(self, json_content: str) -> dict:
        """从 JSON 字符串导入规则（用于 API JSON Body 上传）。"""
        try:
            new_rules = json.loads(json_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 解析失败: {e}")
        self._validate_schema(new_rules)
        # Convert and persist as YAML
        with open(self.filepath, 'w', encoding='utf-8') as f:
            yaml.dump(new_rules, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        self.rules = new_rules
        return {"status": "ok", "message": "规则已从 JSON 格式更新"}

    def export_as_yaml(self) -> str:
        """将当前规则序列化为 YAML 字符串返回。"""
        return yaml.dump(
            copy.deepcopy(self.rules),
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False
        )

    def export_as_json(self) -> str:
        """将当前规则序列化为 JSON 字符串返回。"""
        return json.dumps(copy.deepcopy(self.rules), ensure_ascii=False, indent=2)

    def get_summary(self) -> dict:
        """返回规则的结构摘要，用于前端展示当前生效规则概览。"""
        doc = self.rules.get("document", {})
        return {
            "default_font_east_asia": doc.get("default_font_east_asia", "未设置"),
            "default_font_ascii": doc.get("default_font_ascii", "未设置"),
            "default_font_size": doc.get("default_font_size", "未设置"),
            "default_line_spacing": doc.get("default_line_spacing", "未设置"),
            "heading_levels": list(self.rules.get("headings", {}).keys()),
            "paragraph_styles": list(self.rules.get("paragraphs", {}).keys()),
            "caption_styles": list(self.rules.get("captions", {}).keys()),
        }
