# 基于 Python + LangGraph 的酒店预订系统

一套前后端分离的酒店在线预订系统：Django 5.2 + DRF 提供 REST API，Vue 3 + Vite + Element Plus 构建界面，
AI 层使用 LangChain + LangGraph 编排 ReAct 智能体（OpenAI 兼容协议接入 DeepSeek 等大模型）。

- 用户端：登录注册、首页大厅、臻选客房、客房详情（预订 / 评价 / 收藏）、我的订单、我的收藏、关于我们（留言反馈）、个人中心、AI 智能预订助手
- 管理端：管理员登录 + 用户 / 房型 / 房间 / 订单 / 留言 / 评论 / 收藏 七类资源的完整增删改查

---

## 一、目录结构

```
code/
├─ backend/                        # 后端 Django 工程
│  ├─ config/                      # 工程配置（settings / urls / wsgi）
│  ├─ accounts/                    # 自定义用户模型 + JWT 登录注册 + 个人中心
│  ├─ rooms/                       # 房型 / 房间 / 订单 / 评价 / 收藏
│  ├─ feedback/                    # 留言反馈
│  ├─ AiChat/                      # AI 对话会话持久化 + LangGraph 智能体
│  │  ├─ Agent/graph.py            # 智能体图结构（agent ⇄ tools 循环）
│  │  ├─ Agent/hotel_tools.py      # 4 个业务工具（闭包绑定 user_id）
│  │  └─ Agent/utils/              # 模型配置、消息序列化、业务序列化
│  ├─ admin_panel/                 # 管理后台通用资源接口
│  ├─ common/utils.py              # 统一响应封装
│  ├─ scripts/                     # 演示数据初始化、智能体图导出
│  ├─ media/rooms/                 # 房型封面图片
│  ├─ .env / .env.example          # 环境变量
│  └─ requirements.txt
├─ frontend/                       # 前端 Vue 3 工程
│  ├─ src/api/                     # axios 封装 + 各模块接口
│  ├─ src/stores/                  # Pinia：用户登录态 / 管理员登录态
│  ├─ src/router/                  # 路由与两级守卫
│  ├─ src/admin/                   # 管理端"配置驱动 UI"配置
│  ├─ src/components/              # 布局、轮播、通用资源表格
│  └─ src/views/                   # 用户端 9 个页面 + 管理端 7 个页面
├─ start_mysql.bat                 # 一键启动 MySQL
├─ start_backend.bat               # 一键启动后端
├─ start_frontend.bat              # 一键启动前端
├─ stop_all.bat                    # 一键停止全部服务（前端 / 后端 / MySQL）
├─ stop_services.py                # 停止逻辑实现（含 MySQL 优雅关闭）
├─ db.sql / init_data.sql          # 原始建表与房型房间数据（参考）
└─ README.md
```

## 二、本机已完成的运行环境

| 组件 | 位置 / 版本 | 说明 |
| --- | --- | --- |
| Python | 3.13.14 | 虚拟环境位于 `backend/.venv` |
| Node.js | 22.22.2 | 前端依赖已安装于 `frontend/node_modules` |
| MySQL | 8.0.46（`D:\mysql\mysql-8.0.46-winx64`） | 已初始化数据目录并创建 `hotel_booking` 库 |
| 数据库账号 | `root` / `123456` | 连接串见 `backend/.env` |

## 三、启动与停止服务

### 启动（推荐双击一键脚本）

在 `code\` 目录下依次双击三个脚本，每个脚本会独占一个命令行窗口，**窗口保持打开、不要关闭**：

| 顺序 | 双击这个 | 作用 | 成功标志 |
| --- | --- | --- | --- |
| 1（可跳过） | `start_mysql.bat` | 启动 MySQL 3306 | 出现 `ready for connections` |
| 2 | `start_backend.bat` | 启动 Django 8000 | 出现 `Starting development server at http://127.0.0.1:8000/` |
| 3 | `start_frontend.bat` | 启动 Vite 5173 | 出现 `Local: http://localhost:5173/` |

