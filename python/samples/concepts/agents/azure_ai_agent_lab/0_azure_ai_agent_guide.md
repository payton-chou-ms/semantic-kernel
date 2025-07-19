# Azure AI Agent 完整開發指南

## 📋 程式碼摘要與架構總覽 (Code Summary & Architecture Overview)

### 🏗️ 核心架構模式 (Core Architecture Patterns)

本指南包含 21 個範例程式，涵蓋 Azure AI Agent 的所有主要功能領域。所有範例遵循統一的架構模式：

```python
# 標準初始化模式
async with (
    DefaultAzureCredential() as creds,
    AzureAIAgent.create_client(credential=creds) as client,
):
    # 1. 建立工具/連接 (如需要)
    tool = SomeTool(connection_id=conn_id)
    
    # 2. 建立代理定義
    agent_definition = await client.agents.create_agent(
        name="AgentName",
        instructions="Agent instructions",
        model=AzureAIAgentSettings().model_deployment_name,
        tools=tool.definitions,  # 如有工具
        tool_resources=tool.resources  # 如有資源
    )
    
    # 3. 建立代理實例
    agent = AzureAIAgent(client=client, definition=agent_definition)
    
    # 4. 執行對話/處理
    response = await agent.invoke(messages=user_input, thread=thread)
    
    # 5. 清理資源
    await client.agents.delete_agent(agent.id)
```

### 📊 功能分類統計 (Feature Classification Statistics)

| 分類           | 範例數量 | 主要用途   | 關鍵技術                  |
| -------------- | -------- | ---------- | ------------------------- |
| **基礎功能**   | 2        | 入門學習   | 基本對話、插件整合        |
| **配置模板**   | 2        | 行為自訂   | 提示模板、截斷策略        |
| **資料處理**   | 2        | 結構化操作 | Pydantic、檔案處理        |
| **串流處理**   | 3        | 即時互動   | 異步串流、回調處理        |
| **程式碼執行** | 2        | 計算分析   | CodeInterpreter、動態執行 |
| **檔案搜尋**   | 2        | 知識檢索   | 向量搜尋、語義匹配        |
| **網路搜尋**   | 3        | 即時資訊   | Bing API、OpenAPI 整合    |
| **AI 搜尋**    | 1        | 企業搜尋   | Azure AI Search           |
| **進階控制**   | 3        | 系統控制   | 過濾器、代理組合          |
| **宣告配置**   | 1        | 配置驅動   | YAML/JSON 配置            |

### 🔧 技術棧總覽 (Technology Stack Overview)

#### 核心依賴 (Core Dependencies)
```python
# 必要套件
from azure.ai.agents.models import *  # Azure AI Agent 模型
from azure.identity.aio import DefaultAzureCredential  # Azure 認證
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings  # SK 整合
from semantic_kernel.contents import *  # 內容類型定義
```

#### 工具生態系統 (Tool Ecosystem)
```python
# 內建工具
- CodeInterpreterTool  # 程式碼執行
- FileSearchTool       # 檔案搜尋
- BingGroundingTool    # 網頁搜尋
- AzureAISearchTool    # AI 搜尋
- OpenApiTool          # API 整合

# 自訂工具
- Semantic Kernel Plugins
- Custom Function Filters  
- Agent-as-Function Wrappers
```

### 🎯 使用場景對應表 (Use Case Mapping)

| 業務需求           | 推薦範例                                                                       | 關鍵技術點            |
| ------------------ | ------------------------------------------------------------------------------ | --------------------- |
| **客服機器人**     | `azure_ai_agent.py` + `azure_ai_agent_plugin.py`                               | 基本對話 + 業務插件   |
| **文件問答系統**   | `azure_ai_agent_file_search.py`                                                | 向量搜尋 + 語義檢索   |
| **程式碼助手**     | `azure_ai_agent_code_interpreter.py`                                           | 程式碼執行 + 結果解析 |
| **資訊搜尋助手**   | `azure_ai_agent_bing_grounding_streaming_with_message_callback_input.py`       | 即時搜尋 + 串流回應   |
| **資料分析助手**   | `azure_ai_agent_structured_outputs.py` + `azure_ai_agent_file_manipulation.py` | 結構化輸出 + 檔案處理 |
| **多功能企業助手** | `azure_ai_agent_as_kernel_function.py`                                         | 代理組合 + 智能路由   |

