# Copyright (c) Microsoft. All rights reserved.
# filepath: azure_ai_agent_lab_task_sol.py

import asyncio
import json
import os
from datetime import datetime
from typing import Annotated, Dict, List

from azure.ai.agents.models import CodeInterpreterTool, FileSearchTool, FilePurpose
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import (
    AzureAIAgent,
    AzureAIAgentSettings,
    AzureAIAgentThread,
    AgentRegistry,
)
from semantic_kernel.contents import AuthorRole
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel import Kernel

"""
題目：多功能學習助理 - 完整解答
整合檔案搜尋、程式碼解讀和學習追蹤功能的 Azure AI Agent
使用 step5 的檔案上傳方式和 step8 的宣告式定義方式
"""


class LearningTrackingPlugin:
    """學習進度追蹤外掛程式"""

    def __init__(self):
        self.learning_data_file = "learning_progress.json"
        self.learning_records = self._load_learning_data()

    def _load_learning_data(self) -> List[Dict]:
        """載入學習資料"""
        if os.path.exists(self.learning_data_file):
            try:
                with open(self.learning_data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_learning_data(self):
        """儲存學習資料"""
        with open(self.learning_data_file, "w", encoding="utf-8") as f:
            json.dump(self.learning_records, f, ensure_ascii=False, indent=2)

    @kernel_function(description="記錄學員的學習活動")
    def record_learning_activity(
        self,
        topic: Annotated[str, "學習主題"],
        activity_type: Annotated[str, "活動類型（如：閱讀、程式碼練習、問題解答）"],
        duration_minutes: Annotated[int, "學習時間（分鐘）"] = 30,
    ) -> Annotated[str, "記錄結果訊息"]:
        """記錄學習活動"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "topic": topic,
            "activity_type": activity_type,
            "duration_minutes": duration_minutes,
            "date": datetime.now().strftime("%Y-%m-%d"),
        }

        self.learning_records.append(record)
        self._save_learning_data()

        return f"✅ 已記錄學習活動：{topic} ({activity_type}) - {duration_minutes} 分鐘"

    @kernel_function(description="產生學習進度報告")
    def get_progress_report(self) -> Annotated[str, "學習進度報告"]:
        """產生學習進度報告"""
        if not self.learning_records:
            return "📊 尚未有學習記錄。開始您的學習之旅吧！"

        # 統計資料
        total_time = sum(record["duration_minutes"] for record in self.learning_records)
        total_sessions = len(self.learning_records)
        topics = set(record["topic"] for record in self.learning_records)
        activity_types = {}

        for record in self.learning_records:
            activity_type = record["activity_type"]
            activity_types[activity_type] = activity_types.get(activity_type, 0) + 1

        # 最近學習活動
        recent_record = max(self.learning_records, key=lambda x: x["timestamp"])

        report = f"""📊 學習進度報告
        
📈 總體統計：
• 總學習時間：{total_time} 分鐘 ({total_time/60:.1f} 小時)
• 學習場次：{total_sessions} 次
• 涵蓋主題：{len(topics)} 個

🎯 學習主題：
{chr(10).join(f"• {topic}" for topic in sorted(topics))}

🎮 活動類型分布：
{chr(10).join(f"• {activity}: {count} 次" for activity, count in activity_types.items())}

🕒 最近學習：
• 主題：{recent_record['topic']}
• 時間：{recent_record['date']}
• 活動：{recent_record['activity_type']}
"""
        return report

    @kernel_function(description="提供個人化學習建議")
    def get_recommendations(self) -> Annotated[str, "學習建議"]:
        """提供個人化學習建議"""
        if not self.learning_records:
            return """💡 學習建議：
            
🚀 開始您的程式學習之旅：
1. 先從 Python 基礎語法開始
2. 多動手練習程式碼
3. 定期復習學過的內容
4. 建立學習習慣，每天至少 30 分鐘
"""

        # 分析學習模式
        topics = [record["topic"] for record in self.learning_records]
        recent_topics = [
            record["topic"] for record in self.learning_records[-5:]
        ]  # 最近5次
        total_time = sum(record["duration_minutes"] for record in self.learning_records)
        avg_session_time = total_time / len(self.learning_records)

        recommendations = ["💡 個人化學習建議：\n"]

        # 學習時間建議
        if avg_session_time < 30:
            recommendations.append("⏰ 建議延長每次學習時間到30-45分鐘，提高學習效率")
        elif avg_session_time > 90:
            recommendations.append("⏰ 學習時間很充足！可以考慮分段學習，避免疲勞")

        # 主題多樣性建議
        unique_topics = set(topics)
        if len(unique_topics) < 3:
            recommendations.append("📚 建議擴展學習主題，嘗試不同的程式設計概念")

        # 復習建議
        if len(recent_topics) > 0:
            most_recent_topic = recent_topics[-1]
            recommendations.append(
                f"🔄 建議復習「{most_recent_topic}」相關內容，鞏固學習成果"
            )

        # 進階建議
        if len(self.learning_records) >= 10:
            recommendations.append("🎯 學習記錄豐富！可以開始嘗試實際項目練習")

        recommendations.append("\n🌟 下一步建議：")
        recommendations.append("1. 選擇一個感興趣的小專案")
        recommendations.append("2. 結合理論學習和實際練習")
        recommendations.append("3. 加入程式社群，與其他學習者交流")

        return "\n".join(recommendations)


async def upload_learning_materials(client) -> tuple[List[str], List[str]]:
    """上傳學習教材檔案 - 使用 step5 的方式"""
    uploaded_file_ids = []
    vector_store_ids = []
    materials_dir = "learning_materials"

    # 建立教材資料夾（如果不存在）
    os.makedirs(materials_dir, exist_ok=True)

    # 建立範例教材檔案
    sample_materials = {
        "python_basics.txt": """Python 基礎教學

1. 變數與資料型別
Python 中的變數不需要宣告型別，直接賦值即可：
- 字串：name = "Alice"
- 整數：age = 25
- 浮點數：height = 175.5
- 布林值：is_student = True

2. 控制結構
# 條件判斷
if age >= 18:
    print("成年人")
else:
    print("未成年")

# 迴圈
for i in range(5):
    print(f"數字：{i}")

3. 函數定義
def greet(name):
    return f"Hello, {name}!"

4. 串列操作
numbers = [1, 2, 3, 4, 5]
squares = [x**2 for x in numbers]
""",
        "python_advanced.txt": """Python 進階概念

1. 物件導向程式設計
class Student:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def study(self, subject):
        return f"{self.name} 正在學習 {subject}"

2. 例外處理
try:
    result = 10 / 0
except ZeroDivisionError:
    print("不能除以零")
finally:
    print("程式結束")

3. 檔案操作
with open("file.txt", "r") as f:
    content = f.read()

4. 模組與套件
import math
from datetime import datetime
""",
        "coding_exercises.txt": """程式練習題

練習1：計算器
def calculator(a, b, operation):
    if operation == "+":
        return a + b
    elif operation == "-":
        return a - b
    elif operation == "*":
        return a * b
    elif operation == "/":
        return a / b if b != 0 else "錯誤：除數不能為零"

練習2：質數檢查
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

練習3：費波納契數列
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
""",
    }

    # 建立並上傳教材檔案 - 使用 step5 的方法
    for filename, content in sample_materials.items():
        file_path = os.path.join(materials_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        try:
            # 使用 step5 的檔案上傳方式
            file_info = await client.agents.files.upload_and_poll(
                file_path=file_path, purpose="assistants"
            )
            uploaded_file_ids.append(file_info.id)
            print(f"✅ 已上傳：{filename} (ID: {file_info.id})")
        except Exception as e:
            print(f"❌ 上傳 {filename} 失敗：{e}")

    # 如果有成功上傳的檔案，建立向量儲存
    if uploaded_file_ids:
        try:
            vector_store = await client.agents.vector_stores.create_and_poll(
                file_ids=uploaded_file_ids, name="程式學習教材"
            )
            vector_store_ids.append(vector_store.id)
            print(f"✅ 已建立向量儲存：{vector_store.id}")
        except Exception as e:
            print(f"❌ 建立向量儲存失敗：{e}")

    return uploaded_file_ids, vector_store_ids


# 宣告式 YAML 規格 - 使用 step8 的方式
def create_agent_spec(vector_store_ids: List[str], file_ids: List[str]) -> str:
    """建立 agent 的 YAML 規格"""

    # 基本工具配置
    tools = [
        "- id: LearningTrackingPlugin.record_learning_activity\n    type: function",
        "- id: LearningTrackingPlugin.get_progress_report\n    type: function",
        "- id: LearningTrackingPlugin.get_recommendations\n    type: function",
        "- type: code_interpreter",
    ]

    # 如果有向量儲存，加入檔案搜尋工具（包含 vector_store_ids）
    if vector_store_ids:
        file_search_tool = (
            f"- type: file_search\n    vector_store_ids: {vector_store_ids}"
        )
        tools.insert(-1, file_search_tool)

    tools_yaml = "\n  ".join(tools)

    # 建立完整的 YAML 規格
    spec = f"""type: foundry_agent
name: AI_Programming_Tutor
instructions: |
  你是一個專業的程式學習助理，名稱是「AI 程式導師」。

  🎯 你的任務：
  1. 協助學員學習程式設計，特別是 Python
  2. 從教學文件中搜尋答案回答問題
  3. 執行和解釋程式碼範例
  4. 追蹤學員的學習進度

  💡 工作原則：
  - 提供清晰、易懂的解釋
  - 鼓勵動手實作
  - 根據學員程度調整教學方式
  - 主動提供學習建議

  🛠️ 可用工具：
  - 檔案搜尋：查找教材中的相關資訊
  - 程式碼執行：運行 Python 程式並解釋結果
  - 學習追蹤：記錄和分析學習進度

  請以友善、耐心的方式與學員互動，讓學習變得有趣且有效！
model:
  id: ${{AzureAI:ChatModelId}}
tools:
  {tools_yaml}"""

    return spec


async def create_learning_assistant(
    client, file_ids: List[str], vector_store_ids: List[str]
) -> AzureAIAgent:
    """建立多功能學習助理 - 混合使用 step5 的工具建立方式和 step8 的外掛方式"""

    # 1. 建立 Kernel 實例並加入外掛
    kernel = Kernel()
    kernel.add_plugin(LearningTrackingPlugin(), "LearningTrackingPlugin")

    # 2. 建立工具列表 - 使用 step5 的方式
    tools = []
    tool_resources = {}

    # 檔案搜尋工具（如果有向量儲存）
    if vector_store_ids:
        file_search_tool = FileSearchTool(vector_store_ids=vector_store_ids)
        tools.extend(file_search_tool.definitions)
        tool_resources.update(file_search_tool.resources)

    # 程式碼解讀器工具（如果有檔案）
    if file_ids:
        code_interpreter_tool = CodeInterpreterTool()
        tools.extend(code_interpreter_tool.definitions)
        tool_resources["code_interpreter"] = {"file_ids": file_ids[:20]}

    # 3. 建立 agent definition - 使用 step5 的方式
    agent_definition = await client.agents.create_agent(
        model=AzureAIAgentSettings().model_deployment_name,
        name="AI_Programming_Tutor",
        instructions="""你是一個專業的程式學習助理，名稱是「AI 程式導師」。

🎯 你的任務：
1. 協助學員學習程式設計，特別是 Python
2. 從教學文件中搜尋答案回答問題
3. 執行和解釋程式碼範例
4. 追蹤學員的學習進度

💡 工作原則：
- 提供清晰、易懂的解釋
- 鼓勵動手實作
- 根據學員程度調整教學方式
- 主動提供學習建議

🛠️ 可用工具：
- 檔案搜尋：查找教材中的相關資訊
- 程式碼執行：運行 Python 程式並解釋結果
- 學習追蹤：記錄和分析學習進度

請以友善、耐心的方式與學員互動，讓學習變得有趣且有效！""",
        tools=tools,
        tool_resources=tool_resources,
    )

    # 4. 建立 Semantic Kernel agent
    agent = AzureAIAgent(
        client=client,
        definition=agent_definition,
        kernel=kernel,  # 加入包含外掛的 kernel
    )

    print("✅ 已成功建立學習助理（使用混合方式）")
    return agent


# 測試對話
TEST_CONVERSATIONS = [
    "你好！我想開始學習 Python 程式設計",
    "請解釋 Python 中的 for 迴圈是什麼？",
    "請執行這段程式碼並解釋結果：\nfor i in range(3):\n    print(f'Hello {i}')",
    "請記錄我今天學習了 Python 基礎語法，這是閱讀活動，花了 45 分鐘",
    "我剛才做了程式碼練習，學習 Python 函數，花了 30 分鐘，請記錄",
    "請給我一份學習進度報告",
    "根據我的學習情況，給我一些建議",
]


async def main() -> None:
    """主程式"""
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        agent = None
        thread = None
        vector_store_ids = []
        file_ids = []

        try:
            # 1. 上傳學習教材 - 使用 step5 方式
            print("🔄 正在上傳學習教材...")
            file_ids, vector_store_ids = await upload_learning_materials(client)
            print(
                f"✅ 已上傳 {len(file_ids)} 個教材檔案，建立 {len(vector_store_ids)} 個向量儲存\n"
            )

            # 2. 建立學習助理 - 使用 step8 宣告式方式
            print("🔄 正在建立學習助理...")
            agent = await create_learning_assistant(client, file_ids, vector_store_ids)
            print("✅ 學習助理建立成功！\n")

            print("=" * 60)
            print("🎓 歡迎使用 AI 程式導師！")
            print("=" * 60)

            # 3. 開始對話測試
            for i, user_input in enumerate(TEST_CONVERSATIONS, 1):
                print(f"\n💬 對話 {i}")
                print("-" * 40)
                print(f"👨‍🎓 學員: {user_input}")
                print("🤖 AI導師: ", end="")

                try:
                    # 與 agent 對話
                    response_parts = []
                    async for response in agent.invoke(
                        messages=user_input,
                        thread=thread,
                    ):
                        if response.role != AuthorRole.TOOL:  # 過濾工具回應
                            response_parts.append(str(response))
                        thread = response.thread

                    full_response = "".join(response_parts)
                    print(full_response)

                except Exception as e:
                    print(f"❌ 對話錯誤: {e}")

                # 在某些對話間加入暫停
                if i in [2, 4]:
                    await asyncio.sleep(1)

            print("\n" + "=" * 60)
            print("🎉 測試完成！學習助理運作正常")
            print("=" * 60)

        except Exception as e:
            print(f"❌ 程式執行錯誤: {e}")
            import traceback

            traceback.print_exc()

        finally:
            # 清理資源 - 使用 step5 的方式
            if thread:
                try:
                    await thread.delete()
                    print("✅ 已清理對話執行緒")
                except:
                    pass

            # 清理向量儲存
            for vector_store_id in vector_store_ids:
                try:
                    await client.agents.vector_stores.delete(vector_store_id)
                    print(f"✅ 已清理向量儲存：{vector_store_id}")
                except:
                    pass

            # 清理檔案
            for file_id in file_ids:
                try:
                    await client.agents.files.delete(file_id)
                    print(f"✅ 已清理檔案：{file_id}")
                except:
                    pass

            # 清理 agent
            if agent:
                try:
                    await client.agents.delete_agent(agent.id)
                    print("✅ 已清理學習助理")
                except:
                    pass


if __name__ == "__main__":
    asyncio.run(main())
