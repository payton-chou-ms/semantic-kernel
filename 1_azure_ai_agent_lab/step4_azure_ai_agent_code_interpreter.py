# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from azure.ai.agents.models import CodeInterpreterTool, FilePurpose
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import (
    AzureAIAgent,
    AzureAIAgentSettings,
    AzureAIAgentThread,
)
from semantic_kernel.contents import AuthorRole

"""
以下範例示範如何建立使用程式碼解讀工具的簡易 Azure AI Agent，
並回答程式問題。
"""

TASK = "What's the total sum of all sales for all segments using Python?"


async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. 在 Azure AI Agent 服務建立包含程式碼解讀工具的 agent
        csv_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            "resources",
            "sales.csv",
        )

        # 2. 上傳 CSV 檔案到 Azure AI Agent 服務
        file = await client.agents.files.upload_and_poll(
            file_path=csv_file_path, purpose=FilePurpose.AGENTS
        )

        # 3. 建立參考上傳檔案的程式碼解讀工具
        code_interpreter = CodeInterpreterTool(file_ids=[file.id])
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            tools=code_interpreter.definitions,
            tool_resources=code_interpreter.resources,
        )

        # 4. 建立 Semantic Kernel 對應的 Azure AI Agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # 5. 建立 agent 對話執行緒
        # 若未提供執行緒，系統將建立並回傳含初始回應的新執行緒
        thread: AzureAIAgentThread | None = None

        try:
            print(f"# User: '{TASK}'")
            # 6. 以指定執行緒呼叫 agent 取得回應
            async for response in agent.invoke(messages=TASK, thread=thread):
                if response.role != AuthorRole.TOOL:
                    print(f"# Agent: {response}")
                thread = response.thread
        finally:
            # 7. 清理資源：刪除執行緒、agent 及上傳檔案
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)
            await client.agents.files.delete(file.id)

        """
        範例輸出：
        # User: 'Give me the code to calculate the total sales for all segments.'

        # AuthorRole.ASSISTANT: 先載入檔案然後計算 total_sales...

        ```python
        import pandas as pd

        # 載入上傳的檔案
        file_path = '/mnt/data/assistant-GBaUAF6AKds3sfdfSpxJZG'
        data = pd.read_excel(file_path) # 嘗試以 Excel 檔案格式載入

        # 顯示前幾筆資料以了解其結構
        data.head(), data.info()
        ```

        # AuthorRole.ASSISTANT: 檔案格式無法自動判斷。讓我嘗試將其載入為 CSV 或其他類型。

        ```python
        # 嘗試將檔案載入為 CSV 格式
        data = pd.read_csv(file_path)

        # 顯示資料集的前幾筆資料及其資訊
        data.head(), data.info()
        ```

        # AuthorRole.ASSISTANT: <class 'pandas.core.frame.DataFrame'>
        RangeIndex: 700 entries, 0 to 699
        Data columns (total 14 columns):
        #   Column        Non-Null Count  Dtype  
        ---  ------        --------------  -----  
        0   Segment       700 non-null    object 
        1   Country       700 non-null    object 
        2   Product       700 non-null    object 
        3   Units Sold    700 non-null    float64
        4   Sale Price    700 non-null    float64
        5   Gross Sales   700 non-null    float64
        6   Discounts     700 non-null    float64
        7   Sales         700 non-null    float64
        8   COGS          700 non-null    float64
        9   Profit        700 non-null    float64
        10  Date          700 non-null    object 
        11  Month Number  700 non-null    int64  
        12  Month Name    700 non-null    object 
        13  Year          700 non-null    int64  
        dtypes: float64(7), int64(2), object(5)
        memory usage: 76.7+ KB
        資料集已成功載入，並包含有關各個區段的銷售、利潤及相關指標的資訊。
        若要計算所有區段的總銷售額，我們可以使用「Sales」欄位。

        以下是計算總銷售額的程式碼：

        ```python
        # 計算所有區段的總銷售額
        total_sales = data['Sales'].sum()

        total_sales
        ```

        # AuthorRole.ASSISTANT: 所有區段的總銷售額約為 **118,726,350.29**。
        如需其他分析或操作此資料的程式碼，請告訴我！
        """


if __name__ == "__main__":
    asyncio.run(main())
