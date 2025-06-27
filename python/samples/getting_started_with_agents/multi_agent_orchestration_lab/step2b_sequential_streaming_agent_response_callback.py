# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import Agent, ChatCompletionAgent, SequentialOrchestration
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import StreamingChatMessageContent

"""
以下範例示範如何建立順序編排，讓多個代理程式依序執行，
即一個代理程式的輸出是下一個代理程式的輸入。

此範例展示建立和啟動運行時、建立順序編排、呼叫編排，
以及最終等待結果的基本步驟。
"""


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


# 標記是否正在接收新訊息
is_new_message = True


def streaming_agent_response_callback(
    message: StreamingChatMessageContent, is_final: bool
) -> None:
    """觀察者函數，用於列印代理程式的訊息。

    Args:
        message (StreamingChatMessageContent): 來自代理程式的串流訊息內容。
        is_final (bool): 指示這是否為訊息的最後部分。
    """
    global is_new_message
    if is_new_message:
        print(f"# {message.name}")
        is_new_message = False
    print(message.content, end="", flush=True)
    if is_final:
        print()
        is_new_message = True


async def main():
    """Main function to run the agents."""
    # 1. Create a sequential orchestration with multiple agents and an agent
    #    回應回調來觀察每個代理程式在串流回應時的輸出。
    agents = get_agents()
    sequential_orchestration = SequentialOrchestration(
        members=agents,
        streaming_agent_response_callback=streaming_agent_response_callback,
    )

    # 2. 建立運行時並啟動
    runtime = InProcessRuntime()
    runtime.start()

    # 3. 使用任務和運行時呼叫編排
    orchestration_result = await sequential_orchestration.invoke(
        task="一個環保的不鏽鋼水瓶，可讓飲料保持24小時的冰冷",
        runtime=runtime,
    )

    # 4. 等待結果
    value = await orchestration_result.get(timeout=20)
    print(f"***** 最終結果 *****\n{value}")

    # 5. 閒置時停止運行時
    await runtime.stop_when_idle()

    """
    範例輸出：
    # ConceptExtractorAgent
    **主要功能：**
    - 採用環保不鏽鋼材質製造
    - 隔熱技術，可讓飲料保持冰冷長達24小時
    - 可重複使用的設計，促進永續發展
    - 可能有不同尺寸和顏色的變化

    **目標受眾：**
    - 具環保意識的消費者
    - 積極活躍的個人和戶外愛好者
    - 關注健康、追求保持水分的個人
    - 尋求時尚和功能性飲具的學生和專業人士

    **獨特賣點：**
    - 將環保特性與高性能保溫相結合
    - 耐用且可重複使用，減少對一次性塑膠的依賴
    - 時尚設計，在保持功能性的同時迎合現代美學
    - 透過負責任的製造實踐支持永續發展倡議
    # WriterAgent
    使用我們環保的不鏽鋼水瓶永續暢飲，專為重視性能和美學的有意識消費者設計。我們的水瓶採用先進的隔熱技術，
    可讓您的飲料保持冰冷長達24小時，非常適合戶外冒險、健身房訓練或忙碌的辦公室一天。從各種尺寸和令人驚豔的
    顏色中選擇，以符合您的個人風格，同時對地球產生正面影響。每個可重複使用的瓶子都有助於減少一次性塑膠，
    支持更清潔、更綠色的世界。加入永續發展運動，無需在風格或功能性上妥協。保持水分、外觀出色並產生影響
    —今天就取得您的環保水瓶！
    # FormatProofAgent
    使用我們環保的不鏽鋼水瓶永續暢飲，專為重視性能和美學的有意識消費者設計。我們的水瓶利用先進的隔熱技術
    讓您的飲料保持冰冷長達24小時，非常適合戶外冒險、健身房訓練或忙碌的辦公室一天。

    從各種尺寸和令人驚豔的顏色中選擇，以符合您的個人風格，同時對地球產生正面影響。每個可重複使用的瓶子
    都有助於減少一次性塑膠，支持更清潔、更綠色的世界。

    加入永續發展運動，無需在風格或功能性上妥協。保持水分、外觀出色並產生影響—今天就取得您的環保水瓶！
    ***** 最終結果 *****
    使用我們環保的不鏽鋼水瓶永續暢飲，專為重視性能和美學的有意識消費者設計。我們的水瓶利用先進的隔熱技術
    讓您的飲料保持冰冷長達24小時，非常適合戶外冒險、健身房訓練或忙碌的辦公室一天。

    從各種尺寸和令人驚豔的顏色中選擇，以符合您的個人風格，同時對地球產生正面影響。每個可重複使用的瓶子
    都有助於減少一次性塑膠，支持更清潔、更綠色的世界。

    加入永續發展運動，無需在風格或功能性上妥協。保持水分、外觀出色並產生影響—今天就取得您的環保水瓶！
    """


if __name__ == "__main__":
    asyncio.run(main())
