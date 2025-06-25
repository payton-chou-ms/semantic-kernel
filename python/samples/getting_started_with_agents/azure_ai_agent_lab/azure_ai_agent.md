# Azure AI Agent 完整指南

## Summary

本文檔涵蓋了 Semantic Kernel 中 Azure AI Agent 的八種主要應用場景，展示如何使用 Azure AI Agent Service 構建智能代理系統：

### 技術架構總覽
- **基礎框架**: Azure AI Agent Service + Semantic Kernel
- **身份驗證**: DefaultAzureCredential (Azure Identity)
- **AI 服務**: Azure AI Agent Service
- **工具整合**: Plugin、Code Interpreter、File Search、OpenAPI

### 八大應用場景
| 範例      | 主要情境     | 核心技術         | 特色功能               |
| --------- | ------------ | ---------------- | ---------------------- |
| **step1** | 基本對話代理 | Azure AI Agent   | 對話記憶、自動線程管理 |
| **step2** | 插件增強代理 | Plugin 整合      | 自訂功能擴展、函數調用 |
| **step3** | 群組協作代理 | AgentGroupChat   | 多代理協作、終止策略   |
| **step4** | 程式執行代理 | Code Interpreter | 檔案上傳、程式碼執行   |
| **step5** | 檔案搜尋代理 | File Search      | 向量搜尋、文件問答     |
| **step6** | API 整合代理 | OpenAPI Tools    | 外部 API 調用、工具鏈  |
| **step7** | 檢索增強代理 | 現有 Agent 整合  | 串流處理、中間步驟監控 |
| **step8** | 宣告式代理   | YAML 配置        | 配置驅動、模板化創建   |

---

## 代理情境分析 (Agent Scenarios Analysis)

### 各範例文件中的代理角色與功能

每個 Python 範例文件都展示了不同的 Azure AI Agent 應用模式，以下詳細說明各代理的功能定位：

#### 基本對話代理 (step1_azure_ai_agent.py)
- **Assistant (助理代理)**: 基本對話助理，能夠記住用戶身份並維持對話上下文
- **功能特色**: 
  - 自動線程管理
  - 對話記憶保持
  - 簡單問答互動

#### 插件增強代理 (step2_azure_ai_agent_plugin.py)
- **Host (主持人代理)**: 餐廳服務員角色，配備 MenuPlugin 回答菜單相關問題
- **MenuPlugin 功能**:
  - `get_specials()`: 提供今日特餐資訊
  - `get_item_price()`: 查詢菜品價格
- **功能特色**: 
  - 自訂插件整合
  - 函數調用能力
  - 領域專業知識

#### 群組協作代理 (step3_azure_ai_agent_group_chat.py)
- **ArtDirector (藝術總監代理)**: 
  - 角色定位: 具有 David Ogilvy 風格的藝術總監
  - 職責: 評估文案品質，決定是否批准發布
  - 終止條件: 當回應包含 "approved" 時結束協作
- **CopyWriter (文案撰寫代理)**:
  - 角色定位: 十年經驗的文案專家，以簡潔和幽默著稱
  - 職責: 創作和改進廣告文案
  - 工作風格: 專注目標、避免閒聊、接受建議改進
- **協作模式**: 循環討論直到獲得批准

#### 程式執行代理 (step4_azure_ai_agent_code_interpreter.py)
- **Code Analyst (程式分析代理)**: 
  - 功能: 使用 Code Interpreter 工具分析 CSV 數據
  - 能力: 檔案上傳、Python 程式碼執行、數據分析
  - 應用場景: 銷售數據統計、報表生成

#### 檔案搜尋代理 (step5_azure_ai_agent_file_search.py)
- **Document Search Agent (文件搜尋代理)**:
  - 功能: 基於上傳的 PDF 檔案回答問題
  - 技術: File Search Tool + Vector Store
  - 應用場景: 員工資料查詢、文件問答系統

#### API 整合代理 (step6_azure_ai_agent_openapi.py)
- **Multi-API Agent (多 API 整合代理)**:
  - 整合工具: Weather API + Countries API
  - 功能: 跨 API 資料整合和分析
  - 應用場景: 地理資訊查詢、天氣資訊獲取

#### 檢索增強代理 (step7_azure_ai_agent_retrieval.py)
- **Existing Agent (現有代理整合)**:
  - 特色: 使用已部署的 Azure AI Agent
  - 功能: 串流回應、中間步驟監控
  - 應用場景: RAG 系統、文檔檢索

