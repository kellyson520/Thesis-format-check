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

    def validate(self, parsed_data):
        issues = []
        doc_defaults = self.rules.get('document', {})
        validators_config = self.rules.get('validators', {})
        page_setup = self.rules.get('page_setup', {})

        elements = parsed_data.get('elements', [])
        sections = parsed_data.get('sections', [])
        
        # 0. Check Page Setup Margins
        if page_setup and sections:
            first_sec = sections[0]
            for direction in ['top', 'bottom', 'left', 'right']:
                config_val = page_setup.get(f'{direction}_margin_cm')
                actual_val = first_sec.get(f'{direction}_margin_cm')
                if config_val is not None and actual_val is not None:
                    # Allow 0.1cm floating point tolerance
                    if abs(config_val - actual_val) > 0.1:
                        issues.append({
                            "id": 0,
                            "type": "Error",
                            "context": "页面边距 (Page Setup)",
                            "message": f"页面边界设定错误：{direction} margin 为 {actual_val:.2f}cm，规范要求 {config_val}cm"
                        })

        # Explicit references read from central configuration completely
        default_ea_font = doc_defaults.get('default_font_east_asia', "宋体")
        default_ascii_font = doc_defaults.get('default_font_ascii', "Times New Roman")
        default_size = doc_defaults.get('default_font_size', 12)

        last_heading_level = 0
        in_references = False
        last_figure_num = 0
        last_table_num = 0

        for el in elements:
            if el['type'] != 'paragraph':
                continue

            style_name = el['style_name']

            # Captions Sequence check
            if "Caption" in style_name or "题注" in style_name:
                import re
                match = re.search(r'(图|表)\s*(\d+)', el['text'])
                if match:
                    c_type = match.group(1)
                    num = int(match.group(2))
                    if c_type == "图":
                        if num != last_figure_num + 1:
                            issues.append({
                                "id": el['index'],
                                "type": "Warn",
                                "context": el['text'],
                                "message": f"图题注编号不连续：当前为图 {num}，但上一图为 {last_figure_num}"
                            })
                        last_figure_num = num
                    elif c_type == "表":
                        if num != last_table_num + 1:
                            issues.append({
                                "id": el['index'],
                                "type": "Warn",
                                "context": el['text'],
                                "message": f"表题注编号不连续：当前为表 {num}，但上一表为 {last_table_num}"
                            })
                        last_table_num = num

            # Hierarchy check logic (H1 -> H2 -> H3 no skipping)
            if validators_config.get('check_hierarchy', False):
                if style_name.startswith('Heading') or style_name.startswith('标题'):
                    level_str = style_name.replace('Heading', '').replace('标题', '').strip()
                    if level_str.isdigit():
                        current_level = int(level_str)
                        if current_level > last_heading_level + 1 and current_level != 1:
                            issues.append({
                                "id": el['index'],
                                "type": "Error",
                                "context": el['text'],
                                "message": f"标题层级错误：从标题 {last_heading_level} 违规跳级至标题 {current_level}"
                            })
                        last_heading_level = current_level

            # References logic
            if el['text'].replace(" ", "") == "参考文献":
                in_references = True
            elif in_references and el['text'].strip() and validators_config.get('check_gb7714', False):
                if not el['text'].strip().startswith("["):
                    issues.append({
                        "id": el['index'],
                        "type": "Warn",
                        "context": el['text'][:25] + "...",
                        "message": "参考文献格式：检测到正文未使用 [1] 开头的标准 GB/T 7714 格式编号"
                    })

            expected_rules = self._determine_rule(style_name)
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
