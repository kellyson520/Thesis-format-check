"""
Infrastructure Layer — 修订模式清理工具 (RevisionCleaner)
职责：
  - 在解析文档前，剥离文档中的“修订记录”（w:del）和“修订插入”（w:ins）标记。
  - 支持将文档恢复为“接受所有修订”后的状态，防止校验引擎查看到已删除的废弃文字。
"""
from __future__ import annotations
import io
import docx
from lxml import etree
from docx.oxml.ns import qn

class RevisionCleaner:
    """
    负责在内存中清理 Docx 对象的修订信息。
    """

    @staticmethod
    def accept_all_revisions(doc: docx.Document) -> docx.Document:
        """
        接受所有修订：移除 w:del 节点，并将 w:ins 节点的内容提升到父节点。
        """
        from lxml import etree
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        # 1. 移除所有删除标记 (w:del)
        # 绕过 python-docx 封装的 xpath (它不支持 namespaces 参数)，直接调用 lxml
        del_xpath = etree.XPath(".//w:del", namespaces=ns)
        for del_el in del_xpath(doc.element):
            parent = del_el.getparent()
            if parent is not None:
                parent.remove(del_el)
        
        # 2. 提升所有插入标记 (w:ins)
        ins_xpath = etree.XPath(".//w:ins", namespaces=ns)
        for ins_el in ins_xpath(doc.element):
            parent = ins_el.getparent()
            if parent is not None:
                for child in ins_el.getchildren():
                    ins_el.addprevious(child)
                parent.remove(ins_el)
        
        # 3. 处理属性修订
        for tag in ['pPrChange', 'rPrChange', 'sectPrChange', 'tblPrChange', 'tcPrChange', 'trPrChange']:
            change_xpath = etree.XPath(f".//w:{tag}", namespaces=ns)
            for change_el in change_xpath(doc.element):
                parent = change_el.getparent()
                if parent is not None:
                    parent.remove(change_el)
                    
        return doc

    @staticmethod
    def strip_hidden_text(doc: docx.Document) -> docx.Document:
        """
        移除所有标记为 'hidden' 的 Run。
        """
        for para in doc.paragraphs:
            for run in para.runs:
                if run.font.hidden:
                    # python-docx 移除 run 比较麻烦，通常只能设为空
                    run.text = ""
        return doc
