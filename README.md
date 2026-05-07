# 智能旅行助手 Mini Trip Assistant

一个基于 **LLM + Tools + Memory + FastAPI + Web UI** 的智能旅行规划 Agent 原型。用户只需要填写出发地、目的地、日期、人数、节奏、预算和偏好，系统就可以自动调用多种工具生成旅行方案，并支持多轮修改、历史版本恢复、项目快照保存和 Markdown / HTML / PDF 导出。

## 项目目标

本项目的目标是构建一个“可真实辅助旅行规划”的智能助手，而不只是简单生成一段文本。

它希望解决的问题包括：

- 根据用户需求生成结构化、可阅读、可修改的旅行计划。
- 在生成前引入天气、交通、预算、景点、酒店、城市活动等工具结果，减少纯大模型幻觉。
- 在生成后继续检查图片匹配、开放时间风险、路线合理性等真实旅行约束。
- 保存每一次行程快照，让用户可以回看历史版本、恢复上一版、继续编辑和导出报告。
- 提供简洁直观的 Web 页面，让完整流程可以通过浏览器使用。

## 主要内容

项目目前包含两种使用形态：

- **Web 版**：基于 FastAPI + 原生 HTML/CSS/JS，提供首页创建行程、历史项目、行程详情、版本记忆、导出与反馈等页面。
- **CLI 版**：保留命令行入口，可通过菜单创建、读取、修改、保存和导出行程。

核心功能包括：

- 旅行需求采集：出发地、目的地、日期、天数、人数、偏好、节奏、预算。
- Agent 工具规划：由 LLM 判断需要调用哪些工具。
- 多工具执行：地图、天气、预算、POI、路线、酒店、交通、开放时间、图片、城市活动等。
- 行程生成：综合用户需求和工具结果生成每日行程。
- 多轮修改：用户可以输入新的修改要求，系统基于当前行程继续调整。
- 记忆管理：记录偏好、约束、避免地点和版本历史。
- 历史快照：保存不同版本的项目 JSON 文件。
- 版本恢复：支持恢复上一版行程。
- 报告导出：支持 Markdown、HTML、PDF。
- 效果评估：记录修改次数、恢复次数、导出次数、采纳状态、满意度等指标。

## 项目亮点

- **不是单次问答，而是完整 Agent 流程**  
  从需求采集、工具规划、工具执行、行程生成，到后处理校验、保存和导出，形成完整闭环。

- **工具增强生成结果**  
  行程生成前会引入真实工具信息，例如城市定位、天气、交通、酒店、景点和预算，提升规划结果的可信度。

- **支持持续迭代**  
  用户可以反复修改同一个行程，系统会保留项目状态、版本历史和记忆信息。

- **项目快照与恢复机制**  
  每次保存和修改都会形成可追踪版本，方便回看历史方案或恢复上一版。

- **Web 化体验完整**  
  包含首页、历史页、详情页、抽屉式记忆面板、导出记录、反馈表单和指标展示，适合演示和二次开发。

- **导出能力完整**  
  可以将最终旅行方案导出为 Markdown、HTML 或 PDF，方便分享和归档。

## 视频展示

> 这里可以放项目演示视频链接。

示例：

- Bilibili：`待补充`
- GitHub Releases 视频文件：`待补充`
- 本地演示文件：`docs/demo.mp4`

建议视频内容：

1. 首页填写旅行需求并生成行程。
2. 查看详情页中的基础信息、天气预算、交通建议和每日行程。
3. 输入修改要求，演示多轮调整。
4. 打开记忆与版本抽屉。
5. 导出 HTML / PDF 报告。
6. 查看历史项目和不同版本快照。

## 技术栈

### 后端

- Python
- FastAPI
- Pydantic
- Uvicorn
- OpenAI-compatible Chat Completions API

### 前端

- HTML
- CSS
- JavaScript
- 原生 Fetch API

### Agent 与工具

- LLM 工具规划
- 高德地图相关 API：地理编码、POI、天气、路线、酒店、交通等
- Unsplash 图片搜索
- Ticketmaster 城市活动搜索
- 本地 JSON 存储
- Markdown / HTML / PDF 导出

## 项目结构

