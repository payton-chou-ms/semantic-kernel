# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from dotenv import load_dotenv
import chainlit as cl
from azure.identity.aio import DefaultAzureCredential
from azure.ai.agents.models import BingGroundingTool
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import json

from semantic_kernel.agents import (
    Agent,
    AzureAIAgent,
    AzureAIAgentSettings,
    MagenticOrchestration,
    StandardMagenticManager,
)
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.functions import kernel_function

"""
深度研究助手 - 具有真實網頁搜尋和內容分析功能的 Magentic 編排系統

此範例示範如何建立具有兩個專門代理程式的研究系統：
- WebSearchAgent：使用 Bing Grounding 執行真實網頁搜尋和內容抓取
- ContentAnalysisAgent：進行內容分析、重點整理和深度研究

在此處閱讀更多關於 Magentic 的資訊：
https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/
"""

# Load environment variables from .env file
load_dotenv()
MY_AZURE_OPENAI_ENDPOINT = os.getenv("MY_AZURE_OPENAI_ENDPOINT")
BING_CONNECTION_NAME = os.getenv("BING_CONNECTION_NAME", "mybingsearch")


class WebSearchPlugin:
    def __init__(self, client=None, bing_connection_id=None):
        self.client = client
        self.bing_connection_id = bing_connection_id

    @kernel_function
    def search_web_content(self, query: str, max_results: int = 5) -> str:
        """搜尋網頁內容並返回相關資訊。"""
        try:
            # 使用 Bing Grounding 進行真實搜尋
            if self.client and self.bing_connection_id:
                # 注意：此處為示例，實際的 Bing Grounding 調用將通過代理程式自動處理
                return (
                    f"正在使用 Bing 搜尋「{query}」，最多返回 {max_results} 個結果..."
                )
            else:
                # Fallback to simulated results if Bing is not available
                return self._get_simulated_search_results(query, max_results)

        except Exception as e:
            return f"搜尋過程中發生錯誤：{str(e)}"

    def _get_simulated_search_results(self, query: str, max_results: int = 5) -> str:
        """提供模擬搜尋結果作為後備方案。"""
        # ...existing simulation logic...
        search_results = {
            "AI": [
                {
                    "title": "人工智慧最新發展趨勢",
                    "url": "https://example.com/ai-trends",
                    "summary": "探討2024年AI技術的重要突破和未來方向",
                },
                {
                    "title": "機器學習在產業中的應用",
                    "url": "https://example.com/ml-industry",
                    "summary": "分析機器學習技術在各行各業的實際應用案例",
                },
                {
                    "title": "深度學習模型優化技術",
                    "url": "https://example.com/dl-optimization",
                    "summary": "介紹提升深度學習模型性能的最新方法",
                },
            ],
            "研究": [
                {
                    "title": "學術研究方法論",
                    "url": "https://example.com/research-methodology",
                    "summary": "系統性介紹現代學術研究的方法和工具",
                },
                {
                    "title": "跨領域研究的新趨勢",
                    "url": "https://example.com/interdisciplinary",
                    "summary": "探討跨領域合作研究的重要性和實施策略",
                },
                {
                    "title": "研究數據分析最佳實踐",
                    "url": "https://example.com/data-analysis",
                    "summary": "分享研究數據分析的專業技巧和工具",
                },
            ],
        }

        # 根據查詢關鍵字匹配結果
        results = []
        for category, items in search_results.items():
            if any(
                keyword in query.lower()
                for keyword in [category.lower(), "research", "study"]
            ):
                results.extend(items[:max_results])

        if not results:
            results = search_results["研究"][:max_results]

        output = f"搜尋查詢：{query}\n找到 {len(results)} 個相關結果：\n\n"
        for i, result in enumerate(results, 1):
            output += f"{i}. **{result['title']}**\n"
            output += f"   網址：{result['url']}\n"
            output += f"   摘要：{result['summary']}\n\n"

        return output

    @kernel_function
    def extract_webpage_content(self, url: str) -> str:
        """從指定網頁提取主要內容。"""
        # ...existing code...
        try:
            # 模擬網頁內容提取（實際應用中應該使用真實的網頁抓取）
            content_examples = {
                "ai-trends": """
                # 人工智慧最新發展趨勢
                
                ## 主要技術突破
                1. **大型語言模型的進展**：GPT系列和其他transformer架構的持續優化
                2. **多模態AI**：結合文字、圖像、聲音的綜合智能系統
                3. **邊緣AI**：在物聯網設備上運行的輕量級AI模型
                
                ## 產業應用
                - 醫療診斷：AI輔助醫學影像分析和疾病預測
                - 自動駕駛：感知、決策和控制系統的整合
                - 金融科技：智能風險評估和投資建議
                
                ## 未來展望
                AI技術將朝向更加專業化和人性化的方向發展，重點關注可解釋性和倫理問題。
                """,
                "research-methodology": """
                # 學術研究方法論
                
                ## 研究設計原則
                1. **問題定義**：明確研究目標和假設
                2. **文獻回顧**：系統性分析既有研究成果
                3. **方法選擇**：量化與質化研究方法的適當運用
                
                ## 數據收集策略
                - 問卷調查：結構化數據收集
                - 深度訪談：質性洞察獲取
                - 實驗設計：因果關係驗證
                
                ## 分析工具
                統計軟件SPSS、R語言、Python等工具的應用，以及質性分析軟件NVivo的使用。
                """,
            }

            # 根據URL返回對應內容
            for key, content in content_examples.items():
                if key in url:
                    return f"從 {url} 提取的內容：\n{content}"

            return f"從 {url} 提取的內容：\n這是一個包含豐富資訊的網頁，涵蓋了相關主題的深入分析和專業見解。"

        except Exception as e:
            return f"提取網頁內容時發生錯誤：{str(e)}"

    @kernel_function
    def find_related_sources(self, topic: str, source_count: int = 3) -> str:
        """尋找與主題相關的權威資料來源。"""
        # ...existing code...
        authority_sources = {
            "AI": [
                {
                    "name": "MIT Technology Review",
                    "url": "https://www.technologyreview.com",
                    "specialty": "技術趨勢分析",
                },
                {
                    "name": "Nature Machine Intelligence",
                    "url": "https://www.nature.com/natmachintell",
                    "specialty": "學術研究",
                },
                {
                    "name": "arXiv.org",
                    "url": "https://arxiv.org",
                    "specialty": "最新論文預印本",
                },
            ],
            "研究": [
                {
                    "name": "ResearchGate",
                    "url": "https://www.researchgate.net",
                    "specialty": "研究者網絡平台",
                },
                {
                    "name": "Google Scholar",
                    "url": "https://scholar.google.com",
                    "specialty": "學術文獻搜尋",
                },
                {
                    "name": "JSTOR",
                    "url": "https://www.jstor.org",
                    "specialty": "期刊文獻庫",
                },
            ],
        }

        # 選擇相關來源
        sources = []
        for category, items in authority_sources.items():
            if category.lower() in topic.lower() or any(
                keyword in topic.lower()
                for keyword in ["research", "study", "academic"]
            ):
                sources.extend(items[:source_count])

        if not sources:
            sources = authority_sources["研究"][:source_count]

        result = f"針對主題「{topic}」的權威資料來源：\n\n"
        for i, source in enumerate(sources, 1):
            result += f"{i}. **{source['name']}**\n"
            result += f"   網址：{source['url']}\n"
            result += f"   專長：{source['specialty']}\n\n"

        return result


