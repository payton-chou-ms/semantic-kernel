# Semantic Kernel Multi-Agent Orchestration 完整指南

## Summary

本文檔涵蓋了 Semantic Kernel 中五種主要的多 Agent 協調模式，每種模式都適用於不同的應用場景：

### 技術架構總覽
- **基礎框架**: Semantic Kernel Agent Framework
- **執行環境**: InProcessRuntime
- **AI 服務**: Azure OpenAI / OpenAI Chat Completion
- **資料格式**: Pydantic 結構化輸出支援

### 五大協調模式
| 模式           | 適用場景       | 核心技術          | 特色功能             |
| -------------- | -------------- | ----------------- | -------------------- |
| **Concurrent** | 獨立並行分析   | 多 Agent 同時執行 | 結構化輸出、超時控制 |
| **Sequential** | 步驟式處理流程 | Agent 串接執行    | 串流回調、取消機制   |
| **GroupChat**  | 多方協作討論   | 狀態機管理器      | 輪轉發言、人機協作   |
| **Handoff**    | 動態任務分流   | 智能交接機制      | 客服分流、結構化輸入 |
| **Magentic**   | 複雜任務解決   | AI 規劃管理器     | 網路搜尋、程式執行   |

---

## 1. Concurrent Orchestration (並行協調)

### 主要情境
多個專家 Agent 同時分析同一問題，適用於需要不同觀點或專業領域獨立分析的場景。

### 技術特色
- **並行執行**: 多個 Agent 同時處理相同任務
- **結果聚合**: 收集所有 Agent 的回應
- **超時控制**: 設定最大等待時間
- **結構化輸出**: 支援 Pydantic 模型格式化輸出

### 核心程式碼

#### 基本並行範例 (step1_concurrent.py)
```python
from semantic_kernel.agents import Agent, ChatCompletionAgent, ConcurrentOrchestration
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

def get_agents() -> list[Agent]:
    physics_agent = ChatCompletionAgent(
        name="PhysicsExpert",
        instructions="You are an expert in physics. You answer questions from a physics perspective.",
        service=AzureChatCompletion(),
    )
    chemistry_agent = ChatCompletionAgent(
        name="ChemistryExpert",
        instructions="You are an expert in chemistry. You answer questions from a chemistry perspective.",
        service=AzureChatCompletion(),
    )
    return [physics_agent, chemistry_agent]

async def main():
    # 1. 建立並行協調器
    agents = get_agents()
    concurrent_orchestration = ConcurrentOrchestration(members=agents)
    
    # 2. 啟動執行環境
    runtime = InProcessRuntime()
    runtime.start()
    
    # 3. 執行任務
    orchestration_result = await concurrent_orchestration.invoke(
        task="What is temperature?",
        runtime=runtime,
    )
    
    # 4. 取得結果
    value = await orchestration_result.get(timeout=20)
    for item in value:
        print(f"# {item.name}: {item.content}")
    
    # 5. 停止執行環境
    await runtime.stop_when_idle()
```

#### 結構化輸出範例 (step1a_concurrent_structured_outputs.py)
```python
from pydantic import BaseModel
from semantic_kernel.agents.orchestration.tools import structured_outputs_transform

class ArticleAnalysis(BaseModel):
    themes: list[str]
    sentiments: list[str]
    entities: list[str]

def get_agents() -> list[Agent]:
    theme_agent = ChatCompletionAgent(
        name="ThemeAgent",
        instructions="You are an expert in identifying themes in articles.",
        service=AzureChatCompletion(),
    )
    sentiment_agent = ChatCompletionAgent(
        name="SentimentAgent", 
        instructions="You are an expert in sentiment analysis.",
        service=AzureChatCompletion(),
    )
    entity_agent = ChatCompletionAgent(
        name="EntityAgent",
        instructions="You are an expert in entity recognition.",
        service=AzureChatCompletion(),
    )
    return [theme_agent, sentiment_agent, entity_agent]

async def main():
    agents = get_agents()
    # 啟用結構化輸出
    concurrent_orchestration = ConcurrentOrchestration[str, ArticleAnalysis](
        members=agents,
        output_transform=structured_outputs_transform(ArticleAnalysis, AzureChatCompletion()),
    )
    
    # 執行並取得結構化結果
    value = await orchestration_result.get(timeout=20)
    if isinstance(value, ArticleAnalysis):
        print(f"Themes: {value.themes}")
        print(f"Sentiments: {value.sentiments}")
        print(f"Entities: {value.entities}")
```
#### 基本並行範例 with UI (step1_concurrent_ui.py)
```python
chainlit run step1_concurrent_ui.py
```
---

