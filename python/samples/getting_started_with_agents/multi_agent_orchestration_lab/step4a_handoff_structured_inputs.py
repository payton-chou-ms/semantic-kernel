# Copyright (c) Microsoft. All rights reserved.

import asyncio
from enum import Enum

from pydantic import BaseModel

from semantic_kernel.agents import Agent, ChatCompletionAgent, HandoffOrchestration, OrchestrationHandoffs
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import AuthorRole, ChatMessageContent
from semantic_kernel.functions import kernel_function

"""
以下範例示範如何建立可根據 GitHub 問題內容進行分流的移交編排。
編排由 3 個代理程式組成，每個都專精於不同領域。

編排的輸入不再是字串或聊天訊息，而是 Pydantic 模型
（即結構化輸入）。模型會在傳遞給代理程式之前轉換為聊天訊息。
這使編排變得更靈活且更容易重複使用。

此範例示範建立和啟動運行時、建立移交編排、
呼叫編排，以及最後等待結果的基本步驟。
"""


class GitHubLabels(Enum):
    """代表 GitHub 標籤的列舉。"""

    PYTHON = "python"
    DOTNET = ".NET"
    BUG = "bug"
    ENHANCEMENT = "enhancement"
    QUESTION = "question"
    VECTORSTORE = "vectorstore"
    AGENT = "agent"


class GithubIssue(BaseModel):
    """代表 GitHub 問題的模型。"""

    id: str
    title: str
    body: str
    labels: list[str] = []


class Plan(BaseModel):
    """代表解決 GitHub 問題計劃的模型。"""

    tasks: list[str]


class GithubPlugin:
    """GitHub 相關操作的外掛。"""

    @kernel_function
    async def add_labels(self, issue_id: str, labels: list[GitHubLabels]) -> None:
        """為 GitHub 問題新增標籤。"""
        await asyncio.sleep(1)  # 模擬網路延遲
        print(f"正在為問題 {issue_id} 新增標籤 {labels}")

    @kernel_function(description="建立解決問題的計劃。")
    async def create_plan(self, issue_id: str, plan: Plan) -> None:
        """為 GitHub 問題建立任務。"""
        await asyncio.sleep(1)  # 模擬網路延遲
        print(f"正在為問題 {issue_id} 建立計劃，任務：\n{plan.model_dump_json(indent=2)}")


def get_agents() -> tuple[list[Agent], OrchestrationHandoffs]:
    """回傳將參與移交編排的代理程式清單和移交關係。

    您可以自由新增或移除代理程式和移交連線。
    """
    triage_agent = ChatCompletionAgent(
        name="TriageAgent",
        description="分流 GitHub 問題的代理程式",
        instructions="給定一個 GitHub 問題，進行分流。",
        service=AzureChatCompletion(),
    )
    python_agent = ChatCompletionAgent(
        name="PythonAgent",
        description="處理 Python 相關問題的代理程式",
        instructions="您是處理 Python 相關 GitHub 問題的代理程式。",
        service=AzureChatCompletion(),
        plugins=[GithubPlugin()],
    )
    dotnet_agent = ChatCompletionAgent(
        name="DotNetAgent",
        description="處理 .NET 相關問題的代理程式",
        instructions="您是處理 .NET 相關 GitHub 問題的代理程式。",
        service=AzureChatCompletion(),
        plugins=[GithubPlugin()],
    )

    # 定義代理程式之間的移交關係
    handoffs = {
        triage_agent.name: {
            python_agent.name: "如果問題與 Python 相關，轉移到此代理程式",
            dotnet_agent.name: "如果問題與 .NET 相關，轉移到此代理程式",
        },
    }

    return [triage_agent, python_agent, dotnet_agent], handoffs


GithubIssueSample = GithubIssue(
    id="12345",
    title=(
        "Bug: SQLite Error 1: 'ambiguous column name:' when including VectorStoreRecordKey in "
        "VectorSearchOptions.Filter"
    ),
    body=(
        "Describe the bug"
        "When using column names marked as [VectorStoreRecordData(IsFilterable = true)] in "
        "VectorSearchOptions.Filter, the query runs correctly."
        "However, using the column name marked as [VectorStoreRecordKey] in VectorSearchOptions.Filter, the query "
        "throws exception 'SQLite Error 1: ambiguous column name: StartUTC"
        ""
        "To Reproduce"
        "Add a filter for the column marked [VectorStoreRecordKey]. Since that same column exists in both the "
        "vec_TestTable and TestTable, the data for both columns cannot be returned."
        ""
        "Expected behavior"
        "The query should explicitly list the vec_TestTable column names to retrieve and should omit the "
        "[VectorStoreRecordKey] column since it will be included in the primary TestTable columns."
        ""
        "Platform"
        ""
        "Microsoft.SemanticKernel.Connectors.Sqlite v1.46.0-preview"
        "Additional context"
        "Normal DBContext logging shows only normal context queries. Queries run by VectorizedSearchAsync() don't "
        "appear in those logs and I could not find a way to enable logging in semantic search so that I could "
        "actually see the exact query that is failing. It would have been very useful to see the failing semantic "
        "query."
    ),
    labels=[],
)


# 預設的輸入轉換會嘗試使用 `json.dump()` 將物件序列化為字串。
# 然而，Pydantic 模型類型的物件無法直接由 `json.dump()` 序列化。
# 因此，我們需要自訂轉換。
def custom_input_transform(input_message: GithubIssue) -> ChatMessageContent:
    return ChatMessageContent(role=AuthorRole.USER, content=input_message.model_dump_json())


async def main():
    """執行代理程式的主要函數。"""
    # 1. 建立具有多個代理程式和自訂輸入轉換的移交編排。
    # 要啟用結構化輸入，您必須指定輸入轉換和編排的泛型類型，
    agents, handoffs = get_agents()
    handoff_orchestration = HandoffOrchestration[GithubIssue, ChatMessageContent](
        members=agents,
        handoffs=handoffs,
        input_transform=custom_input_transform,
    )

    # 2. 建立運行時並啟動
    runtime = InProcessRuntime()
    runtime.start()

    # 3. 使用任務和運行時呼叫編排
    orchestration_result = await handoff_orchestration.invoke(
        task=GithubIssueSample,
        runtime=runtime,
    )

    # 4. 等待結果
    value = await orchestration_result.get(timeout=100)
    print(value)

    # 5. 閒置時停止運行時
    await runtime.stop_when_idle()

    """
    範例輸出：
    正在為問題 12345 新增標籤 [<GitHubLabels.BUG: 'bug'>, <GitHubLabels.DOTNET: '.NET'>, <GitHubLabels.VECTORSTORE: 'vectorstore'>]
    正在為問題 12345 建立計劃，任務：
    {
    "tasks": [
        "調查問題以確認在篩選器中使用 VectorStoreRecordKey 時 SQL 查詢的歧義性。",
        "修改查詢生成邏輯以明確列出 vec_TestTable 的欄位名稱並防止歧義。",
        "測試解決方案以確保 VectorStoreRecordKey 可以在篩選器中使用而不會造成 SQLite 錯誤。",
        "更新文件以提供在篩選器中使用 VectorStoreRecordKey 的指引，避免類似問題。",
        "考慮增加日誌記錄功能來追蹤語意搜尋查詢，以便將來更容易除錯。"
    ]
    }
    任務已完成，摘要：未提供移交代理程式名稱且未設定人類回應函數。結束任務。
    """


if __name__ == "__main__":
    asyncio.run(main())
