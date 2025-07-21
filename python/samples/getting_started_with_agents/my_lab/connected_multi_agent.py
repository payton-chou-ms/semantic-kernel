# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
import os
from typing import Dict, List, Optional
from enum import Enum

# 添加 dotenv 支援
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv 未安裝，將使用系統環境變數")

from azure.ai.agents.models import BingGroundingTool
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import (
    AzureAIAgent,
    AzureAIAgentSettings,
    AzureAIAgentThread,
)

"""
Connected Multi-Agent System Implementation

這個系統實作了一個多代理協作架構，包含：
- 1個 Master Agent（任務分派大師）
- 4個專業 Sub Agents（網路搜尋、翻譯重寫、專業顧問、筆記整理）

支援單一任務和複合任務的智能分派與協作處理。
"""


class AgentType(Enum):
    """代理類型枚舉"""

    MASTER = "master"
    WEB_SEARCHER = "web_searcher"
    TRANSLATOR = "translator"
    CONSULTANT = "consultant"
    NOTE_TAKER = "note_taker"


class MultiAgentOrchestrator:
    """多代理協調器"""

    def __init__(self):
        self.agents: Dict[AgentType, AzureAIAgent] = {}
        self.threads: Dict[AgentType, AzureAIAgentThread] = {}
        self.client = None
        self.conversation_history: List[Dict] = []

    async def initialize(self):
        """初始化所有代理"""
        print("🚀 正在初始化多代理系統...")

        try:
            # 從環境變數讀取配置
            azure_ai_endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
            model_deployment_name = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME")

            if not azure_ai_endpoint:
                raise ValueError(
                    "請在 .env 檔案中設置 AZURE_AI_AGENT_ENDPOINT\n"
                    f"範例: AZURE_AI_AGENT_ENDPOINT=https://foundry4i2v.services.ai.azure.com/api/projects/basic-project"
                )

            if not model_deployment_name:
                raise ValueError(
                    "請在 .env 檔案中設置 AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME\n"
                    f"範例: AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME=gpt-4.1"
                )

            print(f"📡 使用端點: {azure_ai_endpoint}")
            print(f"🤖 使用模型: {model_deployment_name}")

            async with DefaultAzureCredential() as creds:
                # 使用正確的參數創建客戶端
                self.client = AzureAIAgent.create_client(
                    credential=creds, endpoint=azure_ai_endpoint
                )
                await self.client.__aenter__()

                # 設置全域模型部署名稱
                self.model_deployment_name = model_deployment_name

                # 創建各個代理
                await self._create_master_agent()
                await self._create_web_searcher_agent()
                await self._create_translator_agent()
                await self._create_consultant_agent()
                await self._create_note_taker_agent()

        except Exception as e:
            error_msg = f"初始化失敗: {str(e)}"
            print(f"❌ {error_msg}")
            print("\n💡 請確保：")
            print("   1. 已創建 .env 檔案並設置以下變數：")
            print("      - AZURE_AI_AGENT_ENDPOINT")
            print("      - AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME")
            print("   2. 已使用 'az login' 登入 Azure CLI")
            print("   3. 您的帳戶有存取 Azure AI 資源的權限")
            raise

        print("✅ 多代理系統初始化完成！")

    async def _create_master_agent(self):
        """創建主代理 - 任務分派大師"""
        instructions = """你是任務分派大師（Orchestrator），負責智能任務路由。

你的職責是：
1. 分析使用者請求，判斷需要哪個專業代理處理
2. 對於複合任務，設計多步驟執行流程
3. 協調各代理間的工作流程

專業代理包括：
- web_searcher：網路搜尋大師 - 處理需要最新資訊、新聞、時事、市場趨勢的查詢
- translator：翻譯重寫大師 - 處理中英互譯、內容重寫優化
- consultant：專業顧問大師 - 提供技術、商業、產業三面向分析建議  
- note_taker：筆記大師 - 整理內容為 Markdown 筆記與心智圖格式

請根據使用者輸入，回應應該使用哪個代理，格式如下：
- 單一任務：{"agent": "agent_name", "task": "specific_task_description"}
- 複合任務：{"workflow": [{"agent": "agent1", "task": "task1"}, {"agent": "agent2", "task": "task2"}]}
- 無法判斷：{"response": "your_direct_response_or_clarification_question"}

只回應 JSON 格式，不要其他文字。"""

        definition = await self.client.agents.create_agent(
            model=self.model_deployment_name,
            name="MyTeam_MasterAgent",
            instructions=instructions,
        )

        self.agents[AgentType.MASTER] = AzureAIAgent(
            client=self.client,
            definition=definition,
        )
        print("✓ Master Agent 創建完成")

    async def _create_web_searcher_agent(self):
        """創建網路搜尋代理"""
        # 設置 Bing Grounding 工具
        try:
            # 使用環境變數中的 Bing 資源名稱（如果有設置）
            bing_resource_name = os.getenv("BING_RESOURCE_NAME", "mybingsearch")
            bing_connection = await self.client.connections.get(name=bing_resource_name)
            conn_id = bing_connection.id
            bing_grounding = BingGroundingTool(connection_id=conn_id)
            tools = bing_grounding.definitions
            print(f"✓ Bing 搜尋工具已連接 ({bing_resource_name})")
        except Exception as e:
            print(f"⚠️  Bing 連接設置失敗，將使用模擬搜尋: {e}")
            tools = None

        instructions = """你是網路搜尋大師，專門處理需要最新資訊的查詢。

你的能力：
- 即時網路搜尋與資訊收集
- 新聞時事、市場趨勢分析
- 產品資訊和技術動態追蹤
- 多來源資訊整合與去重

請使用 Bing 搜尋工具查找最新資訊，並提供：
1. 搜尋結果摘要
2. 關鍵資訊要點
3. 相關網址連結
4. 資訊可信度評估

如果無法使用搜尋工具，請說明你會如何搜尋並提供模擬結果。"""

        definition = await self.client.agents.create_agent(
            name="MyTeam_WebSearcher",
            instructions=instructions,
            model=self.model_deployment_name,
            tools=tools,
        )

        self.agents[AgentType.WEB_SEARCHER] = AzureAIAgent(
            client=self.client,
            definition=definition,
        )
        print("✓ Web Searcher Agent 創建完成")

    async def _create_translator_agent(self):
        """創建翻譯重寫代理"""
        instructions = """你是翻譯重寫大師，專精於語言轉換與內容優化。

對於每段輸入，請提供三種版本的翻譯：

1. **精簡翻譯**：保留核心意思，簡化表達
2. **完整翻譯**：語句通順，語意完整保留
3. **重點描述**：條列式重點摘要說明

技術特點：
- 自動識別輸入語言（中文/英文）
- 智能判斷翻譯方向
- 語境適應性調整
- 專業術語準確轉換

請按照以下格式輸出：
## 精簡翻譯
[精簡版本內容]

## 完整翻譯  
[完整版本內容]

## 重點描述
- [重點1]
- [重點2]
- [重點3]"""

        definition = await self.client.agents.create_agent(
            model=self.model_deployment_name,
            name="MyTeam_Translator",
            instructions=instructions,
        )

        self.agents[AgentType.TRANSLATOR] = AzureAIAgent(
            client=self.client,
            definition=definition,
        )
        print("✓ Translator Agent 創建完成")

    async def _create_consultant_agent(self):
        """創建專業顧問代理"""
        instructions = """你是專業顧問大師，提供多維度戰略分析。

對於每個問題，請從三個維度進行深度分析：

## 技術面分析
- 可行性評估
- 效能與擴展性
- 技術限制與風險
- 競爭優勢分析

## 商業面分析  
- 成本效益分析
- 營收模式設計
- 目標客群定位
- 市場定位策略
- 價值主張提煉

## 產業面分析
- 競爭對手分析
- 市場趨勢預測
- 合規法規要求
- 產業鏈生態分析

## 整體建議摘要
[基於三個面向的綜合建議，包含行動方案和風險緩解策略]

每個面向請用條列式呈現，最後提供整體建議摘要。"""

        definition = await self.client.agents.create_agent(
            model=self.model_deployment_name,
            name="MyTeam_Consultant",
            instructions=instructions,
        )

        self.agents[AgentType.CONSULTANT] = AzureAIAgent(
            client=self.client,
            definition=definition,
        )
        print("✓ Consultant Agent 創建完成")

    async def _create_note_taker_agent(self):
        """創建筆記整理代理"""
        instructions = """你是筆記大師，專精於知識整理與結構化。

請將輸入內容整理為兩種格式：

## Markdown 筆記
使用清晰的標題層次結構、有序的段落組織、便於閱讀的清單格式，支援後續編輯與引用。

## 心智圖說明
以階層式條列方式，展示邏輯結構與關鍵節點：
```
主題
├── 核心概念1
│   ├── 子概念1.1
│   └── 子概念1.2
├── 核心概念2
│   ├── 子概念2.1
│   └── 子概念2.2
└── 核心概念3
    └── 子概念3.1
```

技術特點：
- 使用繁體中文輸出
- 結構化資訊組織
- 知識點關聯分析
- 便於複習的格式設計

請確保內容結構清晰，支援知識記錄與後續複習使用。"""

        definition = await self.client.agents.create_agent(
            model=self.model_deployment_name,
            name="MyTeam_NoteTaker",
            instructions=instructions,
        )

        self.agents[AgentType.NOTE_TAKER] = AzureAIAgent(
            client=self.client,
            definition=definition,
        )
        print("✓ Note Taker Agent 創建完成")

    def _analyze_task_intent(self, user_input: str) -> dict:
        """分析用戶輸入的任務意圖（備用邏輯）"""
        user_input_lower = user_input.lower()

        # 關鍵詞匹配邏輯
        if any(
            keyword in user_input_lower
            for keyword in ["搜尋", "查詢", "最新", "新聞", "時事", "趨勢"]
        ):
            return {"agent": "web_searcher", "task": user_input}
        elif any(
            keyword in user_input_lower
            for keyword in ["翻譯", "翻成", "英文", "中文", "重寫"]
        ):
            return {"agent": "translator", "task": user_input}
        elif any(
            keyword in user_input_lower
            for keyword in ["分析", "評估", "建議", "可行性", "導入"]
        ):
            return {"agent": "consultant", "task": user_input}
        elif any(
            keyword in user_input_lower
            for keyword in ["整理", "筆記", "心智圖", "markdown"]
        ):
            return {"agent": "note_taker", "task": user_input}
        else:
            return {
                "response": "您好，我是任務分派大師。請告訴我您需要什麼協助？我可以安排專業代理處理搜尋、翻譯、分析或筆記整理等任務。"
            }

    async def _get_agent_response(self, agent_type: AgentType, message: str) -> str:
        """獲取指定代理的回應"""
        agent = self.agents[agent_type]

        # 為每個代理維護獨立的對話線程
        if agent_type not in self.threads:
            self.threads[agent_type] = None

        try:
            response = await agent.get_response(
                messages=message, thread=self.threads[agent_type]
            )

            # 更新線程
            self.threads[agent_type] = response.thread

            return str(response)

        except (ConnectionError, TimeoutError) as e:
            return f"❌ {agent_type.value} 處理時發生連線錯誤: {str(e)}"

    async def process_user_input(self, user_input: str) -> str:
        """處理用戶輸入"""
        print(f"\n📝 用戶輸入: {user_input}")
        print("🔄 正在分析任務...")

        # 記錄對話歷史
        self.conversation_history.append({"role": "user", "content": user_input})

        try:
            # 使用 Master Agent 進行任務分析
            master_response = await self._get_agent_response(
                AgentType.MASTER, user_input
            )

            # 解析 Master Agent 的回應
            try:
                # 嘗試解析 JSON
                task_analysis = json.loads(master_response)
            except json.JSONDecodeError:
                # 如果 JSON 解析失敗，使用備用邏輯
                print("⚠️  使用備用任務分析邏輯")
                task_analysis = self._analyze_task_intent(user_input)

            return await self._execute_task(task_analysis, user_input)

        except Exception as e:
            error_msg = f"❌ 處理用戶輸入時發生錯誤: {str(e)}"
            print(error_msg)
            return error_msg

    async def _execute_task(self, task_analysis: dict, original_input: str) -> str:
        """執行任務"""
        try:
            # 單一代理任務
            if "agent" in task_analysis:
                agent_name = task_analysis["agent"]
                task_desc = task_analysis.get("task", original_input)

                print(f"🎯 委派給: {agent_name}")

                agent_type = self._get_agent_type(agent_name)
                if agent_type:
                    result = await self._get_agent_response(agent_type, task_desc)
                    self.conversation_history.append(
                        {"role": "assistant", "content": result}
                    )
                    return result
                else:
                    return f"❌ 未找到代理: {agent_name}"

            # 複合工作流程
            elif "workflow" in task_analysis:
                print("🔄 執行複合工作流程...")
                results = []
                intermediate_result = original_input

                for step in task_analysis["workflow"]:
                    agent_name = step["agent"]
                    task_desc = step.get("task", intermediate_result)

                    print(f"📋 步驟: {agent_name} - {task_desc[:50]}...")

                    agent_type = self._get_agent_type(agent_name)
                    if agent_type:
                        step_result = await self._get_agent_response(
                            agent_type, task_desc
                        )
                        results.append(f"**{agent_name.title()} 結果:**\n{step_result}")
                        intermediate_result = step_result  # 將結果傳遞給下一個步驟
                    else:
                        results.append(f"❌ 未找到代理: {agent_name}")

                final_result = "\n\n---\n\n".join(results)
                self.conversation_history.append(
                    {"role": "assistant", "content": final_result}
                )
                return final_result

            # 直接回應
            elif "response" in task_analysis:
                response = task_analysis["response"]
                self.conversation_history.append(
                    {"role": "assistant", "content": response}
                )
                return response

            else:
                return "❌ 無法理解任務分析結果"

        except Exception as e:
            error_msg = f"❌ 執行任務時發生錯誤: {str(e)}"
            print(error_msg)
            return error_msg

    def _get_agent_type(self, agent_name: str) -> Optional[AgentType]:
        """根據代理名稱獲取代理類型"""
        agent_mapping = {
            "web_searcher": AgentType.WEB_SEARCHER,
            "translator": AgentType.TRANSLATOR,
            "consultant": AgentType.CONSULTANT,
            "note_taker": AgentType.NOTE_TAKER,
        }
        return agent_mapping.get(agent_name)

    async def cleanup(self):
        """清理資源"""
        print("\n🧹 清理資源...")

        try:
            await self._cleanup_threads()
            await self._cleanup_agents()
            await self._cleanup_client()
            print("✅ 資源清理完成")

        except Exception as e:
            print(f"❌ 清理過程中發生錯誤: {str(e)}")

    async def _cleanup_threads(self):
        """清理線程"""
        for thread in self.threads.values():
            if thread:
                try:
                    await thread.delete()
                except Exception as e:
                    print(f"⚠️  清理線程時發生錯誤: {e}")

    async def _cleanup_agents(self):
        """清理代理"""
        for agent in self.agents.values():
            if agent:
                try:
                    await self.client.agents.delete_agent(agent.id)
                except Exception as e:
                    print(f"⚠️  清理代理時發生錯誤: {e}")

    async def _cleanup_client(self):
        """關閉客戶端"""
        if self.client:
            try:
                await self.client.__aexit__(None, None, None)
            except Exception as e:
                print(f"⚠️  關閉客戶端時發生錯誤: {e}")


