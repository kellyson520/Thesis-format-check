# 论文格式智能校验系统 (Thesis Format Checker)

> 基于 **FastAPI + PyWebView + Vue 3** 的个人 PC 端论文格式校验利器

## 功能特性

| 功能 | 描述 |
|------|------|
| 🔍 深度格式校验 | 逐段扫描 `.docx`，精准比对中英文字体、字号、首行缩进、段落对齐 |
| 📝 批注式导出 | 将问题以红色批注直接注入文档副本，可在 Word 中查看 |
| ⚙️ 规则自定义 | 支持 YAML / JSON 格式规则文件的导入导出与在线热重载 |
| 📊 系统日志 | 结构化双轨日志，支持级别过滤与清空 |
| 🎨 极客 UI | 毛玻璃暗系设计，三栏式侧边栏 PC 端客户端 |

## 技术架构

```
frontend/          # Vite + Vue 3 前端 (Glassmorphism UI)
src/
  main.py          # FastAPI 应用入口 + PyWebView 窗体启动
  version.py       # 版本声明
  config/
    rules.yaml     # 格式校验规则基准配置
  engine/
    docx_parser.py # Word XML DOM 解析引擎
    validator.py   # 多层规则校验器
    rule_loader.py # 规则加载/导入/导出管理器
    logger.py      # 统一结构化日志处理器
docs/              # 任务文档 (PSB 协议)
```

## 快速开始

```bash
# Python 后端
pip install -r requirements.txt
cd src && python main.py

# 前端开发模式
cd frontend && npm install && npm run dev

# 以 dev 模式启动（前端连接 Vite devServer）
cd src && python main.py --dev
```

## 规则配置

编辑 `src/config/rules.yaml` 设定您学校的格式要求，或通过 UI 的**规则管理**面板直接导入自定义文件。

## 版本历史

详见 [CHANGELOG.md](./CHANGELOG.md)