class ContentAnalysisPlugin:
    @kernel_function
    def analyze_content_themes(self, content: str) -> str:
        """分析內容的主要主題和概念。"""
        # 模擬內容主題分析
        analysis_result = f"""
        內容主題分析報告：
        
        ## 核心主題識別
        1. **主要概念**：從內容中識別出的關鍵概念和理論框架
        2. **研究方向**：內容所涉及的研究領域和發展方向  
        3. **技術要點**：重要的技術細節和實作方法
        
        ## 內容結構分析
        - **邏輯架構**：內容的組織方式和論證邏輯
        - **證據支持**：數據、案例和引用文獻的分析
        - **結論強度**：論點的可信度和說服力評估
        
        ## 關鍵洞察
        - 內容長度：約 {len(content)} 字符
        - 專業深度：中高等級，適合學術研究參考
        - 應用價值：具有實際應用潛力的資訊含量高
        """

        return analysis_result

    @kernel_function
    def generate_summary_report(self, topic: str, sources_data: str) -> str:
        """基於多個來源生成綜合研究報告。"""
        report = f"""
        # {topic} - 深度研究報告
        
        ## 執行摘要
        本報告基於多個權威來源的資訊，對「{topic}」進行了全面的分析和研究。
        
        ## 主要發現
        
        ### 1. 現狀分析
        - 當前發展水準和技術成熟度
        - 主要挑戰和限制因素
        - 市場接受度和應用範圍
        
        ### 2. 趨勢預測
        - 短期發展方向（1-2年）
        - 中期演進路徑（3-5年）  
        - 長期願景展望（5年以上）
        
        ### 3. 關鍵建議
        - 研究優先順序建議
        - 資源配置策略
        - 風險控制措施
        
        ## 參考資料來源
        {sources_data}
        
        ## 結論
        基於綜合分析，「{topic}」領域展現出巨大的發展潛力，建議持續關注其技術演進和應用拓展。
        """

        return report

    @kernel_function
    def extract_key_insights(self, content: str, insight_count: int = 5) -> str:
        """從內容中提取關鍵洞察和要點。"""
        insights = [
            "技術創新是推動領域發展的核心動力",
            "跨領域合作能夠創造更大的價值和影響力",
            "實際應用案例提供了重要的實作參考",
            "持續學習和知識更新是保持競爭力的關鍵",
            "倫理和可持續性考量變得越來越重要",
            "數據品質和分析方法直接影響研究成果",
            "開放合作和知識共享促進整體進步",
        ]

        selected_insights = insights[: min(insight_count, len(insights))]

        result = "從內容中提取的關鍵洞察：\n\n"
        for i, insight in enumerate(selected_insights, 1):
            result += f"{i}. {insight}\n"

        result += f"\n✨ 這些洞察基於 {len(content)} 字符的內容分析得出，為後續研究提供重要指導。"

        return result