## 2. Sequential Orchestration (順序協調)

### 主要情境
需要明確步驟順序的處理流程，前一個 Agent 的輸出成為下一個 Agent 的輸入。

### 技術特色
- **流水線處理**: Agent 按序執行，輸出串接
- **回調機制**: 即時監控每個 Agent 的輸出
- **串流支援**: 即時顯示 Agent 生成內容
- **取消機制**: 支援中途取消執行

### 核心程式碼

#### 基本順序範例 (step2_sequential.py)
```python
from semantic_kernel.agents import Agent, ChatCompletionAgent, SequentialOrchestration
from semantic_kernel.contents import ChatMessageContent

def get_agents() -> list[Agent]:
    concept_extractor_agent = ChatCompletionAgent(
        name="ConceptExtractorAgent",
        instructions=(
            "You are a marketing analyst. Given a product description, identify:\n"
            "- Key features\n- Target audience\n- Unique selling points\n"
        ),
        service=AzureChatCompletion(),
    )
    writer_agent = ChatCompletionAgent(
        name="WriterAgent",
        instructions=(
            "You are a marketing copywriter. Compose compelling marketing copy "
            "that highlights the features, audience, and USPs."
        ),
        service=AzureChatCompletion(),
    )
    format_proof_agent = ChatCompletionAgent(
        name="FormatProofAgent",
        instructions=(
            "You are an editor. Correct grammar, improve clarity, "
            "ensure consistent tone, and make it polished."
        ),
        service=AzureChatCompletion(),
    )
    # Agent 執行順序由列表順序決定
    return [concept_extractor_agent, writer_agent, format_proof_agent]

def agent_response_callback(message: ChatMessageContent) -> None:
    """監控每個 Agent 的輸出"""
    print(f"# {message.name}\n{message.content}")

async def main():
    agents = get_agents()
    sequential_orchestration = SequentialOrchestration(
        members=agents,
        agent_response_callback=agent_response_callback,
    )
    
    runtime = InProcessRuntime()
    runtime.start()
    
    orchestration_result = await sequential_orchestration.invoke(
        task="An eco-friendly stainless steel water bottle that keeps drinks cold for 24 hours",
        runtime=runtime,
    )
    
    value = await orchestration_result.get(timeout=20)
    print(f"***** Final Result *****\n{value}")
```

#### 取消機制範例 (step2a_sequential_cancellation_token.py)
```python
async def main():
    # ... 設定 agents 和 orchestration
    
    orchestration_result = await sequential_orchestration.invoke(
        task="An eco-friendly stainless steel water bottle...",
        runtime=runtime,
    )
    
    # 延遲後取消執行
    await asyncio.sleep(1)
    orchestration_result.cancel()
    
    try:
        value = await orchestration_result.get(timeout=20)
        print(f"Result: {value}")
    except Exception as e:
        print(f"Orchestration was cancelled: {e}")
    finally:
        await runtime.stop_when_idle()
```

#### 串流回調範例 (step2b_sequential_streaming_agent_response_callback.py)
```python
from semantic_kernel.contents import StreamingChatMessageContent

is_new_message = True

def streaming_agent_response_callback(message: StreamingChatMessageContent, is_final: bool) -> None:
    """即時顯示 Agent 串流輸出"""
    global is_new_message
    if is_new_message:
        print(f"\n# {message.name}\n", end="", flush=True)
        is_new_message = False
    
    print(message.content, end="", flush=True)
    
    if is_final:
        print("\n")
        is_new_message = True

async def main():
    sequential_orchestration = SequentialOrchestration(
        members=agents,
        streaming_agent_response_callback=streaming_agent_response_callback,
    )
    # ... 其餘執行邏輯
```

---

## 3. GroupChat Orchestration (群組聊天協調)

### 主要情境
多個 Agent 進行群組討論，適用於需要多方意見交流和反覆討論的協作場景。

### 技術特色
- **狀態機管理**: 控制對話流程（繼續、終止、用戶輸入）
- **輪轉機制**: RoundRobinGroupChatManager 控制發言順序
- **人機協作**: 支援人類介入對話流程
- **AI 管理器**: 使用 AI 服務自動決定對話流程

### 核心程式碼

