# 移除软著生成相关代码 (Remove Copyright Tool)

## 背景 (Context)
用户要求移除"软著申报源码材料"生成功能及其相关代码，清理 `src/main.py` 中的 API 及对应的 `CopyrightGenerator` 逻辑类。

## 待办清单 (Checklist)

### Phase 1: 代码清理 (Cleanup)
- [x] 移除 `src/main.py` 中的 `from use_cases.copyright_generator import CopyrightGenerator` 引用
- [x] 移除 `src/main.py` 中的 `Advanced Tools` API 路由块
- [x] 删除 `src/use_cases/copyright_generator.py` 文件
- [x] 检查是否有其他地方引用了 `CopyrightGenerator`


### Phase 2: 验证与验收 (Verification)
- [x] 确保项目可以正常启动
- [x] 检查 API 列表确认路由已消失
- [x] 更新 `process.md` 进度

