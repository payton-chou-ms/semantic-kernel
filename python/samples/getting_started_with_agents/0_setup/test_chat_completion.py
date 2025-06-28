"""
Chat Completion 環境測試腳本
測試 Azure OpenAI Chat Completion 服務連線
"""

import asyncio
import os
from dotenv import load_dotenv
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

# 載入環境變數
load_dotenv()


async def test_chat_completion():
    """測試 Chat Completion 基本功能"""
    print("🔧 Chat Completion 環境測試開始...")

    try:
        # 1. 檢查環境變數
        print("📋 檢查環境變數...")
        endpoint = os.getenv("MY_AZURE_OPENAI_ENDPOINT")

        if not endpoint:
            print("❌ 環境變數設定不完整")
            print("   請設定 MY_AZURE_OPENAI_ENDPOINT")
            return False

        print(f"✅ 環境變數設定完成")
        print(f"   Endpoint: {endpoint}")

        # 2. 建立 Chat Completion 代理
        print("🤖 建立 Chat Completion 代理...")
        agent = ChatCompletionAgent(
            service=AzureChatCompletion(
                endpoint=endpoint,
            ),
            name="TestAssistant",
            instructions="You are a test assistant. Respond with 'Hello from Chat Completion Agent!'",
        )

        # 3. 測試代理回應
        print("💬 測試代理回應...")
        response = await agent.get_response(
            messages="Say hello!",
        )
        print(f"✅ 代理回應: {response}")

        print("🎉 Chat Completion 環境測試完成！")
        return True

    except Exception as e:
        print(f"❌ Chat Completion 環境測試失敗: {e}")
        print("💡 請檢查:")
        print("   1. Azure OpenAI 服務是否已部署")
        print("   2. API 金鑰或身份認證設定是否正確")
        print("   3. 模型部署名稱是否正確")
        print("   4. 網路連線是否正常")
        return False


if __name__ == "__main__":
    asyncio.run(test_chat_completion())