#### 宣告式代理 (step8_azure_ai_agent_declarative.py)
- **YAML-Defined Host (宣告式主持人代理)**:
  - 特色: 透過 YAML 配置創建
  - 功能: 與 step2 相同的 MenuPlugin 功能
  - 優勢: 配置驅動、易於維護和部署

### 代理設計模式分析

#### 1. 服務角色模式
- **服務導向**: Host (餐廳服務)、Assistant (通用助理)
- **專業諮詢**: ArtDirector (創意總監)、CopyWriter (文案專家)
- **技術分析**: Code Analyst (數據分析)、Document Search Agent (文件搜尋)

#### 2. 工具增強模式
- **插件擴展**: MenuPlugin 提供菜單查詢功能
- **內建工具**: Code Interpreter、File Search、OpenAPI Tools
- **外部整合**: Weather API、Countries API

#### 3. 協作工作流模式
- **審查流程**: CopyWriter 創作 → ArtDirector 審查 → 批准/修改
- **迭代改進**: 基於反饋持續優化輸出品質
- **終止機制**: 自訂 ApprovalTerminationStrategy

#### 4. 配置驅動模式
- **宣告式定義**: YAML 配置檔案
- **模板化創建**: AgentRegistry.create_from_yaml()
- **靈活部署**: 支援動態配置和環境變數

---

## 1. 基本 Azure AI Agent (step1_azure_ai_agent.py)

### 主要情境
創建基本的 Azure AI Agent，展示最基礎的對話功能和線程管理。

### 技術特色
- **Azure 身份驗證**: 使用 DefaultAzureCredential
- **自動線程管理**: Agent 自動維護對話上下文
- **對話記憶**: 能記住用戶身份和對話歷史

### 核心程式碼

```python
import asyncio
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread

# 模擬對話輸入
USER_INPUTS = [
    "Hello, I am John Doe.",
    "What is your name?", 
    "What is my name?",
]

async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. 在 Azure AI Agent Service 上創建代理
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            name="Assistant",
            instructions="Answer the user's questions.",
        )

        # 2. 為 Azure AI Agent 創建 Semantic Kernel 代理
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # 3. 創建對話線程
        thread: AzureAIAgentThread = None

        try:
            for user_input in USER_INPUTS:
                print(f"# User: {user_input}")
                # 4. 調用代理獲取回應
                response = await agent.get_response(messages=user_input, thread=thread)
                print(f"# {response.name}: {response}")
                thread = response.thread
        finally:
            # 5. 清理：刪除線程和代理
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)
```

### 關鍵特性
- **自動上下文保持**: 代理記住 "John Doe" 的身份
- **線程管理**: 自動創建和維護對話線程
- **資源清理**: 自動清理創建的資源

---

## 2. 插件增強 Agent (step2_azure_ai_agent_plugin.py)

### 主要情境
展示如何為 Azure AI Agent 添加自訂插件，擴展代理的功能能力。

### 技術特色
- **Plugin 整合**: 自訂 MenuPlugin 提供菜單查詢功能
- **函數調用**: 代理能自動調用合適的插件函數
- **串流回應**: 使用 invoke() 方法獲取串流回應

### 核心程式碼

```python
from typing import Annotated
from semantic_kernel.functions import kernel_function

# 定義菜單插件
class MenuPlugin:
    """餐廳菜單插件範例"""

    @kernel_function(description="Provides a list of specials from the menu.")
    def get_specials(self) -> Annotated[str, "Returns the specials from the menu."]:
        return """
        Special Soup: Clam Chowder
        Special Salad: Cobb Salad
        Special Drink: Chai Tea
        """

    @kernel_function(description="Provides the price of the requested menu item.")
    def get_item_price(
        self, menu_item: Annotated[str, "The name of the menu item."]
    ) -> Annotated[str, "Returns the price of the menu item."]:
        return "$9.99"

# 對話輸入
USER_INPUTS = [
    "Hello",
    "What is the special soup?",
    "How much does that cost?", 
    "Thank you",
]

async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. 創建代理定義
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            name="Host",
            instructions="Answer questions about the menu.",
        )

        # 2. 創建帶插件的代理
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
            plugins=[MenuPlugin()],  # 添加插件到代理
        )

        thread = None
        try:
            for user_input in USER_INPUTS:
                print(f"# User: {user_input}")
                # 3. 串流調用代理
                async for response in agent.invoke(
                    messages=user_input,
                    thread=thread,
                ):
                    print(f"# {response.name}: {response}")
                    thread = response.thread
        finally:
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)
```

