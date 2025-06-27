# Step2 系列功能差異比較

本文檔比較 `step2_sequential.py`、`step2a_sequential_cancellation_token.py` 和 `step2b_sequential_streaming_agent_response_callback.py` 三個文件的功能差異。

## 📊 功能差異比較表

| 功能特點     | **step2_sequential.py**   | **step2a_sequential_cancellation_token.py** | **step2b_sequential_streaming_agent_response_callback.py** |
| ------------ | ------------------------- | ------------------------------------------- | ---------------------------------------------------------- |
| **核心功能** | 基本順序編排              | 順序編排 + 取消機制                         | 順序編排 + 串流回調                                        |
| **回調類型** | `agent_response_callback` | 無回調                                      | `streaming_agent_response_callback`                        |
| **輸出方式** | 完整訊息一次性輸出        | 無輸出（因取消）                            | 即時串流輸出                                               |
| **日誌功能** | ❌                         | ✅ (DEBUG 等級)                              | ❌                                                          |
| **取消機制** | ❌                         | ✅                                           | ❌                                                          |
| **錯誤處理** | 完整錯誤處理              | 基本錯誤處理                                | 完整錯誤處理                                               |

## 🔍 詳細功能分析

### **Step2 - 基本順序編排**

**主要特色：**
- 🎯 展示基本的順序編排功能
- 📝 每個代理程式完成後一次性顯示完整結果
- 🛡️ 包含完整的錯誤處理和超時機制
- 🧹 包含資源清理邏輯

**核心程式碼：**
```python
# 使用標準的代理程式回應回調
sequential_orchestration = SequentialOrchestration(
    members=agents,
    agent_response_callback=agent_response_callback,  # 完整訊息回調
)

def agent_response_callback(message: ChatMessageContent) -> None:
    """觀察者函數，用於列印代理程式的訊息。"""
    print(f"# {message.name}\n{message.content}")
```

**適用場景：**
- 學習基礎的順序編排概念
- 需要完整的錯誤處理機制
- 生產環境中的穩定實現

### **Step2a - 取消機制範例**

**主要特色：**
- ⏹️ 展示如何取消正在執行的編排
- 📊 啟用 DEBUG 日誌以觀察內部運作
- 🔍 演示取消後的異常處理
- 📋 提供詳細的執行日誌輸出

**核心程式碼：**
```python
# 設定日誌記錄以查看呼叫過程
logging.basicConfig(level=logging.WARNING)
logging.getLogger("semantic_kernel.agents.orchestration.sequential").setLevel(logging.DEBUG)

# 沒有使用回調函數
sequential_orchestration = SequentialOrchestration(members=agents)

# 模擬取消操作
await asyncio.sleep(1)  # 模擬取消前的一些延遲
orchestration_result.cancel()
```

**適用場景：**
- 需要取消長時間運行的任務
- 調試和故障排除
- 學習編排的內部運作機制

### **Step2b - 串流回調範例**

**主要特色：**
- 🌊 展示即時串流輸出功能
- ⚡ 代理程式生成內容時立即顯示
- 🎭 更好的用戶體驗（即時反饋）
- 🔄 使用全域變數追蹤訊息狀態

**核心程式碼：**
```python
# 使用串流回調來即時顯示輸出
sequential_orchestration = SequentialOrchestration(
    members=agents,
    streaming_agent_response_callback=streaming_agent_response_callback,  # 串流回調
)

def streaming_agent_response_callback(message: StreamingChatMessageContent, is_final: bool) -> None:
    """即時顯示串流輸出"""
    global is_new_message
    if is_new_message:
        print(f"# {message.name}")
        is_new_message = False
    print(message.content, end="", flush=True)  # 即時輸出
    if is_final:
        print()
        is_new_message = True
```

**適用場景：**
- 需要即時用戶反饋的應用
- 提升用戶體驗的互動式應用
- 長時間運行的任務需要進度指示

## 🎯 使用場景建議

| 場景                         | 推薦文件        | 原因               |
| ---------------------------- | --------------- | ------------------ |
| **學習基礎概念**             | step2           | 最完整的基本實現   |
| **需要取消長時間運行的任務** | step2a          | 專門展示取消機制   |
| **需要即時用戶反饋**         | step2b          | 提供串流式用戶體驗 |
| **調試和故障排除**           | step2a          | 包含詳細的日誌記錄 |
| **生產環境應用**             | step2 或 step2b | 更完整的錯誤處理   |

## 💡 共同架構

所有三個文件都基於相同的 Azure AI Agent 架構：

### 代理程式設置
```python
async def get_agents(client) -> list[Agent]:
    # 創建概念提取代理程式
    concept_extractor_agent = AzureAIAgent(
        client=client,
        definition=concept_extractor_definition,
    )
    
    # 創建文案撰寫代理程式
    writer_agent = AzureAIAgent(
        client=client,
        definition=writer_definition,
    )
    
    # 創建格式校對代理程式
    format_proof_agent = AzureAIAgent(
        client=client,
        definition=format_proof_definition,
    )
    
    return [concept_extractor_agent, writer_agent, format_proof_agent]
```

### 基本流程
1. **建立 Azure AI Agent service client**
2. **創建代理程式實例**
3. **設置順序編排**
4. **啟動運行時**
5. **執行編排任務**
6. **處理結果和清理資源**

## 🔧 技術細節

### 錯誤處理模式
- **完整錯誤處理** (step2, step2b)：包含 TimeoutError 和一般 Exception 處理
- **基本錯誤處理** (step2a)：主要關注取消操作的異常

### 輸出模式比較
- **批次輸出** (step2)：代理程式完成後顯示完整結果
- **無輸出** (step2a)：因為編排被取消
- **串流輸出** (step2b)：實時顯示生成過程

### 日誌配置
只有 step2a 包含詳細的日誌配置：
```python
logging.basicConfig(level=logging.WARNING)
logging.getLogger("semantic_kernel.agents.orchestration.sequential").setLevel(logging.DEBUG)
```

## 📈 學習路徑建議

1. **第一步：掌握基礎** - 從 `step2` 開始，理解基本的順序編排概念
2. **第二步：學習控制** - 使用 `step2a` 學習如何控制編排執行
3. **第三步：提升體驗** - 通過 `step2b` 學習如何提供更好的用戶體驗

## 💼 實際應用考量

在實際項目中選擇實現方式時，建議考慮：

- **性能要求**：串流回調可能增加系統負載
- **用戶體驗**：即時反饋通常能提升用戶滿意度
- **調試需求**：開發階段可能需要詳細日誌
- **穩定性要求**：生產環境應優先考慮錯誤處理完整性

## 🔄 擴展性

這三個範例為更複雜的應用提供了良好的基礎：

- 可以組合不同的回調機制
- 可以添加自定義的錯誤處理邏輯
- 可以整合到更大的應用程式架構中
- 可以根據具體需求調整代理程式配置

---

*本文檔基於 Semantic Kernel Multi-Agent Orchestration 框架的 step2 系列範例進行分析，旨在幫助開發者理解不同實現方式的特點和適用場景。*