---

## 概述 (Overview)

本指南提供了 Azure AI Agent 在 Semantic Kernel 框架中的完整開發指南，涵蓋從基礎概念到進階應用的所有內容。Azure AI Agent 是微軟推出的企業級 AI 代理服務，能夠建立智能、專業化的對話代理和任務執行系統。

### 核心優勢
- **企業級可靠性**: Azure 雲端服務的高可用性和安全性
- **豐富的工具生態**: 內建程式碼解釋器、檔案搜尋、網頁搜尋等專業工具
- **靈活的整合能力**: 支援 OpenAPI、自訂插件和多代理協作
- **宣告式配置**: 支援 YAML/JSON 配置驅動的代理建立和管理

---

## 技術架構總覽 (Technical Architecture)

| 層級       | 技術組件                 | 功能描述                |
| ---------- | ------------------------ | ----------------------- |
| **服務層** | Azure AI Agent Service   | 雲端 AI 代理服務        |
| **SDK 層** | Semantic Kernel          | 代理編排和管理框架      |
| **認證層** | DefaultAzureCredential   | Azure 身份認證          |
| **通訊層** | AzureAIAgent Client      | 與 Azure 服務的通訊介面 |
| **工具層** | Built-in Tools + Plugins | 專業功能和自訂擴展      |

---

## 功能範例完整目錄 (Complete Feature Examples Index)

### 🏗️ 基礎功能範例 (Basic Features)

#### 1. 基本對話代理 (Basic Chat Agent)
**檔案**: `azure_ai_agent.py`
**功能**: 展示最基本的 Azure AI Agent 使用方法

```python
# 最簡單的 Azure AI Agent 實現
async def basic_agent_example():
    async with DefaultAzureCredential() as creds:
        async with AzureAIAgent.create_client(credential=creds) as client:
            # 建立代理定義
            agent_definition = await client.agents.create_agent(
                model="gpt-4o",
                name="BasicAssistant", 
                instructions="You are a helpful assistant."
            )
            
            # 建立代理實例
            agent = AzureAIAgent(client=client, definition=agent_definition)
            
            # 進行對話
            response = await agent.get_response(messages="Hello, how are you?")
            print(f"Agent: {response}")
```

**特色功能**:
- ✅ 自動對話歷史管理
- ✅ 簡潔的 API 介面
- ✅ Azure 身份認證整合

#### 2. 插件增強代理 (Plugin-Enhanced Agent)
**檔案**: `azure_ai_agent_plugin.py`
**功能**: 示範如何使用 Semantic Kernel 插件擴展代理功能

```python
# 具備自訂插件功能的代理
class MenuPlugin:
    @kernel_function(description="Get menu specials")
    def get_specials(self) -> str:
        return "Today's Special: Clam Chowder $9.99"

# 將插件整合到代理
agent = AzureAIAgent(
    client=client,
    definition=agent_definition,
    plugins=[MenuPlugin()]  # 添加插件
)
```

**特色功能**:
- ✅ 自訂函數呼叫
- ✅ 業務邏輯封裝
- ✅ 插件化架構

### 🔧 配置和模板功能 (Configuration & Template Features)

#### 3. 提示模板代理 (Prompt Template Agent)
**檔案**: `azure_ai_agent_prompt_templating.py`
**功能**: 展示如何使用不同的提示模板格式來自訂代理行為

```python
# 支援多種模板格式：semantic-kernel、jinja2、handlebars
prompt_config = PromptTemplateConfig(
    template="Write a poem in the style of {{$style}}.",
    template_format="semantic-kernel"
)

agent = AzureAIAgent(
    client=client,
    definition=agent_definition,
    prompt_template_config=prompt_config,
    arguments=KernelArguments(style="haiku")
)
```