```text
mini_trip_assistant/
├── api/
│   ├── main_api.py          # FastAPI 应用入口
│   ├── schemas.py           # API 请求模型
│   └── trip_routes.py       # 行程相关 API 路由
├── frontend/
│   ├── index.html           # 首页：创建行程
│   ├── history.html         # 历史项目页
│   ├── detail.html          # 行程详情页
│   ├── styles.css           # 页面样式
│   └── js/
│       ├── common.js
│       ├── home.js
│       ├── history.js
│       └── detail.js
├── tools/                   # 外部工具封装
├── saved_trips/             # 行程项目快照
├── exports/                 # 导出的报告文件
├── app.py                   # CLI 主流程
├── main.py                  # CLI 启动入口
├── trip_service.py          # 核心业务服务
├── planner.py               # 行程生成
├── itinerary_editor.py      # 行程修改
├── memory_manager.py        # 记忆与版本管理
├── storage.py               # 项目存储
├── exporter.py              # 报告导出
├── requirements.txt
└── README.md
```

## 环境准备

建议使用 Python 3.10+。

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS / Linux：

```bash
source .venv/bin/activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

## 环境变量配置

在项目根目录创建 `.env` 文件：

```env
LLM_API_KEY=your_llm_api_key
LLM_BASE_URL=https://your-openai-compatible-endpoint/v1
LLM_MODEL=your_model_name

AMAP_API_KEY=your_amap_api_key
UNSPLASH_ACCESS_KEY=your_unsplash_access_key
TICKETMASTER_API_KEY=your_ticketmaster_api_key
```

说明：

- `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL` 用于调用 OpenAI-compatible 大模型接口。
- `AMAP_API_KEY` 用于地图、天气、路线、POI、酒店、交通等工具。
- `UNSPLASH_ACCESS_KEY` 用于补充旅行图片。
- `TICKETMASTER_API_KEY` 用于查询城市活动信息。

部分工具密钥缺失时，项目仍可能运行，但对应工具会返回缺失配置提示，生成质量会受到影响。

## 启动方式

### 启动 Web 版

```bash
uvicorn api.main_api:app --host 127.0.0.1 --port 8000 --reload
```

浏览器打开：

```text
http://127.0.0.1:8000/
```

常用页面：

```text
首页：http://127.0.0.1:8000/
历史项目：http://127.0.0.1:8000/history
API 文档：http://127.0.0.1:8000/docs
```

### 启动 CLI 版

```bash
python main.py
```

CLI 版会通过菜单完成创建行程、读取历史、修改、保存、导出、恢复上一版和查看记忆等操作。

## API 简介

主要接口：

```text
POST /api/trips/generate    生成新行程
GET  /api/trips             获取历史项目
GET  /api/trips/detail      获取行程详情
POST /api/trips/edit        修改行程
POST /api/trips/restore     恢复上一版
GET  /api/trips/memory      获取当前记忆
POST /api/trips/export      导出报告
POST /api/trips/adopt       标记采纳
POST /api/trips/feedback    提交反馈
```

完整接口说明可在启动服务后访问：

```text
http://127.0.0.1:8000/docs
```

## 使用流程

1. 打开首页，填写旅行需求。
2. 点击“生成行程”，等待系统调用工具和大模型。
3. 在详情页查看基础信息、天气预算、交通建议、每日行程、酒店建议和风险提示。
4. 如需调整，在“修改行程”中输入新的要求。
5. 使用“查看当前记忆”了解偏好、约束和版本历史。
6. 导出 Markdown / HTML / PDF 报告。
7. 在历史项目页查看不同项目和快照版本。

## 数据与导出

- `saved_trips/`：保存项目快照 JSON 文件。
- `exports/`：保存导出的 Markdown、HTML、PDF 文件。
- 每个项目会记录 `project_id`、`snapshot_version`、`trip_data`、`tool_results`、`memory`、`version_history`、`export_history`、`evaluation` 等信息。

如果要上传到 GitHub，建议不要提交真实密钥文件：

```text
.env
```

项目已提供 `.env.example` 作为配置示例。

## 上传到 GitHub 参考命令

如果当前目录还不是 Git 仓库，可以执行：

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/你的用户名/你的仓库名.git
git push -u origin main
```

如果已经是 Git 仓库：

```bash
git add README.md
git commit -m "Add project README"
git push
```

## 后续优化方向

- 增加用户登录和多用户项目隔离。
- 使用数据库替代本地 JSON 文件存储。
- 增加地图可视化路线展示。
- 增加更完整的错误恢复和工具降级策略。
- 增加自动化测试和端到端浏览器测试。
- 部署到云服务器或 Serverless 平台，形成可公开访问的在线 Demo。
