# AI 智能体模块 · 答辩讲稿

> 适用场景：课程设计 / 毕业设计答辩，本人负责「AI 智能体模块」部分
> 代码范围：`backend/AiChat/`（1313 行）+ `frontend/src/views/AiChatView.vue` + `frontend/src/api/aiChat.js`
> 讲解原则：**先说为什么这样设计，再说怎么实现**。评委记住的是你的决策逻辑，不是你的代码行数。

---

## 零、30 秒开场陈述（背下来，第一个说）

> "我负责的是 AI 智能体模块。这个模块的目标不是做一个能聊天的客服，而是让大模型**真正具备下单能力**。
>
> 用户用自然语言说『帮我订一间两人住、含早、五百以内的房』，系统要能自己查库、自己判断库存、自己完成订单写入。
>
> 技术上我用 **LangGraph 显式编排 ReAct 循环**，把 4 个酒店业务能力封装成工具交给模型调用，并且用**闭包绑定用户身份**保证它只能操作当前登录用户的数据。
>
> 整个模块 1313 行代码，核心只有三个文件：`graph.py` 编排、`hotel_tools.py` 工具、`views.py` 接口。"

这段陈述的价值：**一句话说清目标、一句话说清技术、一句话说清代码规模**。后面所有内容都是这三句话的展开。

---

## 一、模块定位：先划清边界

讲解时要主动说明"我负责什么、不负责什么"，这是责任边界，也是专业性的体现。

| 属于本模块 | 不属于本模块 |
| --- | --- |
| 智能体编排逻辑（LangGraph 状态图） | 用户注册登录（`accounts` 模块） |
| 4 个业务工具的封装与参数校验 | 房型/订单的底层数据模型（`rooms` 模块） |
| 对话接口（同步 + SSE 流式） | 前端页面框架、路由（前端公共部分） |
| 对话会话与消息的持久化 | 库存扣减的**事务策略**（复用 `rooms` 模块的业务规则） |
| 大模型配置与异常翻译 | 大模型服务本身（阿里云百炼，外部依赖） |

> **答辩技巧**：主动承认"库存事务这块我复用了 `rooms` 模块已有的行锁方案，保证 AI 下单和页面下单走同一套规则"，比假装全是自己写的更可信，也顺带说明了你理解了模块间协作。

---

## 二、技术选型：为什么是 LangGraph

这是**必被问到**的问题。不要答"因为教程用了"，要答出比较。

| 方案 | 优点 | 为什么不选 |
| --- | --- | --- |
| 直接调 LLM API（拼 prompt） | 最简单 | 无法调用工具，只能聊天，做不了下单 |
| LangChain `AgentExecutor` | 开箱即用 | 执行流程是**黑盒**，无法插入自定义节点、难以精细控制流式输出 |
| **LangGraph `StateGraph`（本项目）** | 流程**显式可见**、可加检查点、天然支持流式、可扩展人工审批节点 | 学习成本略高，需理解状态图范式 |

**关键论点（这句要说得重）**：

> "选 LangGraph 的核心原因是——**业务流程需要被显式表达，而不是藏在框架里**。
>
> 酒店的预订流程有强约束：必须先查房、再确认、最后下单。用 `AgentExecutor` 我只能靠 prompt 祈求模型遵守；用 LangGraph 我把这个循环画成一张图，每个节点做什么、什么条件下跳转，都是代码里看得见的。"

**加分补充**：可以现场打开 `backend/images/agent_graph.png` 展示这张图——这是用 `graph.get_graph().draw_mermaid_png()` 导出的**真实**图结构，不是手画的。这一手很能说明问题。

---

## 三、整体架构：四层分离

讲架构时用这个图，从左到右是"一次用户提问的完整旅程"。

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  ① 接口层     │   │  ② 编排层     │   │  ③ 工具层     │   │  ④ 持久层     │
│  views.py    │──▶│  graph.py    │──▶│hotel_tools.py│──▶│ models.py    │
│              │   │              │   │              │   │ services.py  │
│  鉴权/SSE编码 │   │ ReAct 状态图  │   │ 4 个业务工具  │   │ 会话/消息落库 │
│  异常翻译     │   │ 会话检查点    │   │ user_id 闭包  │   │              │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
       ▲                                                          │
       │                      ┌──────────────┐                    │
       └──────────────────────│  ⑤ 前端       │◀───────────────────┘
                              │ AiChatView   │   会话历史可回看
                              │ SSE 手动解析  │
                              └──────────────┘
```

**分层带来的好处（讲解要点）**：

1. **接口层与智能体解耦**：`graph.py` 完全不知道 HTTP 的存在，脱离 Django 也能跑（我用它写了离线导出图结构的脚本）。
2. **工具层是唯一的数据访问入口**：模型只能通过 4 个工具碰数据库，不能直接拼 SQL。
3. **持久层与编排层解耦**：LangGraph 的上下文存在内存检查点里，对话记录另外落 MySQL——**两者目的不同**，后面会详细讲。

---

## 四、五个核心设计决策（答辩的主体，务必讲透）

### 决策 1：为什么是 ReAct 循环，而不是一次性提问

**ReAct = Reasoning（推理）+ Acting（行动）**，即"想一步、做一步、看结果、再想"。

```
用户提问 ──▶ agent 节点（模型思考）
                │
                ├─ 需要数据？──▶ tools 节点（执行工具）──▶ 结果回传给 agent
                │                                            │
                └─ 信息够了？──▶ 生成最终回复，结束 ◀──────────┘
```

**为什么必须这样**：用户问"推荐一个适合两个人的房型"，模型**不知道**你数据库里有什么房型。它必须先调 `search_room_types` 拿到真实数据，再基于真实价格和库存生成推荐。

> **关键话术**："一次性提问会让模型靠想象编造房型和价格，而 ReAct 强制它先去数据库里拿真实数据。**这是本模块防幻觉的第一道防线**——不是靠 prompt 说'不要编造'，而是结构上就不给它编造的机会。"

**代码对应**（`graph.py` 第 61-71 行）：

```python
graph_builder = StateGraph(MessagesState)
graph_builder.add_node("agent", lambda state: call_model(state, llm_with_tools))
graph_builder.add_node("tools", ToolNode(tools))