#### 基本群組聊天範例 (step3_group_chat.py)
```python
from semantic_kernel.agents import Agent, ChatCompletionAgent, GroupChatOrchestration, RoundRobinGroupChatManager

def get_agents() -> list[Agent]:
    writer = ChatCompletionAgent(
        name="Writer",
        description="A content writer.",
        instructions="You create new content and edit contents based on feedback.",
        service=AzureChatCompletion(),
    )
    reviewer = ChatCompletionAgent(
        name="Reviewer", 
        description="A content reviewer.",
        instructions="You review content and provide feedback to the writer.",
        service=AzureChatCompletion(),
    )
    return [writer, reviewer]

def agent_response_callback(message: ChatMessageContent) -> None:
    print(f"**{message.name}**\n{message.content}")

async def main():
    agents = get_agents()
    group_chat_orchestration = GroupChatOrchestration(
        members=agents,
        # 設定最大輪次，奇數讓 Writer 獲得最後發言權
        manager=RoundRobinGroupChatManager(max_rounds=5),
        agent_response_callback=agent_response_callback,
    )
    
    runtime = InProcessRuntime()
    runtime.start()
    
    orchestration_result = await group_chat_orchestration.invoke(
        task="Create a slogan for a new electric SUV that is affordable and fun to drive.",
        runtime=runtime,
    )
    
    value = await orchestration_result.get()
    print(f"***** Result *****\n{value}")
```

#### 人機協作範例 (step3a_group_chat_human_in_the_loop.py)
```python
from semantic_kernel.agents.orchestration.group_chat import BooleanResult, RoundRobinGroupChatManager
from semantic_kernel.contents import AuthorRole, ChatHistory, ChatMessageContent
from typing_extensions import override

class CustomRoundRobinGroupChatManager(RoundRobinGroupChatManager):
    """自訂輪轉管理器，啟用用戶輸入"""
    
    @override
    async def should_request_user_response(self, history: ChatHistory) -> BooleanResult:
        """決定是否需要用戶輸入"""
        # 在 Reviewer 回應後請求用戶輸入
        if history and history[-1].name == "Reviewer":
            return BooleanResult(value=True, termination_reason="Requesting user feedback")
        return BooleanResult(value=False)

async def human_response_function(chat_history: ChatHistory) -> ChatMessageContent:
    """取得用戶輸入"""
    user_input = input("User: ")
    return ChatMessageContent(role=AuthorRole.USER, content=user_input)

async def main():
    agents = get_agents()
    group_chat_orchestration = GroupChatOrchestration(
        members=agents,
        manager=CustomRoundRobinGroupChatManager(
            max_rounds=5,
            human_response_function=human_response_function,
        ),
        agent_response_callback=agent_response_callback,
    )
    # ... 其餘執行邏輯
```

#### AI 管理器範例 (step3b_group_chat_with_chat_completion_manager.py)
```python
from semantic_kernel.agents.orchestration.group_chat import GroupChatManager, MessageResult, StringResult
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template import KernelPromptTemplate, PromptTemplateConfig

class ChatCompletionGroupChatManager(GroupChatManager):
    """使用 AI 服務控制群組聊天流程"""
    
    def __init__(self, chat_completion_service: ChatCompletionClientBase):
        self.chat_completion_service = chat_completion_service
        self.kernel = Kernel()
        
    @override
    async def select_next_agent(self, history: ChatHistory) -> MessageResult:
        """AI 決定下一個發言者"""
        # 使用 prompt template 讓 AI 決定
        prompt_config = PromptTemplateConfig(
            template="""
            Based on the conversation history, decide which agent should speak next.
            Available agents: {{agents}}
            
            Conversation history:
            {{history}}
            
            Return only the agent name.
            """,
            execution_settings={"temperature": 0.1}
        )
        
        # AI 分析對話歷史並選擇下一個 Agent
        result = await self.chat_completion_service.get_chat_message_content(...)
        return MessageResult(agent_name=result.content.strip())

def get_agents() -> list[Agent]:
    # 建立代表不同觀點的 Agent
    farmer = ChatCompletionAgent(
        name="Farmer",
        description="A rural farmer from Southeast Asia.",
        instructions="You value tradition and sustainability. Challenge others respectfully.",
        service=AzureChatCompletion(),
    )
    developer = ChatCompletionAgent(
        name="Developer",
        description="An urban software developer from the United States.",
        instructions="You value innovation and work-life balance. Challenge others respectfully.",
        service=AzureChatCompletion(),
    )
    return [farmer, developer, ...]
```

---

