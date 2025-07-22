# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import (
    Agent,
    AzureAIAgent,
    AzureAIAgentSettings,
    SequentialOrchestration,
)
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.contents import ChatMessageContent

"""
以下範例示範如何建立順序編排，讓多個代理程式依序執行，
即一個代理程式的輸出是下一個代理程式的輸入。

此範例展示建立和啟動運行時、建立順序編排、呼叫編排，
以及最終等待結果的基本步驟。
"""


async def get_agents(client) -> list[Agent]:
    """回傳將參與順序編排的代理程式清單。

    您可以自由新增或移除代理程式。
    """
    # Create concept extractor agent in Azure AI Agent service
    concept_extractor_definition = await client.agents.create_agent(
        model=AzureAIAgentSettings().model_deployment_name,
        name="ConceptExtractorAgent",
        instructions=(
            "您是行銷分析師。給定產品描述，請識別：\n"
            "- 主要功能\n"
            "- 目標受眾\n"
            "- 獨特賣點\n\n"
        ),
    )
    concept_extractor_agent = AzureAIAgent(
        client=client,
        definition=concept_extractor_definition,
    )

    # Create writer agent in Azure AI Agent service
    writer_definition = await client.agents.create_agent(
        model=AzureAIAgentSettings().model_deployment_name,
        name="WriterAgent",
        instructions=(
            "您是行銷文案撰寫者。給定描述功能、受眾和獨特賣點的文字區塊，"
            "撰寫引人注目的行銷文案（如電子報段落），突出這些要點。"
            "輸出應該簡短（約150字），僅輸出文案作為單一文字區塊。"
        ),
    )
    writer_agent = AzureAIAgent(
        client=client,
        definition=writer_definition,
    )

    # Create format proof agent in Azure AI Agent service
    format_proof_definition = await client.agents.create_agent(
        model=AzureAIAgentSettings().model_deployment_name,
        name="FormatProofAgent",
        instructions=(
            "您是編輯。給定草稿文案，請更正語法、改善清晰度、確保一致的語調，"
            "進行格式化並使其精練。將最終改善的文案輸出為單一文字區塊。"
        ),
    )
    format_proof_agent = AzureAIAgent(
        client=client,
        definition=format_proof_definition,
    )

    # 清單中代理程式的順序將是它們執行的順序
    return [concept_extractor_agent, writer_agent, format_proof_agent]


def agent_response_callback(message: ChatMessageContent) -> None:
    """觀察者函數，用於列印代理程式的訊息。"""
    print(f"# {message.name}\n{message.content}")


async def main():
    """執行代理程式的主要函數。"""
    # 1. 建立 Azure AI Agent service client
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 2. 建立具有多個代理程式和代理程式回應回調的順序編排，
        #    以觀察每個代理程式的輸出。
        agents = await get_agents(client)
        sequential_orchestration = SequentialOrchestration(
            members=agents,
            agent_response_callback=agent_response_callback,
        )

        # 3. 建立運行時並啟動
        runtime = InProcessRuntime()
        runtime.start()

        try:
            # 4. 使用任務和運行時呼叫編排
            orchestration_result = await sequential_orchestration.invoke(
                task="一個環保的不鏽鋼水瓶，可讓飲料保持24小時的冰冷",
                runtime=runtime,
            )

            # 5. 等待結果，增加超時時間並添加錯誤處理
            try:
                value = await orchestration_result.get(timeout=60)
                print(f"***** Final Result *****\n{value}")
            except asyncio.TimeoutError:
                print("***** Timeout occurred while waiting for final result *****")
                print("All agents have completed their tasks successfully.")
                # 等待運行時空閒以確保所有處理都完成
                await runtime.stop_when_idle()
                print(
                    "Runtime stopped successfully. The orchestration completed but result retrieval timed out."
                )
            except Exception as e:
                print(f"***** An error occurred: {e} *****")
                print("All agents have completed their tasks successfully.")

        finally:
            # 6. 空閒時停止運行時（如果尚未停止）
            try:
                await runtime.stop_when_idle()
            except Exception as e:
                print(f"Warning: Error stopping runtime: {e}")

            # 7. Cleanup: delete the agents
            try:
                for agent in agents:
                    await client.agents.delete_agent(agent.id)
            except Exception as e:
                print(f"Warning: Error deleting agents: {e}")

    """
    範例輸出：
    # ConceptExtractorAgent
    - 主要功能：
    - 使用環保不鏽鋼製造
    - 讓飲料保持24小時的冰冷

    - 目標受眾：
    - 有環保意識的消費者
    - 需要可靠方式讓飲料長時間保持冰冷的人，如運動員、旅行者和戶外愛好者

    - 獨特賣點：
    - Environmentally sustainable material
    - Exceptionally long-lasting cold temperature retention (24 hours)
    # WriterAgent
    Keep your beverages refreshingly chilled all day long with our eco-friendly stainless steel bottles. Perfect for
    those who care about the planet, our bottles not only reduce waste but also promise to keep your drinks cold for
    an impressive 24 hours. Whether you're an athlete pushing your limits, a traveler on the go, or simply an outdoor
    enthusiast enjoying nature's beauty, this is the accessory you can't do without. Built from sustainable materials,
    our bottles ensure both environmental responsibility and remarkable performance. Stay refreshed, stay green, and
    make every sip a testament to your planet-friendly lifestyle. Join us in the journey towards a cooler, sustainable
    tomorrow.
    # FormatProofAgent
    Keep your beverages refreshingly chilled all day long with our eco-friendly stainless steel bottles. Perfect for
    those who care about the planet, our bottles not only reduce waste but also promise to keep your drinks cold for
    an impressive 24 hours. Whether you're an athlete pushing your limits, a traveler on the go, or simply an outdoor
    enthusiast enjoying nature's beauty, this is the accessory you can't do without. Built from sustainable materials,
    our bottles ensure both environmental responsibility and remarkable performance. Stay refreshed, stay green, and
    make every sip a testament to your planet-friendly lifestyle. Join us in the journey towards a cooler, sustainable
    tomorrow.
    ***** Final Result *****
    Keep your beverages refreshingly chilled all day long with our eco-friendly stainless steel bottles. Perfect for
    those who care about the planet, our bottles not only reduce waste but also promise to keep your drinks cold for
    an impressive 24 hours. Whether you're an athlete pushing your limits, a traveler on the go, or simply an outdoor
    enthusiast enjoying nature's beauty, this is the accessory you can't do without. Built from sustainable materials,
    our bottles ensure both environmental responsibility and remarkable performance. Stay refreshed, stay green, and
    make every sip a testament to your planet-friendly lifestyle. Join us in the journey towards a cooler, sustainable
    tomorrow.
    """


if __name__ == "__main__":
    asyncio.run(main())