### Plugin 設計要點
- **函數註解**: 使用 `@kernel_function` 裝飾器
- **型別提示**: 使用 `Annotated` 提供參數描述
- **自動調用**: 代理根據用戶問題自動選擇合適的函數

---

## 3. 群組協作 Agent (step3_azure_ai_agent_group_chat.py)

### 主要情境
展示多個 Azure AI Agent 協作完成創意任務，實現代理間的動態互動。

### 技術特色
- **多代理協作**: 兩個代理協作完成文案創作任務
- **自訂終止策略**: ApprovalTerminationStrategy 控制協作流程
- **角色專業化**: 每個代理有明確的角色定位和專業領域

### 核心程式碼

```python
from semantic_kernel.agents import AgentGroupChat, AzureAIAgent
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.contents import AuthorRole

# 自訂終止策略
class ApprovalTerminationStrategy(TerminationStrategy):
    """決定代理何時應該終止的策略"""

    async def should_agent_terminate(self, agent, history):
        """檢查代理是否應該終止"""
        return "approved" in history[-1].content.lower()

# 代理角色定義
REVIEWER_NAME = "ArtDirector"
REVIEWER_INSTRUCTIONS = """
You are an art director who has opinions about copywriting born of a love for David Ogilvy.
The goal is to determine if the given copy is acceptable to print.
If so, state that it is approved. Do not use the word "approve" unless you are giving approval.
If not, provide insight on how to refine suggested copy without example.
"""

COPYWRITER_NAME = "CopyWriter"  
COPYWRITER_INSTRUCTIONS = """
You are a copywriter with ten years of experience and are known for brevity and a dry humor.
The goal is to refine and decide on the single best copy as an expert in the field.
Only provide a single proposal per response.
You're laser focused on the goal at hand.
Don't waste time with chit chat.
Consider suggestions when refining an idea.
"""

TASK = "a slogan for a new line of electric cars."

async def main():
    ai_agent_settings = AzureAIAgentSettings()
    
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. 創建審查代理
        reviewer_agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name=REVIEWER_NAME,
            instructions=REVIEWER_INSTRUCTIONS,
        )
        agent_reviewer = AzureAIAgent(
            client=client,
            definition=reviewer_agent_definition,
        )

        # 2. 創建文案代理
        copy_writer_agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name=COPYWRITER_NAME,
            instructions=COPYWRITER_INSTRUCTIONS,
        )
        agent_writer = AzureAIAgent(
            client=client,
            definition=copy_writer_agent_definition,
        )

        # 3. 建立群組聊天與自訂終止策略
        chat = AgentGroupChat(
            agents=[agent_writer, agent_reviewer],
            termination_strategy=ApprovalTerminationStrategy(
                agents=[agent_reviewer], 
                maximum_iterations=10
            ),
        )

        try:
            # 4. 添加任務訊息到群組聊天
            await chat.add_chat_message(message=TASK)
            print(f"# {AuthorRole.USER}: '{TASK}'")
            
            # 5. 執行聊天
            async for content in chat.invoke():
                print(f"# {content.role} - {content.name or '*'}: '{content.content}'")
        finally:
            # 6. 清理資源
            await chat.reset()
            await client.agents.delete_agent(agent_reviewer.id)
            await client.agents.delete_agent(agent_writer.id)
```

### 協作流程
1. **CopyWriter** 創作初始文案
2. **ArtDirector** 評估並提供反饋
3. **CopyWriter** 根據反饋修改
4. 循環直到 ArtDirector 說出 "approved"

---

## 4. 程式執行 Agent (step4_azure_ai_agent_code_interpreter.py)

### 主要情境
展示 Azure AI Agent 如何使用 Code Interpreter 工具分析上傳的檔案並執行 Python 程式碼。

### 技術特色
- **檔案上傳**: 上傳 CSV 檔案到 Azure AI Agent Service
- **程式碼執行**: 使用 Code Interpreter 工具執行 Python 程式碼
- **數據分析**: 自動生成數據分析程式碼並執行

### 核心程式碼