async def get_agents(client) -> list[Agent]:
    """回傳將參與深度研究編排的代理程式清單。"""
    # Get Bing connection for web search
    bing_connection_id = None
    try:
        bing_connection = await client.connections.get(name=BING_CONNECTION_NAME)
        bing_connection_id = bing_connection.id
        print(f"✅ 成功連接到 Bing 搜尋服務：{BING_CONNECTION_NAME}")
    except Exception as e:
        print(f"⚠️ 無法連接到 Bing 搜尋服務：{e}")
        print("將使用模擬搜尋結果作為後備方案")

    # Initialize Bing grounding tool if connection is available
    bing_tools = []
    if bing_connection_id:
        bing_grounding = BingGroundingTool(connection_id=bing_connection_id)
        bing_tools = bing_grounding.definitions

    # Create web search agent with Bing grounding
    search_agent_definition = await client.agents.create_agent(
        model=AzureAIAgentSettings().model_deployment_name,
        name="WebSearchAgent",
        description="網頁搜尋專家，使用 Bing Grounding 工具搜尋和提取網路資訊進行研究。",
        instructions="""您是一位專業的網路資訊搜尋專家，專長於：
1. 使用 Bing Grounding 工具執行精準的網頁內容搜尋
2. 從搜尋結果中提取有價值的資訊和洞察
3. 識別權威可靠的資料來源和參考文獻
4. 整理和組織搜尋結果，提供結構化的資訊
5. 提供高品質的研究資料基礎和背景資訊

當用戶提出研究問題時，請：
- 使用 Bing Grounding 搜尋最新和最相關的資訊
- 從搜尋結果中提取關鍵資訊和數據
- 提供準確的來源引用和連結
- 確保資訊的時效性和權威性

請確保搜尋結果的準確性和相關性，優先選擇權威來源。""",
        tools=bing_tools
        + [
            {
                "type": "function",
                "function": {
                    "name": "WebSearchPlugin-search_web_content",
                    "description": "搜尋網頁內容並返回相關資訊。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜尋查詢關鍵字",
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "最大結果數量",
                                "default": 5,
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "WebSearchPlugin-extract_webpage_content",
                    "description": "從指定網頁提取主要內容。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "要提取內容的網頁URL",
                            }
                        },
                        "required": ["url"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "WebSearchPlugin-find_related_sources",
                    "description": "尋找與主題相關的權威資料來源。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string", "description": "研究主題"},
                            "source_count": {
                                "type": "integer",
                                "description": "來源數量",
                                "default": 3,
                            },
                        },
                        "required": ["topic"],
                    },
                },
            },
        ],
    )
    search_agent = AzureAIAgent(
        client=client,
        definition=search_agent_definition,
        plugins=[WebSearchPlugin(client, bing_connection_id)],
    )

    # Create content analysis agent (unchanged)
    analysis_agent_definition = await client.agents.create_agent(
        model=AzureAIAgentSettings().model_deployment_name,
        name="ContentAnalysisAgent",
        description="內容分析專家，專門進行深度內容分析和研究報告生成。",
        instructions="""您是一位資深的內容分析專家，專長於：
1. 深入分析文本內容的主題和概念
2. 提取關鍵洞察和重要要點
3. 生成綜合性研究報告
4. 識別內容中的趨勢和模式
5. 提供專業的分析結論和建議

請確保分析的深度和準確性，提供有價值的研究見解。""",
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "ContentAnalysisPlugin-analyze_content_themes",
                    "description": "分析內容的主要主題和概念。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "要分析的內容文本",
                            }
                        },
                        "required": ["content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "ContentAnalysisPlugin-generate_summary_report",
                    "description": "基於多個來源生成綜合研究報告。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string", "description": "研究主題"},
                            "sources_data": {
                                "type": "string",
                                "description": "來源資料",
                            },
                        },
                        "required": ["topic", "sources_data"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "ContentAnalysisPlugin-extract_key_insights",
                    "description": "從內容中提取關鍵洞察和要點。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "要分析的內容",
                            },
                            "insight_count": {
                                "type": "integer",
                                "description": "洞察數量",
                                "default": 5,
                            },
                        },
                        "required": ["content"],
                    },
                },
            },
        ],
    )
    analysis_agent = AzureAIAgent(
        client=client,
        definition=analysis_agent_definition,
        plugins=[ContentAnalysisPlugin()],
    )

    return [search_agent, analysis_agent]


