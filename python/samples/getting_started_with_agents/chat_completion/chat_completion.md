# Semantic Kernel Chat Completion Agent 範例總覽
## Note:
- step12_chat_completion_agent_code_interpreter.py 範例需要 Azure Container Apps 的支援，請參考相關文檔進行配置。
目前還不能在本地環境執行

## Summary

本文檔總結了 Semantic Kernel Python 中 Chat Completion Agent 的 12 個主要範例，涵蓋從基礎的單一代理對話到複雜的多代理協作與進階功能。

### 主要技術與情境總覽

| 範例    | 主要情境         | 核心技術                                      | 特色功能          |
| ------- | ---------------- | --------------------------------------------- | ----------------- |
| Step 01 | 基礎單一代理對話 | `ChatCompletionAgent` + `AzureChatCompletion` | 最簡單的代理實作  |
| Step 02 | 對話歷史管理     | `ChatHistoryAgentThread`                      | 維護多輪對話記憶  |
| Step 03 | Kernel 整合      | `Kernel` + 服務註冊                           | 標準化服務管理    |
| Step 04 | 插件功能         | `@kernel_function` + 自定義插件               | 擴展代理能力      |
| Step 05 | 自動函數調用     | `FunctionChoiceBehavior.Auto()`               | 智能函數執行      |
| Step 06 | 多代理群組聊天   | `AgentGroupChat` + 自定義終止策略             | 代理協作          |
| Step 07 | 智能策略控制     | `KernelFunctionSelectionStrategy`             | AI 驅動的代理選擇 |
| Step 08 | 結構化輸出       | Pydantic + JSON 響應格式                      | 格式化結果輸出    |
| Step 09 | 日誌與監控       | Python logging                                | 開發調試支援      |
| Step 10 | 結構化推理       | 複雜 Pydantic 模型                            | 詳細推理過程      |
| Step 11 | 聲明式配置       | YAML + `AgentRegistry`                        | 配置驅動開發      |
| Step 12 | 代碼解釋器       | `SessionsPythonTool`                          | 動態代碼執行      |

---

## 詳細範例分析

### Step 01: 基礎聊天完成代理 (step01_chat_completion_agent_simple.py)

**主要情境**: 建立最基本的聊天代理，回答用戶問題

**技術重點**:
- 直接使用 `AzureChatCompletion` 服務
- 無狀態的簡單對話

**核心程式碼**:
```python
agent = ChatCompletionAgent(
    service=AzureChatCompletion(),
    name="Assistant",
    instructions="Answer questions about the world in one sentence.",
)

response = await agent.get_response(messages=user_input)
```

**使用場景**: 快速原型開發、簡單問答系統

---

### Step 02: 對話線程管理 (step02_chat_completion_agent_thread_management.py)

**主要情境**: 維護多輪對話的上下文記憶

**技術重點**:
- `ChatHistoryAgentThread` 管理對話歷史
- 跨多個訊息保持上下文

**核心程式碼**:
```python
thread: ChatHistoryAgentThread = None

response = await agent.get_response(
    messages=user_input,
    thread=thread,
)
thread = response.thread  # 保存線程狀態
```

**使用場景**: 客服機器人、長期對話系統

---

### Step 03: Kernel 整合 (step03_chat_completion_agent_with_kernel.py)

**主要情境**: 使用 Kernel 管理 AI 服務

**技術重點**:
- 集中式服務管理
- 標準化配置方式

**核心程式碼**:
```python
kernel = Kernel()
kernel.add_service(AzureChatCompletion())

agent = ChatCompletionAgent(
    kernel=kernel,
    name="Assistant",
    instructions="Answer the user's questions.",
)
```

**使用場景**: 企業級應用、多服務整合

---

### Step 04: 簡單插件功能 (step04_chat_completion_agent_plugin_simple.py)

**主要情境**: 擴展代理功能，提供特定領域知識

**技術重點**:
- 自定義插件類別
- `@kernel_function` 裝飾器

**核心程式碼**:
```python
class MenuPlugin:
    @kernel_function(description="Provides a list of specials from the menu.")
    def get_specials(self) -> Annotated[str, "Returns the specials from the menu."]:
        return "Special Soup: Clam Chowder..."

agent = ChatCompletionAgent(
    service=AzureChatCompletion(),
    plugins=[MenuPlugin()],
)
```

**使用場景**: 專業領域助手、業務特定功能

---

### Step 05: Kernel 插件與自動函數調用 (step05_chat_completion_agent_plugin_with_kernel.py)

**主要情境**: 智能化函數執行，代理自動決定何時調用插件

