# 软著资源提取工具移除报告 (Report)

## 任务摘要 (Summary)
根据用户要求，已成功从项目中移除"软著申报源码材料"一键生成功能相关的全部代码，包括 API 端点、业务逻辑类及相关文件。

## 变更详情 (Implementation Details)
1.  **后端 API 清理**: 移除 `src/main.py` 中的 `@app.get("/api/tools/copyright/extract")` 路由。
2.  **业务逻辑删除**: 删除 `src/use_cases/copyright_generator.py` 文件及对应的 `CopyrightGenerator` 类实现。
3.  **引用清理**: 移除 `src/main.py` 中对 `CopyrightGenerator` 的 `import` 语句。
4.  **全量扫描**: 经 `grep` 扫描，项目中已不再包含任何指向 "CopyrightGenerator"、"软著材料" 或 "extract_copyright_source" 的业务代码。

## 验证结果 (Verification)
- `python -m py_compile src/main.py` 语法校验通过。
- 全量搜索确认库中已无相关遗留关键词。

## 说明 (Manual)
该功能已彻底下线，相关 API `/api/tools/copyright/extract` 不再可用。