停止服务见下方「停止服务（一键）」。

> MySQL 若已常驻运行，第 1 步可跳过。同一服务不要启动两次，否则会提示端口被占用（这是正常提示，不是故障）。

浏览器访问 <http://localhost:5173> 即可，演示账号见下一节。

### 手动启动（与脚本等价）

```powershell
# MySQL
D:\mysql\mysql-8.0.46-winx64\bin\mysqld.exe --basedir="D:/mysql/mysql-8.0.46-winx64" `
  --datadir="D:/mysql/mysql-8.0.46-winx64/data" --port=3306 --bind-address=127.0.0.1 --console

# 后端（不用 activate，直接调用虚拟环境解释器最稳）
cd code\backend
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000

# 前端
cd code\frontend
npm run dev
```

首次部署时执行数据库迁移与演示数据注入（本机已完成，可跳过）：

```powershell
cd code\backend
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe scripts\init_data.py
```

### 修改 `.bat` 脚本时必须遵守的格式

`.bat` 文件对编码和换行极其敏感，三个脚本均为 **CRLF 换行 + 纯 ASCII + 无 BOM**。若自行编辑后脚本失效（双击一闪而过、不执行），优先检查这三项：

- **换行必须是 CRLF**：用 LF（Unix 换行）保存会让 `cmd` 解析错行，`pause` 和部分命令被跳过，窗口一闪即关。
- **不要写入中文等多字节字符**：配合 `chcp 65001` 时 `cmd` 存在按字节偏移读行的缺陷，会导致后续命令错位丢失。因此脚本内的提示信息统一使用英文。
- **不要加 UTF-8 BOM**：BOM 会让首行 `@echo off` 被识别成非法命令。

用记事本编辑默认满足以上条件；用 VS Code 编辑后请确认右下角换行符显示为 `CRLF`。

### 停止服务（一键）

在 `code\` 目录下双击：

```powershell
stop_all.bat
```

脚本会自动停掉 **前端 5173 → 后端 8000 → MySQL 3306**（按此顺序，避免数据库在前后端写入时被切断），执行完打印每个服务的最终状态。

两个设计细节：

- **按端口反查 PID 再精确关闭**，不按 `python.exe` / `node.exe` 进程名批量杀，因此不会误伤机器上其他 Python / Node 程序。
- **MySQL 走官方 `mysqladmin shutdown` 优雅关闭**（日志输出 `Normal shutdown` → `Shutdown complete`），保证 InnoDB 正常刷盘；口令通过 `MYSQL_PWD` 环境变量传递，不出现在命令行参数里。

核心逻辑在同目录的 `stop_services.py`，可直接运行；`stop_all.bat` 只是它的启动器。

若只启动了其中一两个服务，脚本会自动跳过未运行的部分，不会报错。

> 手动方式（脚本没用时）：在各自窗口按 `Ctrl + C`；或按端口查进程号后 `taskkill /PID <PID> /F`。
> 不要用 `taskkill /F /IM python.exe` 这类按名批量杀，会连带杀掉机器上其他 Python 程序。

## 四、演示账号

| 端 | 地址 | 账号 | 密码 |
| --- | --- | --- | --- |
| 用户端 | <http://localhost:5173/login> | `guest` | `guest123456` |
| 管理端 | <http://localhost:5173/admin/login> | `admin` | `admin123456` |
| Django Admin | <http://127.0.0.1:8000/admin> | `admin` | `admin123456` |

演示数据包含 8 种房型、35 间客房，以及 2 笔订单、2 条收藏、1 条评价。

## 五、启用 AI 智能体

AI 助手基于 OpenAI 兼容协议，可对接任意兼容服务。**密钥与 Base URL 必须来自同一个平台**，
否则会出现 `401 Authentication Fails` —— 这是最常见的配置错误。

### 平台一：阿里云百炼（本项目当前使用）

```ini
AI_CHAT_MODEL=qwen3.8-flash
AI_CHAT_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_CHAT_API_KEY=你的百炼API Key
AI_CHAT_TEMPERATURE=0.2
```

- 密钥获取：阿里云百炼控制台 → API-KEY 管理。新签发的密钥以 `sk-ws-` 开头，旧格式为 `sk-`，两者均可正常调用。
- 已实测支持工具调用（Function Calling）的模型：`qwen3.8-flash`、`qwen3.8-max`、
  `deepseek-v4-pro-0813`、`deepseek-v3`。改 `AI_CHAT_MODEL` 一行即可切换。

### 平台二：DeepSeek

```ini
AI_CHAT_MODEL=deepseek-chat
AI_CHAT_BASE_URL=https://api.deepseek.com
AI_CHAT_API_KEY=你的DeepSeek API Key
AI_CHAT_TEMPERATURE=0.2
```

- 密钥获取：<https://platform.deepseek.com/api_keys>，格式为 `sk-` 加 32 位字符（约 35 位）。
- 若手上的密钥长达上百位且以 `sk-ws-` 开头，说明它属于阿里云百炼，请改用上面的配置。

### 两个必须注意的点

1. **只改 `.env`，不要改 `.env.example`。** 后者是提交到仓库的模板文件，真实配置一律以 `.env` 为准。
2. **改完必须重启后端** —— `.env` 只在 Django 启动时读取一次。

未配置密钥时其余功能均可正常使用，AI 页面会提示"尚未配置大模型密钥"。

智能体的 4 个工具：`search_room_types`（条件查房 + 收藏优先排序）、`get_user_context`（历史订单与收藏）、
`get_user_profile`（预订联系人资料，判断能否自动填单）、`create_booking`（事务 + 行锁安全下单）。

导出智能体图结构（可选，需联网渲染 PNG）：

```powershell
cd code\backend
.\.venv\Scripts\python.exe scripts\export_agent_graph.py
```

## 六、一键自检（可选）

后端启动后，可运行内置冒烟测试脚本，一次性校验登录、房型、订单、收藏、评价、留言、
AI 会话与后台 7 类资源等共 31 项用例，并验证下单/取消的库存一致性：

```powershell
cd code\backend
.\.venv\Scripts\python.exe scripts\smoke_test.py
```

全部通过时会输出 `冒烟测试结果：31/31 通过` 与 `ALL-PASS`。
脚本只打印用例名与 HTTP 状态码，不会输出令牌等敏感内容。

两点设计说明：

- **密钥与平台匹配校验**：脚本会静态比对 `AI_CHAT_API_KEY` 的格式与 `AI_CHAT_BASE_URL`。
  例如检测到百炼的 `sk-ws-` 密钥却指向 DeepSeek 时会直接判 FAIL，
  不必等到接口返回 401 才发现。
- **AI 真实调用会跳过**：已配置密钥时该用例标记为 `[SKIP]`，不真实请求模型，
  避免每次自检都消耗 token；未配置密钥时则校验流式接口是否正确返回「友好提示」事件。

> 注意：账号模块（`/api/accounts/`）返回**原样结构**（如 `{"access": "...", "user": {...}}`），
> 而客房、留言、AI、后台模块返回统一包装 `{"code", "msg", "data"}`。前端已按该差异适配，接入时请勿混用。

## 七、主要接口一览

| 模块 | 前缀 | 关键端点 |
| --- | --- | --- |
| 账号 | `/api/accounts/` | `register/`、`login/`、`profile/`（GET/PATCH）、`change-password/`、`logout/` |
| 客房 | `/api/rooms/` | `types/`、`types/<id>/`、`stats/`、`types/<id>/favorite/`、`types/<id>/book/`、`bookings/`、`bookings/<id>/cancel/`、`types/<id>/reviews/`、`favorites/` |
| 留言 | `/api/feedback/` | ``（GET 列表 / POST 提交） |
| AI | `/api/ai-chat/` | `chat/`、`chat/stream/`（SSE）、`sessions/`、`sessions/<session_id>/` |
| 管理端 | `/api/admin-panel/` | `login/`、`profile/`、`stats/`、`users/`、`room-types/`、`rooms/`、`bookings/`、`feedbacks/`、`reviews/`、`favorites/`（均支持列表 / 新增 / 详情 / 更新 / 删除） |

统一响应结构：`{"code": 业务状态码, "msg": 提示信息, "data": 业务数据}`。

## 八、关键技术点

1. **自定义用户模型 + JWT**：`AbstractUser` 扩展手机号与角色，`simplejwt` 签发 8 小时令牌；
   用户端与管理端使用两套独立令牌存储键，互不干扰。
2. **库存并发安全**：下单与取消订单均在 `transaction.atomic()` 内以 `select_for_update()` 锁定房型行与房间行，
   先锁后判，杜绝超卖；取消订单将订单置为已取消、释放物理房间、回补库存三步原子完成。
3. **配置驱动的管理端**：后端 `BaseAdminResourceAPIView` 一个基类提供 5 种通用操作，前端 `AdminResourceTable`
   读取 `resourceConfigs` 自动渲染搜索、表格与表单，新增一个管理模块只需写配置。
4. **LangGraph 智能体**：`StateGraph(MessagesState)` + `ToolNode` + `tools_condition` 构成 ReAct 循环，
   `InMemorySaver` 检查点以 `session_id` 作为线程编号保存多轮上下文；工具通过闭包绑定 `user_id`，
   模型无法越权访问他人数据。
5. **SSE 流式对话**：后端以 `stream_mode=["messages", "values"]` 双模式推送 token 与图状态快照，
   前端用 `fetch` + `ReadableStream` 手动解析事件块，实现打字机效果与工具调用过程可视化。
6. **媒体地址处理**：后端序列化时通过 `request.build_absolute_uri` 把相对路径拼成绝对 URL，
   前端 `resolveMediaUrl` 兜底处理，Vite 同时代理 `/api` 与 `/media`。

## 九、常见问题

- **前端提示 401 / 自动跳登录页**：令牌已过期（8 小时），重新登录即可；用户端与管理端需分别登录。
- **接口报 500 且提示数据库连接失败**：确认 MySQL 窗口仍在运行，`backend/.env` 中密码为 `123456`。
- **图片不显示**：确认 `backend/media/rooms/` 下存在 8 张 `.avif` 封面图，且 Vite 已代理 `/media`。
- **AI 页面报"AI 智能体执行失败"**：检查 `AI_CHAT_API_KEY` 是否填写、`AI_CHAT_BASE_URL` 是否可访问。
- **双击 `start_*.bat` 窗口一闪而过、服务没起来**：脚本换行符被改成了 LF 或混入了中文字符。
  用记事本打开该脚本另存一次，或参照「三、启动步骤」末尾「修改 `.bat` 脚本时必须遵守的格式」修正。
- **双击 `start_*.bat` 提示「端口已被占用 / Address already in use」**：该服务已在运行，
  说明脚本本身正常。先确认是否已开过窗口，或按端口结束残留进程后再启动。
- **文件名看不到 `.bat` 后缀**：Windows 默认隐藏已知扩展名，右键 → 属性查看「文件类型」为
  「Windows 批处理文件 (.bat)」即正常，双击可直接运行。
- **AI 报 `401 Authentication Fails ... api key is invalid`**：不是密钥坏了，而是**密钥与 Base URL 平台不匹配**。
  例如把阿里云百炼的 `sk-ws-` 密钥发给了 `https://api.deepseek.com`，必然 401。
  请对照「五、启用 AI 智能体」把 `AI_CHAT_API_KEY` 与 `AI_CHAT_BASE_URL` 配成同一平台。
- **AI 报 `402` / 余额不足**：平台账户欠费，充值后重试。
- **填了密钥却不生效**：确认改的是 `backend/.env` 而非 `.env.example`，且已重启后端。
- **AI 报 `404` 或模型不存在**：`AI_CHAT_MODEL` 名称在该平台不存在，参考上文替换为已实测可用的模型名。
