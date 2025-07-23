# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
import os

from azure.ai.agents.models import OpenApiAnonymousAuthDetails, OpenApiTool
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.contents import ChatMessageContent, FunctionCallContent, FunctionResultContent

"""
以下範例示範如何建立使用 OpenAPI 工具的簡易 Azure AI Agent，
並回答使用者問題。
"""


# 模擬與 agent 的對話
USER_INPUTS = [
    "What is the name and population of the country that uses currency with abbreviation THB",
    "What is the current weather in the capital city of the country?",
]


async def handle_streaming_intermediate_steps(message: ChatMessageContent) -> None:
    for item in message.items or []:
        if isinstance(item, FunctionResultContent):
            print(f"Function Result:> {item.result} for function: {item.name}")
        elif isinstance(item, FunctionCallContent):
            print(f"Function Call:> {item.name} with arguments: {item.arguments}")
        else:
            print(f"{item}")


async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. 載入 OpenAPI 規格檔
        openapi_spec_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            "resources",
        )
        with open(os.path.join(openapi_spec_file_path, "weather.json")) as weather_file:
            weather_openapi_spec = json.loads(weather_file.read())
        with open(os.path.join(openapi_spec_file_path, "countries.json")) as countries_file:
            countries_openapi_spec = json.loads(countries_file.read())

        # 2. 建立 OpenAPI 工具
        # 注意：若使用連線或託管身分識別 (Managed Identity)，
        #       需在 Azure 端額外設定授權
        auth = OpenApiAnonymousAuthDetails()
        openapi_weather = OpenApiTool(
            name="get_weather",
            spec=weather_openapi_spec,
            description="Retrieve weather information for a location",
            auth=auth,
        )
        openapi_countries = OpenApiTool(
            name="get_country",
            spec=countries_openapi_spec,
            description="Retrieve country information",
            auth=auth,
        )

        # 3. 在 Azure AI Agent 服務建立包含 OpenAPI 工具的 agent
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            tools=openapi_weather.definitions + openapi_countries.definitions,
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
                # 7. 以指定執行緒呼叫 agent 取得回應
                async for response in agent.invoke(messages=user_input, thread=thread):
                    print(f"# Agent: {response}")
                    thread = response.thread
        finally:
            # 8. 清理資源：刪除執行緒及 agent
            await client.agents.threads.delete(thread.id) if thread else None
            await client.agents.delete_agent(agent.id)

        """
        範例輸出：
        # User: 'What is the name and population of the country that uses currency with abbreviation THB'
        # Agent: It seems I encountered an issue while trying to retrieve data about the country that uses the ...
        
        As of the latest estimates, the population of Thailand is approximately 69 million people. If you ...
        # User: 'What is the current weather in the capital city of the country?'
        # Agent: The current weather in Bangkok, Thailand, the capital city, is as follows:
        
        - **Temperature**: 24°C (76°F)
        - **Feels Like**: 26°C (79°F)
        - **Weather Description**: Light rain
        - **Humidity**: 69%
        - **Cloud Cover**: 75%
        - **Pressure**: 1017 hPa
        - **Wind Speed**: 8 km/h (5 mph) from the east-northeast (ENE)
        - **Visibility**: 10 km (approximately 6 miles)
        
        This weather information reflects the current conditions as of the latest observation. If you need ...
        """


if __name__ == "__main__":
    asyncio.run(main())