## 4. Handoff Orchestration (交接協調)

### 主要情境
動態任務分流系統，Agent 根據任務性質智能交接給專門的處理 Agent。

### 技術特色
- **智能分流**: 根據請求內容動態選擇處理 Agent
- **交接規則**: 定義 Agent 間的交接關係
- **插件支援**: Agent 可配備專門的功能插件
- **結構化輸入**: 支援 Pydantic 模型作為輸入

### 核心程式碼

#### 客服分流範例 (step4_handoff.py)
```python
from semantic_kernel.agents import Agent, ChatCompletionAgent, HandoffOrchestration, OrchestrationHandoffs
from semantic_kernel.functions import kernel_function

class OrderStatusPlugin:
    @kernel_function
    def check_order_status(self, order_id: str) -> str:
        """檢查訂單狀態"""
        return f"Order {order_id} is shipped and will arrive in 2-3 days."

class OrderRefundPlugin:
    @kernel_function
    def process_refund(self, order_id: str, reason: str) -> str:
        """處理退款"""
        print(f"Processing refund for order {order_id} due to: {reason}")
        return f"Refund for order {order_id} has been processed successfully."

class OrderReturnPlugin:
    @kernel_function
    def process_return(self, order_id: str, reason: str) -> str:
        """處理退貨"""
        print(f"Processing return for order {order_id} due to: {reason}")
        return f"Return for order {order_id} has been processed successfully."

def get_agents() -> tuple[list[Agent], OrchestrationHandoffs]:
    # 建立專門 Agent
    support_agent = ChatCompletionAgent(
        name="TriageAgent",
        description="A customer support agent that triages issues.",
        instructions="Handle customer requests.",
        service=AzureChatCompletion(),
    )
    
    refund_agent = ChatCompletionAgent(
        name="RefundAgent",
        description="A customer support agent that handles refunds.",
        instructions="Handle refund requests.",
        service=AzureChatCompletion(),
        plugins=[OrderRefundPlugin()],  # 配備退款插件
    )
    
    order_status_agent = ChatCompletionAgent(
        name="OrderStatusAgent", 
        description="A customer support agent that checks order status.",
        instructions="Handle order status requests.",
        service=AzureChatCompletion(),
        plugins=[OrderStatusPlugin()],  # 配備查詢插件
    )
    
    order_return_agent = ChatCompletionAgent(
        name="OrderReturnAgent",
        description="A customer support agent that handles order returns.",
        instructions="Handle order return requests.",
        service=AzureChatCompletion(),
        plugins=[OrderReturnPlugin()],  # 配備退貨插件
    )
    
    # 定義交接關係
    handoffs = (
        OrchestrationHandoffs()
        .add_many(
            source_agent=support_agent.name,
            target_agents={
                refund_agent.name: "Transfer to this agent if the issue is refund related",
                order_status_agent.name: "Transfer to this agent if the issue is order status related", 
                order_return_agent.name: "Transfer to this agent if the issue is order return related",
            },
        )
        .add(
            source_agent=refund_agent.name,
            target_agent=support_agent.name,
            description="Transfer to this agent if the issue is not refund related",
        )
        # ... 其他交接規則
    )
    
    return [support_agent, refund_agent, order_status_agent, order_return_agent], handoffs

def agent_response_callback(message: ChatMessageContent) -> None:
    print(f"**{message.name}**\n{message.content}")

def human_response_function() -> ChatMessageContent:
    """人機互動"""
    user_input = input("Customer: ")
    return ChatMessageContent(role=AuthorRole.USER, content=user_input)

async def main():
    agents, handoffs = get_agents()
    handoff_orchestration = HandoffOrchestration(
        members=agents,
        handoffs=handoffs,
        agent_response_callback=agent_response_callback,
        human_response_function=human_response_function,
    )
    
    runtime = InProcessRuntime()
    runtime.start()
    
    orchestration_result = await handoff_orchestration.invoke(
        task="I want to check the status of my order #12345",
        runtime=runtime,
    )
    
    value = await orchestration_result.get()
    print(f"***** Result *****\n{value}")
```

