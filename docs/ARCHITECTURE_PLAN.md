针对前面找出的核心痛点与底层 Bug，要对该系统的 `engine`（解析与校验引擎）进行彻底的优化和重构，建议从**架构重组、解析策略、状态管理以及性能提升**四个维度入手。

以下是具体的引擎改进与优化方案：

### 1. 彻底重构 `DocxParser`：建立“真实样式解析树”
当前的 `DocxParser` 是扁平化的，这也是导致后续字重、字号、字体继承频频误报的根源。需要将其升级为具备**层叠样式表（CSS-like）解析能力**的引擎。

* **构建样式继承解析器 (Style Resolver)**：在遍历文档段落之前，先读取 Word 的 `styles.xml` 和 `settings.xml`（`document defaults`）。建立一个内部的字典树，预先计算好每个样式的最终计算值（Computed Style）。
    * *改进逻辑*：当解析到一个 `Run` 时，如果 `run.bold` 为 `None`，引擎不应直接赋 `False`，而是调用 `resolver.get_computed_bold(para.style, run_style)` 来获取真实的渲染状态。
* **停止暴力 `strip()`，保留排版骨架**：移除 `if not run.text.strip(): continue` 这种粗暴的过滤。引入“不可见元素标记（Invisible Tokens）”，将 Tab、多个全角/半角空格解析为特定的 Token，这对于后续精准校验“首行缩进（2个中文字符即4个半角空格）”至关重要。
* **扩展解析广度**：引入针对 `doc.tables` 和列表节点（`w:numPr`）的遍历机制，将表格单元格内的段落同样转化为标准的元素字典输入校验器。

### 2. 升级 `Validator`：引入“状态机 (State Machine)”机制
目前的校验器是一个无脑的 `for` 循环，导致了诸如“参考文献状态泄露”和“图表题注正则灾难”等问题。需要引入状态机来感知文档的“上下文结构”。

* **文档区域状态机**：
    定义明确的文档区域枚举（如 `COVER`, `ABSTRACT`, `TOC`, `BODY`, `REFERENCES`, `APPENDIX`）。
    * *进出机制*：当遇到“参考文献”时，进入 `REFERENCES` 状态；当遇到下一个一级标题（如“致谢”或“附录”）时，强制**退出** `REFERENCES` 状态并切换上下文。这样就能彻底解决状态泄露引发的全篇格式误报。
* **上下文感知的正则与计数**：
    针对题注（图 1-1, 表 2-3），放弃全局正则匹配。改为：先解析章节号（当前处于第几章），然后在该章节的上下文中校验图表序号。如果跨章，计数器重置。
* **解耦硬编码，引入“样式映射字典 (Style Mapper)”**：
    删除 `style_name.startswith("Heading 1")` 这样的硬编码。在 `rules.yaml` 中增加一块 `mapping` 区域，允许用户定义：`"我的奇葩一级标题" -> level_1`。校验器只根据 mapping 后的标准化枚举进行校验。

### 3. 重塑数据校验算法：提升精确度与容错率
* **改进中英文混排校验（替换 `has_chinese` / `has_ascii`）**：
    当前逐字符判断 `ord(char) < 128` 会被空格和数字严重污染。
    * *优化方案*：使用正则表达式清洗纯数字和空白符后，再进行字符集探测；或者更专业地，使用 `unicodedata` 模块识别字符的具体 Block（是否为 CJK 统一表意文字），从而精准决定应该校验 `east_asia_font` 还是 `ascii_font`。
* **统一物理单位换算引擎**：
    摒弃 `first_line_indent.pt / 12` 这种魔法数字（Magic Number）。建立一个专门的 `UnitConverter` 工具类，根据当前段落**实际继承的字号大小**（如小四=12pt，五号=10.5pt），动态换算 pt、cm 和字符（chars）之间的关系。

### 4. 解决长文档的性能瓶颈 (Performance Optimization)
处理几百页的 `.docx` 时，纯 Python 的字符串与 DOM 遍历是非常消耗 CPU 的。FastAPI 的 `async` 无法拯救 CPU 密集型任务。
* **引入多进程或后台任务队列**：
    将 `DocxParser.parse()` 和 `Validator.validate()` 放入 `concurrent.futures.ProcessPoolExecutor` 或 FastAPI 的 `BackgroundTasks` 中执行。
* **批量正则预编译**：
    在 `Validator` 初始化时，将所有需要用到的正则表达式（如图表匹配、参考文献匹配）使用 `re.compile()` 预先编译，避免在几万个段落的循环中反复实时编译正则。
* **惰性加载与流式校验（Generator 模式）**：
    如果可能，将 `DocxParser` 改造为 Python 生成器 (`yield` 模式)。解析出一个段落立刻扔给 Validator 校验并产出 Issue，而不是等几十兆的文档全部解析进内存列表（`parsed_data`）后再校验，从而大幅度降低峰值内存占用。

### 5. 补齐闭环：打通 Validator 与 Fixer
MVP 阶段最大的遗憾是“查而不改”。
* 在 `Validator` 发现错误生成 `issue` 时，同时生成一个**标准化的修复补丁指令 (Patch Object)**，例如：`{"action": "set_font", "target_run_id": "...", "value": "Times New Roman"}`。
* 在 `engine` 目录中完善 `Fixer` 或引入 `Reporter` 类，接收这些 Patch，直接调用 `python-docx` 将属性覆写回原始内存对象，最后统一调用 `doc.save('checked.docx')`，实现真正的“一键查改结合”。