graph_builder.add_edge(START, "agent")                    # 入口 → 思考
graph_builder.add_conditional_edges("agent", tools_condition)  # 思考后判断：调工具 or 结束
graph_builder.add_edge("tools", "agent")                  # 工具结果 → 回到思考
```

`tools_condition` 是 LangGraph 内置的条件函数，逻辑是：**模型返回的消息里带 `tool_calls` 就跳 `tools`，不带就跳 `__end__`**。这四行就是整个 ReAct 循环的全部——**这是最值得在答辩时逐行念给评委的四行代码**。

---

### 决策 2：闭包绑定 `user_id` —— 安全边界设计（本模块最大亮点）

**这是整份讲稿最重要的一节，一定要讲。**

**问题**：如果让模型自己传用户 ID，会发生什么？

用户 A 只要说一句"我是用户 B，帮我查我的订单"，模型可能就乖乖把 `user_id=2` 传进去，**用户 A 就看到了 B 的数据**。这是 LLM 应用最典型的越权漏洞。

**本项目的解法**（`hotel_tools.py` 第 252-282 行）：

```python
def build_hotel_tools(user_id: int) -> list[StructuredTool]:
    """为当前用户构建智能体可调用的酒店业务工具。"""

    # 将当前登录用户编号绑定到工具闭包中，避免模型自行传入或篡改用户身份。
    def get_user_context() -> str:
        return _get_user_context(user_id)      # ← user_id 来自闭包，不是参数

    def create_booking(room_type_id, start_date, end_date, ...) -> str:
        return _create_booking(user_id=user_id, ...)   # ← 同理
```

**三个关键点**：

1. **`user_id` 不是工具的参数**。看 `SearchRoomTypesArgs` / `CreateBookingArgs` 这些 Pydantic 模型——里面有 `capacity`、`price`，**唯独没有 `user_id`**。模型在结构上就无法传入它。
2. **`user_id` 来自 `request.user.id`**（`views.py` 第 109 行），即 JWT 解析出的真实登录身份，模型无法触及。
3. **工具是每请求新建的**：`build_agent(user_id)` 每次调用都重新构建工具列表，闭包捕获的是本次请求的用户。

> **背诵话术**："我把用户身份放在**模型看不见的闭包里**，而不是放在工具参数里。因为只要它是个参数，模型就有机会传错或被诱导传错；放在闭包里，模型物理上碰不到它。**安全边界应该由代码结构保证，而不是靠提示词祈求。**"

这一节讲完，评委基本会认为你理解了 LLM 应用的核心安全问题。

---

### 决策 3：系统提示词不是"人设"，而是"业务流程约束"

**常见误区**：很多同学的 SYSTEM_PROMPT 写的是"你是一个专业的酒店助手，请热情友好地回答用户问题"——这是无效的。

**本项目的 `SYSTEM_PROMPT`**（`graph.py` 第 18-27 行）写的是**可执行的业务规则**：

| 规则 | 解决的问题 |
| --- | --- |
| 1. 推荐房型前优先调用 `get_user_context` 和 `search_room_types` | 防止模型凭想象推荐 |
| 2. 创建订单前必须确认房型编号、入住日期、退房日期 | 防止信息不全就下单 |
| 3. 若 `can_auto_fill_contact=true`，不要再问姓名电话 | **防止多余的追问，提升体验** |
| 4. 只有工具返回 `missing_fields` 时才追问 | 把"该不该追问"的决策权交给数据，不交给模型 |
| 5. 用户没明确同意，只能推荐或追问，不能调用 `create_booking` | **防止误下单，最关键的约束** |
| 6. 工具失败时要向用户解释原因并给出建议 | 防止静默失败 |
| 7. 回复要简洁自然，包含关键订单信息 | 输出质量 |

> **讲解话术**："注意第 3、4 条——我没有让模型自己判断'要不要问用户电话'，而是让 `get_user_profile` 这个工具返回一个布尔字段 `can_auto_fill_contact`，模型只负责读这个字段。**能用确定性代码做的判断，就不要交给概率性的模型。**"

这句话是整场答辩的高分点。

---

### 决策 4：双通道接口 —— 同步 + SSE 流式

**为什么要两个接口？**

| 接口 | 路径 | 用途 |
| --- | --- | --- |
| 同步 | `POST /api/ai-chat/chat/` | 逻辑简单、便于测试、便于外部系统集成 |
| 流式 | `POST /api/ai-chat/chat/stream/` | 前端打字机效果，**用户不用干等 5-10 秒** |

**为什么流式很重要（用户体验层面的论据）**：

ReAct 循环可能要调 2-3 个工具，每次工具调用都是一次完整的模型往返，总耗时 5-15 秒。如果是同步接口，用户面对的是一个转圈的 loading；流式接口下，用户能看到文字逐个蹦出来，**同时在过程卡片里看到"智能体正在调用 search_room_types"**——等待焦虑被转化成"它在认真干活"的观感。

**技术实现的关键**（`graph.py` 第 103-107 行）：

```python
for stream_mode, payload in agent.stream(
    {"messages": [HumanMessage(content=message)]},
    config=config,
    stream_mode=["messages", "values"],     # ← 重点：同时订阅两种模式
):
```

> **讲解话术**："我同时订阅了两种流模式，这是这个接口的设计核心。
>
> - `messages` 模式吐出的是**逐字的内容块**（AIMessageChunk），我用来做打字机效果；
> - `values` 模式吐出的是**完整的图状态快照**，我从中提取工具调用记录，用来渲染'执行过程卡片'。
>
> **只订阅一种都做不出来**：只用 `messages` 拿不到工具调用的结构化信息，只用 `values` 就只能整段整段地跳。"

**SSE 事件协议**（`views.py` 第 62-65 行定义了编码函数）：

| 事件 | 触发时机 | 前端动作 |
| --- | --- | --- |
| `start` | 请求刚建立 | 立即显示"正在分析你的需求"，消除白屏 |
| `token` | 模型每吐出一段文字 | 追加到气泡，打字机效果 |
| `message` | 图状态更新（工具调用/结果） | 插入执行过程卡片 |
| `done` | 全部完成 | 结束 loading，刷新会话列表 |
| `error` | 任何异常 | 显示中文错误提示 |

---

### 决策 5：三层防幻觉 / 防误操作体系

这是把前面几点串起来的**总结性框架**，建议放在 PPT 的收尾页。

| 层 | 手段 | 代码位置 |
| --- | --- | --- |
| **结构层** | ReAct 循环强制先查库再回答；`user_id` 闭包绑定 | `graph.py` / `hotel_tools.py` |
| **约束层** | 系统提示词 7 条业务规则；工具 description 写明使用前提 | `graph.py` / `hotel_tools.py` |
| **校验层** | 工具入口参数校验 + 业务层事务校验 + 异常兜底 | `hotel_tools.py` |

**校验层的具体内容**（`_create_booking`，第 182-207 行），这些是**确定性的代码校验，不依赖模型**：

```python
# 1. 日期格式解析（支持 3 种格式容错）
parsed_start_date = parse_date_value(start_date, "入住日期")