**技術重點**:
- `FunctionChoiceBehavior.Auto()` 自動函數選擇
- 智能化插件執行

**核心程式碼**:
```python
settings = kernel.get_prompt_execution_settings_from_service_id(service_id=service_id)
settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

agent = ChatCompletionAgent(
    kernel=kernel,
    arguments=KernelArguments(settings=settings),
)
```

**使用場景**: 智能助手、自動化工作流程

---

### Step 06: 代理群組聊天 (step06_chat_completion_agent_group_chat.py)

**主要情境**: 多個代理協作完成複雜任務

**技術重點**:
- `AgentGroupChat` 多代理協調
- 自定義終止策略

**核心程式碼**:
```python
class ApprovalTerminationStrategy(TerminationStrategy):
    async def should_agent_terminate(self, agent, history):
        last_message = history[-1].content.lower()
        return "approved" in last_message and "not approved" not in last_message

group_chat = AgentGroupChat(
    agents=[agent_writer, agent_reviewer],
    termination_strategy=ApprovalTerminationStrategy(agents=[agent_reviewer], maximum_iterations=10),
)
```

**使用場景**: 創意協作、多角色工作流程

---

### Step 07: Kernel 函數策略 (step07_kernel_function_strategies.py)

**主要情境**: 使用 AI 驅動的策略控制代理行為

**技術重點**:
- `KernelFunctionSelectionStrategy` AI 選擇下一個代理
- `KernelFunctionTerminationStrategy` AI 決定何時結束

**核心程式碼**:
```python
termination_function = KernelFunctionFromPrompt(
    function_name="termination",
    prompt="Determine if the copy has been approved. If so, respond with a single word: yes"
)

selection_function = KernelFunctionFromPrompt(
    function_name="selection",
    prompt="Determine which participant takes the next turn..."
)
```

**使用場景**: 複雜決策流程、動態工作流程

---

### Step 08: JSON 結果處理 (step08_chat_completion_agent_json_result.py)

**主要情境**: 獲取結構化的 JSON 格式回應

**技術重點**:
- Pydantic 模型定義
- 結構化響應格式

**核心程式碼**:
```python
class InputScore(BaseModel):
    score: int
    notes: str

settings.response_format = InputScore

class ThresholdTerminationStrategy(TerminationStrategy):
    async def should_agent_terminate(self, agent, history):
        result = InputScore.model_validate_json(history[-1].content or "")
        return result.score >= self.threshold
```

**使用場景**: 評分系統、結構化數據處理

---

### Step 09: 日誌記錄 (step09_chat_completion_agent_logging.py)

**主要情境**: 監控和調試代理互動過程

**技術重點**:
- Python logging 模組
- 詳細的互動記錄

**核心程式碼**:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

**使用場景**: 開發調試、系統監控、性能分析

---

### Step 10: 結構化輸出 (step10_chat_completion_agent_structured_outputs.py)

**主要情境**: 獲取複雜的結構化推理過程

**技術重點**:
- 複雜 Pydantic 模型嵌套
- 詳細推理步驟記錄

**核心程式碼**:
```python
class Step(BaseModel):
    explanation: str
    output: str

class Reasoning(BaseModel):
    steps: list[Step]
    final_answer: str

settings = AzureChatPromptExecutionSettings()
settings.response_format = Reasoning
```

**使用場景**: 教育系統、解題過程展示、透明化 AI 推理

---

### Step 11: 聲明式代理 (step11_chat_completion_agent_declarative.py)

**主要情境**: 使用 YAML 配置驅動的代理創建

**技術重點**:
- YAML 配置檔案
- `AgentRegistry` 從配置創建代理

**核心程式碼**:
```python
AGENT_YAML = """
type: chat_completion_agent
name: Assistant
description: A helpful assistant.
instructions: Answer the user's questions using the menu functions.
tools:
  - id: MenuPlugin.get_specials
    type: function
"""

agent = await AgentRegistry.create_from_yaml(
    AGENT_YAML, kernel=kernel, service=OpenAIChatCompletion()
)
```

**使用場景**: 配置驅動開發、動態代理創建、DevOps 整合

---

### Step 12: 代碼解釋器 (step12_chat_completion_agent_code_interpreter.py)

**主要情境**: 賦予代理執行 Python 代碼的能力

**技術重點**:
- `SessionsPythonTool` 代碼執行
- Azure Container Apps 會話池
- 檔案上傳與處理

