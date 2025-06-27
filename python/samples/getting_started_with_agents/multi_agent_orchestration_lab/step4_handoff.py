# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import (
    Agent,
    AzureAIAgent,
    AzureAIAgentSettings,
    HandoffOrchestration,
    OrchestrationHandoffs,
)
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.contents import (
    AuthorRole,
    ChatMessageContent,
    FunctionCallContent,
    FunctionResultContent,
)
from semantic_kernel.functions import kernel_function

"""
以下範例示範如何建立代表客戶支援分流系統的移交編排。
編排由4個代理程式組成，每個都專精於客戶支援的不同領域：
分流、退款、訂單狀態和訂單退貨。

根據客戶的請求，代理程式可以將對話移交給適當的代理程式。

人類參與迴圈是透過回調函數實現的，類似於群組聊天編排中使用的函數。
不同之處在於，在移交編排中，所有代理程式都可以存取人類回應函數，
而在群組聊天編排中，只有管理員可以存取人類回應函數。

此範例示範建立和啟動運行時、建立移交編排、
呼叫編排，以及最後等待結果的基本步驟。
"""


class OrderStatusPlugin:
    @kernel_function
    def check_order_status(self, order_id: str) -> str:
        """檢查訂單狀態。"""
        # 模擬檢查訂單狀態
        return f"訂單 {order_id} 已出貨，將在2-3天內到達。"


class OrderRefundPlugin:
    @kernel_function
    def process_refund(self, order_id: str, reason: str) -> str:
        """處理訂單退款。"""
        # 模擬處理退款
        print(f"正在處理訂單 {order_id} 的退款，原因：{reason}")
        return f"訂單 {order_id} 的退款已成功處理。"


class OrderReturnPlugin:
    @kernel_function
    def process_return(self, order_id: str, reason: str) -> str:
        """處理訂單退貨。"""
        # 模擬處理退貨
        print(f"正在處理訂單 {order_id} 的退貨，原因：{reason}")
        return f"訂單 {order_id} 的退貨已成功處理。"


async def get_agents(client) -> tuple[list[Agent], OrchestrationHandoffs]:
    """回傳將參與移交編排的代理程式清單和移交關係。

    您可以自由新增或移除代理程式和移交連線。
    """
    # Create support agent in Azure AI Agent service
    support_agent_definition = await client.agents.create_agent(
        model=AzureAIAgentSettings().model_deployment_name,
        name="TriageAgent",
        description="分流問題的客戶支援代理程式。",
        instructions="分流問題的客戶支援代理程式。處理客戶請求。",
    )
    support_agent = AzureAIAgent(
        client=client,
        definition=support_agent_definition,
    )

    # Create refund agent in Azure AI Agent service
    refund_agent_definition = await client.agents.create_agent(
        model=AzureAIAgentSettings().model_deployment_name,
        name="RefundAgent",
        description="處理退款的客戶支援代理程式。",
        instructions="處理退款的客戶支援代理程式。處理退款請求。",
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "OrderRefundPlugin-process_refund",
                    "description": "處理訂單退款。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {"type": "string", "description": "訂單編號"},
                            "reason": {"type": "string", "description": "退款原因"},
                        },
                        "required": ["order_id", "reason"],
                    },
                },
            }
        ],
    )
    refund_agent = AzureAIAgent(
        client=client,
        definition=refund_agent_definition,
        plugins=[OrderRefundPlugin()],
    )

    # Create order status agent in Azure AI Agent service
    order_status_agent_definition = await client.agents.create_agent(
        model=AzureAIAgentSettings().model_deployment_name,
        name="OrderStatusAgent",
        description="檢查訂單狀態的客戶支援代理程式。",
        instructions="檢查訂單狀態的客戶支援代理程式。處理訂單狀態請求。",
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "OrderStatusPlugin-check_order_status",
                    "description": "檢查訂單狀態。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {"type": "string", "description": "訂單編號"}
                        },
                        "required": ["order_id"],
                    },
                },
            }
        ],
    )
    order_status_agent = AzureAIAgent(
        client=client,
        definition=order_status_agent_definition,
        plugins=[OrderStatusPlugin()],
    )

    # Create order return agent in Azure AI Agent service
    order_return_agent_definition = await client.agents.create_agent(
        model=AzureAIAgentSettings().model_deployment_name,
        name="OrderReturnAgent",
        description="處理訂單退貨的客戶支援代理程式。",
        instructions="處理訂單退貨的客戶支援代理程式。處理訂單退貨請求。",
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "OrderReturnPlugin-process_return",
                    "description": "處理訂單退貨。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {"type": "string", "description": "訂單編號"},
                            "reason": {"type": "string", "description": "退貨原因"},
                        },
                        "required": ["order_id", "reason"],
                    },
                },
            }
        ],
    )
    order_return_agent = AzureAIAgent(
        client=client,
        definition=order_return_agent_definition,
        plugins=[OrderReturnPlugin()],
    )

    # 定義代理程式之間的移交關係
    handoffs = (
        OrchestrationHandoffs()
        .add_many(
            source_agent=support_agent.name,
            target_agents={
                refund_agent.name: "如果問題與退款相關，轉移到此代理程式",
                order_status_agent.name: "如果問題與訂單狀態相關，轉移到此代理程式",
                order_return_agent.name: "如果問題與訂單退貨相關，轉移到此代理程式",
            },
        )
        .add(
            source_agent=refund_agent.name,
            target_agent=support_agent.name,
            description="如果問題與退款無關，轉移到此代理程式",
        )
        .add(
            source_agent=order_status_agent.name,
            target_agent=support_agent.name,
            description="如果問題與訂單狀態無關，轉移到此代理程式",
        )
        .add(
            source_agent=order_return_agent.name,
            target_agent=support_agent.name,
            description="如果問題與訂單退貨無關，轉移到此代理程式",
        )
    )

    return [
        support_agent,
        refund_agent,
        order_status_agent,
        order_return_agent,
    ], handoffs


