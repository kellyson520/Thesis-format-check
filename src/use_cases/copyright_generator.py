"""
Use Cases Layer — CopyrightGenerator (软著源码提取工具)
职责：按软著申报要求，从 src/ 目录下提取前 3000 行和后 3000 行代码（合集）。
过滤条件：忽略 venv, __pycache__, node_modules, .git 等无关目录。
"""
import os
from typing import List

class CopyrightGenerator:
    """批量从代码目录收集源码并格式化。"""
    
    EXCLUDE_DIRS = {".git", "venv", "__pycache__", "node_modules", "dist", ".agent", ".github", ".pytest_cache"}
    INCLUDE_EXTS = {".py", ".js", ".vue", ".ts", ".html", ".css", ".yaml"}

    def __init__(self, root_dir: str):
        self._root = root_dir

    def generate_src_merged(self) -> str:
        """
        遍历所有文件并合并其内容。
        """
        all_lines: List[str] = []
        
        for root, dirs, files in os.walk(self._root):
            # 过滤不需要的目录
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]
            
            for file in sorted(files):
                if any(file.endswith(ext) for ext in self.INCLUDE_EXTS):
                    path = os.path.join(root, file)
                    rel_path = os.path.relpath(path, self._root)
                    
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                            all_lines.append(f"\n// --- File: {rel_path} ---\n")
                            all_lines.extend(lines)
                    except Exception:
                        pass # 忽略读取错误的二进制或乱码文件
        
        total_lines = len(all_lines)
        if total_lines <= 6000:
            return "".join(all_lines)
            
        # 否则截取前 3000 行和后 3000 行
        head = all_lines[:3000]
        tail = all_lines[-3000:]
        
        sep = "\n\n... (中间代码已省略，由于软著申请仅需前后各3000行) ...\n\n"
        return "".join(head) + sep + "".join(tail)
