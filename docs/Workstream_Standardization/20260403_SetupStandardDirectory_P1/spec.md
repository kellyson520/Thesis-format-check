# 标准目录设计规范 (Standard Directory Design Spec)

## 背景 (Background)
为了解决项目中标准文件散乱的问题，统一在根目录建立 `标准/` (Standards) 文件夹。该目录将作为项目所有"硬性约束"的单一事实来源。

## 目录结构设计 (Folder Structure)

```text
标准/
├── 系统架构标准.md      (原 ARCHITECTURE_STANDARD.md 或 Standard_Whitepaper.md)
├── 插件开发标准.md      (Plugin Development Guidelines)
├── 接口协议标准.md      (API Contract / IPC Standard)
└── UI视觉标准.md        (Design Tokens / Style Guide)
```

## 执行步骤 (Implementation Steps)

1. **根目录整理**: 
   - 寻找 `ARCHITECTURE_STANDARD.md` 并将其重命名/迁移。
   - 提取 `architecture-auditor` 技能中的核心规则到标准文档。
   - 创建 `插件开发标准.md`，根据 `src/use_cases/plugins/` 的现有模式提取规范。

2. **文档同步**:
   - 确保 `AGENTS.md` 中的 `architecture-auditor` 规则与 `标准/系统架构标准.md` 一致。
   - 确保 `task-lifecycle-manager` 与项目现行的任务流对齐。
