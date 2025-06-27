# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentThread
from semantic_kernel.contents import (
    ChatMessageContent,
    FunctionCallContent,
    FunctionResultContent,
)

"""
以下範例示範如何在 Semantic Kernel 中使用已存在的
Azure AI Agent。本範例假設您已先前建立好 agent（透過程式、Portal 或 CLI）。
"""

# 新增 agent_id 變數
# agent_id = "<your-agent-id>"
agent_id = "asst_a6eaEyTgtC6e4hjEixEiNjuI"

# 模擬與 agent 的對話
USER_INPUTS = [
    "Using the provided doc, tell me about the evolution of RAG.",
]


async def handle_streaming_intermediate_steps(message: ChatMessageContent) -> None:
    for item in message.items or []:
        if isinstance(item, FunctionResultContent):
            print(f"Function Result:> {item.result} for function: {item.name}")
        elif isinstance(item, FunctionCallContent):
            print(f"Function Call:> {item.name} with arguments: {item.arguments}")
        else:
            print(f"{item}")


async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. 根據 agent_id 取得 agent 定義
        # 將 "<your-agent-id>" 換成您要使用的實際 agent ID
        agent_definition = await client.agents.get_agent(
            agent_id=agent_id,
        )

        # 2. 建立 Semantic Kernel 對應的 Azure AI Agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # 3. 建立 agent 對話執行緒
        # 若未提供執行緒，系統將建立並回傳含初始回應的新執行緒
        thread: AzureAIAgentThread = None

        try:
            for user_input in USER_INPUTS:
                print(f"# User: '{user_input}'")
                # 4. 以指定執行緒呼叫 agent 並串流回應
                async for response in agent.invoke_stream(
                    messages=user_input,
                    thread=thread,
                    on_intermediate_message=handle_streaming_intermediate_steps,
                ):
                    # Print the agent's response
                    print(f"{response}", end="", flush=True)
                    # Update the thread for subsequent messages
                    thread = response.thread
        finally:
            # 5. 清理資源：刪除執行緒
            # 不刪除 agent，以便重複使用
            await thread.delete() if thread else None
            # Do not clean up the agent so it can be used again

        """
        範例輸出：
        # User: 'Why is the sky blue?'
        # Agent: The sky appears blue because molecules in the Earth's atmosphere scatter sunlight,
        and blue light is scattered more than other colors due to its shorter wavelength.
        """


if __name__ == "__main__":
    asyncio.run(main())
