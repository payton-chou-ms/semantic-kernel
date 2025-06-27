# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import Agent, ChatCompletionAgent, HandoffOrchestration, OrchestrationHandoffs
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import (
    AuthorRole,
    ChatMessageContent,
    FunctionCallContent,
    FunctionResultContent,
    StreamingChatMessageContent,
)
from semantic_kernel.functions import kernel_function

"""
以下範例示範如何建立代表客戶支援分流系統的移交編排。
編排由4個代理程式組成，每個都專精於客戶支援的不同領域：
分流、退款、訂單狀態和訂單退貨。

編排配置了串流代理程式回應回調，在代理程式產生訊息時列印訊息。

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
        """Check the status of an order."""
        # Simulate checking the order status
        return f"Order {order_id} is shipped and will arrive in 2-3 days."


class OrderRefundPlugin:
    @kernel_function
    def process_refund(self, order_id: str, reason: str) -> str:
        """Process a refund for an order."""
        # Simulate processing a refund
        print(f"Processing refund for order {order_id} due to: {reason}")
        return f"Refund for order {order_id} has been processed successfully."


class OrderReturnPlugin:
    @kernel_function
    def process_return(self, order_id: str, reason: str) -> str:
        """Process a return for an order."""
        # Simulate processing a return
        print(f"Processing return for order {order_id} due to: {reason}")
        return f"Return for order {order_id} has been processed successfully."


def get_agents() -> tuple[list[Agent], OrchestrationHandoffs]:
    """Return a list of agents that will participate in the Handoff orchestration and the handoff relationships.

    Feel free to add or remove agents and handoff connections.
    """
    support_agent = ChatCompletionAgent(
        name="TriageAgent",
        description="A customer support agent that triages issues.",
        instructions="Handle customer requests.",
        service=AzureChatCompletion(),
    )

    refund_agent = ChatCompletionAgent(
        name="RefundAgent",
        description="A customer support agent that handles refunds.",
        instructions="Handle refund requests.",
        service=AzureChatCompletion(),
        plugins=[OrderRefundPlugin()],
    )

    order_status_agent = ChatCompletionAgent(
        name="OrderStatusAgent",
        description="A customer support agent that checks order status.",
        instructions="Handle order status requests.",
        service=AzureChatCompletion(),
        plugins=[OrderStatusPlugin()],
    )

    order_return_agent = ChatCompletionAgent(
        name="OrderReturnAgent",
        description="A customer support agent that handles order returns.",
        instructions="Handle order return requests.",
        service=AzureChatCompletion(),
        plugins=[OrderReturnPlugin()],
    )

    # Define the handoff relationships between agents
    handoffs = (
        OrchestrationHandoffs()
        .add_many(
            source_agent=support_agent.name,
            target_agents={
                refund_agent.name: "Transfer to this agent if the issue is refund related",
                order_status_agent.name: "Transfer to this agent if the issue is order status related",
                order_return_agent.name: "Transfer to this agent if the issue is order return related",
            },
        )
        .add(
            source_agent=refund_agent.name,
            target_agent=support_agent.name,
            description="Transfer to this agent if the issue is not refund related",
        )
        .add(
            source_agent=order_status_agent.name,
            target_agent=support_agent.name,
            description="Transfer to this agent if the issue is not order status related",
        )
        .add(
            source_agent=order_return_agent.name,
            target_agent=support_agent.name,
            description="Transfer to this agent if the issue is not order return related",
        )
    )

    return [support_agent, refund_agent, order_status_agent, order_return_agent], handoffs


# Flag to indicate if a new message is being received
is_new_message = True


def streaming_agent_response_callback(message: StreamingChatMessageContent, is_final: bool) -> None:
    """Observer function to print the messages from the agents.

    Please note that this function is called whenever the agent generates a response,
    including the internal processing messages (such as tool calls) that are not visible
    to other agents in the orchestration.

    In streaming mode, the FunctionCallContent and FunctionResultContent are provided as a
    complete message.

    Args:
        message (StreamingChatMessageContent): The streaming message content from the agent.
        is_final (bool): Indicates if this is the final part of the message.
    """
    global is_new_message
    if is_new_message:
        print(f"{message.name}: ", end="", flush=True)
        is_new_message = False
    print(message.content, end="", flush=True)

    for item in message.items:
        if isinstance(item, FunctionCallContent):
            print(f"Calling '{item.name}' with arguments '{item.arguments}'", end="", flush=True)
        if isinstance(item, FunctionResultContent):
            print(f"Result from '{item.name}' is '{item.result}'", end="", flush=True)

    if is_final:
        print()
        is_new_message = True


def human_response_function() -> ChatMessageContent:
    """觀察函數，用於列印來自代理程式的訊息。"""
    user_input = input("使用者：")
    return ChatMessageContent(role=AuthorRole.USER, content=user_input)


async def main():
    """執行代理程式的主要函數。"""
    # 1. 建立具有多個代理程式的移交編排
    agents, handoffs = get_agents()
    handoff_orchestration = HandoffOrchestration(
        members=agents,
        handoffs=handoffs,
        streaming_agent_response_callback=streaming_agent_response_callback,
        human_response_function=human_response_function,
    )

    # 2. 建立運行時並啟動
    runtime = InProcessRuntime()
    runtime.start()

    # 3. 使用任務和運行時呼叫編排
    orchestration_result = await handoff_orchestration.invoke(
        task="問候尋求支援的客戶。",
        runtime=runtime,
    )

    # 4. 等待結果
    value = await orchestration_result.get()
    print(value)

    # 5. 呼叫完成後停止運行時
    await runtime.stop_when_idle()

    """
    範例輸出：
    TriageAgent: 您好！感謝您聯繫尋求支援。今天我能如何協助您？
    使用者：我想要追蹤我的訂單狀態
    TriageAgent: 正在呼叫 'Handoff-transfer_to_OrderStatusAgent'，參數為 '{}'
    TriageAgent: 來自 'Handoff-transfer_to_OrderStatusAgent' 的結果為 'None'
    OrderStatusAgent: 您能否提供您的訂單編號？這將幫助我檢查您的訂單狀態。
    使用者：我的訂單編號是 123
    OrderStatusAgent: 正在呼叫 'OrderStatusPlugin-check_order_status'，參數為 '{"order_id":"123"}'
    OrderStatusAgent: 來自 'OrderStatusPlugin-check_order_status' 的結果為 '訂單 123 已出貨，將在2-3天內到達。'
    OrderStatusAgent: 您的訂單編號 123 已經出貨，預計在2-3天內到達。如果您有更多問題，隨時提出！
    使用者：我想要退貨我的另一個訂單
    OrderStatusAgent: 正在呼叫 'Handoff-transfer_to_TriageAgent'，參數為 '{}'
    OrderStatusAgent: 來自 'Handoff-transfer_to_TriageAgent' 的結果為 'None'
    TriageAgent: 正在呼叫 'Handoff-transfer_to_OrderReturnAgent'，參數為 '{}'
    TriageAgent: 來自 'Handoff-transfer_to_OrderReturnAgent' 的結果為 'None'
    OrderReturnAgent: 您能否提供您想要退貨的訂單編號以及退貨原因？
    使用者：訂單編號 321
    OrderReturnAgent: 退貨訂單編號 321 的原因是什麼？
    使用者：商品損壞
    正在處理訂單 321 的退貨，原因：商品損壞
    OrderReturnAgent: 正在呼叫 'OrderReturnPlugin-process_return'，參數為 '{"order_id":"321","reason":"商品損壞"}'
    OrderReturnAgent: 來自 'OrderReturnPlugin-process_return' 的結果為 '訂單 321 的退貨已成功處理。'
    OrderReturnAgent: 任務已完成，摘要：處理了訂單編號 321 因商品損壞的退貨。
    正在呼叫 'Handoff-complete_task'，參數為 '{"task_summary":"處理了訂單編號 321 因商品損壞的退貨。"}'
    OrderReturnAgent: 來自 'Handoff-complete_task' 的結果為 'None'
    """


if __name__ == "__main__":
    asyncio.run(main())