```python
import os
from azure.ai.agents.models import CodeInterpreterTool, FilePurpose

TASK = "What's the total sum of all sales for all segments using Python?"

async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. 準備 CSV 檔案路徑
        csv_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 
            "resources", 
            "sales.csv"
        )

        # 2. 上傳 CSV 檔案到 Azure AI Agent Service
        file = await client.agents.files.upload_and_poll(
            file_path=csv_file_path, 
            purpose=FilePurpose.AGENTS
        )

        # 3. 創建程式碼解釋器工具，引用上傳的檔案
        code_interpreter = CodeInterpreterTool(file_ids=[file.id])
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            tools=code_interpreter.definitions,
            tool_resources=code_interpreter.resources,
        )

        # 4. 創建 Semantic Kernel 代理
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        thread: AzureAIAgentThread | None = None

        try:
            print(f"# User: '{TASK}'")
            # 5. 調用代理進行數據分析
            async for response in agent.invoke(messages=TASK, thread=thread):
                if response.role != AuthorRole.TOOL:
                    print(f"# Agent: {response}")
                thread = response.thread
        finally:
            # 6. 清理：刪除線程、代理和檔案
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)
            await client.agents.files.delete(file.id)
```

### Code Interpreter 功能
- **自動程式碼生成**: 根據問題自動生成 Python 程式碼
- **檔案處理**: 自動載入和分析上傳的檔案
- **數據視覺化**: 支援 matplotlib 等視覺化庫
- **錯誤處理**: 自動處理程式碼執行錯誤並重試

---

## 5. 檔案搜尋 Agent (step5_azure_ai_agent_file_search.py)

### 主要情境
展示如何使用 File Search 工具讓 Azure AI Agent 基於上傳的文件回答問題。

### 技術特色
- **文件上傳**: 上傳 PDF 檔案到 Azure AI Agent Service
- **向量搜尋**: 使用 Vector Store 進行語義搜尋
- **文件問答**: 基於文件內容回答用戶問題

### 核心程式碼

```python
import os
from azure.ai.agents.models import FileInfo, FileSearchTool, VectorStore

# 模擬對話輸入
USER_INPUTS = [
    "Who is the youngest employee?",
    "Who works in sales?",
    "I have a customer request, who can help me?",
]

async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. 讀取並上傳 PDF 檔案
        pdf_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 
            "resources", 
            "employees.pdf"
        )
        file: FileInfo = await client.agents.files.upload_and_poll(
            file_path=pdf_file_path, 
            purpose="assistants"
        )
        
        # 2. 創建向量儲存庫
        vector_store: VectorStore = await client.agents.vector_stores.create_and_poll(
            file_ids=[file.id], 
            name="my_vectorstore"
        )

        # 3. 創建檔案搜尋工具
        file_search = FileSearchTool(vector_store_ids=[vector_store.id])

        # 4. 創建帶檔案搜尋工具的代理
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            tools=file_search.definitions,
            tool_resources=file_search.resources,
        )

        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        thread: AzureAIAgentThread = None

        try:
            for user_input in USER_INPUTS:
                print(f"# User: '{user_input}'")
                # 5. 調用代理進行檔案搜尋問答
                async for response in agent.invoke(messages=user_input, thread=thread):
                    if response.role != AuthorRole.TOOL:
                        print(f"# Agent: {response}")
                    thread = response.thread
        finally:
            # 6. 清理資源
            await thread.delete() if thread else None
            await client.agents.vector_stores.delete(vector_store.id)
            await client.agents.files.delete(file.id)
            await client.agents.delete_agent(agent.id)
```

### File Search 特色
- **語義搜尋**: 基於向量相似度搜尋相關內容
- **多文件支援**: 可同時搜尋多個上傳的文件
- **上下文感知**: 保持對話上下文進行連續問答

---

## 6. OpenAPI 整合 Agent (step6_azure_ai_agent_openapi.py)

### 主要情境
展示如何讓 Azure AI Agent 整合外部 OpenAPI 服務，實現跨 API 的資料整合。

### 技術特色
- **多 API 整合**: 同時整合天氣 API 和國家資訊 API
- **OpenAPI 工具**: 自動解析 OpenAPI 規格並生成工具
- **跨域查詢**: 結合多個 API 的資料回答複雜問題

### 核心程式碼