def agent_response_callback(message: ChatMessageContent) -> None:
    """觀察函數，用於列印來自代理程式的訊息。

    請注意，此函數會在代理程式產生回應時被呼叫，
    包括編排中其他代理程式不可見的內部處理訊息（如工具呼叫）。
    """
    print(f"{message.name}: {message.content}")
    for item in message.items:
        if isinstance(item, FunctionCallContent):
            print(f"正在呼叫 '{item.name}'，參數為 '{item.arguments}'")
        if isinstance(item, FunctionResultContent):
            print(f"來自 '{item.name}' 的結果為 '{item.result}'")


def human_response_function() -> ChatMessageContent:
    """觀察函數，用於列印來自代理程式的訊息。"""
    user_input = input("使用者：")
    return ChatMessageContent(role=AuthorRole.USER, content=user_input)


async def main():
    """執行代理程式的主要函數。"""
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. 建立具有多個代理程式的移交編排
        agents, handoffs = await get_agents(client)
        handoff_orchestration = HandoffOrchestration(
            members=agents,
            handoffs=handoffs,
            agent_response_callback=agent_response_callback,
            human_response_function=human_response_function,
        )

        # 2. 建立運行時並啟動
        runtime = InProcessRuntime()
        runtime.start()

        try:
            # 3. 使用任務和運行時呼叫編排
            orchestration_result = await handoff_orchestration.invoke(
                task="問候尋求支援的客戶。",
                runtime=runtime,
            )

            # 4. 等待結果
            value = await orchestration_result.get()
            print(value)

        finally:
            # 5. 呼叫完成後停止運行時
            await runtime.stop_when_idle()

            # 6. Cleanup: delete the agents
            for agent in agents:
                await client.agents.delete_agent(agent.id)

    """
    範例輸出：
    TriageAgent: 您好！感謝您聯繫尋求支援。今天我能如何協助您？
    使用者：我想要追蹤我的訂單狀態
    TriageAgent:
    正在呼叫 'Handoff-transfer_to_OrderStatusAgent'，參數為 '{}'
    TriageAgent:
    來自 'Handoff-transfer_to_OrderStatusAgent' 的結果為 'None'
    OrderStatusAgent: 您能否提供您的訂單編號，讓我為您檢查狀態？
    使用者：我的訂單編號是 123
    OrderStatusAgent:
    正在呼叫 'OrderStatusPlugin-check_order_status'，參數為 '{"order_id":"123"}'
    OrderStatusAgent:
    來自 'OrderStatusPlugin-check_order_status' 的結果為 '訂單 123 已出貨，將在2-3天內到達。'
    OrderStatusAgent: 您的訂單編號 123 已經出貨，預計在2-3天內到達。如果您有更多問題，隨時提出！
    使用者：我想要退貨我的另一個訂單
    OrderStatusAgent: 我可以協助您。您能否提供您想要退貨的訂單編號？
    使用者：訂單編號 321
    OrderStatusAgent:
    正在呼叫 'Handoff-transfer_to_TriageAgent'，參數為 '{}'
    OrderStatusAgent:
    來自 'Handoff-transfer_to_TriageAgent' 的結果為 'None'
    TriageAgent:
    正在呼叫 'Handoff-transfer_to_OrderReturnAgent'，參數為 '{}'
    TriageAgent:
    來自 'Handoff-transfer_to_OrderReturnAgent' 的結果為 'None'
    OrderReturnAgent: 您能否提供訂單編號 321 的退貨原因？
    使用者：商品損壞
    正在處理訂單 321 的退貨，原因：商品損壞
    OrderReturnAgent:
    正在呼叫 'OrderReturnPlugin-process_return'，參數為 '{"order_id":"321","reason":"商品損壞"}'
    OrderReturnAgent:
    來自 'OrderReturnPlugin-process_return' 的結果為 '訂單 321 的退貨已成功處理。'
    OrderReturnAgent: 訂單編號 321 因商品損壞的退貨已成功處理。如果您需要進一步協助或有其他問題，請隨時告訴我！
    使用者：不用了，再見
    任務已完成，摘要：處理了訂單編號 321 因商品損壞的退貨請求。
    OrderReturnAgent:
    正在呼叫 'Handoff-complete_task'，參數為 '{"task_summary":"處理了訂單編號 321 因商品損壞的退貨請求。"}'
    OrderReturnAgent:
    來自 'Handoff-complete_task' 的結果為 'None'
    """


if __name__ == "__main__":
    asyncio.run(main())