**特色功能**:
- ✅ 多種模板格式支援
- ✅ 動態參數替換
- ✅ 可配置預設值

#### 4. 截斷策略代理 (Truncation Strategy Agent)
**檔案**: `azure_ai_agent_truncation_strategy.py`
**功能**: 展示如何配置對話記憶體截斷策略

```python
# 配置截斷策略保留最後 N 條訊息
truncation_strategy = TruncationObject(type="last_messages", last_messages=2)

response = await agent.get_response(
    messages=user_input, 
    thread=thread, 
    truncation_strategy=truncation_strategy
)
```

**特色功能**:
- ✅ 記憶體管理優化
- ✅ 可配置截斷規則
- ✅ 長對話支援

### 📊 資料處理功能 (Data Processing Features)

#### 5. 結構化輸出代理 (Structured Output Agent)
**檔案**: `azure_ai_agent_structured_outputs.py`
**功能**: 使用 Pydantic 模型定義結構化輸出格式

```python
# 使用 Pydantic 模型定義輸出格式
class Planet(BaseModel):
    planet: Planets
    mass: float

# 配置結構化輸出
agent_definition = await client.agents.create_agent(
    response_format=ResponseFormatJsonSchemaType(
        json_schema=ResponseFormatJsonSchema(
            name="planet_data",
            schema=Planet.model_json_schema()
        )
    )
)
```

**應用場景**:
- 📋 表單資料提取
- 📊 結構化資料轉換
- 🏷️ 實體識別和標註
- 📝 規範化回應格式

#### 6. 檔案操作代理 (File Manipulation Agent)
**檔案**: `azure_ai_agent_file_manipulation.py`
**功能**: 展示代理如何處理和操作檔案

```python
# 上傳檔案並使用程式碼解釋器處理
file = await client.agents.files.upload_and_poll(
    file_path=csv_file_path, 
    purpose=FilePurpose.AGENTS
)

code_interpreter = CodeInterpreterTool(file_ids=[file.id])
```

**應用場景**:
- 📊 CSV 資料分析
- 📈 圖表生成
- 📄 報表製作
- 💾 檔案處理自動化

### 🚀 串流和即時處理功能 (Streaming & Real-time Features)

#### 7. 串流回應代理 (Streaming Response Agent)
**檔案**: `azure_ai_agent_streaming.py`
**功能**: 實現即時串流回應，提升用戶體驗

```python
# 即時串流回應
async for response in agent.invoke_stream(messages=user_input):
    print(response.content, end="", flush=True)
```

**特色功能**:
- ⚡ 即時回應顯示
- 🔄 降低延遲感知
- 📡 連續資料流處理

#### 8. 訊息回調代理 (Message Callback Agent)
**檔案**: `azure_ai_agent_message_callback.py`
**功能**: 處理中間訊息和函數呼叫回調

```python
# 處理中間步驟的回調函數
async def handle_intermediate_steps(message: ChatMessageContent) -> None:
    for item in message.items or []:
        if isinstance(item, FunctionResultContent):
            print(f"Function Result: {item.result}")
        elif isinstance(item, FunctionCallContent):
            print(f"Function Call: {item.name}")

# 使用回調
async for response in agent.invoke(
    messages=user_input,
    on_intermediate_message=handle_intermediate_steps
):
    print(f"Agent: {response}")
```

**特色功能**:
- 🔍 中間步驟可見性
- 🛠️ 函數呼叫監控
- 📝 詳細執行日誌

#### 9. 串流訊息回調代理 (Streaming Message Callback Agent)
**檔案**: `azure_ai_agent_message_callback_streaming.py`
**功能**: 結合串流和訊息回調功能

**特色功能**:
- ⚡ 即時搜尋結果串流
- 🔗 來源引用和註解
- 📊 搜尋過程可視化

### 🧮 程式碼執行功能 (Code Execution Features)

