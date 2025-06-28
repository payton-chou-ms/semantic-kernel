"""
Azure AI Agent 環境測試腳本
測試 Azure AI Agent 服務連線和基本功能
"""

import asyncio
import os
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# 載入環境變數
load_dotenv()


async def test_azure_ai_agent():
    """測試 Azure AI Agent 基本功能"""
    print("🔧 Azure AI Agent 環境測試開始...")

    try:
        # 1. 檢查環境變數
        print("📋 檢查環境變數...")
        endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
        model_name = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME")

        if not endpoint or not model_name:
            print("❌ 環境變數設定不完整")
            print(f"   AZURE_AI_AGENT_ENDPOINT: {'✅' if endpoint else '❌'}")
            print(
                f"   AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME: {'✅' if model_name else '❌'}"
            )
            return False

        print(f"✅ 環境變數設定完成")
        print(f"   Endpoint: {endpoint[:50]}...")
        print(f"   Model: {model_name}")

        # 2. 測試 Azure 身份認證
        print("🔐 測試 Azure 身份認證...")
        async with DefaultAzureCredential() as creds:
            # 3. 測試 Azure AI Agent 服務連線
            print("🔗 測試 Azure AI Agent 服務連線...")
            async with AzureAIAgent.create_client(credential=creds) as client:
                # 4. 建立測試代理
                print("🤖 建立測試代理...")
                agent_definition = await client.agents.create_agent(
                    model=AzureAIAgentSettings().model_deployment_name,
                    name="TestAgent",
                    instructions="You are a test assistant. Respond with 'Hello from Azure AI Agent!'",
                )

                agent = AzureAIAgent(
                    client=client,
                    definition=agent_definition,
                )

                # 5. 測試代理回應
                print("💬 測試代理回應...")
                response = await agent.get_response(messages="Say hello!")
                print(f"✅ 代理回應: {response}")

                # 6. 清理資源
                print("🧹 清理測試資源...")
                if response.thread:
                    await response.thread.delete()
                await client.agents.delete_agent(agent.id)

        print("🎉 Azure AI Agent 環境測試完成！")
        return True

    except Exception as e:
        print(f"❌ Azure AI Agent 環境測試失敗: {e}")
        print("💡 請檢查:")
        print("   1. Azure 身份認證設定是否正確")
        print("   2. Azure AI Agent 服務是否已啟用")
        print("   3. 環境變數設定是否正確")
        print("   4. 網路連線是否正常")
        return False


if __name__ == "__main__":
    asyncio.run(test_azure_ai_agent())
