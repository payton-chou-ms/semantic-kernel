# Copyright (c) Microsoft. All rights reserved.

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
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

"""
以下範例示範如何建立具有兩個代理程式的 Magentic 編排：
- 可執行網路搜尋的研究代理程式
- 可進行程式碼分析和資料處理的編碼代理程式

在此處閱讀更多關於 Magentic 的資訊：
https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/

此範例示範建立和啟動運行時、建立具有兩個 Azure AI 代理程式和 Magentic 管理員的 Magentic 編排、
呼叫編排，以及最後等待結果的基本步驟。

Magentic 管理員需要支援結構化輸出的聊天完成模型。
"""
# Load environment variables from .env file
load_dotenv()
MY_AZURE_OPENAI_ENDPOINT = os.getenv("MY_AZURE_OPENAI_ENDPOINT")


class ResearchPlugin:
    @kernel_function
    def research_topic(self, topic: str) -> str:
        """研究指定主題的資訊。"""
        # 模擬研究功能
        return f"已研究主題：{topic}。找到相關的學術資料和最新研究成果。"


class CodeAnalysisPlugin:
    @kernel_function
    def analyze_data(self, data_type: str) -> str:
        """分析指定類型的資料。"""
        # 模擬資料分析功能
        return f"已分析 {data_type} 資料，生成統計報告和視覺化圖表。"

    @kernel_function
    def calculate_energy_consumption(self, model_name: str, hours: int) -> str:
        """計算模型的能源消耗。"""
        # 模擬能源消耗計算
        energy_values = {"ResNet-50": 5.76, "BERT-base": 9.18, "GPT-2": 12.96}
        energy = energy_values.get(model_name, 10.0) * (hours / 24)
        return f"{model_name} 在 {hours} 小時內消耗 {energy:.2f} kWh 能源。"


async def get_agents(client) -> list[Agent]:
    """回傳將參與 Magentic 編排的代理程式清單。

    您可以自由新增或移除代理程式。
    """
    # Create research agent in Azure AI Agent service
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

    # Create coder agent in Azure AI Agent service
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
                            "data_type": {
                                "type": "string",
                                "description": "要分析的資料類型",
                            }
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
    """觀察函數，用於列印來自代理程式的訊息。"""
    print(f"**{message.name}**\n{message.content}")


async def main():
    """執行代理程式的主要函數。"""
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. 建立具有兩個 Azure AI 代理程式和 Magentic 管理員的 Magentic 編排
        # 注意，標準 Magentic 管理員使用經過精心調整的提示，
        # 但對於進階使用者和情境，它接受自訂提示。
        # 對於更進階的情境，您可以子類化 MagenticManagerBase
        # 並實作您自己的管理員邏輯。
        # 標準管理員也需要支援結構化輸出的聊天完成模型。
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

            # 6. Cleanup: delete the agents
            for agent in agents_list:
                await client.agents.delete_agent(agent.id)

    """
    範例輸出：
    **ResearchAgent**
    已研究主題：機器學習模型能源效率。找到相關的學術資料和最新研究成果。

    **CoderAgent**
    ResNet-50 在 24 小時內消耗 5.76 kWh 能源。
    已分析 ResNet-50 資料，生成統計報告和視覺化圖表。

    **CoderAgent**
    BERT-base 在 24 小時內消耗 9.18 kWh 能源。
    已分析 BERT-base 資料，生成統計報告和視覺化圖表。

    **CoderAgent**
    GPT-2 在 24 小時內消耗 12.96 kWh 能源。
    已分析 GPT-2 資料，生成統計報告和視覺化圖表。

    這是每個模型（ResNet-50、BERT-base 和 GPT-2）在 24 小時期間的能源消耗和 CO₂ 排放量比較：

    | 模型      | 能源 (kWh) | CO₂ 排放西歐 (kg) | CO₂ 排放瑞典中部 (kg) |
    |-----------|------------|-------------------|----------------------|
    | ResNet-50 | 5.76       | 0.639             | 0.086                |
    | BERT-base | 9.18       | 1.019             | 0.138                |
    | GPT-2     | 12.96      | 1.439             | 0.194                |

    ### 能源效率建議：

    1. **影像分類（ResNet-50）**：最節能選擇，適合影像處理任務
    2. **文字分類（BERT-base）**：中等能源消耗，平衡效能與效率
    3. **文字生成（GPT-2）**：能源消耗最高，但提供強大的生成能力

    最終結果：
    基於研究和分析，ResNet-50 是最節能的模型，特別適合影像分類任務。
    對於文字處理，BERT-base 提供了較好的能源效率平衡。
    """


if __name__ == "__main__":
    asyncio.run(main())
