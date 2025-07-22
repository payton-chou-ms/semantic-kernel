# 技術問題解決中心 - 多代理群組聊天實作

## 📋 專案概述

這是一個完整的多代理技術問題解決系統，整合了 Semantic Kernel 的進階功能，包含群組聊天、自定義策略、結構化輸出和日誌記錄。三位專業代理（技術專家、測試工程師、文檔撰寫員）協作解決技術問題，並產生結構化的技術報告。

## 🎯 學習目標

透過此專案，你將學會：
- 設計多代理群組聊天系統
- 實作自定義終止策略
- 使用 Pydantic 進行結構化輸出
- 整合日誌記錄系統
- 處理複雜的代理互動流程

## 🔧 主要功能特色

### 1. 多代理群組聊天 (Step 6)
- **技術專家 (TechnicalExpert)**：負責問題診斷和解決方案設計
- **測試工程師 (TestEngineer)**：設計測試案例和驗證邏輯
- **文檔撰寫員 (DocumentationWriter)**：整理文檔和使用指南

### 2. 自定義策略 (Step 7)
- **SolutionCompletionStrategy**：智能終止策略
- 檢查關鍵字：`"解決方案完成"`、`"測試完成"`、`"文檔完成"`
- 至少需要 2 個任務完成才終止對話

### 3. JSON 結構化輸出 (Step 8)
- **TechnicalSolutionReport**：完整的技術解決方案報告
- **TestCase**：測試案例模型
- **SolutionStep**：解決步驟模型
- **Documentation**：文檔模型

### 4. 詳細日誌記錄 (Step 9)
- 完整的互動過程記錄
- 時間戳記和等級分類
- 易於除錯和監控

### 5. 結構化輸出 (Step 10)
- 使用 Pydantic 模型確保輸出格式
- 自動驗證和格式化
- 品質評分機制

## 🚀 執行範例

程式將處理三個預設的技術問題：

1. **Python CSV 檔案記憶體最佳化**
2. **React 應用程式效能最佳化**
3. **資料庫查詢效能問題**

每個問題都會產生包含解決步驟、測試案例和文檔的完整結構化報告！


## 🔍 程式碼解析

### 結構化輸出模型

```python
class TechnicalSolutionReport(BaseModel):
    """技術解決方案報告"""
    problem_summary: str
    solution_steps: List[SolutionStep]
    test_cases: List[TestCase]
    documentation: List[Documentation]
    final_recommendation: str
    quality_score: int
```

### 自定義終止策略

```python
class SolutionCompletionStrategy(TerminationStrategy):
    """自定義終止策略 - 當所有專家完成工作時終止"""
    
    required_keywords: List[str] = ["解決方案完成", "測試完成", "文檔完成"]
    
    async def should_agent_terminate(self, agent, history):
        # 檢查完成關鍵字
        recent_messages = [msg.content.lower() for msg in history[-3:]]
        completed_tasks = sum(1 for keyword in self.required_keywords 
                            if any(keyword in msg for msg in recent_messages))
        return completed_tasks >= 2
```

### 代理角色定義

#### 技術專家
- 分析技術問題的根本原因
- 提供詳細的解決步驟和程式碼範例
- 評估解決方案的可行性和效能影響

#### 測試工程師
- 根據技術專家提供的解決方案設計測試案例
- 撰寫測試程式碼和驗證邏輯
- 評估測試覆蓋率和品質保證策略

#### 文檔撰寫員
- 整理技術專家和測試工程師的工作成果
- 撰寫使用指南、API 文檔和最佳實務
- 確保文檔的可讀性和完整性

## 📊 預期輸出

```
🔧 技術問題解決中心啟動
==================================================

📋 處理問題 1: Python 程式在處理大型 CSV 檔案時記憶體使用量過高，如何最佳化？
--------------------------------------------------
🗣️  專家團隊討論中...
💬 TechnicalExpert: 我將分析這個記憶體使用量過高的問題...
💬 TestEngineer: 基於技術專家的分析，我設計了以下測試案例...
💬 DocumentationWriter: 我整理了完整的解決方案文檔...

📊 生成結構化報告...
✅ 報告生成完成！品質評分: 95/100
📝 解決方案步驟數: 5
🧪 測試案例數: 3
📚 文檔章節數: 4

📋 問題摘要: Python CSV 檔案記憶體最佳化解決方案
💡 最終建議: 建議使用 pandas 的 chunksize 參數進行分批處理...
```

## 🎨 自定義與擴展

### 新增代理角色
```python
security_expert = ChatCompletionAgent(
    kernel=_create_kernel_with_chat_completion("security_expert"),
    name="SecurityExpert",
    instructions="你是一位資訊安全專家，負責評估解決方案的安全性...",
)
```

### 新增結構化模型
```python
class SecurityAssessment(BaseModel):
    """安全評估模型"""
    security_level: str
    vulnerabilities: List[str]
    recommendations: List[str]
```

### 修改終止條件
```python
required_keywords: List[str] = ["解決方案完成", "測試完成", "文檔完成", "安全檢查完成"]
```

## ✅ 功能檢查清單

- [x] **Step 6**: 多代理群組聊天
  - [x] 技術專家代理
  - [x] 測試工程師代理
  - [x] 文檔撰寫員代理
  - [x] AgentGroupChat 整合

- [x] **Step 7**: 自定義策略
  - [x] SolutionCompletionStrategy 實作
  - [x] 關鍵字檢測機制
  - [x] 智能終止邏輯

- [x] **Step 8**: JSON 結構化輸出
  - [x] TechnicalSolutionReport 模型
  - [x] 子模型定義 (TestCase, SolutionStep, Documentation)
  - [x] JSON 序列化和驗證

- [x] **Step 9**: 詳細日誌記錄
  - [x] 基本日誌配置
  - [x] 時間戳記和等級分類
  - [x] 互動過程記錄

- [x] **Step 10**: 結構化輸出格式化
  - [x] Pydantic 模型驗證
  - [x] 自動格式化
  - [x] 品質評分機制