#### 10. 程式碼解釋器代理 (Code Interpreter Agent)
**檔案**: `azure_ai_agent_code_interpreter.py`
**功能**: 使用內建的程式碼解釋器執行 Python 程式碼

```python
# 程式碼執行和資料分析
code_interpreter = CodeInterpreterTool(file_ids=[file.id])

agent_definition = await client.agents.create_agent(
    model="gpt-4o",
    tools=code_interpreter.definitions,
    tool_resources=code_interpreter.resources
)
```

**應用場景**:
- 📊 資料分析和視覺化
- 🔢 數學計算和統計分析
- 📈 報表自動生成
- 🧮 演算法實現和測試

#### 11. 串流程式碼解釋器 (Streaming Code Interpreter)
**檔案**: `azure_ai_agent_code_interpreter_streaming_with_message_callback.py`
**功能**: 串流模式的程式碼執行和回調處理

**特色功能**:
- ⚡ 即時程式碼執行
- 📊 串流結果顯示
- 🔍 執行過程監控

### 📚 檔案搜尋功能 (File Search Features)

#### 12. 檔案搜尋代理 (File Search Agent)
**檔案**: `azure_ai_agent_file_search.py`
**功能**: 智能文件檢索和問答

```python
# 智能文件檢索
vector_store = await client.agents.vector_stores.create_and_poll(
    file_ids=[file.id],
    name="knowledge_base"
)

file_search = FileSearchTool(vector_store_ids=[vector_store.id])
```

**應用場景**:
- 📚 企業知識庫問答
- 📄 文件內容智能檢索
- 🔍 多文件語義搜尋
- 💡 知識發現和整合

#### 13. 執行緒訊息檢索 (Thread Message Retrieval)
**檔案**: `azure_ai_agent_retrieve_messages_from_thread.py`
**功能**: 從對話執行緒中檢索和顯示歷史訊息

```python
# 檢索執行緒中的所有訊息
async for msg in thread.get_messages(sort_order="asc"):
    print(f"# {msg.role} for name={msg.name}: {msg.content}")
```

**特色功能**:
- 📋 完整對話歷史
- 🔄 可排序訊息列表
- 💾 持久化對話記錄

### 🌐 網路搜尋功能 (Web Search Features)

#### 14. Bing 搜尋代理 (Bing Grounding Agent)
**檔案**: `azure_ai_agent_bing_grounding.py`
**功能**: 使用真實的 Bing 搜尋進行資訊檢索

```python
# 真實網頁搜尋功能
bing_connection = await client.connections.get(name="mybingsearch")
bing_grounding = BingGroundingTool(connection_id=bing_connection.id)

agent_definition = await client.agents.create_agent(
    name="WebSearchAgent",
    instructions="Use Bing to search for current information",
    tools=bing_grounding.definitions
)
```

**應用場景**:
- 🌐 即時資訊查詢
- 📰 新聞和趨勢分析
- 🔬 研究資料搜集
- 📊 市場情報收集

#### 15. 串流 Bing 搜尋代理 (Streaming Bing Grounding Agent)
**檔案**: `azure_ai_agent_bing_grounding_streaming_with_message_callback.py`
**功能**: 結合串流和 Bing 搜尋功能

**特色功能**:
- ⚡ 即時搜尋結果串流
- 🔗 來源引用和註解
- 📊 搜尋過程可視化

#### 16. OpenAPI 整合代理 (OpenAPI Integration Agent)
**檔案**: `azure_ai_agent_openapi.py`
**功能**: 整合外部 OpenAPI 服務

```python
# 外部 API 服務整合
weather_tool = OpenApiTool(
    name="weather_api",
    spec=weather_openapi_spec,
    description="Get weather information",
    auth=OpenApiAnonymousAuthDetails()
)
```

**應用場景**:
- 🌤️ 天氣資訊服務
- 💱 匯率查詢服務
- 🗺️ 地理位置服務
- 📦 物流追蹤服務

### 🔍 Azure AI 搜尋功能 (Azure AI Search Features)

