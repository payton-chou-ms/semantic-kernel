# Azure AI Agent 完整指南

## Summary

本文檔涵蓋了 Azure AI Agent 的八個主要範例，展示如何在 Semantic Kernel 中使用 Azure AI Agent 服務來建立智能代理：

### 技術架構總覽
- **基礎框架**: Azure AI Agent Service + Semantic Kernel
- **身份認證**: DefaultAzureCredential (Azure 身份認證)
- **AI 服務**: Azure OpenAI / Azure AI Agent Service
- **核心元件**: AzureAIAgent, AzureAIAgentThread, AzureAIAgentSettings

### 八大功能範例
| 範例      | 主要功能     | 核心技術                     | 特色能力           |
| --------- | ------------ | ---------------------------- | ------------------ |
| **step1** | 基本對話代理 | AzureAIAgent 基礎使用        | 自動維護對話歷史   |
| **step2** | 插件增強代理 | Semantic Kernel Plugin       | 自訂函數呼叫       |
| **step3** | 群組聊天代理 | AgentGroupChat               | 多代理協作對話     |
| **step4** | 程式碼解釋器 | CodeInterpreterTool          | 程式執行與檔案分析 |
| **step5** | 檔案搜尋代理 | FileSearchTool + VectorStore | 文件檢索與問答     |
| **step6** | OpenAPI 整合 | OpenApiTool                  | 外部 API 呼叫      |
| **step7** | 現有代理檢索 | 代理 ID 檢索                 | 重用已建立的代理   |
| **step8** | 宣告式代理   | YAML 規格定義                | 配置驅動的代理建立 |

---

## 代理情境分析 (Agent Scenarios Analysis)

### 各範例文件中的代理角色與功能

每個 Python 範例文件都展示了不同的代理設計模式和應用情境，以下詳細說明各代理的功能定位：

#### Basic Agent 基本代理範例

**step1_azure_ai_agent.py**
- **Assistant (助理代理)**: 基本對話助手，回答用戶問題並維護對話記憶
- **功能特色**: 自動對話歷史管理、簡單問答互動
- **應用場景**: 客服聊天機器人、基礎問答系統

**step2_azure_ai_agent_plugin.py**
- **Host (主持人代理)**: 餐廳服務員角色，使用 MenuPlugin 回答菜單相關問題
- **功能增強**: 整合 Semantic Kernel Plugin 提供專業功能
- **應用場景**: 餐廳點餐系統、產品諮詢服務

#### Collaborative Agent 協作代理範例

**step3_azure_ai_agent_group_chat.py**
- **ArtDirector (藝術總監代理)**: 內容審查者角色，評估文案品質並提供專業建議
- **CopyWriter (文案撰寫代理)**: 專業文案撰寫師，創作簡潔有力的廣告標語
- **協作模式**: 使用 ApprovalTerminationStrategy 實現審批流程
- **應用場景**: 創意團隊協作、內容審核流程

#### Specialized Tool Agent 專業工具代理範例

**step4_azure_ai_agent_code_interpreter.py**
- **Code Analyst (程式分析代理)**: 資料分析師角色，使用 Python 分析 CSV 檔案
- **工具能力**: CodeInterpreterTool 提供程式執行環境
- **應用場景**: 資料分析、報表生成、程式碼執行

**step5_azure_ai_agent_file_search.py**
- **Document Assistant (文件助理代理)**: 企業知識管理助手，搜尋員工資料庫
- **工具能力**: FileSearchTool + VectorStore 提供智能文件檢索
- **應用場景**: 企業知識庫、文件問答系統

**step6_azure_ai_agent_openapi.py**
- **Information Broker (資訊仲介代理)**: 整合多個外部 API 的資訊查詢助手
- **工具能力**: OpenApiTool 整合天氣和國家資訊 API
- **應用場景**: 多 API 整合服務、資訊聚合平台

#### Advanced Usage Agent 進階使用範例

**step7_azure_ai_agent_retrieval.py**
- **Existing Agent (現有代理)**: 重用先前建立的代理實例
- **技術特色**: 代理檢索與串流回應處理
- **應用場景**: 代理重用、持久化服務

**step8_azure_ai_agent_declarative.py**
- **Declarative Host (宣告式主持人代理)**: 使用 YAML 配置定義的餐廳服務代理
- **技術特色**: 配置驅動的代理建立、AgentRegistry 管理
- **應用場景**: 配置化代理部署、企業級代理管理

---

## 1. Basic Azure AI Agent (基本 Azure AI 代理)