async def get_user_input() -> str:
    """獲取用戶輸入"""
    try:
        user_input = await asyncio.to_thread(
            input, "\n💬 請輸入您的需求 (或輸入 'exit' 退出): "
        )
        return user_input.strip()
    except (KeyboardInterrupt, EOFError):
        return "exit"


async def main():
    """主程序"""
    print("=" * 60)
    print("🤖 Connected Multi-Agent System")
    print("=" * 60)
    print("歡迎使用多代理協作系統！")
    print("\n系統包含以下專業代理：")
    print("🌐 網路搜尋大師 - 即時資訊查詢")
    print("✍️ 翻譯重寫大師 - 中英互譯與內容優化")
    print("🧩 專業顧問大師 - 技術商業產業分析")
    print("📝 筆記大師 - Markdown 筆記與心智圖")
    print("=" * 60)

    orchestrator = MultiAgentOrchestrator()

    try:
        # 初始化系統
        await orchestrator.initialize()

        # 互動循環
        while True:
            user_input = await get_user_input()

            if user_input.lower() in ["exit", "quit", "退出", "結束"]:
                print("👋 感謝使用，再見！")
                break

            if not user_input:
                print("⚠️  請輸入有效內容")
                continue

            # 處理用戶請求
            print("\n" + "=" * 60)
            response = await orchestrator.process_user_input(user_input)
            print("\n🤖 系統回應:")
            print("=" * 60)
            print(response)
            print("=" * 60)

    except Exception as e:
        print(f"❌ 系統運行時發生錯誤: {str(e)}")
        import traceback

        print(f"詳細錯誤信息: {traceback.format_exc()}")

    finally:
        # 清理資源
        await orchestrator.cleanup()


if __name__ == "__main__":
    print("🚀 啟動多代理協作系統...")
    asyncio.run(main())