#### 結構化輸入範例 (step4a_handoff_structured_inputs.py)
```python
from enum import Enum
from pydantic import BaseModel

class GitHubLabels(Enum):
    PYTHON = "python"
    DOTNET = ".NET" 
    BUG = "bug"
    ENHANCEMENT = "enhancement"
    VECTORSTORE = "vectorstore"
    AGENT = "agent"

class GithubIssue(BaseModel):
    """GitHub 問題模型"""
    id: str
    title: str
    body: str
    labels: list[str] = []

class Plan(BaseModel):
    """解決方案模型"""
    tasks: list[str]

class GithubPlugin:
    @kernel_function
    def add_labels(self, issue_id: str, labels: list[str]) -> str:
        """為 GitHub 問題添加標籤"""
        return f"Added labels {labels} to issue {issue_id}"
    
    @kernel_function  
    def create_plan(self, issue_description: str) -> Plan:
        """為問題建立解決計劃"""
        tasks = [
            "Analyze the issue",
            "Identify root cause", 
            "Implement solution",
            "Test and verify"
        ]
        return Plan(tasks=tasks)

# 自訂輸入轉換函數
def custom_input_transform(input_message: GithubIssue) -> ChatMessageContent:
    """將 Pydantic 模型轉換為聊天訊息"""
    content = f"""
    GitHub Issue #{input_message.id}
    Title: {input_message.title}
    
    Description:
    {input_message.body}
    
    Current Labels: {', '.join(input_message.labels) if input_message.labels else 'None'}
    """
    return ChatMessageContent(role=AuthorRole.USER, content=content)

# 範例 GitHub 問題
GithubIssueSample = GithubIssue(
    id="12345",
    title="Bug: SQLite Error 1: 'ambiguous column name:' when including VectorStoreRecordKey",
    body="When using column names marked as [VectorStoreRecordData(IsFilterable = true)]...",
    labels=[],
)

async def main():
    agents, handoffs = get_agents()
    handoff_orchestration = HandoffOrchestration(
        members=agents,
        handoffs=handoffs,
        input_transform=custom_input_transform,  # 使用自訂輸入轉換
        agent_response_callback=agent_response_callback,
    )
    
    # 使用結構化輸入
    orchestration_result = await handoff_orchestration.invoke(
        task=GithubIssueSample,  # 直接傳入 Pydantic 模型
        runtime=runtime,
    )
```

#### 串流回調範例 (step4b_handoff_streaming_agent_response_callback.py)
```python
from semantic_kernel.contents import StreamingChatMessageContent

is_new_message = True

def streaming_agent_response_callback(message: StreamingChatMessageContent, is_final: bool) -> None:
    """串流顯示 Agent 回應"""
    global is_new_message
    if is_new_message:
        print(f"\n**{message.name}**\n", end="", flush=True)
        is_new_message = False
    
    print(message.content, end="", flush=True)
    
    if is_final:
        print("\n")
        is_new_message = True

async def main():
    handoff_orchestration = HandoffOrchestration(
        members=agents,
        handoffs=handoffs,
        streaming_agent_response_callback=streaming_agent_response_callback,
        human_response_function=human_response_function,
    )
    # ... 其餘執行邏輯
```

---

## 5. Magentic Orchestration (Magentic 協調)

### 主要情境
複雜任務解決系統，結合研究和執行能力，靈感來自 Microsoft Research 的 Magentic One 系統。適用於需要多種專業能力協作完成的複雜任務。

### 技術特色
- **AI 規劃管理**: StandardMagenticManager 使用精調 prompt 控制流程
- **多功能 Agent**: 結合資訊收集和資料分析能力
- **Azure AI Agent**: 使用 Azure AI Agent 服務和自訂插件
- **結構化輸出**: 管理器需要支援結構化輸出的模型

### 核心程式碼 (step5_magentic.py)

