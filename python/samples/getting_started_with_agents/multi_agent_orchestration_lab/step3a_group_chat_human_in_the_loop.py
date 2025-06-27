# Copyright (c) Microsoft. All rights reserved.

import asyncio
import sys

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import (
    Agent,
    AzureAIAgent,
    AzureAIAgentSettings,
    GroupChatOrchestration,
    RoundRobinGroupChatManager,
)
from semantic_kernel.agents.orchestration.group_chat import (
    BooleanResult,
)
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.contents import AuthorRole, ChatHistory, ChatMessageContent

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

"""
以下範例示範如何建立具有人類參與迴圈的群組聊天編排。
人類參與迴圈是透過覆寫預設的輪詢管理員來實現，
允許在審查員代理程式的訊息後進行使用者輸入。

將群組聊天管理員視為狀態機，具有以下可能的狀態：
- 請求使用者訊息
- 終止，在此之後管理員將嘗試從對話中篩選結果
- 繼續，在此管理員將選擇下一個要發言的代理程式

此範例示範自訂群組聊天管理員以進入使用者輸入狀態、
建立人類回應函數來取得使用者輸入，並將其提供給群組聊天管理員的基本步驟。

此編排中有兩個代理程式：撰寫者和審查員。
他們反覆合作為新的電動SUV改善口號。
"""


async def get_agents(client) -> list[Agent]:
    """回傳將參與群組風格討論的代理程式清單。

    您可以自由新增或移除代理程式。
    """
    # Create writer agent in Azure AI Agent service
    writer_agent_definition = await client.agents.create_agent(
        model=AzureAIAgentSettings().model_deployment_name,
        name="Writer",
        instructions="您是一位優秀的內容作家。您會根據回饋建立新內容並編輯內容。",
        description="內容作家。",
    )
    writer = AzureAIAgent(
        client=client,
        definition=writer_agent_definition,
    )

    # Create reviewer agent in Azure AI Agent service
    reviewer_agent_definition = await client.agents.create_agent(
        model=AzureAIAgentSettings().model_deployment_name,
        name="Reviewer",
        instructions="您是一位優秀的內容審查者。您會審查內容並向作家提供回饋。",
        description="內容審查者。",
    )
    reviewer = AzureAIAgent(
        client=client,
        definition=reviewer_agent_definition,
    )

    # 清單中代理程式的順序將是輪詢管理器選擇它們的順序
    return [writer, reviewer]


class CustomRoundRobinGroupChatManager(RoundRobinGroupChatManager):
    """自訂輪詢群組聊天管理員以啟用使用者輸入。"""

    @override
    async def should_request_user_input(
        self, chat_history: ChatHistory
    ) -> BooleanResult:
        """覆寫預設行為，在審查員訊息後請求使用者輸入。

        管理員將在每個代理程式訊息後檢查是否需要人類輸入。
        """
        if len(chat_history.messages) == 0:
            return BooleanResult(
                result=False,
                reason="尚無代理程式發言。",
            )
        last_message = chat_history.messages[-1]
        if last_message.name == "Reviewer":
            return BooleanResult(
                result=True,
                reason="在審查員訊息後需要使用者輸入。",
            )

        return BooleanResult(
            result=False,
            reason="如果最後一個訊息不是來自審查員，則不需要使用者輸入。",
        )


def agent_response_callback(message: ChatMessageContent) -> None:
    """觀察函數，用於列印來自代理程式的訊息。"""
    print(f"**{message.name}**\n{message.content}")


async def human_response_function(chat_history: ChatHistory) -> ChatMessageContent:
    """取得使用者輸入的函數。"""
    user_input = await asyncio.to_thread(input, "使用者：")
    return ChatMessageContent(role=AuthorRole.USER, content=user_input)


async def main():
    """執行代理程式的主要函數。"""
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Create Azure AI agents using the Azure AI Agent service
        agents = await get_agents(client)

        # 2. 建立具有輪詢管理員的群組聊天編排
        group_chat_orchestration = GroupChatOrchestration(
            members=agents,
            # max_rounds 是奇數，這樣撰寫者可以獲得最後一輪
            manager=CustomRoundRobinGroupChatManager(
                max_rounds=5,
                human_response_function=human_response_function,
            ),
            agent_response_callback=agent_response_callback,
        )

        # 3. 建立運行時並啟動
        runtime = InProcessRuntime()
        runtime.start()

        try:
            # 4. 使用任務和運行時呼叫編排
            orchestration_result = await group_chat_orchestration.invoke(
                task="為新的電動SUV建立一個口號，要求經濟實惠且駕駛樂趣。",
                runtime=runtime,
            )

            # 5. 等待結果
            value = await orchestration_result.get()
            print(f"***** 結果 *****\n{value}")

        finally:
            # 6. 呼叫完成後停止運行時
            await runtime.stop_when_idle()

            # 7. Cleanup: delete the agents
            for agent in agents:
                await client.agents.delete_agent(agent.id)

    """
    **Writer**
    "點亮您的旅程：實惠的冒險等待著您！"
    **Reviewer**
    您的口號捕捉了經濟實惠又有趣的本質，這很棒！不過，您可能想要...
    使用者：我希望它也能押韻
    **Writer**
    當然！以下是您的電動SUV的幾個押韻口號選項：

    1. "街道飛馳，感受節拍！"
    2. "充電駕駛，感受活力！"
    3. "點亮您的駕駛，讓樂趣成為您的嚮導！"
    4. "時尚飛馳，微笑駕駛！"

    如果您想要更多選項或變化，請告訴我！
    **Reviewer**
    這些押韻口號富有創意且充滿活力！它們有效地捕捉了樂趣面向，同時推廣...
    使用者：請繼續審查員的建議
    **Writer**
    絕對沒問題！讓我們基於審查員的建議來改善和擴展，創造更精緻和吸引人的押韻集合...
    ***** 結果 *****
    絕對沒問題！讓我們基於審查員的建議來改善和擴展，創造更精緻和吸引人的押韻集合...
    """


if __name__ == "__main__":
    asyncio.run(main())
