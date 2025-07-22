# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
import logging
import os
from dotenv import load_dotenv
from typing import List

from pydantic import BaseModel

from semantic_kernel import Kernel
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.functions import KernelArguments

# Load environment variables from .env file
load_dotenv()

# Constants
MY_AZURE_OPENAI_ENDPOINT = os.getenv("MY_AZURE_OPENAI_ENDPOINT")

"""
技術問題解決中心
結合結構化輸出、群組聊天和日誌記錄。技術專家、測試工程師和文檔撰寫員團隊合作解決程式問題，
輸出包含解決步驟、測試案例和文檔的結構化結果。

此範例展示如何：
1. 使用群組聊天進行多代理協作 (Step 6)
2. 使用核心函數策略控制對話流程 (Step 7)
3. 使用 JSON 結果進行結構化輸出 (Step 8)
4. 啟用詳細的日誌記錄 (Step 9)
5. 使用結構化輸出格式化最終結果 (Step 10)
"""

# 啟用詳細日誌記錄
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


# 定義結構化輸出模型
class TestCase(BaseModel):
    """測試案例模型"""

    test_name: str
    test_description: str
    expected_result: str
    test_code: str


class SolutionStep(BaseModel):
    """解決步驟模型"""

    step_number: int
    description: str
    code_example: str
    explanation: str


class Documentation(BaseModel):
    """文檔模型"""

    section: str
    content: str
    code_snippets: List[str]


class TechnicalSolutionReport(BaseModel):
    """技術解決方案報告"""

    problem_summary: str
    solution_steps: List[SolutionStep]
    test_cases: List[TestCase]
    documentation: List[Documentation]
    final_recommendation: str
    quality_score: int


class ProblemAnalysis(BaseModel):
    """問題分析結果"""

    problem_type: str
    complexity_level: str
    estimated_solution_time: str
    required_expertise: List[str]


class SolutionCompletionStrategy(TerminationStrategy):
    """自定義終止策略 - 當所有專家完成工作時終止"""

    agents: List = []
    required_keywords: List[str] = ["解決方案完成", "測試完成", "文檔完成"]

    def __init__(self, agents, maximum_iterations: int = 15, **data):
        super().__init__(maximum_iterations=maximum_iterations, **data)
        self.agents = agents

    async def should_agent_terminate(self, agent, history):
        """檢查是否應該終止"""
        if len(history) < 3:  # 至少需要三輪對話
            return False

        # 檢查最近的訊息是否包含完成關鍵字
        recent_messages = [msg.content.lower() for msg in history[-3:]]
        completed_tasks = sum(
            1
            for keyword in self.required_keywords
            if any(keyword in msg for msg in recent_messages)
        )

        return completed_tasks >= 2 or await super().should_agent_terminate(
            agent, history
        )


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    """建立具有聊天完成服務的 Kernel"""
    kernel = Kernel()
    kernel.add_service(
        AzureChatCompletion(endpoint=MY_AZURE_OPENAI_ENDPOINT, service_id=service_id)
    )
    return kernel


# 代理角色定義
TECHNICAL_EXPERT_NAME = "TechnicalExpert"
TECHNICAL_EXPERT_INSTRUCTIONS = """
你是一位資深技術專家，專精於程式問題診斷和解決方案設計。
你的職責：
1. 分析技術問題的根本原因
2. 提供詳細的解決步驟和程式碼範例
3. 評估解決方案的可行性和效能影響
4. 當你完成分析和解決方案時，請在回應中包含「解決方案完成」

請保持技術準確性，並提供實用的解決方案。
使用繁體中文回應。
"""

TEST_ENGINEER_NAME = "TestEngineer"
TEST_ENGINEER_INSTRUCTIONS = """
你是一位經驗豐富的測試工程師，專門設計測試案例和驗證解決方案。
你的職責：
1. 根據技術專家提供的解決方案設計測試案例
2. 撰寫測試程式碼和驗證邏輯
3. 評估測試覆蓋率和品質保證策略
4. 當你完成測試案例設計時，請在回應中包含「測試完成」

請確保測試案例全面且實用。
使用繁體中文回應。
"""

DOCUMENTATION_WRITER_NAME = "DocumentationWriter"
DOCUMENTATION_WRITER_INSTRUCTIONS = """
你是一位專業的技術文檔撰寫員，負責將技術解決方案整理成清晰的文檔。
你的職責：
1. 整理技術專家和測試工程師的工作成果
2. 撰寫使用指南、API 文檔和最佳實務
3. 確保文檔的可讀性和完整性
4. 當你完成文檔撰寫時，請在回應中包含「文檔完成」

請確保文檔清晰易懂，適合不同技術水平的讀者。
使用繁體中文回應。
"""