```python
import json
import os
from azure.ai.agents.models import OpenApiAnonymousAuthDetails, OpenApiTool

# 對話輸入
USER_INPUTS = [
    "What is the name and population of the country that uses currency with abbreviation THB",
    "What is the current weather in the capital city of the country?",
]

async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. 讀取 OpenAPI 規格檔案
        openapi_spec_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            "resources",
        )
        with open(os.path.join(openapi_spec_file_path, "weather.json")) as weather_file:
            weather_openapi_spec = json.loads(weather_file.read())
        with open(os.path.join(openapi_spec_file_path, "countries.json")) as countries_file:
            countries_openapi_spec = json.loads(countries_file.read())

        # 2. 創建 OpenAPI 工具
        auth = OpenApiAnonymousAuthDetails()
        openapi_weather = OpenApiTool(
            name="get_weather",
            spec=weather_openapi_spec,
            description="Retrieve weather information for a location",
            auth=auth,
        )
        openapi_countries = OpenApiTool(
            name="get_country",
            spec=countries_openapi_spec,
            description="Retrieve country information",
            auth=auth,
        )

        # 3. 創建帶 OpenAPI 工具的代理
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            tools=openapi_weather.definitions + openapi_countries.definitions,
        )

        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        thread: AzureAIAgentThread = None

        try:
            for user_input in USER_INPUTS:
                print(f"# User: '{user_input}'")
                # 4. 調用代理進行跨 API 查詢
                async for response in agent.invoke(messages=user_input, thread=thread):
                    print(f"# Agent: {response}")
                    thread = response.thread
        finally:
            await client.agents.threads.delete(thread.id) if thread else None
            await client.agents.delete_agent(agent.id)
```

### OpenAPI 整合優勢
- **自動工具生成**: 基於 OpenAPI 規格自動生成工具
- **認證支援**: 支援多種認證方式
- **錯誤處理**: 自動處理 API 調用錯誤

---

## 7. 檢索增強 Agent (step7_azure_ai_agent_retrieval.py)

### 主要情境
展示如何使用已存在的 Azure AI Agent，並實現串流處理和中間步驟監控。

### 技術特色
- **現有 Agent 整合**: 使用已部署的 Azure AI Agent
- **串流處理**: 即時顯示代理回應
- **中間步驟監控**: 監控函數調用和結果

### 核心程式碼

```python
from semantic_kernel.contents import ChatMessageContent, FunctionCallContent, FunctionResultContent

USER_INPUTS = [
    "Using the provided doc, tell me about the evolution of RAG.",
]

async def handle_streaming_intermediate_steps(message: ChatMessageContent) -> None:
    """處理串流中間步驟"""
    for item in message.items or []:
        if isinstance(item, FunctionResultContent):
            print(f"Function Result:> {item.result} for function: {item.name}")
        elif isinstance(item, FunctionCallContent):
            print(f"Function Call:> {item.name} with arguments: {item.arguments}")
        else:
            print(f"{item}")

async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. 基於 agent_id 檢索代理定義
        # 將 "your-agent-id" 替換為實際的代理 ID
        agent_definition = await client.agents.get_agent(
            agent_id="<your-agent-id>",
        )

        # 2. 為 Azure AI Agent 創建 Semantic Kernel 代理
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        thread: AzureAIAgentThread = None

        try:
            for user_input in USER_INPUTS:
                print(f"# User: '{user_input}'")
                # 3. 串流調用代理
                async for response in agent.invoke_stream(
                    messages=user_input,
                    thread=thread,
                    on_intermediate_message=handle_streaming_intermediate_steps,
                ):
                    print(f"{response}", end="", flush=True)
                    thread = response.thread
        finally:
            await thread.delete() if thread else None
            # 不清理代理，以便重複使用
```

### 串流處理特色
- **即時回應**: 逐字串流顯示代理回應
- **中間監控**: 監控函數調用過程
- **現有資源重用**: 使用已部署的代理資源

---

## 8. 宣告式 Agent (step8_azure_ai_agent_declarative.py)

### 主要情境
展示如何使用 YAML 配置創建 Azure AI Agent，實現配置驅動的代理開發。

### 技術特色
- **YAML 配置**: 使用宣告式語法定義代理
- **模板化**: 支援環境變數和模板語法
- **配置驅動**: 無需程式碼即可創建代理

### 核心程式碼

