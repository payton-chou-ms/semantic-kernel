# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AgentRegistry, AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel import Kernel

"""
以下範例示範如何使用宣告式 YAML 規格建立 Azure AI Agent，
並透過 Semantic Kernel Plugin 回答有關範例菜單的問題。
"""


# 定義範例外掛
class MenuPlugin:
    """用於概念範例的範例菜單外掛。"""

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


# 模擬與 agent 的對話
USER_INPUTS = [
    "Hello",
    "What is the special soup?",
    "How much does that cost?",
    "Thank you",
]

# 定義範例的 YAML 字串
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
        # 宣告式 agent 需要 kernel 來解析外掛
        kernel = Kernel()
        kernel.add_plugin(MenuPlugin())

        # 2. 使用宣告式 YAML 規格建立 Azure AI Agent
        agent: AzureAIAgent = await AgentRegistry.create_from_yaml(
            SPEC,
            kernel=kernel,
            settings=settings,
            client=client,
        )

        # 3. 建立 agent 對話執行緒
        # 若未提供執行緒，系統將建立並回傳含初始回應的新執行緒
        thread = None

        try:
            for user_input in USER_INPUTS:
                print(f"# User: {user_input}")
                # 4. 以指定執行緒呼叫 agent 取得回應
                async for response in agent.invoke(
                    messages=user_input,
                    thread=thread,
                ):
                    print(f"# {response.name}: {response}")
                    thread = response.thread
        finally:
            # 5. 清理資源：刪除執行緒及 agent
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
