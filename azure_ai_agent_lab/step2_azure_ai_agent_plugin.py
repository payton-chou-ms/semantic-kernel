# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.functions import kernel_function

"""
以下範例示範如何建立一個使用 Semantic Kernel 外掛程式來回答
範例選單問題的 Azure AI 代理程式。
"""


# 為範例定義一個範例外掛程式
class MenuPlugin:
    """用於概念範例的選單外掛程式範例。"""

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


# 模擬與代理程式的對話
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
        # 1. 在 Azure AI 代理程式服務上建立一個代理程式
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            name="Host",
            instructions="Answer questions about the menu.",
        )

        # 2. 為 Azure AI 代理程式建立一個 Semantic Kernel 代理程式
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
            plugins=[MenuPlugin()],  # 將外掛程式加入代理程式
        )

        # 3. 為代理程式建立一個對話執行緒
        # 如果沒有提供執行緒，會建立一個新的執行緒
        # 並隨著初始回應一起回傳
        thread = None

        try:
            for user_input in USER_INPUTS:
                print(f"# User: {user_input}")
                # 4. 為指定的執行緒呼叫代理程式以取得回應
                async for response in agent.invoke(
                    messages=user_input,
                    thread=thread,
                ):
                    print(f"# {response.name}: {response}")
                    thread = response.thread
        finally:
            # 5. 清理：刪除執行緒和代理程式
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)

        """
        範例輸出：
        # User: Hello
        # Agent: Hello! How can I assist you today?
        # User: What is the special soup?
        # ...
        """


if __name__ == "__main__":
    asyncio.run(main())