#### 17. Azure AI 搜尋代理 (Azure AI Search Agent)
**檔案**: `azure_ai_agent_azure_ai_search.py`
**功能**: 使用 Azure AI Search 進行智能搜尋

```python
# Azure AI Search 工具
ai_search = AzureAISearchTool(
    index_connection_id=ai_search_conn_id, 
    index_name=AZURE_AI_SEARCH_INDEX_NAME
)
```

**應用場景**:
- 🏨 飯店查詢系統
- 🛍️ 產品搜尋引擎
- 📚 文件搜尋服務
- 🎯 精準內容檢索

### 🎛️ 進階控制功能 (Advanced Control Features)

#### 18. 函數呼叫過濾器 (Function Invocation Filter)
**檔案**: `azure_ai_agent_auto_func_invocation_filter.py`
**功能**: 自訂函數呼叫過濾和修改

```python
# 自訂函數呼叫過濾和修改
@kernel.filter(FilterTypes.AUTO_FUNCTION_INVOCATION)
async def custom_filter(context: AutoFunctionInvocationContext, next):
    print(f"Calling function: {context.function.name}")
    await next(context)
    
    # 修改函數結果
    if "special_case" in context.function.name:
        context.function_result = FunctionResult(
            function=context.function_result.function,
            value="Modified result"
        )
```

**應用場景**:
- 🛡️ 安全性控制和審核
- 📝 日誌記錄和監控
- 🔄 結果後處理和轉換
- ⚠️ 錯誤處理和容錯

#### 19. 串流函數過濾器 (Streaming Function Filter)
**檔案**: `azure_ai_agent_auto_func_invocation_filter_streaming.py`
**功能**: 串流模式下的函數呼叫過濾

**特色功能**:
- ⚡ 即時函數呼叫控制
- 🔄 串流結果修改
- 📊 動態過濾規則

#### 20. 代理作為核心函數 (Agent as Kernel Function)
**檔案**: `azure_ai_agent_as_kernel_function.py`
**功能**: 將 Azure AI Agent 封裝為 Semantic Kernel 函數

```python
# 將代理用作其他代理的工具
triage_agent = ChatCompletionAgent(
    service=AzureChatCompletion(endpoint=MY_AZURE_OPENAI_ENDPOINT),
    kernel=kernel,
    name="TriageAgent",
    instructions="Route requests to appropriate agents",
    plugins=[billing_agent, refund_agent]  # 代理作為插件
)
```

**應用場景**:
- 🎯 智能請求路由
- 🔄 代理間協作
- 📊 分工專業化
- 🏢 企業級工作流程

### 📋 宣告式配置範例 (Declarative Configuration)

#### 21. YAML 配置代理 (YAML-Based Agent)
**檔案**: `azure_ai_agent_declarative.py`
**功能**: 使用 YAML 配置檔案定義代理

```yaml
type: foundry_agent
name: WeatherAgent
instructions: Answer weather questions using external APIs
model:
  id: ${AzureAI:ChatModelId}
  connection:
    endpoint: ${AzureAI:Endpoint}
tools:
  - type: openapi
    id: weather_api
    description: Weather information service
```
---

## 結論 (Conclusion)

Azure AI Agent 結合 Semantic Kernel 提供了一個強大且靈活的 AI 代理開發平台。從簡單的對話機器人到複雜的多代理企業系統，這個平台都能提供完整的解決方案。

### 關鍵成功因素

1. **正確的架構設計**: 合理規劃代理職責和協作關係
2. **有效的資源管理**: 妥善處理連接、執行緒和記憶體資源
3. **完善的錯誤處理**: 建立健壯的異常處理和恢復機制
4. **持續的效能監控**: 實施全面的監控和優化策略

### 開發建議

- **從簡單開始**: 先實現基本功能，再逐步添加複雜特性
- **模組化設計**: 保持代理功能的單一職責和可複用性
- **測試驅動**: 建立完整的測試套件確保系統穩定性
- **文件完整**: 維護完善的技術文件和使用指南
