# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from azure.ai.agents.models import FileInfo, FileSearchTool, VectorStore
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import (
    AzureAIAgent,
    AzureAIAgentSettings,
    AzureAIAgentThread,
)
from semantic_kernel.contents import AuthorRole

"""
以下範例示範如何建立使用檔案搜尋工具的簡易 Azure AI Agent，
並回答使用者問題。
"""

# 模擬與 agent 的對話
USER_INPUTS = [
    "Who is the youngest employee?",
    "Who works in sales?",
    "I have a customer request, who can help me?",
]


async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. 讀取並上傳檔案到 Azure AI Agent 服務
        pdf_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            "resources",
            "employees.pdf",
        )
        file: FileInfo = await client.agents.files.upload_and_poll(
            file_path=pdf_file_path, purpose="assistants"
        )
        vector_store: VectorStore = await client.agents.vector_stores.create_and_poll(
            file_ids=[file.id], name="my_vectorstore"
        )

        # 2. 使用上傳資源建立檔案搜尋工具
        file_search = FileSearchTool(vector_store_ids=[vector_store.id])

        # 3. 在 Azure AI Agent 服務建立包含檔案搜尋工具的 agent
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            tools=file_search.definitions,
            tool_resources=file_search.resources,
        )

        # 4. 建立 Semantic Kernel 對應的 Azure AI Agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # 5. 建立 agent 對話執行緒
        # 若未提供執行緒，系統將建立並回傳含初始回應的新執行緒
        thread: AzureAIAgentThread = None

        try:
            for user_input in USER_INPUTS:
                print(f"# User: '{user_input}'")
                # 6. 以指定執行緒呼叫 agent 取得回應
                async for response in agent.invoke(messages=user_input, thread=thread):
                    if response.role != AuthorRole.TOOL:
                        print(f"# Agent: {response}")
                    thread = response.thread
        finally:
            # 7. 清理資源：刪除執行緒、向量資料庫、檔案及 agent
            await thread.delete() if thread else None
            await client.agents.vector_stores.delete(vector_store.id)
            await client.agents.files.delete(file.id)
            await client.agents.delete_agent(agent.id)

        """
        範例輸出：
        # User: 'Who is the youngest employee?'
        # Agent: The youngest employee is Teodor Britton, who is an accountant and was born on January 9, 1997...
        # User: 'Who works in sales?'
        """


if __name__ == "__main__":
    asyncio.run(main())
