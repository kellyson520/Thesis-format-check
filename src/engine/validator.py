from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

class Validator:
    def __init__(self, rules):
        self.rules = rules

    def _map_alignment(self, align_val):
        # Maps Python docx alignments to configuration mappings
        if align_val == WD_PARAGRAPH_ALIGNMENT.CENTER:
            return "center"
        if align_val == WD_PARAGRAPH_ALIGNMENT.LEFT:
            return "left"
        if align_val == WD_PARAGRAPH_ALIGNMENT.RIGHT:
            return "right"
        if align_val == WD_PARAGRAPH_ALIGNMENT.JUSTIFY:
            return "justify"
        return "left" # Default implicit fallback

    def _determine_rule(self, style_name):
        # Strictly Match standard Word styles to dynamic yaml rule mappings
        if style_name.startswith("Heading 1") or style_name.startswith("标题 1"):
            return self.rules.get('headings', {}).get('level_1')
        elif style_name.startswith("Heading 2") or style_name.startswith("标题 2"):
            return self.rules.get('headings', {}).get('level_2')
        elif style_name.startswith("Heading 3") or style_name.startswith("标题 3"):
            return self.rules.get('headings', {}).get('level_3')
        elif "Caption" in style_name or "题注" in style_name:
            if "Figure" in style_name or "图" in style_name:
                return self.rules.get('captions', {}).get('figure_caption')
            else:
                return self.rules.get('captions', {}).get('table_caption')
        else:
            return self.rules.get('paragraphs', {}).get('body_text')

    def validate(self, elements):
        issues = []
        doc_defaults = self.rules.get('document', {})
        
        # Explicit references read from central configuration completely
        default_ea_font = doc_defaults.get('default_font_east_asia', "宋体")
        default_ascii_font = doc_defaults.get('default_font_ascii', "Times New Roman")
        default_size = doc_defaults.get('default_font_size', 12)

        for el in elements:
            if el['type'] != 'paragraph':
                continue

            expected_rules = self._determine_rule(el['style_name'])
            if not expected_rules:
                continue

            # Load expected state
            exp_ea_font = expected_rules.get('font_east_asia', default_ea_font)
            exp_ascii_font = expected_rules.get('font_ascii', default_ascii_font)
            exp_size = expected_rules.get('font_size', default_size)
            exp_bold = expected_rules.get('bold', False)
            exp_alignment = expected_rules.get('alignment')
            exp_indent = expected_rules.get('first_line_indent')

            rule_context_name = expected_rules.get('name', '默认正文')

            # 1. Check Runs (Validating Fonts, Size, Block Elements Attributes)
            for run in el['runs']:
                run_text = run['text'].strip()
                if not run_text:
                    continue

                # Distinct font checks for Unicode characters block
                has_chinese = any('\u4e00' <= char <= '\u9fff' for char in run_text)
                has_ascii = any(ord(char) < 128 for char in run_text)

                # Sub-validator: Chinese Font 
                if has_chinese and run['east_asia_font'] and run['east_asia_font'] != exp_ea_font:
                    if exp_ea_font not in run['east_asia_font']:
                        issues.append({
                            "id": el['index'],
                            "type": "Error",
                            "context": run_text,
                            "message": f"中文字体不符：[{rule_context_name}] 使用了 '{run['east_asia_font']}'，强制要求 '{exp_ea_font}'"
                        })
                # Sub-validator: ASCII Font
                elif has_ascii and run['ascii_font'] and run['ascii_font'] != exp_ascii_font:
                    if exp_ascii_font not in run['ascii_font']:
                        issues.append({
                            "id": el['index'],
                            "type": "Error",
                            "context": run_text,
                            "message": f"英文字体不符：[{rule_context_name}] 使用了 '{run['ascii_font']}'，强制要求 '{exp_ascii_font}'"
                        })

                # Sub-validator: Font Size
                if run['size'] and run['size'] != exp_size:
                    issues.append({
                        "id": el['index'],
                        "type": "Error",
                        "context": run_text,
                        "message": f"字号越界：[{rule_context_name}] 为 {run['size']}pt，规范指标要求 {exp_size}pt"
                    })
                
                # Sub-validator: Semantic Weight / Boldness
                if exp_bold is not None and run['bold'] != exp_bold:
                    issues.append({
                        "id": el['index'],
                        "type": "Warn",
                        "context": run_text,
                        "message": f"字重粗细不符：当前片段处于违规{'加粗' if run['bold'] else '未加粗'}状态"
                    })

            # 2. Check Paragraph Alignment & Global formatting
            if exp_alignment and el['alignment'] is not None:
                current_alignment = self._map_alignment(el['alignment'])
                if current_alignment != exp_alignment:
                    issues.append({
                        "id": el['index'],
                        "type": "Warn",
                        "context": el['text'][:25] + "..." if len(el['text']) > 25 else el['text'],
                        "message": f"段落对齐偏差：排版方向检测为 '{current_alignment}'，应更正为 '{exp_alignment}'"
                    })

            # 3. Check Paragraph Indentation Constraints
            if exp_indent is not None and el['first_line_indent_chars'] < exp_indent:
                issues.append({
                        "id": el['index'],
                        "type": "Warn",
                        "context": el['text'][:25] + "..." if len(el['text']) > 25 else el['text'],
                        "message": f"首行缩进约束：段首缩进当前约 {el['first_line_indent_chars']} 字符，未能达到 {exp_indent} 字符缩进阈值"
                    })

        return issues
