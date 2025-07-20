# 題目：多功能學習助理

## 練習目標

建立整合多種功能的 Azure AI Agent 學習助理，結合檔案搜尋、程式碼執行和學習追蹤功能

## 核心功能

1. **檔案搜尋**：從上傳的教材文件中搜尋並回答程式設計問題
2. **程式碼執行**：執行 Python 程式碼並提供詳細解釋
3. **學習追蹤**：記錄學習活動、生成進度報告、提供個人化建議

## 技術架構
### 混合式架構（推薦）
- 使用 step5 的工具建立方式：`FileSearchTool` + `CodeInterpreterTool`
- 結合 step8 的外掛系統：自訂 `LearningTrackingPlugin`
- 優點：穩定可靠，避免 YAML 解析問題

## 實作重點

### 1. 學習追蹤外掛
```python
class LearningTrackingPlugin:
    @kernel_function
    def record_learning_activity(self, topic: str, activity_type: str, duration_minutes: int = 30)
    
    @kernel_function  
    def get_progress_report(self) -> str
    
    @kernel_function
    def get_recommendations(self) -> str
```

### 2. 檔案上傳與向量儲存
```python
# 使用 step5 的檔案上傳方式
file_info = await client.agents.files.upload_and_poll(file_path, purpose="assistants")
vector_store = await client.agents.vector_stores.create_and_poll(file_ids, name="教材")
```

### 3. Agent 建立
```python
# 建立工具
file_search_tool = FileSearchTool(vector_store_ids=[vector_store.id])
code_interpreter_tool = CodeInterpreterTool()

# 建立 agent
agent_definition = await client.agents.create_agent(
    model=AzureAIAgentSettings().model_deployment_name,
    tools=tools,
    tool_resources=tool_resources,
)

# 結合 Kernel 外掛
agent = AzureAIAgent(client=client, definition=agent_definition, kernel=kernel)
```

## 測試案例

```python
TEST_CONVERSATIONS = [
    "你好！我想開始學習 Python 程式設計",
    "請解釋 Python 中的 for 迴圈是什麼？",
    "請執行這段程式碼並解釋結果：\nfor i in range(3):\n    print(f'Hello {i}')",
    "請記錄我今天學習了 Python 基礎語法，這是閱讀活動，花了 45 分鐘",
    "請給我一份學習進度報告",
    "根據我的學習情況，給我一些建議",
]
```

## 關鍵技巧

1. **檔案管理**：教材存放在 `learning_materials/` 目錄
2. **資料持久化**：學習記錄保存為 `learning_progress.json`
3. **錯誤處理**：完整的 try-catch 和資源清理
4. **工具整合**：智慧選擇適當工具回應用戶需求

## 參考範例

- `step5_azure_ai_agent_file_search.py` - 檔案搜尋實作
- `step8_azure_ai_agent_declarative.py` - 宣告式 Agent 和外掛整合
- `step4_azure_ai_agent_code_interpreter.py` - 程式碼執行功能



開始前請確保您的 `.env` 設定正確，並參考相關範例程式碼！