# 2. 日期先后关系
if parsed_start_date >= parsed_end_date:
    return build_json_response({"success": False, "message": "入住日期必须早于退房日期。"})

# 3. 日期边界（不能订过去的房）
if parsed_start_date < date.today():
    return build_json_response({"success": False, "message": "入住日期不能早于当前日期。"})

# 4. 房型是否存在 + 库存是否充足（行锁内校验）
room_type = RoomType.objects.select_for_update().filter(pk=room_type_id).first()
if room_type.remaining_stock <= 0:
    return build_json_response({"success": False, "message": "该房型当前暂无可预订库存。"})

# 5. 是否还有空闲物理客房
room = Room.objects.select_for_update().filter(
    room_type=room_type, status=Room.Status.VACANT).first()
if room is None:
    return build_json_response({"success": False, "message": "未找到可分配的空闲房间。"})
```

> **关键话术**："这五道校验全部在 Python 里执行，**模型无权绕过**。即便模型被用户诱导传入了一个不存在的房型 ID，第 4 道校验会直接拒绝。我的原则是——**模型负责理解意图和生成表达，正确性由代码保证。**"

---

## 五、代码逐层讲解（按调用链顺序）

### 5.1 入口层：`views.py`（243 行）

**接口清单**（`AiChat/urls.py`）：

| 方法 | 路径 | 视图类 | 说明 |
| --- | --- | --- | --- |
| POST | `/api/ai-chat/chat/` | `AiChatAPIView` | 同步对话 |
| POST | `/api/ai-chat/chat/stream/` | `AiChatStreamAPIView` | 流式对话（SSE） |
| GET | `/api/ai-chat/sessions/` | `AiChatSessionListAPIView` | 历史会话列表 |
| GET/DELETE | `/api/ai-chat/sessions/<id>/` | `AiChatSessionDetailAPIView` | 会话详情 / 删除 |

**四个值得讲的实现细节**：

**① 延迟导入**（第 96 行、153 行）：
```python
# 从智能体模块延迟导入，避免未安装 LangGraph 时影响其他接口。
from AiChat.Agent.graph import run_hotel_agent
```
> 讲法："`AiChat` 依赖 LangGraph，而 LangGraph 依赖链很长（langchain-core、openai 等）。我把它放在函数内部导入，这样即使 LangGraph 没装好，**其他所有接口仍能正常工作**，只是 AI 功能不可用。这是可用性隔离。"

**② 密钥缺失的优雅降级**（第 26-28 行、90-93 行）：
```python
def is_llm_configured() -> bool:
    return bool(os.getenv("AI_CHAT_API_KEY") or os.getenv("OPENAI_API_KEY"))
```
> 讲法："没配密钥时不让它抛 500，而是返回一句中文提示，告诉用户去 `.env` 里填什么。"

**③ 异常翻译器 `describe_llm_error()`**（第 31-59 行）——**这是很实用的一个设计，值得单独讲**：

```python
if "401" in text or "authentication" in lowered:
    return "大模型鉴权失败（401）：API Key 无效或已失效。请确认 ... AI_CHAT_BASE_URL 与该平台匹配"
if "429" in text or "rate limit" in lowered:
    return "请求过于频繁（429）：已触发服务商限流，请稍后重试。"
if any(token in lowered for token in ("connection", "timed out", "timeout", "max retries", "proxy")):
    return "无法连接大模型服务：请检查本机网络或代理 ..."
```

> 讲法："大模型服务商的原始报错是英文 JSON，比如 `Error code: 401 - {'error': {'message': 'Authentication Fails...'}}`，直接给用户看毫无意义。我写了一个翻译器把 401/402/403/404/429 和网络异常映射成中文可操作提示。**这个函数在开发阶段帮我们定位了一个真实问题——密钥是阿里云百炼的，却被配到了 DeepSeek 的地址，两者不匹配导致 401。**"

（这个真实案例很有说服力，说明你的错误处理不是摆设。）

**④ SSE 响应头设置**（第 195-197 行）：
```python
response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
response["Cache-Control"] = "no-cache"
response["X-Accel-Buffering"] = "no"
```
> 讲法："`X-Accel-Buffering: no` 是给 Nginx 看的，告诉它不要缓冲这个响应。不加的话，如果将来部署时前面挡了 Nginx，流式数据会被攒成一坨再吐出来，打字机效果就没了。"

---

### 5.2 编排层：`graph.py`（133 行）

**文件职责**：定义状态图、系统提示词、会话线程映射、同步/流式两个运行入口。

**① 检查点与会话映射**（第 30、43-46 行）：

```python
MEMORY = InMemorySaver()        # 模块级单例

def build_thread_config(user_id: int, session_id: str) -> dict:
    # 以用户编号作为命名空间，避免不同用户在内存检查点中复用同一线程。
    return {"configurable": {"thread_id": f"user-{user_id}-{session_id}"}}
```

> **讲解要点（这是多轮对话的核心）**："LangGraph 用 `thread_id` 区分不同的对话线程，同一 `thread_id` 共享历史消息。
>
> 我的 `thread_id` 是 `user-{user_id}-{session_id}` 两段式。**为什么要带 `user_id`？** 如果只用 `session_id`，当两个用户恰好拿到同一个 session_id（比如前端 bug 或恶意构造），他们的上下文就会串到一起——A 会看到 B 的历史对话。加上 `user_id` 前缀后，线程天然隔离。"

**② 模型节点的封装**（第 33-40 行）：

```python
def call_model(state: MessagesState, llm_with_tools) -> dict:
    # 构造系统提示和历史消息，保证每轮都遵守预订约束。
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}
```

> 讲法："注意 `SYSTEM_PROMPT` 是**每一轮都重新拼在最前面**的，而不是只在第一轮发送。因为 `state["messages"]` 里累积的是历史对话，如果系统提示不进这个列表，多轮之后约束会被稀释。"

**③ 流式运行的完整实现**（第 89-133 行）——前面决策 4 已展开，这里补两个技术细节：

```python
# messages 模式返回 AIMessageChunk，可用于前端逐字显示模型输出。
if stream_mode == "messages":
    chunk, metadata = payload
    chunk_content = format_message_content(chunk.content)
    if metadata.get("langgraph_node") == "agent" and chunk_content:   # ← 只取 agent 节点的输出
        last_reply += chunk_content
