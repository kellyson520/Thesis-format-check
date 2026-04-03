# 增加系统设置界面 (Add Settings Feature)

## 背景 (Context)
用户需要一个统一的设置界面来管理插件开关、查看版本信息、检查更新以及清理系统缓存，以提升工具的可维护性和用户体验。

## 策略 (Strategy)
1. **后端实现**: 
   - 定义版本号常量。
   - 实现设置管理 API，支持获取和更新插件启用状态。
   - 实现缓存清理逻辑和模拟更新检查接口。
2. **前端实现**:
   - 设计并实现一个高颜值的 "Settings" 侧边栏或模态框。
   - 集成插件开关控制、版本展示、缓存清理等交互。

## 待办清单 (Checklist)

### Phase 1: 后端基础设施与 API
- [x] 创建 `src/version.py` 定义版本号
- [x] 在 `main.py` 或相关路由中增加 `/api/settings` GET 接口 (获取版本、插件列表、缓存大小)
- [x] 增加 `/api/settings/plugin` POST 接口 (开启/关闭插件)
- [x] 增加 `/api/settings/clear_cache` POST 接口 (清理 `.cache` 目录)
- [x] 增加 `/api/settings/check_update` GET 接口 (模拟检查更新)

### Phase 2: 前端 UI 与集成
- [x] 在 `App.vue` 或独立组件中创建设置面板
- [x] 实现插件开关列表 (基于后端返回的 Dynamic Config)
- [x] 实现版本信息展示与更新检查按钮及状态反馈
- [x] 实现清理缓存按钮及 Loading 效果
- [x] 优化 UI 视觉效果 (深色模式适配、平滑动画)

### Phase 3: 验证与验收
- [ ] 断点测试 API 响应
- [ ] 验证插件关闭后校验逻辑是否真的跳过
- [ ] 验证缓存目录是否被正确清空
- [ ] 交付报告
