# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from dotenv import load_dotenv

from pydantic import BaseModel

from semantic_kernel.agents import Agent, ChatCompletionAgent, ConcurrentOrchestration
from semantic_kernel.agents.orchestration.tools import structured_outputs_transform
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

# Load environment variables from .env file
load_dotenv()

# Constants
MY_AZURE_OPENAI_ENDPOINT = os.getenv("MY_AZURE_OPENAI_ENDPOINT")

# Debug: Check if environment variable is loaded
if not MY_AZURE_OPENAI_ENDPOINT:
    raise ValueError("MY_AZURE_OPENAI_ENDPOINT environment variable is not set")

print(f"Using Azure OpenAI endpoint: {MY_AZURE_OPENAI_ENDPOINT}")

"""
以下範例示範如何建立並行編排，讓多個代理程式同時執行相同任務並回傳結構化輸出。

此範例展示建立和啟動運行時、建立具有結構化輸出轉換的多代理程式並行編排、
呼叫編排，以及最終等待結果的基本步驟。
"""


class ArticleAnalysis(BaseModel):
    """用於保存文章分析的模型。"""

    themes: list[str]
    sentiments: list[str]
    entities: list[str]


def get_agents() -> list[Agent]:
    """回傳將參與並行編排的代理程式清單。

    您可以自由新增或移除代理程式。
    """
    theme_agent = ChatCompletionAgent(
        name="ThemeAgent",
        instructions="您是識別文章主題的專家。給定一篇文章，識別主要主題。",
        service=AzureChatCompletion(
            endpoint=MY_AZURE_OPENAI_ENDPOINT,
        ),
    )
    sentiment_agent = ChatCompletionAgent(
        name="SentimentAgent",
        instructions="您是情感分析專家。給定一篇文章，識別情感。",
        service=AzureChatCompletion(
            endpoint=MY_AZURE_OPENAI_ENDPOINT,
        ),
    )
    entity_agent = ChatCompletionAgent(
        name="EntityAgent",
        instructions="您是實體識別專家。給定一篇文章，提取實體。",
        service=AzureChatCompletion(
            endpoint=MY_AZURE_OPENAI_ENDPOINT,
        ),
    )

    return [theme_agent, sentiment_agent, entity_agent]


async def main():
    """執行代理程式的主要函數。"""
    try:
        # 1. 建立具有多個代理程式和結構化輸出轉換的並行編排。
        # 要啟用結構化輸出，您必須指定輸出轉換和編排的泛型類型。
        # 注意：提供給結構化輸出轉換的聊天完成服務和模型必須支援結構化輸出。
        agents = get_agents()
        print(f"Created {len(agents)} agents")

        concurrent_orchestration = ConcurrentOrchestration[str, ArticleAnalysis](
            members=agents,
            output_transform=structured_outputs_transform(
                ArticleAnalysis,
                AzureChatCompletion(
                    endpoint=MY_AZURE_OPENAI_ENDPOINT,
                ),
            ),
        )

        # 2. 從檔案讀取任務
        with open(
            os.path.join(
                os.path.dirname(__file__),
                "../resources",
                "Hamlet_full_play_summary.txt",
            ),
            encoding="utf-8",
        ) as file:
            task = file.read()

        print(f"Task loaded, length: {len(task)} characters")

        # 3. 建立運行時並啟動
        runtime = InProcessRuntime()
        runtime.start()
        print("Runtime started")

        # 4. 使用任務和運行時呼叫編排
        print("Invoking orchestration...")
        orchestration_result = await concurrent_orchestration.invoke(
            task=task,
            runtime=runtime,
        )

        # 5. 等待結果（增加超時時間到 60 秒）
        print("Waiting for results...")
        value = await orchestration_result.get(timeout=60)
        if isinstance(value, ArticleAnalysis):
            print("Success! Results:")
            print(value.model_dump_json(indent=2))
        else:
            print("未預期的結果類型:", type(value))

        # 6. 呼叫完成後停止運行時
        await runtime.stop_when_idle()
        print("Runtime stopped")

    except Exception as e:
        print(f"Error occurred: {e}")
        print(f"Error type: {type(e)}")
        # 確保運行時被停止
        try:
            await runtime.stop_when_idle()
        except:
            pass
        raise

    """
    範例輸出：
    {
    "themes": [
        "復仇與正義",
        "瘋狂",
        "腐敗與權力",
        "死亡與死亡率",
        "表象與現實",
        "家庭與忠誠"
    ],
    "sentiments": [
        "dark",
        "somber",
        "negative"
    ],
    "entities": [
        "Elsinore Castle",
        "Denmark",
        "Horatio",
        "King Hamlet",
        "Claudius",
        "Queen Gertrude",
        "Prince Hamlet",
        "Rosencrantz",
        "Guildenstern",
        "Polonius",
        "Ophelia",
        "Laertes",
        "England",
        "King of England",
        "France",
        "Osric",
        "Fortinbras",
        "Poland"
    ]
    }"""


if __name__ == "__main__":
    asyncio.run(main())