```

> 讲法："这里有个容易出错的地方：工具节点和模型节点都会产生消息，如果不加 `metadata.get("langgraph_node") == "agent"` 这个判断，工具返回的 JSON 也会被当成回复文字吐到前端，用户会看到一堆原始 JSON。**必须只过滤出模型节点的输出。**"

另一个细节：
```python
# 先返回开始事件，确保前端立即收到响应，避免长时间等待导致超时。
yield {"event": "start", "data": {...}}
```
> 讲法："先发一个 `start` 事件，让前端立刻把 loading 显示出来。这是 SSE 的常规手法，避免首字节延迟太长。"

---

### 5.3 工具层：`hotel_tools.py`（320 行）——**本模块最重要的文件**

**四个工具的分工设计**：

| 工具 | 入参 | 用途 | 设计意图 |
| --- | --- | --- | --- |
| `search_room_types` | capacity / max_price / breakfast / window / keyword | 按条件查可订房型 | 推荐的基础，防幻觉 |
| `get_user_context` | 无 | 历史订单 + 收藏 | 做**个性化推荐**的依据 |
| `get_user_profile` | 无 | 姓名 + 电话 + 缺失字段 | 让下单能自动填表 |
| `create_booking` | 房型ID / 起止日期 / 联系人 | 真实写订单 | 唯一的写操作 |

**① 为什么把 `get_user_context` 和 `get_user_profile` 拆成两个工具？**（这是个容易被问的点）

> 讲法："两者的数据源完全不同，且使用时机不同。
>
> `get_user_context` 返回历史订单和收藏，**只在做偏好分析时需要**，数据量大（含订单详情），传给模型很费 token；`get_user_profile` 只返回姓名和电话，**在下单前才需要**，数据极小。
>
> 如果合成一个工具，那么每次分析偏好都要把联系人信息一起捞出来——既浪费 token，又扩大了敏感信息的暴露面。**职责分离在这个场景下同时优化了成本和安全性。**"

**② Pydantic 参数约束**（第 27-46 行）——这是让模型"正确调用工具"的关键：

```python
class SearchRoomTypesArgs(BaseModel):
    capacity: int | None = Field(default=None, description="入住人数下限")
    max_price: float | None = Field(default=None, description="每晚最高预算")
    breakfast: bool | None = Field(default=None, description="是否要求含早餐")
    window: bool | None = Field(default=None, description="是否要求有窗")
    keyword: str | None = Field(default=None, description="房型名称或描述关键词")
```

> 讲法："这些 `description` 不是给人看的注释，**是给模型看的**——Function Calling 时模型就是靠这些描述来决定传什么参数。所有字段都设了默认值 `None`，意味着**模型可以只传它确定知道的条件**。
>
> 这点很重要。配合工具 description 里那句『调用时只传用户明确提出的条件，未提出的条件不要传』——如果用户只说"两个人住"，模型就**只传 `capacity=2`**，不会自作主张补一个 `max_price=300`。**否则会出现'我只说了两个人住，它却给我筛掉了 500 以上的房间'这种体验事故。**"

**③ 收藏优先的推荐排序**（第 76-86 行）——**这是"智能"感的来源，答辩时值得展示**：

```python
# 读取用户收藏房型编号，用于推荐排序和结果标记。
favorite_ids = set(Favorite.objects.filter(user=user).values_list("room_type_id", flat=True))

# 先按是否收藏排序，再按价格升序排序。
room_types = sorted(
    queryset[:20],
    key=lambda item: (item.id not in favorite_ids, item.price),
)
result = [serialize_room_type(item, item.id in favorite_ids) for item in room_types[:8]]
```

> 讲法："这个排序键是个二元组：**第一优先级是'用户是否收藏过'，第二优先级才是价格**。
>
> Python 里 `False < True`，所以 `item.id not in favorite_ids` 为 `False`（即已收藏）的会排到前面。这样用户收藏过的房型会自动置顶——**模型不需要理解'用户喜欢什么'，它拿到的数据已经被按用户偏好排好序了。**
>
> 我认为这是本模块比较巧妙的一处：**把个性化逻辑放在确定性的代码里，而不是让模型去猜。**"

**④ `create_booking` 的事务与行锁**（第 194-232 行）——**技术上最硬的部分**：

```python
with transaction.atomic():
    # 第一步：锁住房型行
    room_type = RoomType.objects.select_for_update().filter(pk=room_type_id).first()
    if room_type is None or room_type.remaining_stock <= 0:
        return build_json_response({"success": False, ...})

    # 第二步：锁定一间空闲物理客房
    room = Room.objects.select_for_update().filter(
        room_type=room_type, status=Room.Status.VACANT).first()
    if room is None:
        return build_json_response({"success": False, "message": "未找到可分配的空闲房间。"})

    # 第三步：更新状态与库存
    room.status = Room.Status.OCCUPIED
    room.save(update_fields=["status"])
    room_type.remaining_stock -= 1
    room_type.save(update_fields=["remaining_stock"])

    # 第四步：计算价格并落单
    stay_days = (parsed_end_date - parsed_start_date).days
    total_price = room_type.price * stay_days
    booking = Booking.objects.create(...)
```

> **这段要讲三个点**：
>
> **第 1 点——为什么必须加锁**："假设只剩 1 间房，两个用户同时下单。如果不用锁，两个请求都读到 `remaining_stock=1`，都判定库存充足，结果卖出 2 间，库存变成 -1。这叫**超卖**。
>
> `select_for_update()` 会在数据库层加排他行锁，第二个请求必须等第一个事务提交后才能读到数据。**这是数据库层面的保证，不是应用层的判断，所以绝对可靠。**"
>
> **第 2 点——为什么按"先房型、后房间"的固定顺序加锁**："如果两段代码加锁顺序相反，就可能死锁：事务 A 持有房型锁等房间锁，事务 B 持有房间锁等房型锁，互相等待。**统一加锁顺序是避免死锁的标准做法。**"
>
> **第 3 点——异常为什么被 catch**："注意最外层有 `try...except`，异常时返回 `{"success": False, "message": "..."}` 而不是抛出去。因为工具抛异常会**中断整个 LangGraph 执行**，用户看到的是崩溃；返回失败结果的话，模型会读到这个失败信息，按照 prompt 第 6 条**向用户解释原因并给出建议**。对话不中断，体验完整。"

**⑤ 工具返回格式统一为 JSON 字符串**（`utils/serializers.py` 第 11-13 行）：

```python
def build_json_response(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)
```

> 讲法："所有工具统一返回 JSON 字符串，包含 `success` 布尔字段。这样有两个好处：一是模型面对一致的结构，学习成本低；二是前端能靠 `"success": true` 这个字符串**判断过程卡片显示成功还是失败样式**（`message_utils.py` 第 103 行就是做这个判断的）。
>
> `ensure_ascii=False` 保证中文不被转义成 `\uXXXX`，否则模型读到的是乱码，浪费 token。"

---

### 5.4 消息转换层：`utils/message_utils.py`（135 行）

**这个文件解决一个具体问题：LangGraph 的消息对象格式复杂，前端要的是简单结构。**

**① 只截取"本轮"消息**（第 24-36 行）——**这是个容易被忽略但必须做对的地方**：

```python
def get_current_turn_messages(messages: list, user_message: str) -> list:
    target_index = None
    # 从后往前定位本轮用户消息，避免多轮会话时前端重复展示历史过程。
    for index in range(len(messages) - 1, -1, -1):
        item = messages[index]
        if isinstance(item, HumanMessage) and format_message_content(item.content) == user_message:
            target_index = index
            break
    if target_index is None:
        return list(messages)
    return list(messages[target_index:])
