# Task: Release v1.2.4 (打包到 GitHub 并打标签)

## 背景 (Context)
系统已完成引擎稳定性修复及 GitHub 真实在线检查更新功能。当前版本 v1.2.4 已在 `src/version.py` 定义，并更新了 `CHANGELOG.md`。需执行最后的质量校验并推送到远端 master 分支并打上 tag。

## 待办清单 (Checklist)

### Phase 1: 质量最后校验 (Verify)
- [ ] 运行 `local-ci.py` 执行架构与代码质量扫描
- [ ] 运行集成测试 `pytest tests/test_api_integration.py` 确保核心 API 正常
- [ ] 审计 `src/infrastructure/updater.py` 的版本对比逻辑是否符合 SemVer

### Phase 2: 发布与标记 (Ship)
- [ ] `git add .` 将所有待办变更暂存
- [ ] `git commit` 提交代码
- [ ] `git tag -a v1.2.4` 创建标注标签
- [ ] `git push origin master` 推送到 GitHub
- [ ] `git push origin v1.2.4` 推送同步标签

### Phase 3: 归档 (Archive)
- [ ] 生成 `report.md`
- [ ] 更新 `docs/process.md` 状态为 100%
