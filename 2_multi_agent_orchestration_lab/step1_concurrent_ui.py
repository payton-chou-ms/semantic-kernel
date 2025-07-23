# Copyright (c) Microsoft. All rights reserved.

import asyncio

import chainlit as cl
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import (
    Agent,
    AzureAIAgent,
    AzureAIAgentSettings,
    ConcurrentOrchestration,
)
from semantic_kernel.agents.runtime import InProcessRuntime

"""
The following sample demonstrates how to create a concurrent orchestration for
executing multiple Azure AI agents on the same task in parallel with Chainlit UI.

This sample demonstrates the basic steps of creating and starting a runtime, creating
Azure AI agents using the Azure AI Agent service, creating a concurrent orchestration 
with these agents, invoking the orchestration through a web interface, and displaying
the results.
"""

# Global variables to store agents and runtime
agents_cache = None
runtime_cache = None
client_cache = None
creds_cache = None


async def get_agents(client) -> list[Agent]:
    """Return a list of Azure AI agents that will participate in the concurrent orchestration.

    Feel free to add or remove agents.
    """
    # Create physics expert agent in Azure AI Agent service
    physics_agent_definition = await client.agents.create_agent(
        model=AzureAIAgentSettings().model_deployment_name,
        name="PhysicsExpert",
        instructions="You are an expert in physics. You answer questions from a physics perspective.",
    )
    physics_agent = AzureAIAgent(
        client=client,
        definition=physics_agent_definition,
    )

    # Create chemistry expert agent in Azure AI Agent service
    chemistry_agent_definition = await client.agents.create_agent(
        model=AzureAIAgentSettings().model_deployment_name,
        name="ChemistryExpert",
        instructions="You are an expert in chemistry. You answer questions from a chemistry perspective.",
    )
    chemistry_agent = AzureAIAgent(
        client=client,
        definition=chemistry_agent_definition,
    )

    return [physics_agent, chemistry_agent]


@cl.on_chat_start
async def on_chat_start():
    """Initialize the agents and runtime when a new chat session starts."""
    global agents_cache, runtime_cache, client_cache, creds_cache

    await cl.Message(content="🔄 正在初始化 Azure AI 代理程式...").send()

    try:
        # Initialize Azure credentials and client
        creds_cache = DefaultAzureCredential()
        client_cache = AzureAIAgent.create_client(credential=creds_cache)

        # Create Azure AI agents
        agents_cache = await get_agents(client_cache)

        # Create and start runtime
        runtime_cache = InProcessRuntime()
        runtime_cache.start()

        # Store in user session
        cl.user_session.set("agents", agents_cache)
        cl.user_session.set("runtime", runtime_cache)
        cl.user_session.set("client", client_cache)
        cl.user_session.set("creds", creds_cache)

        await cl.Message(
            content="✅ 代理程式已成功初始化！\n\n"
            "🧪 **可用的專家代理程式：**\n"
            "- 🔬 PhysicsExpert - 物理學專家\n"
            "- ⚗️ ChemistryExpert - 化學專家\n\n"
            "請輸入您的問題，兩位專家會同時回答！"
        ).send()

    except Exception as e:
        await cl.Message(content=f"❌ 初始化失敗: {str(e)}").send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages and process them with the concurrent orchestration."""
    agents = cl.user_session.get("agents")
    runtime = cl.user_session.get("runtime")

    if not agents or not runtime:
        await cl.Message(content="❌ 代理程式未初始化，請重新整理頁面。").send()
        return

    # Show processing message
    processing_msg = cl.Message(content="🤔 專家們正在思考您的問題...")
    await processing_msg.send()

    try:
        # Create concurrent orchestration
        concurrent_orchestration = ConcurrentOrchestration(members=agents)

        # Invoke the orchestration
        orchestration_result = await concurrent_orchestration.invoke(
            task=message.content,
            runtime=runtime,
        )

        # Wait for results with timeout
        results = await orchestration_result.get(timeout=30)

        # Update processing message
        await processing_msg.remove()

        # Display results from each agent
        response_content = "## 專家回應\n\n"

        for i, result in enumerate(results):
            icon = "🔬" if "Physics" in result.name else "⚗️"
            response_content += (
                f"### {icon} {result.name}\n\n{result.content}\n\n---\n\n"
            )

        await cl.Message(content=response_content).send()

    except asyncio.TimeoutError:
        await processing_msg.remove()
        await cl.Message(content="⏰ 請求超時，請稍後再試。").send()
    except Exception as e:
        await processing_msg.remove()
        await cl.Message(content=f"❌ 處理請求時發生錯誤: {str(e)}").send()


@cl.on_chat_end
async def on_chat_end():
    """Clean up resources when chat session ends."""
    agents = cl.user_session.get("agents")
    runtime = cl.user_session.get("runtime")
    client = cl.user_session.get("client")
    creds = cl.user_session.get("creds")

    try:
        if runtime:
            await runtime.stop_when_idle()

        if agents and client:
            for agent in agents:
                try:
                    await client.agents.delete_agent(agent.id)
                except Exception:
                    pass  # Ignore cleanup errors

        if client:
            await client.close()

        if creds:
            await creds.close()

    except Exception as e:
        print(f"清理資源時發生錯誤: {e}")

    """
    範例使用方式：
    1. 安裝 chainlit: pip install chainlit
    2. 執行應用程式: chainlit run step1_concurrent_ui.py
    3. 在瀏覽器中開啟 http://localhost:8000
    4. 開始與多個 AI 專家對話！
    
    範例問題：
    - "What is temperature?"
    - "Explain photosynthesis"
    - "How does gravity work?"
    """


# For command line execution (optional)
if __name__ == "__main__":
    print("請使用 'chainlit run step1_concurrent_ui.py' 來啟動應用程式")
