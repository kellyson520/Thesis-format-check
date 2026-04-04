"""
Domain Interfaces — 抽象接口定义
规则：此模块只依赖 domain.models，禁止导入任何外部库。
所有具体实现必须在 infrastructure/ 或 use_cases/ 层完成。
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
from domain.models import (
    ParagraphNode, SectionNode, DocumentModel, Issue, RuleContext, Patch
)


class BaseRulePlugin(ABC):
    """
    规则插件基类。
    每个子类只负责一种格式规则的检查，实现开闭原则（OCP）。
    新增规则 = 新增文件，不修改任何已有代码。
    """

    @abstractmethod
    def check(
        self,
        node: ParagraphNode,
        context: RuleContext,
    ) -> List[Issue]:
        """
        对单个段落节点执行规则检查。
        :param node: 当前段落的抽象表示
        :param context: 只读文档上下文（当前区域、标题层级等）
        :return: 本次检查发现的所有 Issue 列表（可为空）
        """
        ...

    @property
    def name(self) -> str:
        """插件的人类可读名称，用于日志与调试。"""
        return self.__class__.__name__


class IParser(ABC):
    """
    解析器接口。
    具体实现（如 DocxParser）在 infrastructure/parsers/ 中。
    use_cases 层只依赖此接口，不依赖 python-docx。
    """

    @abstractmethod
    def parse(self) -> DocumentModel:
        """
        将源文档解析为抽象文档模型。
        :return: DocumentModel（纯 Python 数据，不含 docx 对象）
        """
        ...


class ISectionPlugin(ABC):
    """
    节级检查插件基类（如页边距检查）。
    对 SectionNode 进行检查，独立于段落 Plugin。
    """

    @abstractmethod
    def check_sections(self, sections: List[SectionNode]) -> List[Issue]:
        """
        对文档节信息执行检查（如页边距）。
        """
        ...


class IFixer(ABC):
    """
    文档修复器接口。
    实现类（如 DocxFixer）负责将 Patch 应用到物理文件。
    """

    @abstractmethod
    def fix(self, patches: List[Patch]) -> bytes:
        """
        应用补丁列表并返回修复后的文件二进制流（Zero-Disk IO）。
        :param patches: 待应用的修复指令列表
        :return: 修复后的文件内容（bytes）
        """
        ...