```

> 讲法："`state["messages"]` 里放着**整个会话的历史**。如果我把全部消息都序列化返回给前端，那么第二轮对话时，前端会把第一轮的'我来查一下房型'、'工具返回了 7 个房型'全部重复渲染一遍——**用户会看到重复的执行过程卡片**。
>
> 所以要从后往前找到**本轮**那条用户消息的位置，只返回它之后的部分。**从后往前找**是为了处理用户说了两遍相同话的情况。"

**② 判断是否已产出最终回复**（第 49-56 行）——利用了 LangChain 的一个约定：

```python
def has_final_ai_message(messages: list, user_message: str) -> bool:
    turn_messages = get_current_turn_messages(messages, user_message)
    last_message = turn_messages[-1]
    return isinstance(last_message, AIMessage) and not getattr(last_message, "tool_calls", None)
```

> 讲法："判断标准是：**这条 AI 消息带不带 `tool_calls`**。带工具调用说明模型还在'想干什么'的阶段；不带工具调用、且有文本内容，才是真正的最终回复。这是 LangChain 消息模型的约定，比自己去猜内容是否为空可靠得多。"

**③ 把消息序列化成前端能渲染的结构**（第 68-113 行）：

三种消息类型映射成三种展示形态：

| LangChain 消息类型 | 前端展示 | `type` 字段 |
| --- | --- | --- |
| `HumanMessage` | 用户气泡 | `human` |
| `AIMessage`（有 `tool_calls`） | 过程卡片"智能体决策：决定调用工具 search_room_types" | `ai` + `has_tool_calls: true` |
| `AIMessage`（无 `tool_calls`） | AI 回复气泡 | `ai` + `has_tool_calls: false` |
| `ToolMessage` | 过程卡片"工具调用结果 · search_room_types" | `tool` |

> **这是本模块"可解释性"的实现**，答辩时值得强调："我把工具调用和工具结果都序列化返回给前端，用户点开过程卡片能看到智能体到底查了什么、拿到了什么数据。**这不是给开发者看的调试信息，是给用户看的——让 AI 的决策过程透明，用户才会信任它的推荐。**"

---

### 5.5 持久层：`models.py` + `services.py`（195 行）

**两张表**：

```
AiChatSession (ai_chat_session)
  ├─ user          FK → 用户（CASCADE）
  ├─ session_id    唯一，前端与 LangGraph 共享
  ├─ title         由首条用户消息生成（截断 40 字）
  └─ created_at / updated_at

AiChatMessage (ai_chat_message)   ──FK──▶ AiChatSession (related_name="messages")
  ├─ role    user | assistant
  ├─ kind    text（用户文本）| reply（AI 回复）| process（执行过程）
  ├─ content 文本内容
  └─ process_payload  JSONField，存工具调用/结果的结构化数据
```

> **讲解要点**："注意 `kind` 字段把消息分成了三类。`process` 类型专门存执行过程，它的 `content` 存一个**可读摘要**（比如"决定调用工具：search_room_types"）用于列表展示，完整的结构化数据放在 `process_payload`（JSONField）里，用于渲染过程卡片细节。**这样历史会话回看时，过程卡片能原样还原，不会丢信息。**"

**会话写入的幂等与隔离**（`services.py` 第 18-30 行）：

```python
def get_or_create_chat_session(user, session_id: str, first_message: str) -> AiChatSession:
    # 按用户和会话编号查询，避免访问到其他用户的会话。
    session = AiChatSession.objects.filter(user=user, session_id=session_id).first()
    if session is not None:
        return session
    return AiChatSession.objects.create(user=user, session_id=session_id, ...)
```

> 讲法："查询条件里**必须同时带 `user=user`**。如果只按 `session_id` 查，一旦 session_id 冲突就会把别的用户的会话拿过来。**这是所有多租户系统的铁律：查询必须带属主条件。**"

**一轮对话的原子写入**（`services.py` 第 87-104 行）：

```python
with transaction.atomic():
    save_user_message(session, user_message)
    for payload in process_messages:
        if should_persist_process_message(payload):
            save_process_message(session, payload)
    save_ai_reply_message(session, reply)
    touch_chat_session(session)
```

> 讲法："一轮对话要写 N+2 条记录（1 条用户消息 + N 条过程消息 + 1 条 AI 回复）。如果不用事务，中途失败会留下'有提问但没有回答'的残缺记录，用户回看时逻辑不通。**加事务保证要么全成功、要么全回滚。**"

**哪些消息该落库**（第 75-84 行）——一个去重设计：

```python
def should_persist_process_message(payload: dict) -> bool:
    # 用户消息和最终 AI 回复已有独立记录，不重复保存为过程消息。
    if payload.get("type") == "human":
        return False
    if payload.get("type") == "ai" and not payload.get("has_tool_calls"):
        return False
    return True
