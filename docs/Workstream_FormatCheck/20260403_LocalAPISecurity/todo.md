# 本地 API 安全隔离

## 背景 (Context)
系统通过 FastAPI 在本地 `127.0.0.1:8000` 暴露接口供 PyWebView 调用。若不配置 Token 鉴权，恶意公网网页脚本可直接窃取用户正在处理的学位论文（学术泄密风险）。

## 策略 (Strategy)
FastAPI 启动时动态生成一次性安全 Token（或随机端口），通过 `pywebview` 的 `js_api` 注入前端。所有 HTTP 请求必须携带此 Token 进行验证。

## 待办清单 (Checklist)

### Phase 1: 安全 Token 机制
- [ ] 在 FastAPI `lifespan` 启动时生成 `secrets.token_urlsafe(32)` 作为 session token
- [ ] 实现 `TokenValidator` 依赖项（`Depends`），验证请求头 `X-Session-Token`
- [ ] 将 token 通过 `pywebview` `js_api` 注入前端 `window.__SESSION_TOKEN__`
- [ ] 所有 `/api/*` 路由注入 `TokenValidator` 依赖

### Phase 2: CORS 严格配置
- [ ] 将 `CORSMiddleware` 的 `allow_origins` 从 `["*"]` 改为 `["null"]`（仅允许 WebView 来源）
- [ ] 配置 `allow_methods` 为精确列表而非 `["*"]`
- [ ] 编写 CORS 安全测试：模拟外部 origin 请求，验证被拒绝

### Phase 3: 随机端口（可选增强）
- [ ] 启动时使用 `socket.bind(('', 0))` 分配随机可用端口
- [ ] 将端口号通过 `js_api` 传递给前端，前端动态构建 API base URL
- [ ] 更新 `docs/spec.md` 记录安全架构设计

### Phase 4: 验证
- [ ] 安全扫描：模拟跨站请求（CSRF），验证 Token 校验生效
- [ ] 使用 OWASP ZAP 或等效工具快速扫描本地接口