```python
import asyncio
import os
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import (
    Agent,
    AzureAIAgent,
    AzureAIAgentSettings,
    MagenticOrchestration,
    StandardMagenticManager,
)
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.functions import kernel_function

# 載入環境變數
load_dotenv()
MY_AZURE_OPENAI_ENDPOINT = os.getenv("MY_AZURE_OPENAI_ENDPOINT")

# 定義研究插件
class ResearchPlugin:
    @kernel_function
    def research_topic(self, topic: str) -> str:
        """研究指定主題的資訊。"""
        return f"已研究主題：{topic}。找到相關的學術資料和最新研究成果。"

# 定義程式分析插件
class CodeAnalysisPlugin:
    @kernel_function
    def analyze_data(self, data_type: str) -> str:
        """分析指定類型的資料。"""
        return f"已分析 {data_type} 資料，生成統計報告和視覺化圖表。"

    @kernel_function
    def calculate_energy_consumption(self, model_name: str, hours: int) -> str:
        """計算模型的能源消耗。"""
        energy_values = {"ResNet-50": 5.76, "BERT-base": 9.18, "GPT-2": 12.96}
        energy = energy_values.get(model_name, 10.0) * (hours / 24)
        return f"{model_name} 在 {hours} 小時內消耗 {energy:.2f} kWh 能源。"

async def get_agents(client) -> list[Agent]:
    """建立參與 Magentic 協調的代理程式清單"""
    
    # 建立研究代理
    research_agent_definition = await client.agents.create_agent(
        model=AzureAIAgentSettings().model_deployment_name,
        name="ResearchAgent",
        description="具有網路搜尋存取權限的有用助手。專門執行研究和資訊收集。",
        instructions="您是研究員。您尋找資訊而不進行額外的計算或量化分析。專注於收集和整理相關的學術和技術資訊。",
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "ResearchPlugin-research_topic",
                    "description": "研究指定主題的資訊。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string", "description": "要研究的主題"}
                        },
                        "required": ["topic"],
                    },
                },
            }
        ],
    )
    research_agent = AzureAIAgent(
        client=client,
        definition=research_agent_definition,
        plugins=[ResearchPlugin()],
    )

    # 建立程式分析代理
    coder_agent_definition = await client.agents.create_agent(
        model=AzureAIAgentSettings().model_deployment_name,
        name="CoderAgent",
        description="撰寫和執行程式碼來處理和分析資料的有用助手。",
        instructions="您使用程式碼解決問題。請提供詳細的分析和計算過程。專精於資料分析、統計計算和能源效率評估。",
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "CodeAnalysisPlugin-analyze_data",
                    "description": "分析指定類型的資料。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "data_type": {"type": "string", "description": "要分析的資料類型"}
                        },
                        "required": ["data_type"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "CodeAnalysisPlugin-calculate_energy_consumption",
                    "description": "計算模型的能源消耗。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "model_name": {"type": "string", "description": "模型名稱"},
                            "hours": {"type": "integer", "description": "運行小時數"},
                        },
                        "required": ["model_name", "hours"],
                    },
                },
            },
        ],
    )
    coder_agent = AzureAIAgent(
        client=client,
        definition=coder_agent_definition,
        plugins=[CodeAnalysisPlugin()],
    )
    
    return [research_agent, coder_agent]

def agent_response_callback(message: ChatMessageContent) -> None:
    """監控 Agent 回應"""
    print(f"**{message.name}**\n{message.content}")

async def main():
    """主要執行函數"""
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. 建立具有兩個 Azure AI 代理程式和 Magentic 管理員的編排
        # StandardMagenticManager 使用經過精心調整的提示
        # 也接受自訂提示供進階使用者使用
        # 標準管理員需要支援結構化輸出的聊天完成模型
        agents_list = await get_agents(client)

        magentic_orchestration = MagenticOrchestration(
            members=agents_list,
            manager=StandardMagenticManager(
                chat_completion_service=AzureChatCompletion(
                    endpoint=MY_AZURE_OPENAI_ENDPOINT,
                )
            ),
            agent_response_callback=agent_response_callback,
        )

        # 2. 建立運行時並啟動
        runtime = InProcessRuntime()
        runtime.start()

        try:
            # 3. 使用任務和運行時呼叫編排
            orchestration_result = await magentic_orchestration.invoke(
                task=(
                    "我正在準備一份關於不同機器學習模型架構能源效率的報告。"
                    "比較在標準資料集上 ResNet-50、BERT-base 和 GPT-2 的預估訓練和推論能源消耗"
                    "（例如，ResNet 使用 ImageNet、BERT 使用 GLUE、GPT-2 使用 WebText）。"
                    "然後，假設在 Azure Standard_NC6s_v3 VM 上訓練 24 小時，估算與每個模型相關的 CO2 排放量。"
                    "為了清晰起見，請提供表格，並建議每種任務類型（影像分類、文字分類和文字生成）"
                    "最節能的模型。"
                ),
                runtime=runtime,
            )

            # 4. 等待結果
            value = await orchestration_result.get()
            print(f"\n最終結果：\n{value}")

        finally:
            # 5. 閒置時停止運行時
            await runtime.stop_when_idle()

            # 6. 清理：刪除代理程式
            for agent in agents_list:
                await client.agents.delete_agent(agent.id)

if __name__ == "__main__":
    asyncio.run(main())
```

### Magentic 系統特色