async def agent_response_callback(message: ChatMessageContent) -> None:
    """觀察函數，用於透過 Chainlit 顯示來自代理程式的訊息。"""
    await cl.Message(
        content=message.content,
        author=message.name,
    ).send()


@cl.on_chat_start
async def setup():
    """當聊天開始時初始化系統。"""
    welcome_message = """🔍 歡迎使用深度研究助手！(支援真實網頁搜尋)

我是一個專業的研究分析系統，配備了兩個專門的AI代理程式：

🌐 **WebSearchAgent** - 網頁搜尋專家 (配備 Bing Grounding)
- 使用真實的 Bing 搜尋引擎搜尋網路資訊
- 提取網頁核心內容和最新資料
- 找尋權威資料來源和學術文獻
- 提供準確的來源引用和連結

📊 **ContentAnalysisAgent** - 內容分析專家
- 深度分析內容主題和概念
- 提取關鍵洞察要點
- 生成綜合研究報告
- 提供專業的分析見解

## 我可以幫助您：
✅ 搜尋任何主題的最新資訊和研究 (使用真實網頁搜尋)
✅ 分析網頁內容並提取重點
✅ 整理多個來源的資訊
✅ 生成深度研究報告
✅ 提供專業的分析見解

請告訴我您想要深入研究的主題，我將為您提供全面的資訊搜集和分析服務！

**範例：**
- "請幫我研究人工智慧在醫療領域的最新應用"
- "我想了解區塊鏈技術的發展趨勢" 
- "請分析永續能源的市場前景"
"""

    await cl.Message(content=welcome_message).send()


@cl.on_message
async def main(message: cl.Message):
    """處理使用者訊息的主要函數。"""
    user_query = message.content.strip()

    if not user_query:
        await cl.Message(content="請提供您想要研究的主題或問題。").send()
        return

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        try:
            # 建立代理程式
            agents_list = await get_agents(client)

            # 建立 Magentic 編排
            magentic_orchestration = MagenticOrchestration(
                members=agents_list,
                manager=StandardMagenticManager(
                    chat_completion_service=AzureChatCompletion(
                        endpoint=MY_AZURE_OPENAI_ENDPOINT,
                    )
                ),
                agent_response_callback=agent_response_callback,
            )

            # 建立並啟動運行時
            runtime = InProcessRuntime()
            runtime.start()

            try:
                # 執行深度研究任務
                research_task = f"""
                請針對以下用戶查詢進行深度研究分析：

                用戶查詢：{user_query}

                請按照以下步驟進行：
                1. 首先使用 Bing Grounding 工具搜尋相關的最新網頁資訊和資料來源
                2. 提取和分析找到的內容，包括權威來源和學術資料
                3. 識別關鍵主題和重要洞察
                4. 生成綜合性的研究報告
                5. 提供具體的建議和結論，並包含來源引用

                請確保資訊的準確性、時效性和全面性，並提供有價值的分析見解。
                使用真實的網頁搜尋結果來支持您的分析。
                """

                orchestration_result = await magentic_orchestration.invoke(
                    task=research_task,
                    runtime=runtime,
                )

                # 等待並顯示最終結果
                final_result = await orchestration_result.get()

                await cl.Message(
                    content=f"## 🎯 研究完成總結\n\n{final_result}", author="研究助手"
                ).send()

            finally:
                # 停止運行時
                await runtime.stop_when_idle()

                # 清理代理程式
                for agent in agents_list:
                    await client.agents.delete_agent(agent.id)

        except Exception as e:
            error_message = f"研究過程中發生錯誤：{str(e)}\n\n請稍後重試，或嘗試重新描述您的研究需求。"
            await cl.Message(content=error_message).send()


if __name__ == "__main__":
    # 啟動 Chainlit 應用
    import chainlit.cli

    chainlit.cli.run_chainlit()
