# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

from semantic_kernel.agents import Agent, ChatCompletionAgent, SequentialOrchestration
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

"""
以下範例示範如何取消仍在執行中的編排呼叫。

此範例展示建立和啟動運行時、建立順序編排、呼叫編排，
以及在完成前取消它的基本步驟。
"""

# 設定日誌記錄以查看呼叫過程
logging.basicConfig(level=logging.WARNING)  # 將預設等級設定為 WARNING
logging.getLogger("semantic_kernel.agents.orchestration.sequential").setLevel(
    logging.DEBUG
)


def get_agents() -> list[Agent]:
    """回傳將參與順序編排的代理程式清單。

    您可以自由新增或移除代理程式。
    """
    concept_extractor_agent = ChatCompletionAgent(
        name="ConceptExtractorAgent",
        instructions=(
            "您是行銷分析師。給定產品描述，請識別：\n"
            "- 主要功能\n"
            "- 目標受眾\n"
            "- 獨特賣點\n\n"
        ),
        service=AzureChatCompletion(),
    )
    writer_agent = ChatCompletionAgent(
        name="WriterAgent",
        instructions=(
            "您是行銷文案撰寫者。給定描述功能、受眾和獨特賣點的文字區塊，"
            "撰寫引人注目的行銷文案（如電子報段落），突出這些要點。"
            "輸出應該簡短（約150字），僅輸出文案作為單一文字區塊。"
        ),
        service=AzureChatCompletion(),
    )
    format_proof_agent = ChatCompletionAgent(
        name="FormatProofAgent",
        instructions=(
            "您是編輯。給定草稿文案，請更正語法、改善清晰度、確保一致的語調，"
            "進行格式化並使其精練。將最終改善的文案輸出為單一文字區塊。"
        ),
        service=AzureChatCompletion(),
    )

    # 清單中代理程式的順序將是它們執行的順序
    return [concept_extractor_agent, writer_agent, format_proof_agent]


async def main():
    """執行代理程式的主要函數。"""
    # 1. 建立具有多個代理程式的順序編排
    agents = get_agents()
    sequential_orchestration = SequentialOrchestration(members=agents)

    # 2. 建立運行時並啟動
    runtime = InProcessRuntime()
    runtime.start()

    # 3. 使用任務和運行時呼叫編排
    orchestration_result = await sequential_orchestration.invoke(
        task="一個環保的不鏽鋼水瓶，可讓飲料保持24小時的冰冷",
        runtime=runtime,
    )

    # 4. 在編排完成前取消它
    await asyncio.sleep(1)  # 模擬取消前的一些延遲
    orchestration_result.cancel()

    try:
        # 嘗試獲取結果將因取消而導致異常
        _ = await orchestration_result.get(timeout=20)
    except Exception as e:
        print(e)
    finally:
        # 5. 停止運行時
        await runtime.stop_when_idle()

    """
    Sample output:
    DEBUG:semantic_kernel.agents.orchestration.sequential:Registered agent actor of type 
        FormatProofAgent_5efa69d39306414c91325ef82145ec19
    DEBUG:semantic_kernel.agents.orchestration.sequential:Registered agent actor of type
        WriterAgent_5efa69d39306414c91325ef82145ec19
    DEBUG:semantic_kernel.agents.orchestration.sequential:Registered agent actor of type
        ConceptExtractorAgent_5efa69d39306414c91325ef82145ec19
    DEBUG:semantic_kernel.agents.orchestration.sequential:Sequential actor 
        (Actor ID: ConceptExtractorAgent_5efa69d39306414c91325ef82145ec19/default; Agent name: ConceptExtractorAgent)
        started processing...
    The invocation was canceled before it could complete.
    DEBUG:semantic_kernel.agents.orchestration.sequential:Sequential actor
        (Actor ID: ConceptExtractorAgent_5efa69d39306414c91325ef82145ec19/default; Agent name: ConceptExtractorAgent)
        finished processing.
    """


if __name__ == "__main__":
    asyncio.run(main())
