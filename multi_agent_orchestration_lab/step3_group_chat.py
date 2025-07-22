# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import (
    Agent,
    AzureAIAgent,
    AzureAIAgentSettings,
    GroupChatOrchestration,
    RoundRobinGroupChatManager,
)
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.contents import ChatMessageContent

"""
以下範例示範如何建立具有預設輪詢管理器的群組聊天編排，
使用 Azure AI Agent 服務，以輪詢方式控制對話流程。

將群組聊天管理器視為狀態機，具有以下可能狀態：
- 請求使用者訊息
- 終止，之後管理器將嘗試從對話中過濾結果
- 繼續，此時管理器將選擇下一個發言的代理程式

此範例展示建立和啟動運行時、使用 Azure AI Agent 服務建立代理程式、
建立具有群組聊天管理器的群組聊天編排、呼叫編排，以及最終等待結果的基本步驟。

此編排中有兩個代理程式：一個作家和一個審查者。
它們反覆合作為新電動SUV優化口號。
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


def agent_response_callback(message: ChatMessageContent) -> None:
    """觀察者函數，用於列印代理程式的訊息。"""
    print(f"**{message.name}**\n{message.content}")


async def main():
    """執行代理程式的主要函數。"""
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Create Azure AI agents using the Azure AI Agent service
        agents = await get_agents(client)

        # 2. 建立具有輪詢管理器的群組聊天編排
        group_chat_orchestration = GroupChatOrchestration(
            members=agents,
            # max_rounds 是奇數，所以作家獲得最後一輪
            manager=RoundRobinGroupChatManager(max_rounds=5),
            agent_response_callback=agent_response_callback,
        )

        # 3. 建立運行時並啟動
        runtime = InProcessRuntime()
        runtime.start()

        try:
            # 4. 使用任務和運行時呼叫編排
            orchestration_result = await group_chat_orchestration.invoke(
                task="為既平價又好玩的新電動SUV創造一個口號。",
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
    範例輸出：
    **Writer**
    "駕馭明日：平價冒險今日啟程！"
    **Reviewer**
    這個口號"駕馭明日：平價冒險今日啟程！"有效地傳達了正在推廣的新電動SUV的核心屬性：
    平價性、樂趣和前瞻性思維。以下是一些回饋：

    ...

    總的來說，這個口號捕捉了創新、愉快和易於接觸的車輛本質。做得很好！
    **Writer**
    "擁抱未來：您的平價電動冒險等著您！"
    **Reviewer**
    這個修改版口號"擁抱未來：您的平價電動冒險等著您！"進一步增強了電動SUV的訊息。
    以下是評估：

    ...

    總的來說，這個版本的口號有效地傳達了車輛的優點，同時保持積極和吸引人的語調。
    繼續保持好工作！
    **Writer**
    "感受電力：冒險與平價在您的新電動SUV中相遇！"
    ***** 結果 *****
    "感受電力：冒險與平價在您的新電動SUV中相遇！"
    """


if __name__ == "__main__":
    asyncio.run(main())
