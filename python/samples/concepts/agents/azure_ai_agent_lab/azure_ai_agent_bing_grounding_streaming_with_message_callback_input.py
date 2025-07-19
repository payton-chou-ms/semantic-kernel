# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.ai.agents.models import BingGroundingTool
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import (
    AzureAIAgent,
    AzureAIAgentSettings,
    AzureAIAgentThread,
)
from semantic_kernel.contents import (
    ChatMessageContent,
    FunctionCallContent,
    FunctionResultContent,
    StreamingAnnotationContent,
)

"""
The following sample demonstrates how to create an Azure AI agent that
uses the Bing grounding tool to answer a user's question with user input.

The agent will search and return URLs found during the search process.

Additionally, the `on_intermediate_message` callback is used to handle intermediate messages
from the agent.

Note: Please visit the following link to learn more about the Bing grounding tool:

https://learn.microsoft.com/en-us/azure/ai-services/agents/how-to/tools/bing-grounding?tabs=python&pivots=overview
"""

# Store found URLs and titles
found_urls = []


async def handle_streaming_intermediate_steps(message: ChatMessageContent) -> None:
    global found_urls
    for item in message.items or []:
        if isinstance(item, FunctionResultContent):
            print(f"Function Result:> {item.result} for function: {item.name}")
        elif isinstance(item, FunctionCallContent):
            print(f"Function Call:> {item.name} with arguments: {item.arguments}")
        else:
            print(f"{item}")


async def get_user_input() -> str:
    """Get search query from user input"""
    try:
        user_query = input("\n請輸入您要搜尋的內容 (或輸入 'exit' 退出): ").strip()
        return user_query
    except (KeyboardInterrupt, EOFError):
        return "exit"


async def main() -> None:
    global found_urls

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Enter your Bing Grounding Connection Name
        bing_connection = await client.connections.get(name="mybingsearch")
        conn_id = bing_connection.id

        # 2. Initialize agent bing tool and add the connection id
        bing_grounding = BingGroundingTool(connection_id=conn_id)

        # 3. Create an agent with Bing grounding on the Azure AI agent service
        agent_definition = await client.agents.create_agent(
            name="BingSearchAgent",
            instructions="""Use the Bing grounding tool to search for information based on user queries. 
            Focus on finding relevant sources and URLs. Provide the titles and URLs of the sources you find.""",
            model=AzureAIAgentSettings().model_deployment_name,
            tools=bing_grounding.definitions,
        )

        # 4. Create a Semantic Kernel agent for the Azure AI agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # 5. Create a thread for the agent
        thread: AzureAIAgentThread | None = None

        try:
            print("🔍 Bing 搜尋助手已啟動！")
            print("=" * 50)

            while True:
                # Get user input
                user_query = await get_user_input()

                if user_query.lower() in ["exit", "退出", "quit", "q"]:
                    print("感謝使用，再見！")
                    break

                if not user_query:
                    print("請輸入有效的搜尋內容。")
                    continue

                print(f"\n🔍 正在搜尋：{user_query}")
                print("-" * 50)

                # Reset found URLs for this search
                found_urls = []

                # 6. Invoke the agent for the specified thread for response
                response_content_parts = []
                async for response in agent.invoke_stream(
                    messages=f"Search for: {user_query}. Please provide the titles and URLs of relevant sources you find.",
                    thread=thread,
                    on_intermediate_message=handle_streaming_intermediate_steps,
                ):
                    # Safely extract content from response
                    content = getattr(response, "content", "") or ""
                    if content:
                        response_content_parts.append(str(content))
                    thread = response.thread

                    # 7. Extract annotations and URLs from items
                    if hasattr(response, "items") and response.items:
                        for item in response.items:
                            if isinstance(item, StreamingAnnotationContent):
                                if hasattr(item, "url") and item.url:
                                    # Extract title from the response content or use a default
                                    title = f"搜尋結果 {len(found_urls) + 1}"
                                    found_urls.append(
                                        {
                                            "title": title,
                                            "url": item.url,
                                        }
                                    )

                # Combine all response content parts
                response_content = "".join(response_content_parts)

                # Print the agent response first
                print("\n🤖 Agent 回應：")
                print("=" * 50)
                print(response_content)
                print("=" * 50)

                # Display search results
                print("\n📋 搜尋結果：")
                print("=" * 50)

                if found_urls:
                    for i, result in enumerate(found_urls, 1):
                        print(f"{i}. {result['title']}")
                        print(f"{result['url']}")
                        print()
                else:
                    # Try to extract URLs from the response content
                    import re

                    url_pattern = r"https?://[^\s\]】」\)）,，。\【\】]*"
                    urls = re.findall(url_pattern, response_content)

                    if urls:
                        print("找到以下網址：")
                        unique_urls = list(set(urls))  # Remove duplicates
                        for i, url in enumerate(unique_urls, 1):
                            print(f"{i}. 搜尋結果 {i}")
                            print(f"{url}")
                            print()
                    else:
                        print("未找到具體的網址連結，但搜尋已完成。")
                        if response_content.strip():
                            print(f"回應內容：{response_content}")

                print("=" * 50)

        except Exception as e:
            print(f"❌ 發生錯誤：{str(e)}")
            import traceback

            print(f"詳細錯誤信息：{traceback.format_exc()}")

        finally:
            # 8. Cleanup: Delete the thread and agent
            if thread:
                try:
                    await thread.delete()
                except Exception as e:
                    print(f"清理 thread 時發生錯誤：{e}")
            try:
                await client.agents.delete_agent(agent.id)
            except Exception as e:
                print(f"清理 agent 時發生錯誤：{e}")
            print("\n🧹 資源清理完成")


if __name__ == "__main__":
    asyncio.run(main())