1. **智能規劃**: StandardMagenticManager 使用預先調校的 prompt 來決定任務分配和執行順序
2. **混合能力**: 結合資訊搜尋（Research Agent）和程式執行（Coder Agent）
3. **自適應流程**: 根據任務複雜度動態調整 Agent 協作方式
4. **可擴展架構**: 支援自訂管理器邏輯和 Agent 組合

### 插件系統

Magentic 協調模式的一個重要特色是使用插件系統來擴展 Agent 的能力：

#### 研究插件 (ResearchPlugin)
```python
class ResearchPlugin:
    @kernel_function
    def research_topic(self, topic: str) -> str:
        """研究指定主題的資訊"""
        # 實際應用中可整合真正的搜尋 API
        return f"已研究主題：{topic}。找到相關的學術資料和最新研究成果。"
```

#### 程式分析插件 (CodeAnalysisPlugin)
```python
class CodeAnalysisPlugin:
    @kernel_function
    def analyze_data(self, data_type: str) -> str:
        """分析指定類型的資料"""
        return f"已分析 {data_type} 資料，生成統計報告和視覺化圖表。"

    @kernel_function
    def calculate_energy_consumption(self, model_name: str, hours: int) -> str:
        """計算模型的能源消耗"""
        energy_values = {"ResNet-50": 5.76, "BERT-base": 9.18, "GPT-2": 12.96}
        energy = energy_values.get(model_name, 10.0) * (hours / 24)
        return f"{model_name} 在 {hours} 小時內消耗 {energy:.2f} kWh 能源。"
```

### 與其他協調模式的比較

| 特性           | Magentic     | Sequential | GroupChat | Handoff  |
| -------------- | ------------ | ---------- | --------- | -------- |
| **執行方式**   | AI 智能規劃  | 固定順序   | 輪轉討論  | 條件分流 |
| **Agent 互動** | 動態協作     | 單向傳遞   | 雙向討論  | 智能交接 |
| **適用場景**   | 複雜任務解決 | 流程處理   | 創意協作  | 服務分流 |
| **管理複雜度** | 高           | 低         | 中        | 中高     |
| **靈活性**     | 極高         | 低         | 中        | 高       |

### 最佳實踐建議

1. **插件設計**: 將複雜功能封裝在插件中，保持 Agent 指令簡潔
2. **任務分解**: 清楚描述複雜任務，讓 AI 管理器能夠正確分配工作
3. **環境管理**: 確保正確設定 Azure 認證和環境變數
4. **錯誤處理**: 實作完整的資源清理機制
5. **監控回調**: 使用回調函數監控執行過程，便於除錯

Magentic 協調模式特別適合需要多種專業能力協作的複雜任務，是 Semantic Kernel 中最先進的協調方式。

---

## 結論

Semantic Kernel 的多 Agent 協調框架提供了完整的工具集，支援從簡單並行處理到複雜智能分流的各種場景。選擇適當的協調模式能夠顯著提升 AI 應用的效率和準確性。

每種模式都有其特定的應用場景和技術特色，開發者可以根據實際需求選擇最適合的協調方式，或者組合多種模式來構建更複雜的 AI 系統。

## 代理情境分析 (Agent Scenarios Analysis)

### 各範例文件中的代理角色與功能

每個 Python 範例文件都展示了不同的代理角色設計和應用情境，以下詳細說明各代理的功能定位：

#### Concurrent 並行範例中的代理

**step1_concurrent.py**
- **PhysicsExpert (物理專家)**: 從物理學角度分析問題，專注於動能、熱力學等物理概念
- **ChemistryExpert (化學專家)**: 從化學角度分析問題，專注於分子運動、化學反應等化學概念

**step1a_concurrent_structured_outputs.py**  
- **ThemeAgent (主題分析代理)**: 專門識別文章中的主要主題和議題
- **SentimentAgent (情感分析代理)**: 專門分析文本的情感傾向和語調
- **EntityAgent (實體識別代理)**: 專門提取文本中的命名實體和關鍵詞

#### Sequential 順序範例中的代理

**step2_sequential.py / step2a_sequential_cancellation_token.py / step2b_sequential_streaming_agent_response_callback.py**
- **ConceptExtractorAgent (概念萃取代理)**: 行銷分析師角色，從產品描述中提取關鍵特色、目標受眾、獨特賣點
- **WriterAgent (文案撰寫代理)**: 行銷文案撰寫師角色，將萃取的概念轉換為吸引人的行銷文案
- **FormatProofAgent (格式校對代理)**: 編輯角色，負責語法修正、語調一致性、內容潤飾

