"""
多代理協調環境測試腳本
測試多代理並行協調功能
"""

import asyncio
import os
from dotenv import load_dotenv
from semantic_kernel.agents import Agent, ChatCompletionAgent, ConcurrentOrchestration
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

# 載入環境變數
load_dotenv()
AZURE_ENDPOINT = os.getenv("MY_AZURE_OPENAI_ENDPOINT")


async def get_test_agents() -> list[Agent]:
    """建立測試用的代理"""
    service = AzureChatCompletion(endpoint=AZURE_ENDPOINT)  # 統一使用指定端點

    agent1 = ChatCompletionAgent(
        name="TestAgent1",
        instructions="You are test agent 1. Always start your response with '[Agent1]'.",
        service=service,
    )

    agent2 = ChatCompletionAgent(
        name="TestAgent2",
        instructions="You are test agent 2. Always start your response with '[Agent2]'.",
        service=service,
    )

    return [agent1, agent2]


async def test_multi_agent():
    """測試多代理協調功能"""
    print("🔧 多代理協調環境測試開始...")

    # 新增端點驗證
    if not AZURE_ENDPOINT:
        print("❌ 環境變數設定不完整")
        print("   請設定 MY_AZURE_OPENAI_ENDPOINT")
        return False

    try:
        # 1. 建立代理
        print("🤖 建立測試代理...")
        agents = await get_test_agents()
        print(f"✅ 建立了 {len(agents)} 個代理")

        # 2. 建立並行協調器
        print("⚙️ 建立並行協調器...")
        concurrent_orchestration = ConcurrentOrchestration(members=agents)

        # 3. 啟動執行環境
        print("🚀 啟動執行環境...")
        runtime = InProcessRuntime()
        runtime.start()

        # 4. 執行協調任務
        print("💼 執行協調任務...")
        orchestration_result = await concurrent_orchestration.invoke(
            task="Say hello and introduce yourself briefly.",
            runtime=runtime,
        )

        # 5. 取得結果
        print("📊 取得協調結果...")
        value = await orchestration_result.get(timeout=10)

        print("✅ 協調結果:")
        for i, item in enumerate(value, 1):
            print(f"   {i}. {item.name}: {item.content[:100]}...")

        # 6. 停止執行環境
        print("🛑 停止執行環境...")
        await runtime.stop_when_idle()

        print("🎉 多代理協調環境測試完成！")
        return True

    except Exception as e:
        print(f"❌ 多代理協調環境測試失敗: {e}")
        print("💡 請檢查:")
        print("   1. Chat Completion 服務是否正常")
        print("   2. 是否有足夠的 API 額度")
        print("   3. 網路連線是否穩定")
        return False


if __name__ == "__main__":
    asyncio.run(test_multi_agent())
