# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import (
    Agent,
    ChatCompletionAgent,
    MagenticOrchestration,
    OpenAIAssistantAgent,
    StandardMagenticManager,
)
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAISettings
from semantic_kernel.contents import ChatMessageContent

"""
以下範例示範如何建立具有兩個代理程式的 Magentic 編排：
- 可執行網路搜尋的研究代理程式
- 可使用程式碼解釋器執行程式碼的編碼代理程式

在此處閱讀更多關於 Magentic 的資訊：
https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/

此範例示範建立和啟動運行時、建立具有兩個代理程式和 Magentic 管理員的 Magentic 編排、
呼叫編排，以及最後等待結果的基本步驟。

Magentic 管理員需要支援結構化輸出的聊天完成模型。
"""


async def agents() -> list[Agent]:
    """回傳將參與 Magentic 編排的代理程式清單。

    您可以自由新增或移除代理程式。
    """
    research_agent = ChatCompletionAgent(
        name="ResearchAgent",
        description="具有網路搜尋存取權限的有用助手。請求它執行網路搜尋。",
        instructions=("您是研究員。您尋找資訊而不進行額外的計算或量化分析。"),
        # 此代理程式需要 gpt-4o-search-preview 模型來執行網路搜尋。
        # 歡迎探索其他支援網路搜尋的代理程式，例如，
        # 具有 bing 基礎的 `OpenAIResponseAgent` 或 `AzureAIAgent`。
        service=OpenAIChatCompletion(ai_model_id="gpt-4o-search-preview"),
    )

    # 建立具有程式碼解釋器功能的 OpenAI Assistant 代理程式
    client = OpenAIAssistantAgent.create_client()
    code_interpreter_tool, code_interpreter_tool_resources = (
        OpenAIAssistantAgent.configure_code_interpreter_tool()
    )
    definition = await client.beta.assistants.create(
        model=OpenAISettings().chat_model_id,
        name="CoderAgent",
        description="撰寫和執行程式碼來處理和分析資料的有用助手。",
        instructions="您使用程式碼解決問題。請提供詳細的分析和計算過程。",
        tools=code_interpreter_tool,
        tool_resources=code_interpreter_tool_resources,
    )
    coder_agent = OpenAIAssistantAgent(
        client=client,
        definition=definition,
    )

    return [research_agent, coder_agent]


def agent_response_callback(message: ChatMessageContent) -> None:
    """觀察函數，用於列印來自代理程式的訊息。"""
    print(f"**{message.name}**\n{message.content}")


async def main():
    """執行代理程式的主要函數。"""
    # 1. 建立具有兩個代理程式和 Magentic 管理員的 Magentic 編排
    # 注意，標準 Magentic 管理員使用經過精心調整的提示，
    # 但對於進階使用者和情境，它接受自訂提示。
    # 對於更進階的情境，您可以子類化 MagenticManagerBase
    # 並實作您自己的管理員邏輯。
    # 標準管理員也需要支援結構化輸出的聊天完成模型。
    magentic_orchestration = MagenticOrchestration(
        members=await agents(),
        manager=StandardMagenticManager(chat_completion_service=OpenAIChatCompletion()),
        agent_response_callback=agent_response_callback,
    )

    # 2. 建立運行時並啟動
    runtime = InProcessRuntime()
    runtime.start()

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

    # 5. 閒置時停止運行時
    await runtime.stop_when_idle()

    """
    範例輸出：
    **ResearchAgent**
    估算 ResNet-50、BERT-base 的訓練和推論能源消耗以及相關的 CO₂ 排放量...

    **CoderAgent**
    這是每個模型（ResNet-50、BERT-base 和 GPT-2）在 24 小時期間的能源消耗和 CO₂ 排放量比較：

    | 模型     | 訓練能源 (kWh) | 推論能源 (kWh) | 總能源 (kWh) | CO₂ 排放 (kg) |
    |----------|---------------|---------------|-------------|---------------|
    | ResNet-50| 21.11         | 0.08232       | 21.19232    | 19.50         |
    | BERT-base| 0.048         | 0.23736       | 0.28536     | 0.26          |
    | GPT-2    | 42.22         | 0.35604       | 42.57604    | 39.17         |

    ### 建議：
    ...

    **CoderAgent**
    這是根據 Azure 西歐和瑞典中部地區碳強度資料，對 ResNet-50、BERT-base 和 GPT-2 的
    能源消耗和 CO₂ 排放量的精細比較表：

    | 模型      | 能源 (kWh) | CO₂ 排放西歐 (kg) | CO₂ 排放瑞典中部 (kg) |
    |-----------|------------|-------------------|----------------------|
    | ResNet-50 | 5.76       | 0.639             | 0.086                |
    | BERT-base | 9.18       | 1.019             | 0.138                |
    | GPT-2     | 12.96      | 1.439             | 0.194                |

    **精細建議：**

    ...

    最終結果：
    這是在 Azure Standard_NC6s_v3 VM 上訓練和推論 24 小時的 ResNet-50、BERT-base 和 GPT-2 模型
    能源效率和 CO₂ 排放量的綜合報告。

    ### 能源消耗和 CO₂ 排放：

    基於精細分析，這是每個模型的預估能源消耗和 CO₂ 排放量：

    | 模型      | 能源 (kWh) | CO₂ 排放西歐 (kg) | CO₂ 排放瑞典中部 (kg) |
    |-----------|------------|-------------------|----------------------|
    | ResNet-50 | 5.76       | 0.639             | 0.086                |
    | BERT-base | 9.18       | 1.019             | 0.138                |
    | GPT-2     | 12.96      | 1.439             | 0.194                |

    ### 能源效率建議：

    ...
    """


if __name__ == "__main__":
    asyncio.run(main())