如果我们将视角从“底层的代码 Bug”拔高到**系统整体架构、进阶排版特性以及本地客户端的安全性**，这个系统在走向一个成熟的商业级/开源高可用软件的过程中，还有以下几个极其关键的进阶改进点：

### 1. 本地微服务的“隐形安全炸弹” (Local API Security Risk)
* **现状**：系统通过 `FastAPI` 在本地（如 `127.0.0.1:8000`）开放接口供 `PyWebView` 的前端调用。
* **痛点**：这是许多本地 Web 混合应用容易忽略的致命弱点。如果本地服务没有配置严格的 CORS（跨域资源共享）或 Token 鉴权，当用户在浏览器中访问一个恶意的公网网页时，该网页的脚本可以直接向 `http://127.0.0.1:8000/api/upload` 或 `/api/rules` 发送请求。
* **后果**：恶意网页可能会静默窃取用户本地正在处理的学位论文（涉及未公开的学术成果、专利数据），造成严重的**学术泄密**。
* **改进**：必须在 FastAPI 启动时动态生成一个一次性的安全 Token（或分配随机动态端口），并通过 `pywebview` 的 `js_api` 注入到前端，前端所有 HTTP 请求必须携带此 Token。

### 2. “巨石型”校验器缺乏插件化架构 (Monolithic Validator Lack of Plugins)
* **现状**：目前的 `Validator.validate` 是一整个巨大的函数，里面堆砌了无数的 `if-else`。
* **痛点**：这种“巨石结构（Monolithic）”违反了开闭原则（OCP）。随着不同学校提出各种奇葩的格式要求（例如：要求特定级别的标题必须使用特定的编号样式，或者图表必须启用跨页断行），这个函数会膨胀到无法维护。
* **改进**：引入**策略模式（Strategy Pattern）与插件化架构**。将每一个校验点抽象为一个独立的类（如 `FontValidator`, `IndentValidator`, `HierarchyValidator`）。在初始化时，根据 `rules.yaml` 的配置，动态加载需要的校验器链（Validator Chain）。这样未来新增规则只需新增一个文件，无需修改核心引擎。

### 3. Word 高级排版特性的“彻底失明” (Blindness to Advanced Pagination)
目前引擎只关注了“字”和“段”的外观，完全忽略了学术论文中极度重要的**“流式排版控制（Pagination & Flow）”**。
* **孤行控制 (Widow/Orphan Control)**：系统无法检测段落是否开启了“孤行控制”。学术规范通常严禁一段文字的最后一行单独掉到下一页，或第一行单独留在上一页。
* **与下段同页 (Keep with Next)**：这是论文**标题排版**的铁律。标题绝对不能孤零零地出现在一页的最后一行，而正文在下一页。目前引擎完全没有提取和校验 `para.paragraph_format.keep_with_next` 属性。
* **隐藏文字与修订模式 (Hidden Text & Track Changes)**：许多学生会在文档中留下未接受的修订记录或隐藏的批注。当前引擎会将被打上“删除线”的隐藏修订文字也当作正文进行校验，产生极度混乱的误报。必须在解析前清理或屏蔽修订模式内容。

### 4. IPC 通信的“黑洞”与超时风险 (IPC Blackhole & Timeout)
* **现状**：纯异步接口处理。
* **痛点**：前端 Vue 3 发送一个上传请求给 FastAPI 处理校验。对于一篇 300 页、包含大量高清图和复杂域代码的博士论文，解析和校验可能需要 15-30 秒甚至更久。
* **后果**：普通的 HTTP 请求在这种耗时下会导致前端长时间“假死”（一直转圈）。用户不知道系统是卡死了还是在处理中，极易强制关闭软件。
* **改进**：
    * 必须引入 **Server-Sent Events (SSE)** 或 **WebSocket**。
    * 后端在解析 DOM、校验规则、生成报告的每个阶段，实时向前端推送进度百分比（例如 `{"status": "parsing_dom", "progress": 45}`）。让前端的“毛玻璃 UI”能展示平滑的进度条，这才符合“极客 UI”的标准。

### 5. 垃圾回收与临时文件灾难 (Temp Files & Resource Leaks)
* **现状**：依赖本地硬盘读写 (`data/` / `tests/temp/`)。
* **痛点**：系统在生成 `[原名]_checked_report.docx` 时，如果发生崩溃、强杀进程，或者用户连续上传了 50 次文档进行调试，本地临时文件夹会迅速堆积大量废弃的 `.docx` 文件。
* **改进**：
    * 引入 `tempfile` 模块或在每次 FastAPI 的 Lifespan 结束时执行严格的目录清理逻辑。
    * 文件在内存中使用 `io.BytesIO` 进行流转，非必要绝不落盘（Zero-Disk IO 策略），只有当用户点击“导出报告”时，才将内存中的流写入用户指定的本地路径。这不仅能解决垃圾堆积问题，还能大幅提升处理速度。

---
**总结您的 MVP 现状**：
它目前是一个“看起来很酷（Vue 3 毛玻璃），但内心很脆弱”的原型。如果要正式发布 1.0 版本让全校同学使用，您需要先进行**底层状态机重构（解决误报）**，然后**重写正则与继承逻辑（解决漏报）**，最后**补齐安全隔离与进度条机制（提升工程健壮性）**。