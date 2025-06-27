# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import (
    AzureAIAgent,
    AzureAIAgentSettings,
    AzureAIAgentThread,
)

"""
以下範例示範如何建立一個能回答使用者問題的 Azure AI 代理程式。
此範例示範建立代理程式和模擬與代理程式對話的基本步驟。

與代理程式的互動是透過 `get_response` 方法進行，該方法會將使用者輸入傳送給代理程式
並接收代理程式的回應。對話歷史由代理程式服務維護，也就是說回應會自動
與對話執行緒關聯。因此，客戶端程式碼不需要維護對話歷史。
"""


# 模擬與代理程式的對話
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
        # 1. 在 Azure AI 代理程式服務上建立一個代理程式
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            name="Assistant",
            instructions="Answer the user's questions.",
        )

        # 2. 為 Azure AI 代理程式建立一個 Semantic Kernel 代理程式
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # 3. 為代理程式建立一個對話執行緒
        # 如果沒有提供執行緒，會建立一個新的執行緒
        # 並隨著初始回應一起回傳
        thread: AzureAIAgentThread = None

        try:
            for user_input in USER_INPUTS:
                print(f"# User: {user_input}")
                # 4. 使用指定的訊息呼叫代理程式以取得回應
                response = await agent.get_response(messages=user_input, thread=thread)
                print(f"# {response.name}: {response}")
                thread = response.thread
        finally:
            # 6. 清理：刪除執行緒和代理程式
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)

        """
        範例輸出：
        # User: Hello, I am John Doe.
        # Assistant: Hello, John! How can I assist you today?
        # User: What is your name?
        # Assistant: I'm here as your assistant, so you can just call me Assistant. How can I help you today?
        # User: What is my name?
        # Assistant: Your name is John Doe. How can I assist you today, John?
        """


if __name__ == "__main__":
    asyncio.run(main())