```python
from semantic_kernel.agents import AgentRegistry, AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.kernel import Kernel

# 定義 YAML 規格
SPEC = """
type: foundry_agent
name: Host
instructions: Respond politely to the user's questions.
model:
  id: ${AzureAI:ChatModelId}
tools:
  - id: MenuPlugin.get_specials
    type: function
  - id: MenuPlugin.get_item_price  
    type: function
"""

async def main() -> None:
    settings = AzureAIAgentSettings()
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. 創建 Kernel 實例
        # 對於宣告式代理，需要 kernel 來解析插件
        kernel = Kernel()
        kernel.add_plugin(MenuPlugin())

        # 2. 從 YAML 創建 Semantic Kernel 代理
        agent: AzureAIAgent = await AgentRegistry.create_from_yaml(
            SPEC,
            kernel=kernel,
            settings=settings,
            client=client,
        )

        thread = None
        try:
            for user_input in USER_INPUTS:
                print(f"# User: {user_input}")
                # 3. 調用代理
                async for response in agent.invoke(
                    messages=user_input,
                    thread=thread,
                ):
                    print(f"# {response.name}: {response}")
                    thread = response.thread
        finally:
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)
```

### YAML 配置語法
- **type**: 代理類型 (foundry_agent)
- **name**: 代理名稱
- **instructions**: 代理指令
- **model**: 模型配置 (支援環境變數)
- **tools**: 工具配置 (函數、插件等)

### 宣告式優勢
- **配置分離**: 業務邏輯與配置分離
- **易於維護**: 修改配置無需重新編譯
- **環境適應**: 支援多環境配置
- **版本控制**: 配置檔案易於版本管理

---

## 技術架構與最佳實踐

### 共同技術架構

所有 Azure AI Agent 範例都基於以下核心架構：

```python
# 1. Azure 身份驗證
async with DefaultAzureCredential() as creds:
    # 2. 創建 Azure AI Agent 客戶端
    async with AzureAIAgent.create_client(credential=creds) as client:
        # 3. 創建代理定義
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            name="AgentName",
            instructions="Agent instructions",
            # 可選：工具、插件等
        )
        
        # 4. 創建 Semantic Kernel 代理
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
            # 可選：插件
        )
        
        # 5. 執行對話
        async for response in agent.invoke(messages=user_input, thread=thread):
            print(response)
            thread = response.thread
            
        # 6. 清理資源
        await client.agents.delete_agent(agent.id)
```

### 開發最佳實踐

#### 1. 身份驗證與安全
- **使用 Managed Identity**: 在 Azure 環境中使用 DefaultAzureCredential
- **環境變數配置**: 敏感資訊透過環境變數管理
- **資源清理**: 確保代理和線程資源正確清理

#### 2. 錯誤處理與監控
```python
try:
    # 代理操作
    pass
except Exception as e:
    print(f"Error: {e}")
finally:
    # 資源清理
    await thread.delete() if thread else None
    await client.agents.delete_agent(agent.id)
```

#### 3. 插件設計原則
- **單一職責**: 每個插件專注特定功能領域
- **清晰註解**: 使用 `@kernel_function` 和 `Annotated` 提供明確描述
- **錯誤處理**: 插件內部處理異常情況

#### 4. 性能優化建議
- **串流處理**: 使用 `invoke()` 或 `invoke_stream()` 提升用戶體驗
- **線程重用**: 在同一對話中重用線程
- **資源池化**: 對於高頻應用考慮代理資源池化

### 工具選擇指南

| 需求場景     | 推薦工具         | 適用範例     |
| ------------ | ---------------- | ------------ |
| 基本對話     | 無額外工具       | step1        |
| 自訂功能     | Plugin           | step2, step8 |
| 多代理協作   | AgentGroupChat   | step3        |
| 數據分析     | Code Interpreter | step4        |
| 文件問答     | File Search      | step5        |
| API 整合     | OpenAPI Tools    | step6        |
| 現有系統整合 | 現有 Agent       | step7        |
| 配置驅動     | YAML 定義        | step8        |

---

## 結論

Azure AI Agent 提供了完整的企業級代理開發平台，從基本對話到複雜的多模態任務處理都有相應的解決方案。通過合理選擇工具組合和架構模式，可以構建出功能強大、可擴展的 AI 代理系統。

每種範例都展示了不同的應用場景和技術特色，開發者可以根據實際需求選擇合適的模式，或者組合多種技術來構建更複雜的 AI 應用系統。關鍵是要理解每種工具的特性和適用場景，並遵循最佳實踐來確保系統的可靠性和可維護性。