### 主要情境 (step1_azure_ai_agent.py)
建立最基本的 Azure AI 代理，展示如何進行簡單的對話互動。

### 技術特色
- **自動對話管理**: Azure AI Agent 服務自動維護對話歷史
- **身份認證**: 使用 DefaultAzureCredential 進行 Azure 認證
- **執行緒管理**: 透過 AzureAIAgentThread 管理對話狀態

### 核心程式碼

```python
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
        # 1. 在 Azure AI 代理服務上建立代理
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            name="Assistant",
            instructions="Answer the user's questions.",
        )

        # 2. 建立 Semantic Kernel 代理
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # 3. 建立執行緒
        thread: AzureAIAgentThread = None

        try:
            for user_input in USER_INPUTS:
                print(f"# User: {user_input}")
                # 4. 呼叫代理取得回應
                response = await agent.get_response(messages=user_input, thread=thread)
                print(f"# {response.name}: {response}")
                thread = response.thread
        finally:
            # 5. 清理資源
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)
```

---

## 2. Plugin-Enhanced Agent (插件增強代理)

### 主要情境 (step2_azure_ai_agent_plugin.py)
展示如何為 Azure AI 代理添加自訂插件功能，實現專業領域的問答能力。

### 技術特色
- **插件整合**: 使用 Semantic Kernel Plugin 擴展代理能力
- **函數呼叫**: 自動識別並呼叫適當的插件函數
- **專業領域**: 針對特定業務場景提供專業服務

### 核心程式碼

```python
from semantic_kernel.functions import kernel_function
from typing import Annotated

# 定義餐廳菜單插件
class MenuPlugin:
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

async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 建立具有插件的代理
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            name="Host",
            instructions="Answer questions about the menu.",
        )

        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
            plugins=[MenuPlugin()],  # 添加插件到代理
        )

        # 使用 invoke 方法進行串流回應
        for user_input in USER_INPUTS:
            print(f"# User: {user_input}")
            async for response in agent.invoke(
                messages=user_input,
                thread=thread,
            ):
                print(f"# {response.name}: {response}")
                thread = response.thread
```

---

## 3. Group Chat Agent (群組聊天代理)

### 主要情境 (step3_azure_ai_agent_group_chat.py)
實現多個代理之間的協作對話，展示團隊工作模式。

### 技術特色
- **多代理協作**: 使用 AgentGroupChat 管理多個代理
- **自訂終止策略**: ApprovalTerminationStrategy 控制對話結束條件
- **角色專業化**: 不同代理擔任不同專業角色

### 核心程式碼

```python
from semantic_kernel.agents import AgentGroupChat, AzureAIAgent
from semantic_kernel.agents.strategies import TerminationStrategy

class ApprovalTerminationStrategy(TerminationStrategy):
    """當內容被批准時終止對話的策略"""
    async def should_agent_terminate(self, agent, history):
        return "approved" in history[-1].content.lower()

# 定義代理角色
REVIEWER_INSTRUCTIONS = """
You are an art director who has opinions about copywriting born of a love for David Ogilvy.
Determine if the given copy is acceptable to print.
If so, state that it is approved.
"""

COPYWRITER_INSTRUCTIONS = """
You are a copywriter with ten years of experience and are known for brevity and dry humor.
Refine and decide on the single best copy as an expert in the field.
"""

async def main():
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 建立審查者代理
        reviewer_agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            name="ArtDirector",
            instructions=REVIEWER_INSTRUCTIONS,
        )
        agent_reviewer = AzureAIAgent(client=client, definition=reviewer_agent_definition)

        # 建立文案撰寫代理
        copy_writer_agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            name="CopyWriter", 
            instructions=COPYWRITER_INSTRUCTIONS,
        )
        agent_writer = AzureAIAgent(client=client, definition=copy_writer_agent_definition)

        # 建立群組聊天
        chat = AgentGroupChat(
            agents=[agent_writer, agent_reviewer],
            termination_strategy=ApprovalTerminationStrategy(
                agents=[agent_reviewer], 
                maximum_iterations=10
            ),
        )

        try:
            await chat.add_chat_message(message="a slogan for a new line of electric cars.")
            async for content in chat.invoke():
                print(f"# {content.role} - {content.name}: '{content.content}'")
        finally:
            await chat.reset()
            await client.agents.delete_agent(agent_reviewer.id)
            await client.agents.delete_agent(agent_writer.id)
```

---

## 4. Code Interpreter Agent (程式碼解釋器代理)

### 主要情境 (step4_azure_ai_agent_code_interpreter.py)
使用程式碼解釋器工具分析檔案和執行程式碼。