**核心程式碼**:
```python
python_code_interpreter = SessionsPythonTool()

agent = ChatCompletionAgent(
    service=AzureChatCompletion(),
    plugins=[python_code_interpreter],
)

# 上傳檔案並執行代碼
file_metadata = await python_code_interpreter.upload_file(local_file_path=csv_file_path)
```

**使用場景**: 數據分析、動態計算、教育平台

---

## 代理情境應用說明

### 1. 基礎對話代理 (Steps 1-3)
- **適用情境**: 簡單問答、資訊查詢、基礎客服
- **特點**: 實作簡單、回應快速、資源消耗低
- **限制**: 功能單一、無記憶能力（Step 1）

### 2. 功能增強代理 (Steps 4-5)
- **適用情境**: 專業領域諮詢、業務特定功能、智能助手
- **特點**: 可擴展、領域專精、智能函數調用
- **優勢**: 結合領域知識與 AI 推理能力

### 3. 協作型代理 (Steps 6-7)
- **適用情境**: 創意協作、多角色工作流程、複雜決策
- **特點**: 多代理協調、智能策略控制、動態互動
- **應用**: 內容創作、產品設計、專案管理

### 4. 進階功能代理 (Steps 8-12)
- **適用情境**: 企業級應用、數據分析、教育平台
- **特點**: 結構化輸出、可監控、配置驅動、代碼執行
- **優勢**: 高度可客製化、強大的擴展能力

### 5. 技術架構選擇建議

**簡單應用**: Steps 1-2  
**企業應用**: Steps 3, 5, 11  
**協作系統**: Steps 6-7  
**分析平台**: Steps 8, 10, 12  
**開發調試**: Step 9

---

## 技術架構總結

### 核心組件
1. **ChatCompletionAgent**: 主要的代理類別
2. **Kernel**: 服務管理與插件註冊
3. **Thread Management**: 對話狀態管理
4. **Plugin System**: 功能擴展機制
5. **Strategy Pattern**: 行為控制策略

### 整合模式
- **直接服務模式**: 直接傳入 AI 服務 (Steps 1, 4)
- **Kernel 模式**: 透過 Kernel 管理服務 (Steps 3, 5)
- **群組模式**: 多代理協作 (Steps 6-7)
- **配置模式**: YAML 驅動創建 (Step 11)

### 最佳實踐
1. 使用 Kernel 進行統一服務管理
2. 實作適當的錯誤處理與日誌記錄
3. 根據應用複雜度選擇合適的架構模式
4. 善用插件系統擴展功能
5. 考慮使用結構化輸出提升可靠性

這些範例展示了從簡單到複雜的完整 Chat Completion Agent 開發路徑，為不同需求的應用提供了具體的實作參考。

---

## Chat Completion Agent vs Azure AI Agent 功能差異比較

### 架構與部署差異

| 特性         | Chat Completion Agent     | Azure AI Agent               |
| ------------ | ------------------------- | ---------------------------- |
| **部署模式** | 本地 Semantic Kernel 執行 | Azure AI 雲端服務託管        |
| **服務管理** | 本地 Kernel 管理 AI 服務  | Azure AI Agent Service 管理  |
| **身份認證** | 直接 AI 服務認證          | Azure DefaultAzureCredential |
| **資源管理** | 本地記憶體管理            | 雲端資源自動管理             |
| **擴展性**   | 受本地資源限制            | Azure 雲端彈性擴展           |

### 核心技術差異

#### 1. 代理創建方式

**Chat Completion Agent**:
```python
# 直接創建，本地執行
agent = ChatCompletionAgent(
    service=AzureChatCompletion(),
    name="Assistant",
    instructions="Answer questions",
)
```

**Azure AI Agent**:
```python
# 雲端服務創建，需要 Azure 客戶端
agent_definition = await client.agents.create_agent(
    model=AzureAIAgentSettings().model_deployment_name,
    name="Assistant", 
    instructions="Answer questions",
)
agent = AzureAIAgent(client=client, definition=agent_definition)
```

#### 2. 對話狀態管理

**Chat Completion Agent**:
- 使用 `ChatHistoryAgentThread` 本地管理
- 需要手動維護對話歷史
- 記憶體限制於本地資源

**Azure AI Agent**:
- 使用 `AzureAIAgentThread` 雲端管理
- Azure 服務自動維護對話歷史
- 雲端持久化，支援跨會話記憶

#### 3. 插件與工具系統

**Chat Completion Agent**:
- 僅支援 Semantic Kernel 插件 (`@kernel_function`)
- 本地函數執行
- 有限的工具整合能力

**Azure AI Agent**:
- 支援 Semantic Kernel 插件
- **額外支援 Azure 原生工具**:
  - `CodeInterpreterTool` (程式碼執行)
  - `FileSearchTool` (文件檢索)
  - `OpenApiTool` (外部 API 整合)