# 模擬的技術問題
TECHNICAL_PROBLEMS = [
    "Python 程式在處理大型 CSV 檔案時記憶體使用量過高，如何最佳化？",
    "React 應用程式載入速度慢，首屏渲染時間超過 3 秒，需要效能最佳化方案。",
    "資料庫查詢效能問題，複雜 JOIN 查詢執行時間過長，影響使用者體驗。",
]


async def create_structured_report(group_chat, problem: str) -> TechnicalSolutionReport:
    """從群組聊天歷史創建結構化報告"""

    # 建立用於結構化輸出的代理
    settings = AzureChatPromptExecutionSettings()
    settings.response_format = TechnicalSolutionReport

    report_agent = ChatCompletionAgent(
        service=AzureChatCompletion(endpoint=MY_AZURE_OPENAI_ENDPOINT),
        name="ReportGenerator",
        instructions=f"""
        根據以下技術問題解決過程，生成結構化的技術解決方案報告。
        
        原始問題：{problem}
        
        請仔細分析對話歷史，提取：
        1. 解決步驟（包含程式碼範例）
        2. 測試案例（包含測試程式碼）
        3. 文檔內容
        4. 最終建議
        5. 品質評分（1-100）
        
        確保所有內容都是繁體中文。
        """,
        arguments=KernelArguments(settings=settings),
    )

    # 取得對話歷史
    chat_history = []
    async for message in group_chat.get_chat_messages():
        chat_history.append(f"{message.name}: {message.content}")

    history_text = "\n".join(chat_history)

    # 生成結構化報告
    response = await report_agent.get_response(
        messages=f"對話歷史：\n{history_text}\n\n請生成結構化報告。"
    )

    # 解析並回傳結構化結果
    report_data = json.loads(response.message.content)
    return TechnicalSolutionReport.model_validate(report_data)


async def main():
    """主程式"""
    print("🔧 技術問題解決中心啟動")
    print("=" * 50)

    # 1. 創建三個專業代理
    technical_expert = ChatCompletionAgent(
        kernel=_create_kernel_with_chat_completion("technical_expert"),
        name=TECHNICAL_EXPERT_NAME,
        instructions=TECHNICAL_EXPERT_INSTRUCTIONS,
    )

    test_engineer = ChatCompletionAgent(
        kernel=_create_kernel_with_chat_completion("test_engineer"),
        name=TEST_ENGINEER_NAME,
        instructions=TEST_ENGINEER_INSTRUCTIONS,
    )

    documentation_writer = ChatCompletionAgent(
        kernel=_create_kernel_with_chat_completion("documentation_writer"),
        name=DOCUMENTATION_WRITER_NAME,
        instructions=DOCUMENTATION_WRITER_INSTRUCTIONS,
    )

    # 2. 建立群組聊天
    group_chat = AgentGroupChat(
        agents=[technical_expert, test_engineer, documentation_writer],
        termination_strategy=SolutionCompletionStrategy(
            agents=[technical_expert, test_engineer, documentation_writer],
            maximum_iterations=15,
        ),
    )

    # 3. 處理技術問題
    for i, problem in enumerate(TECHNICAL_PROBLEMS, 1):
        print(f"\n📋 處理問題 {i}: {problem}")
        print("-" * 50)

        # 添加問題到群組聊天
        await group_chat.add_chat_message(message=problem)

        # 執行群組討論
        print("🗣️  專家團隊討論中...")
        async for content in group_chat.invoke():
            print(f"💬 {content.name}: {content.content[:200]}...")

        # 生成結構化報告
        print("\n📊 生成結構化報告...")
        try:
            report = await create_structured_report(group_chat, problem)
            print(f"✅ 報告生成完成！品質評分: {report.quality_score}/100")
            print(f"📝 解決方案步驟數: {len(report.solution_steps)}")
            print(f"🧪 測試案例數: {len(report.test_cases)}")
            print(f"📚 文檔章節數: {len(report.documentation)}")

            # 顯示詳細報告（可選）
            print(f"\n📋 問題摘要: {report.problem_summary}")
            print(f"💡 最終建議: {report.final_recommendation}")

        except Exception as e:
            print(f"❌ 報告生成失敗: {str(e)}")

        print("\n" + "=" * 50)

        # 清理聊天歷史以處理下一個問題
        # 注意: 實際使用時可能需要根據 API 調整清理方式
        group_chat = AgentGroupChat(
            agents=[technical_expert, test_engineer, documentation_writer],
            termination_strategy=SolutionCompletionStrategy(
                agents=[technical_expert, test_engineer, documentation_writer],
                maximum_iterations=15,
            ),
        )

    print("🎉 技術問題解決中心任務完成！")


if __name__ == "__main__":
    asyncio.run(main())