### 技術特色
- **檔案上傳**: 上傳 CSV 檔案到 Azure AI 服務
- **程式執行**: CodeInterpreterTool 提供 Python 執行環境
- **資料分析**: 自動生成和執行資料分析程式碼

### 核心程式碼

```python
from azure.ai.agents.models import CodeInterpreterTool, FilePurpose

TASK = "What's the total sum of all sales for all segments using Python?"

async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. 上傳 CSV 檔案
        csv_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 
            "resources", "sales.csv"
        )
        file = await client.agents.files.upload_and_poll(
            file_path=csv_file_path, 
            purpose=FilePurpose.AGENTS
        )

        # 2. 建立程式碼解釋器工具
        code_interpreter = CodeInterpreterTool(file_ids=[file.id])
        
        # 3. 建立具有程式碼解釋器的代理
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            tools=code_interpreter.definitions,
            tool_resources=code_interpreter.resources,
        )

        agent = AzureAIAgent(client=client, definition=agent_definition)

        try:
            print(f"# User: '{TASK}'")
            async for response in agent.invoke(messages=TASK, thread=thread):
                if response.role != AuthorRole.TOOL:
                    print(f"# Agent: {response}")
                thread = response.thread
        finally:
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)
            await client.agents.files.delete(file.id)
```

---

## 5. File Search Agent (檔案搜尋代理)

### 主要情境 (step5_azure_ai_agent_file_search.py)
使用向量搜尋技術在上傳的文件中尋找相關資訊。

### 技術特色
- **向量搜尋**: 使用 VectorStore 進行語意搜尋
- **文件檢索**: FileSearchTool 提供智能文件查詢
- **多檔案支援**: 支援 PDF 等多種文件格式

### 核心程式碼

```python
from azure.ai.agents.models import FileInfo, FileSearchTool, VectorStore

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
        # 1. 上傳 PDF 檔案並建立向量儲存
        pdf_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 
            "resources", "employees.pdf"
        )
        file: FileInfo = await client.agents.files.upload_and_poll(
            file_path=pdf_file_path, 
            purpose="assistants"
        )
        vector_store: VectorStore = await client.agents.vector_stores.create_and_poll(
            file_ids=[file.id], 
            name="my_vectorstore"
        )

        # 2. 建立檔案搜尋工具
        file_search = FileSearchTool(vector_store_ids=[vector_store.id])

        # 3. 建立具有檔案搜尋功能的代理
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            tools=file_search.definitions,
            tool_resources=file_search.resources,
        )

        agent = AzureAIAgent(client=client, definition=agent_definition)

        try:
            for user_input in USER_INPUTS:
                print(f"# User: '{user_input}'")
                async for response in agent.invoke(messages=user_input, thread=thread):
                    if response.role != AuthorRole.TOOL:
                        print(f"# Agent: {response}")
                    thread = response.thread
        finally:
            await thread.delete() if thread else None
            await client.agents.vector_stores.delete(vector_store.id)
            await client.agents.files.delete(file.id)
            await client.agents.delete_agent(agent.id)
```

---

## 6. OpenAPI Integration Agent (OpenAPI 整合代理)

### 主要情境 (step6_azure_ai_agent_openapi.py)
整合外部 OpenAPI 服務，實現跨平台資料查詢。

### 技術特色
- **多 API 整合**: 同時整合天氣和國家資訊 API
- **OpenAPI 規格**: 使用標準 OpenAPI 3.0 規格檔案
- **匿名認證**: 支援無需認證的公開 API

### 核心程式碼

```python
from azure.ai.agents.models import OpenApiAnonymousAuthDetails, OpenApiTool

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
        with open(os.path.join(openapi_spec_file_path, "weather.json")) as weather_file:
            weather_openapi_spec = json.loads(weather_file.read())
        with open(os.path.join(openapi_spec_file_path, "countries.json")) as countries_file:
            countries_openapi_spec = json.loads(countries_file.read())

        # 2. 建立 OpenAPI 工具
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

        # 3. 建立具有 OpenAPI 工具的代理
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            tools=openapi_weather.definitions + openapi_countries.definitions,
        )

        agent = AzureAIAgent(client=client, definition=agent_definition)

        try:
            for user_input in USER_INPUTS:
                print(f"# User: '{user_input}'")
                async for response in agent.invoke(messages=user_input, thread=thread):
                    print(f"# Agent: {response}")
                    thread = response.thread
        finally:
            await client.agents.threads.delete(thread.id) if thread else None
            await client.agents.delete_agent(agent.id)
```

---

## 7. Existing Agent Retrieval (現有代理檢索)