- 雲端工具執行環境

### 功能特性比較

| 功能領域       | Chat Completion Agent  | Azure AI Agent                 | 優勢分析            |
| -------------- | ---------------------- | ------------------------------ | ------------------- |
| **基礎對話**   | ✅ 支援                 | ✅ 支援                         | 兩者功能相當        |
| **插件系統**   | ✅ Semantic Kernel 插件 | ✅ SK 插件 + Azure 工具         | Azure AI 工具更豐富 |
| **多代理協作** | ✅ AgentGroupChat       | ✅ AgentGroupChat               | 功能相同            |
| **結構化輸出** | ✅ Pydantic 模型        | ✅ Pydantic 模型                | 功能相同            |
| **代碼執行**   | ⚠️ SessionsPythonTool   | ✅ CodeInterpreterTool          | Azure 原生整合更佳  |
| **文件處理**   | ❌ 不支援               | ✅ FileSearchTool + VectorStore | Azure 獨有功能      |
| **API 整合**   | ⚠️ 需自行開發           | ✅ OpenApiTool                  | Azure 原生支援      |
| **配置管理**   | ✅ YAML + AgentRegistry | ✅ YAML + AgentRegistry         | 功能相同            |
| **代理檢索**   | ❌ 不支援               | ✅ 支援現有代理檢索             | Azure 獨有功能      |

### 開發複雜度比較

#### Chat Completion Agent 開發模式
```python
# 簡單直接，適合快速開發
agent = ChatCompletionAgent(
    service=AzureChatCompletion(),
    plugins=[CustomPlugin()],
)
response = await agent.get_response(messages="Hello")
```

#### Azure AI Agent 開發模式
```python
# 需要 Azure 服務設定，但功能更強大
async with DefaultAzureCredential() as creds:
    async with AzureAIAgent.create_client(credential=creds) as client:
        agent_definition = await client.agents.create_agent(...)
        agent = AzureAIAgent(client=client, definition=agent_definition)
        # 需要手動清理雲端資源
        await client.agents.delete_agent(agent.id)
```

### 適用場景建議

#### Chat Completion Agent 適用場景
- **快速原型開發**: 本地開發，無需 Azure 設定
- **簡單應用**: 基礎問答、客服機器人
- **離線應用**: 不依賴雲端服務
- **成本敏感**: 無雲端服務費用
- **開發學習**: 理解 Semantic Kernel 核心概念

#### Azure AI Agent 適用場景
- **企業級應用**: 需要穩定雲端服務
- **複雜工具整合**: 需要代碼執行、文件搜尋、API 整合
- **大規模部署**: 需要雲端彈性擴展
- **持久化需求**: 跨會話資料保存
- **團隊協作**: 共享代理資源

### 技術選擇決策樹

```
是否需要雲端服務？
├── 否 → Chat Completion Agent
│   ├── 快速原型 ✅
│   ├── 簡單應用 ✅
│   └── 學習用途 ✅
│
└── 是 → Azure AI Agent
    ├── 需要代碼執行？ → ✅ CodeInterpreter
    ├── 需要文件搜尋？ → ✅ FileSearch
    ├── 需要 API 整合？ → ✅ OpenAPI
    ├── 需要企業級部署？ → ✅ Azure 託管
    └── 需要持久化？ → ✅ 雲端儲存
```

### 遷移考量

從 Chat Completion Agent 遷移到 Azure AI Agent：

**優勢**:
- 獲得更強大的工具支援
- 雲端服務的穩定性和擴展性
- 自動資源管理

**挑戰**:
- 需要 Azure 帳戶和權限設定
- 雲端服務成本考量
- 代碼需要重構以支援 async/await 模式
- 需要處理雲端資源清理

### 結論

**Chat Completion Agent** 適合快速開發和簡單應用，提供了 Semantic Kernel 的核心代理功能，是學習和原型開發的理想選擇。

**Azure AI Agent** 則是企業級解決方案，提供了完整的雲端代理服務，包含強大的工具生態系統，適合需要高可用性、擴展性和複雜功能整合的生產環境。

選擇哪種方案主要取決於：
1. **部署需求** (本地 vs 雲端)
2. **功能複雜度** (基礎對話 vs 複雜工具整合)  
3. **資源預算** (開發成本 vs 營運成本)
4. **擴展需求** (固定規模 vs 彈性擴展)

兩者都基於相同的 Semantic Kernel 核心架構，提供了良好的學習路徑和遷移可能性。
