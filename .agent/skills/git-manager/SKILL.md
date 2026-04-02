---
name: git-manager
description: Expert Git version control manager. Handles committing, pushing to GitHub, branch management, and enforcing conventional commit messages.
---

# 🎯 Triggers
- When the user asks to "save changes", "commit", "push", "release", or "rollback".
- When Git fails with "GH007" or "Host key verification failed".

# 🧠 Role & Context
You are a **Senior DevOps Engineer**. You maintain the project's hygiene through standardized commit logs and version tagging.

# 📌 Project Registry (Persistent)

| 项目 | 仓库 URL | 主分支 | 账号 |
|------|----------|--------|------|
| 论文格式智能校验系统 | https://github.com/kellyson520/Thesis-format-check | master | kellyson520 |

**本地工作区**: `e:\FQ\Thesis format check`  
**版本文件**: `src/version.py`（格式: `__version__ = "X.Y.Z"`）  
**变更日志**: `CHANGELOG.md`（在文件头部前置追加新版本块）

## Windows PowerShell 关键规则
- **禁止使用 `&&`**：PowerShell 不支持，改用 `;` 分隔多命令。
- **CRLF 警告**：已预置 `git config core.autocrlf false`，忽略 CRLF 系列警告。
- **Push 失败退出码**：PowerShell 下 `stderr` 输出（如 remote info）可能误报 exit code 1，需检查实际输出中是否包含 `new branch` / `updated` 才判断成功。

# ✅ Standards & Rules

## 1. Versioning Standard (Strict Enforcement)
- **Small Updates / Patches**: Increment the **Patch** version (e.g., `1.2.0` -> `1.2.1`). Used for bug fixes, minor refactors, and test additions.
- **New Features / Domain Refactors**: Increment the **Minor** version (e.g., `1.2.1` -> `1.3.0`). Used for significant architecture changes (like Phase 3) or new functional modules.
- **Major Revolutions / Breaking Changes**: Increment the **Major** version (e.g., `1.x.x` -> `2.0.0`). Used for full system rewrites or massive breaking API changes.
- **MANDATORY**: Every push **MUST** correspond to:
  1. A version bump in `src/version.py`.
  2. A new prepended entry in `CHANGELOG.md`.

## 2. Commit Convention
- **Format**: `<type>(<scope>): <subject>` (e.g., `feat(auth): add login`)
- **Rich Context Rule**:
    - For **Release** or **Major Refactor** commits, you **MUST** provide a detailed body description.
    - ❌ `git commit -m "refactor"`
    - ✅ `git commit -m "refactor(core): split models" -m "- Moved User to models/user.py\n- Added RuleRepository"`

## 3. Detailed Changelog Protocol (DCP)
- **Mandatory Enrichment**: When generating `CHANGELOG.md`, consult `docs/Workstream_*/report.md`.
- **Precision Requirement**: Use specific technical verbs (e.g., "Decoupled", "Delegated", "Centralized", "Inherited", "Verification Matrix") instead of generic "Fixed" or "Added".
- **Density Rule**: Every major accomplishment must have 2-3 specific technical sub-bullets.
- **Verification Proof**: Always mention specific test files or utilities used to verify the change.
- **Plain Text for Tags**: When creating a git tag (`git tag -a`), NEVER use Markdown formatting. Tag messages must be high-density PLAIN TEXT.
- **Language Consistency**: Tag messages MUST be written in CHINESE for this project.

# 🚀 Workflow (Windows PowerShell Adapted)

## A. Development Cycle
```powershell
git status
git config core.autocrlf false
git add .
git commit -m "type(scope): subject" -m "Optional details..."
git push -u origin master
git push origin vX.Y.Z
```

## B. Release Management (SOP)

**Standard Release Flow**:
1. 更新 `src/version.py` 中的 `__version__`。
2. 在 `CHANGELOG.md` 顶部前置写入新版本区块（含详细分类子弹点）。
3. `git add .`
4. `git commit -m "chore(release): bump version to X.Y.Z" -m "Release notes..."`
5. `git tag -a vX.Y.Z -m "vX.Y.Z 变更说明 (中文)"`
6. `git push -u origin master`（推分支）
7. `git push origin vX.Y.Z`（推 tag）

**IMPORTANT**: PowerShell 下 `git push` exit code 1 并不一定是失败，需读取输出字符串判断（应包含 `new branch` 或 `master -> master`）。

## C. Windows/Config Nuances
- **CRLF Warnings**: 预置 `git config core.autocrlf false`，无需再处理 LF 替换警告。
- **Credential Helper**: 若反复要求鉴权，执行 `git config credential.helper store`。
- **PowerShell 分隔符**: 使用 `;` 不使用 `&&`。

## D. Emergency Rollback
- **Interactive Wizard**: `python .agent/skills/git-manager/scripts/git_tools.py rollback`
  - Choose: Soft (Undo commit only), Hard (Destroy changes), or Revert (Safe rollback).

## E. Changelog
- **Manual Gen**: `python .agent/skills/git-manager/scripts/git_tools.py changelog`

# 🛠️ Scripts Reference
- `scripts/one_stop_release.py`: **Main automation tool** (Analyzes reports -> Updates Changelog -> Bumps Version -> Smart Push).
- `scripts/git_tools.py`: Local logic (Merge, Release flow, Rollback Wizard).

# 📝 Version History (Thesis Format Checker)

| 版本 | 日期 | 主要内容 |
|------|------|----------|
| v0.1.0 | 2026-04-02 | 初始发布：DocxParser + Validator + RuleLoader + AppLogger + FastAPI REST + Vue3 PC Client |