### 主要情境 (step7_azure_ai_agent_retrieval.py)
檢索和使用先前建立的 Azure AI 代理。

### 技術特色
- **代理檢索**: 使用代理 ID 檢索現有代理
- **串流回應**: 支援即時串流回應處理
- **中間步驟監控**: 監控函數呼叫和結果

### 核心程式碼

```python
from semantic_kernel.contents import ChatMessageContent, FunctionCallContent, FunctionResultContent

async def handle_streaming_intermediate_steps(message: ChatMessageContent) -> None:
    """處理串流中間步驟"""
    for item in message.items or []:
        if isinstance(item, FunctionResultContent):
            print(f"Function Result:> {item.result} for function: {item.name}")
        elif isinstance(item, FunctionCallContent):
            print(f"Function Call:> {item.name} with arguments: {item.arguments}")

async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. 根據代理 ID 檢索代理定義
        agent_definition = await client.agents.get_agent(
            agent_id="<your-agent-id>",  # 替換為實際的代理 ID
        )

        # 2. 建立 Semantic Kernel 代理
        agent = AzureAIAgent(client=client, definition=agent_definition)

        try:
            for user_input in USER_INPUTS:
                print(f"# User: '{user_input}'")
                # 3. 使用串流模式呼叫代理
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

---

## 8. Declarative Agent (宣告式代理)

### 主要情境 (step8_azure_ai_agent_declarative.py)
使用 YAML 配置檔案定義代理，實現配置驅動的代理建立。

### 技術特色
- **YAML 配置**: 使用 YAML 格式定義代理規格
- **AgentRegistry**: 統一管理和建立代理
- **配置驅動**: 支援企業級代理配置管理

### 核心程式碼

```python
from semantic_kernel.agents import AgentRegistry
from semantic_kernel.kernel import Kernel

# YAML 代理規格定義
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
        # 1. 建立 Kernel 實例
        kernel = Kernel()
        kernel.add_plugin(MenuPlugin())

        # 2. 從 YAML 建立代理
        agent: AzureAIAgent = await AgentRegistry.create_from_yaml(
            SPEC,
            kernel=kernel,
            settings=settings,
            client=client,
        )

        try:
            for user_input in USER_INPUTS:
                print(f"# User: {user_input}")
                async for response in agent.invoke(messages=user_input, thread=thread):
                    print(f"# {response.name}: {response}")
                    thread = response.thread
        finally:
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)
```

---

## 技術架構與最佳實踐

### 共同技術架構

所有 Azure AI Agent 範例都基於以下核心架構：

```python
# 1. Azure 身份認證
async with DefaultAzureCredential() as creds:
    # 2. 建立 Azure AI Agent 客戶端
    async with AzureAIAgent.create_client(credential=creds) as client:
        # 3. 建立代理定義
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            name="AgentName",
            instructions="Agent instructions",
            tools=tools,  # 可選工具
        )
        
        # 4. 建立 Semantic Kernel 代理
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
            plugins=plugins,  # 可選插件
        )
        
        # 5. 執行對話
        async for response in agent.invoke(messages=user_input, thread=thread):
            print(f"# {response.name}: {response}")
            thread = response.thread
        
        # 6. 清理資源
        await thread.delete() if thread else None
        await client.agents.delete_agent(agent.id)
```

### 開發最佳實踐

1. **身份認證設定**: 確保正確配置 Azure 身份認證和權限
2. **資源管理**: 務必在 finally 區塊中清理代理和執行緒資源
3. **錯誤處理**: 使用 try-catch 處理 Azure 服務呼叫異常
4. **工具整合**: 善用 CodeInterpreter、FileSearch、OpenAPI 等工具
5. **插件開發**: 開發自訂插件擴展代理功能

### 適用場景建議

- **基本代理**: 適合簡單的問答和客服場景
- **插件代理**: 適合需要專業功能的業務應用
- **群組代理**: 適合需要多方協作的複雜任務
- **工具代理**: 適合資料分析、文件處理等專業工作
- **整合代理**: 適合需要整合多個外部服務的應用
- **宣告式代理**: 適合企業級代理管理和部署

---

## 結論

Azure AI Agent 提供了強大的代理建立和管理能力，結合 Semantic Kernel 的插件系統，可以建立功能豐富、高度專業化的智能代理。從基本的對話代理到複雜的多工具整合代理，Azure AI Agent 都能提供穩定可靠的解決方案。

選擇適當的代理模式和工具組合，能夠顯著提升 AI 應用的功能性和實用性，滿足各種企業級應用需求。