```

> 讲法："前端返回的 `process_messages` 里其实混着用户消息和 AI 最终回复，但它们已经有独立的 `text` / `reply` 记录了。这里做一次过滤，**只把工具调用、工具结果、AI 决策这三类真正的'过程'存下来**，避免同一句话在数据库里存两遍。"

---

### 5.6 前端：`api/aiChat.js` + `AiChatView.vue`

**① 为什么用 `fetch` 手动解析 SSE，而不是浏览器原生的 `EventSource`？**

**这是必问点，答案在代码注释里已经写了**（`aiChat.js` 第 16-17 行）：

```javascript
// 以流式方式发送消息。
// 浏览器原生 EventSource 不支持 POST 与自定义请求头，因此使用 fetch 手动解析 SSE。
```

> 讲法："`EventSource` 有三个限制让它在这里不可用：
> 1. **只支持 GET 方法**，我们的对话需要 POST 传消息体；
> 2. **不能自定义请求头**，无法带 `Authorization: Bearer <JWT>`；
> 3. 不能传请求体。
>
> 所以改用 `fetch` + `ReadableStream` 手动解析。代价是要自己处理**粘包问题**——网络传输不保证一次 `read()` 就是一个完整事件，可能一个事件被切成两半。"

**② 粘包的处理**（`aiChat.js` 第 78-91 行）——**这是这段代码最有技术含量的地方**：

```javascript
while (true) {
  const { value, done } = await reader.read()
  if (done) break
  buffer += decoder.decode(value, { stream: true })
  // 只处理以空行分隔的完整事件块，剩余半截事件留到下一次读取后拼接。
  const blocks = buffer.split('\n\n')
  buffer = blocks.pop() || ''      // ← 最后一段可能是半截的，留着
  blocks.forEach(dispatchEventBlock)
}
if (buffer.trim()) dispatchEventBlock(buffer)   // 流结束时处理残留
```

> 讲法："SSE 协议规定事件之间用**空行**（`\n\n`）分隔。这里的策略是：
> - 把缓冲区按 `\n\n` 切分；
> - **最后一段 `pop()` 出来留在缓冲区**，因为它可能是被切断的半截事件；
> - 前面的完整块逐个派发；
> - 数据流结束后再处理残留，防止最后一条事件丢掉。
>
> `decoder.decode(value, { stream: true })` 里的 `stream: true` 也很关键——它告诉解码器**不要因为末尾是不完整的多字节字符就报错**，中文被切断时尤其需要。"

> **加分话术**："这一段的实现我参考了 SSE 规范里对'不完整事件'的处理要求。如果只是简单地按 `\n\n` 切分并立即解析，会在网络波动时偶发丢消息或 JSON 解析失败——这属于**低频但真实存在的 bug**，测试时不容易复现。"

**③ 前端的事件分发**（第 66-75 行）：把 5 种事件映射到 5 个回调，结构清晰：

```javascript
if (eventName === 'start') handlers.onStart?.(payload)
else if (eventName === 'token') handlers.onToken?.(payload)
else if (eventName === 'message') handlers.onMessage?.(payload)
else if (eventName === 'done') handlers.onDone?.(payload)
else if (eventName === 'error') handlers.onError?.(payload)
```

**④ 页面上的两个用户体验设计**（`AiChatView.vue`）：

- **执行过程卡片**（模板第 343-364 行）：用 `el-collapse` 折叠展示工具调用的参数（`call.name(JSON.stringify(call.args))`）和返回结果。默认收起，不干扰阅读；点开能看到细节。
- **快捷提问词**（第 37-42 行）：`quickPrompts` 提供了 4 条示例，包括一条**完整的下单指令**"帮我预订一间 5 月 1 日到 5 月 3 日的豪华大床房"。

> 讲法："快捷提问词不是装饰。**用户第一次面对 AI 对话框时不知道能问什么**，给 4 条示例能直接把用户引导到核心场景上，特别是最后一条完整下单指令，能一步演示出智能体的完整能力。"

- **Markdown 渲染 + XSS 防护**（第 27 行）：
```javascript
const md = new MarkdownIt({ html: false, linkify: true, breaks: true })
```
> 讲法："`html: false` 是**故意的安全设置**。模型的输出属于不可信内容，如果允许渲染 HTML，理论上存在 XSS 风险（虽然模型输出 XSS 的概率低，但不能不防）。关掉 `html` 后 markdown-it 会把 HTML 标签转义成文本，只保留列表、加粗、表格这些安全语法。"

---

## 六、三个可以深挖的技术亮点（PPT 收尾页用）

如果你只有 3 分钟讲技术，讲这三个：

### 亮点 1：可解释的执行过程（Explainability）
把 ReAct 循环的每一步（决策 → 工具调用 → 工具结果）都序列化展示给用户，而不只是给最终答案。用户在过程卡片里能看到智能体查了什么条件、拿到了几条数据。

**为什么重要**：LLM 应用最大的信任障碍是"黑盒感"。展示过程让推荐结果变得可追溯。

### 亮点 2：确定性与概率性的边界划分
- **交给模型**：理解用户意图、组织自然语言表达、决定下一步调哪个工具
- **交给代码**：用户身份（闭包）、参数校验、日期合法性、库存判断、价格计算、个性化排序

**为什么重要**：LLM 的输出是概率性的，不能用来保证正确性。把一切"必须正确"的判断从模型手里拿走，系统才可靠。

### 亮点 3：库存并发安全的行锁方案
`transaction.atomic()` + `select_for_update()`，固定加锁顺序（先房型后房间），保证 AI 下单与页面下单走同一套并发策略。

**为什么重要**：这是"AI 真的能操作业务系统"必须跨过的门槛。让 LLM 具备写操作能力，前提是写操作本身是安全的。

---

## 七、现场演示脚本（建议照这个顺序演）

**准备工作**：提前把后端、前端、MySQL 都启动好，登录 `guest / guest123456`，确保 `.env` 里 AI Key 有效。

| 步骤 | 操作 | 讲解重点 | 预期结果 |
| --- | --- | --- | --- |
| 1 | 打开 AI 助手页，展示欢迎区 | "注意这 4 条快捷提问" | 三个能力卡片 + 4 条示例 |
| 2 | 点"我之前的订单和收藏偏好是什么样的？" | **演示只调 `get_user_context`** | 过程卡片显示 1 次工具调用；回复引用真实订单 |
| 3 | 输入"推荐一间两人入住、含早餐、有窗的房间" | **演示多工具链式调用** | 过程卡片显示先 `get_user_context` 后 `search_room_types`；回复列出房型+价格+库存 |
| 4 | 追问"帮我订 5 月 1 日到 5 月 3 日的第 X 间" | **演示下单** | 自动用资料补齐联系人，不再追问姓名电话 → 展示第 3 条 prompt 的效果 |
| 5 | 打开"我的订单"页 | **闭环验证** | 刚才的订单确实写进了数据库 |
| 6 | 回 AI 页点开过程卡片 | **演示可解释性** | 展开能看到 `search_room_types({"capacity":2,"breakfast":true,"window":true})` |
| 7 | 刷新页面 / 点左侧历史会话 | **演示持久化** | 对话完整还原，含过程卡片 |
| 8 | （可选）手改前端传一个不存在的 `room_type_id` | **演示防护** | 返回"未找到指定房型"，不崩溃 |

> **演示技巧**：步骤 4 是最关键的展示点——**让评委注意到"它没有问我电话"**。这句话主动说出来，比等评委发现更有力："这里它没有再问我的姓名和电话，因为 `get_user_profile` 返回了 `can_auto_fill_contact: true`，模型读了这个字段就直接用我的资料填了。"

---

## 八、预期提问与标准回答（20 条）

### 关于技术选型

**Q1：为什么用 LangGraph，不用 LangChain 自带的 Agent？**
> `AgentExecutor` 的执行流程是黑盒，我无法插入自定义节点、也不能精细控制流式输出的粒度。我的业务需要"必须先查房再下单"这种强顺序约束，LangGraph 把循环显式画成一张图，每个节点和跳转条件都在代码里可见。另外 LangGraph 的 checkpointer 机制让多轮上下文管理和会话隔离更自然。

**Q2：ReAct 是什么？和普通的 prompt 调用有什么区别？**
> ReAct 是 Reasoning + Acting 的循环。普通 prompt 调用是"你问我答"，模型只能用已有知识回答；ReAct 让模型可以在回答前**先调用工具获取真实数据**，看到结果再决定下一步。我的场景里模型不可能知道数据库里有什么房型，所以必须先查再答。

**Q3：为什么不直接把数据库数据塞进 prompt？**
> 数据量大（8 个房型 + 35 个房间 + 订单历史），全塞进去 token 成本高，而且模型每次都要在一大段无关数据里找答案，准确率反而下降。工具调用是按需查询，只在需要时拿需要的数据。

### 关于安全

**Q4：怎么防止用户通过对话越权访问别人的数据？**
> 三层：① 用户身份 `user_id` 通过**闭包**绑定到工具里，不是工具参数，模型在结构上无法传入；② 工具内部的查询都基于这个 `user_id` 过滤；③ 会话查询 `AiChatSession.objects.filter(user=user, session_id=...)` 强制带属主条件，`resolve_session_id` 还会检查 session_id 是否已被其他用户占用，是则重新生成。

**Q5：怎么防止 AI 乱下单 / 误下单？**
> ① prompt 第 5 条明确禁止未确认就下单；② `create_booking` 的 description 写明"在用户明确确认房型、入住日期和退房日期后创建"；③ 参数层面 `room_type_id`、`start_date`、`end_date` 都是必填（Pydantic 没有默认值），模型不确认就拿不到这些参数；④ 即便模型真的调了，工具里还有五道业务校验。

**Q6：如果模型被诱导，传入一个不存在的房型 ID 会怎样？**
> 会有明确失败。`_create_booking` 用 `RoomType.objects.select_for_update().filter(pk=room_type_id).first()` 查，查不到就返回 `{"success": false, "message": "未找到指定房型。"}`。模型读到这个结果后按 prompt 第 6 条向用户解释。**正确性由代码保证，不依赖模型的自觉。**

**Q7：API Key 泄露风险怎么控制？**
> Key 存在 `backend/.env`，已在 `.gitignore` 里，不会进仓库；`.env.example` 只留空占位模板。另外我在开发中还发现过一个真实问题——`settings.py` 里 `.env.example` 的加载顺序在前，而 `python-dotenv` 默认不覆盖已有变量，导致模板里的值会抢占真实配置。这个顺序已经修正为 `.env` 优先。

### 关于并发与数据一致性

**Q8：两个人同时抢最后一间房会超卖吗？**
> 不会。`_create_booking` 在 `transaction.atomic()` 里用 `select_for_update()` 对房型行加排他锁。第二个事务必须等第一个提交后才能读到数据，此时 `remaining_stock` 已经是 0，会被库存校验拦下。这是数据库层的行锁，不是应用层判断，所以可靠。

**Q9：会不会死锁？**
> 我固定了加锁顺序——先锁 `RoomType`，再锁 `Room`。所有下单路径都遵循这个顺序，不会出现两个事务反向持锁互相等待的情况。这是避免死锁的标准做法。

**Q10：为什么还要锁定具体的 `Room` 而不只锁房型库存？**
> 因为业务需要分配一个具体的物理房间号。`remaining_stock` 是房型层面的可售数量，`Room.status` 是物理房间的占用状态，两者都要一致才能保证"卖出去了就真的有房间给客人"。

### 关于多轮对话与状态

**Q11：多轮对话的上下文存在哪里？**
> 有两套，目的不同：① **LangGraph 的 `InMemorySaver` 检查点**，按 `thread_id = user-{user_id}-{session_id}` 隔离，供模型在多轮中记住对话；② **MySQL 的 `ai_chat_session` / `ai_chat_message` 两张表**，存对话记录供用户回看历史。前者是"模型的短期记忆"，后者是"用户的对话档案"。

**Q12：为什么 `thread_id` 要拼上 `user_id`？**
> 防止不同用户的上下文串线。如果只用 `session_id`，一旦两个用户拿到同一个 ID，A 就能看到 B 的历史对话。加上 `user_id` 前缀后，线程天然按用户隔离。

**Q13：（必问）内存检查点重启就丢了吧？**
> 是的，这是当前实现的已知限制，要如实说明。`InMemorySaver` 存在进程内存里，重启后端后模型就"忘记"之前的上下文了。
>
> LangGraph 提供了持久化的检查点实现（`SqliteSaver` / `PostgresSaver` / `RedisSaver`），只要把 `InMemorySaver()` 换成对应实现、并在 `setup()` 里建表即可，改动量很小（一行）。当前选择内存版是因为演示环境单进程部署、且对话记录已经落 MySQL 可以回看。
>
> **主动承认 + 给出升级路径，比被问出来好得多。**

**Q14：同一用户的两个浏览器窗口会不会互相干扰？**
> 不会。前端每个会话有独立 `session_id` 存在 `localStorage`，`thread_id` 不同则检查点不同。只有用户主动打开同一个历史会话时才会共享上下文，这是符合预期的。

### 关于流式与前端

**Q15：为什么不用 WebSocket 而用 SSE？**
> 这个场景是**单向推送**——只有服务端往客户端推文字，客户端不需要在同一个连接上持续发消息。SSE 基于普通 HTTP，实现简单、自带重连语义、不需要额外的协议升级和服务端连接管理。WebSocket 是双向的，用在这里属于过度设计。需要升双向时再换。

**Q16：为什么不用 `EventSource`？**
> 三个限制：只支持 GET、不能自定义请求头（带不了 JWT）、不能传请求体。所以用 `fetch` + `ReadableStream` 手动解析 SSE，代价是要自己处理粘包——按 `\n\n` 切分、把最后一段半截事件留在缓冲区等下次拼接、流结束后再处理残留。

**Q17：`stream_mode=["messages", "values"]` 为什么要两个？**
> 一个都不够。`messages` 模式给的是逐字的 `AIMessageChunk`，用它做打字机效果；`values` 模式给的是完整图状态快照，从中能拿到工具调用的结构化信息，用来渲染执行过程卡片。只用 `messages` 拿不到工具信息，只用 `values` 只能整段跳。

**Q18：前端怎么区分"模型在说话"和"模型在调工具"？**
> 靠 LangChain 消息模型里的 `tool_calls` 字段。`AIMessage` 如果带 `tool_calls`，说明模型决定了要调工具，我把它渲染成"智能体决策"卡片；不带 `tool_calls` 且有文本内容的，才是真正给用户的回复。后端 `serialize_agent_message` 就是做这个分支判断的。

### 关于测试与工程

**Q19：怎么验证这个模块是能跑的？**
> 三重验证：① 31 项接口冒烟测试（`backend/scripts/smoke_test.py`），覆盖登录、房型、订单、收藏、评价、留言、AI 会话、后台 7 类资源，还包含下单-取消的库存一致性验证（库存 4→3→4）；② 端到端智能体调用验证，确认它能自主调用 `get_user_context` + `search_room_types` 并返回带真实价格的推荐；③ 图结构导出验证（`scripts/export_agent_graph.py`），确认 ReAct 循环的节点和边符合预期。

**Q20：成本怎么控制？**
> 四个手段：① `temperature=0.2`，业务场景需要稳定而非发散；② `search_room_types` 先取 20 条再截取前 8 条（`queryset[:20]` → `result[:8]`），控制进 prompt 的数据量；③ 拆分 `get_user_context` / `get_user_profile`，避免为查资料而拉全量历史订单；④ 工具返回 JSON 且统一 `ensure_ascii=False`，避免中文被转义成 `\uXXXX` 导致 token 膨胀。

---

## 九、可能被问倒的点 & 诚实回答话术

**答辩不是要你完美，是要你清楚边界。** 被问到不足时，承认 + 给方案，比硬撑更得分。

| 可能的追问 | 诚实且专业的回答 |
| --- | --- |
| 检查点不持久，重启就丢上下文 | 是已知限制。生产环境换成 `RedisSaver` 或 `PostgresSaver`，改动量约为一行代码 + 建表。对话记录已落 MySQL，历史可回看，所以影响可控。 |
| 没有知识库 / RAG | 当前场景的"知识"是结构化的房型数据，用工具查询比向量检索更准、更可控。如果将来要接入酒店政策、FAQ 这类非结构化文本，再引入 RAG 更合适。 |
| 没有限制工具调用次数 | LangGraph 有默认的 `recursion_limit`（25 步）兜底，能防止无限循环。如果需要更严格的限制，可以在图上加一个计数节点，超过阈值强制结束。 |
| `id_card` 没有格式校验 | 它是可选字段，目前透传不校验。如果要严格化，可以在 `_create_booking` 里加 18 位身份证正则，与 `contact_phone` 的校验放在一起。 |
| 流式不能中途停止生成 | 前端目前没有做中断按钮。技术上可以用 `AbortController` 中断 fetch 请求，后端 `event_stream` 生成器会在客户端断开时停止迭代。这是个可以补的点。 |
| 单一模型，没有兜底 | 目前只配了阿里云百炼一个平台。如果要高可用，可以在 `get_llm()` 里加多平台配置和失败重试切换。 |
| 没有对话历史长度控制 | 长会话下 `state["messages"]` 会持续增长，可能超出模型上下文窗口。可以加一个消息裁剪策略（保留最近 N 轮）或做摘要压缩。 |
| 前端没做单元测试 | 前端以接口联调和构建验证为主（`vite build` 无报错 + 代理连通性验证）。如果要补，可以用 Vitest 对 `aiChat.js` 的 SSE 解析函数做单元测试，那里是最值得测的纯函数逻辑。 |

---

## 十、代码地图速查表（打印出来放桌上）

| 你想讲什么 | 打开这个文件 | 关键行 |
| --- | --- | --- |
| ReAct 循环怎么搭的 | `AiChat/Agent/graph.py` | 61-71 |
| 系统提示词的 7 条业务约束 | `AiChat/Agent/graph.py` | 18-27 |
| 会话线程怎么隔离 | `AiChat/Agent/graph.py` | 43-46 |
| 流式怎么同时取消息和状态 | `AiChat/Agent/graph.py` | 103-126 |
| **用户身份怎么绑定的（安全亮点）** | `AiChat/Agent/hotel_tools.py` | 252-282 |
| 工具参数怎么约束模型 | `AiChat/Agent/hotel_tools.py` | 27-46 |
| 收藏优先的推荐排序 | `AiChat/Agent/hotel_tools.py` | 76-86 |
| **下单的事务与行锁（技术亮点）** | `AiChat/Agent/hotel_tools.py` | 194-232 |
| 五道业务校验 | `AiChat/Agent/hotel_tools.py` | 167-207 |
| 错误码翻译成中文 | `AiChat/views.py` | 31-59 |
| SSE 事件怎么编码 | `AiChat/views.py` | 62-65 |
| 会话属主校验 | `AiChat/views.py` | 68-77 |
| 只取本轮消息（防重复渲染） | `AiChat/Agent/utils/message_utils.py` | 24-36 |
| 过程消息怎么序列化给前端 | `AiChat/Agent/utils/message_utils.py` | 68-113 |
| 工具返回 JSON 的格式约定 | `AiChat/Agent/utils/serializers.py` | 11-13 |
| 日期解析容错（3 种格式） | `AiChat/Agent/utils/serializers.py` | 21-32 |
| 会话消息落库事务 | `AiChat/services.py` | 87-104 |
| 前端 SSE 粘包处理 | `frontend/src/api/aiChat.js` | 78-91 |
| 执行过程卡片渲染 | `frontend/src/views/AiChatView.vue` | 343-364 |

---

## 附：一张图的总结（PPT 尾页）

```
                     用户自然语言提问
                            │
              ┌─────────────▼─────────────┐
              │  接口层：JWT 鉴权 + SSE 编码  │  views.py
              └─────────────┬─────────────┘
                            │  user_id 从 JWT 取出（模型不可见）
              ┌─────────────▼─────────────┐
              │  编排层：ReAct 状态图        │  graph.py
              │  agent ⇄ tools 循环        │  7 条业务约束 + 检查点
              └─────────────┬─────────────┘
                            │  模型决定调哪个工具
              ┌─────────────▼─────────────┐
              │  工具层：4 个业务能力        │  hotel_tools.py
              │  user_id 闭包绑定           │  5 道确定性校验
              └─────────────┬─────────────┘
                            │  事务 + 行锁
              ┌─────────────▼─────────────┐
              │  持久层：订单 / 会话 / 消息   │  models.py
              └─────────────┬─────────────┘
                            │
              真实订单写入，前端可回看过程

核心主张：模型负责理解与表达，代码负责正确与安全。
```

---

**最后一句提醒**：答辩时如果被问到不会的，说"这个我目前没有深入，我的理解是……，回去我会确认一下"。**编造的答案比不知道更容易被追问穿。**