#### GroupChat 群組聊天範例中的代理

**step3_group_chat.py / step3a_group_chat_human_in_the_loop.py**
- **Writer (作家代理)**: 內容創作者角色，負責創建新內容並根據反饋進行修改
- **Reviewer (評論代理)**: 內容審查者角色，負責評估內容品質並提供建設性反饋

**step3b_group_chat_with_chat_completion_manager.py**
- **Farmer (農民代理)**: 東南亞農村農民角色，代表傳統價值觀和永續發展觀點
- **Developer (開發者代理)**: 美國城市軟體開發者角色，代表創新科技和工作生活平衡觀點
- **Teacher (教師代理)**: 東歐退休歷史教師角色，帶來歷史哲學觀點和文化傳承視角
- **Activist (活動家代理)**: 南美年輕活動家角色，專注社會正義、環境權利和世代變革

#### Handoff 交接範例中的代理

**step4_handoff.py / step4b_handoff_streaming_agent_response_callback.py**
- **TriageAgent (分流代理)**: 客戶支援一線接待，負責問題分類和初步處理
- **RefundAgent (退款代理)**: 退款專員角色，配備 OrderRefundPlugin 處理退款流程
- **OrderStatusAgent (訂單狀態代理)**: 訂單查詢專員，配備 OrderStatusPlugin 查詢訂單狀態
- **OrderReturnAgent (退貨代理)**: 退貨專員角色，配備 OrderReturnPlugin 處理退貨流程

**step4a_handoff_structured_inputs.py**
- **PythonAgent (Python 代理)**: 專門處理 Python 相關的 GitHub 問題
- **DotNetAgent (.NET 代理)**: 專門處理 .NET 相關的 GitHub 問題  
- **VectorStoreAgent (向量儲存代理)**: 專門處理向量儲存相關的技術問題

#### Magentic 複雜任務範例中的代理

**step5_magentic.py**
- **ResearchAgent (研究代理)**: 研究員角色，具備網路搜尋能力，專門收集和分析資訊
- **CoderAgent (程式代理)**: 程式設計師角色，使用 OpenAI Assistant 和 Code Interpreter，能執行程式碼進行資料處理和分析

### 代理設計模式分析

#### 1. 專業分工模式
每個代理都有明確的專業領域和職責範圍，避免功能重疊：
- **領域專家**: PhysicsExpert、ChemistryExpert
- **功能專家**: ThemeAgent、SentimentAgent、EntityAgent
- **流程專家**: ConceptExtractorAgent、WriterAgent、FormatProofAgent

#### 2. 角色扮演模式
代理被設計成具有特定身份背景和價值觀的角色：
- **職業角色**: Writer、Reviewer、Farmer、Developer、Teacher
- **地域文化**: 東南亞農民、美國開發者、東歐教師、南美活動家
- **世代觀點**: 年輕活動家 vs 退休教師

#### 3. 工作流程模式
代理按照真實世界的工作流程進行設計：
- **客服流程**: TriageAgent → 專門代理 (RefundAgent/OrderStatusAgent/OrderReturnAgent)
- **內容創作流程**: ConceptExtractorAgent → WriterAgent → FormatProofAgent
- **研究分析流程**: ResearchAgent → CoderAgent

#### 4. 能力增強模式
透過 Plugin 系統為代理增加特定功能：
- **OrderRefundPlugin**: 為 RefundAgent 提供退款處理能力
- **OrderStatusPlugin**: 為 OrderStatusAgent 提供訂單查詢能力
- **Code Interpreter**: 為 CoderAgent 提供程式執行能力

### 代理協作策略

#### 並行協作 (Concurrent)
- 適用於需要多元觀點的分析任務
- 代理間無依賴關係，可同時執行
- 結果需要整合和比較

#### 順序協作 (Sequential)  
- 適用於有明確步驟順序的任務
- 上游代理的輸出是下游代理的輸入
- 強調流程的完整性和連貫性

#### 討論協作 (GroupChat)
- 適用於需要反覆討論和改進的任務
- 代理間可以相互回應和辯論
- 強調觀點交流和共識建立

#### 分流協作 (Handoff)
- 適用於複雜的服務分流場景
- 根據問題類型動態選擇合適的專門代理
- 強調專業化處理和效率

#### 智能協作 (Magentic)
- 適用於需要多種能力組合的複雜任務
- AI 管理器智能調度不同功能的代理
- 強調任務分解和能力互補
