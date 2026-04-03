"""
Use Cases Layer — FixerPipeline
职责：接收一组 Issue，收集其中的 Patch，并将其应用到指定的文档上。
规则：
  - 维持 Zero-Disk IO 环境（接收 bytes/BytesIO，返回 bytes）。
  - 不含具体 docx 处理逻辑，依赖 IFixer 抽象。
"""
from __future__ import annotations
import io
from typing import List
from domain.models import Issue, Patch
from domain.interfaces import IFixer


class FixerPipeline:
    """
    业务逻辑：过滤出有 Patch 的问题，批量应用修复。
    """

    def __init__(self, fixer_factory):
        """
        :param fixer_factory: 一个可根据 BytesIO 创建 IFixer 实例的工厂函数。
                              (通常为 infrastructure.reporters.docx_fixer.DocxFixer)
        """
        self._fixer_factory = fixer_factory

    def apply_fixes(
        self, 
        doc_bytes: bytes, 
        issues: List[Issue],
    ) -> bytes:
        """
        过滤带 Patch 的 Issue 项并应用。
        :param doc_bytes: 原始文档（二进制）
        :param issues: Validator 产生的错误列表
        :return: 修复后的文档（二进制）
        """
        # 1. 提取所有有效的 Patch
        patches: List[Patch] = [
            i.suggested_patch for i in issues 
            if i.suggested_patch is not None
        ]
        
        if not patches:
            return doc_bytes  # 无需修复，直接返回原件
            
        # 2. 创建物理修复器辅助对象（通过工厂解耦）
        fixer: IFixer = self._fixer_factory(io.BytesIO(doc_bytes))
        
        # 3. 执行批量修复并导出
        fixed_bytes = fixer.fix(patches)
        
        return fixed_bytes
