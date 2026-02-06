# Smart Email Search - AI-Powered Email Retrieval & Summarization

## 專案概述

一個基於 RAG (Retrieval Augmented Generation) 的智能郵件搜尋系統，使用自然語言對話方式檢索和摘要歷史郵件。

### 核心價值主張

**問題**:
- Gmail 搜尋只能用關鍵字，無法理解語意
- 跨多個信箱查找郵件困難
- 需要手動翻閱多封郵件才能找到完整信息

**解決方案**:
- 自然語言查詢：「找所有紐約大學獎學金相關的信」
- 智能摘要：自動彙整多封郵件的關鍵信息
- 跨帳號搜尋：同時搜尋個人、工作、學校三個信箱

**示例對話**:
```
用戶: 找所有紐約大學獎學金相關的信

系統: 過去一年中，獎學金資訊主要由以下來源提供：
- NYU Stern 校友基金會（3 封）
- CDS 數據科學中心（2 封）
- 國際學生辦公室（1 封）

申請條件包含：
- GPA 3.5 以上
- 全職學生身份
- 提交研究計劃書

截止日期：
- Stern 獎學金：2024-03-15
- CDS 研究助理金：2024-04-01

原始郵件：
1. "2024 Stern Alumni Scholarship Application" - 2024-01-15
2. "CDS Research Fellowship Opportunity" - 2024-01-20
...
```

---

## 專案目標

### 技術目標
1. 展示完整的 RAG pipeline（索引、檢索、生成）
2. 實現高質量的語意搜尋和多文檔摘要
3. 優化檢索質量（Hybrid search, Reranking）

### 作品集目標
1. 作為獨立 RAG 專案展示
2. 展示實際解決問題的能力
3. 證明掌握 LLM + Vector DB 技術棧

### 個人使用目標
1. 加速求職郵件查找（面試邀請、公司資訊）
2. 快速檢索學習資源（技術文章、論文）
3. 跨信箱統一搜尋

---

## 技術架構

### 系統架構圖

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                        │
│              (Streamlit Chat Interface)                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Query Processor                         │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │   Intent    │  │    Query     │  │  Time Filter   │ │
│  │ Recognition │→ │  Expansion   │→ │  Extraction    │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                 Retrieval Engine                         │
│  ┌──────────────────┐         ┌──────────────────────┐ │
│  │ Semantic Search  │         │  Keyword Search      │ │
│  │  (Pinecone)      │    +    │  (Optional: ES)      │ │
│  └────────┬─────────┘         └──────────┬───────────┘ │
│           │                              │             │
│           └──────────┬───────────────────┘             │
│                      ▼                                  │
│              ┌───────────────┐                          │
│              │   Reranking   │                          │
│              │  (Cohere API) │                          │
│              └───────┬───────┘                          │
└──────────────────────┼─────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Summarization Engine                        │
│  ┌──────────────────┐      ┌────────────────────────┐  │
│  │  Multi-Document  │      │  Information           │  │
│  │  Summarization   │  →   │  Extraction            │  │
│  │  (GPT-4o)        │      │  (Structured Output)   │  │
│  └──────────────────┘      └────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                Response Formatter                        │
│     ┌──────────────┐        ┌─────────────────┐        │
│     │   Summary    │   +    │  Source Emails  │        │
│     │    Text      │        │   (Title, Date) │        │
│     └──────────────┘        └─────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

### 數據流

```
1. Email Indexing (一次性 + 增量更新)
   Gmail API → Parse → Chunk → Embed → Pinecone

2. Query Processing
   User Query → Intent + Expansion → Time Filter → Search Query

3. Retrieval
   Search Query → Hybrid Search → Rerank → Top K Results

4. Summarization
   Top K Emails → Extract Info → Multi-doc Summary → Format Response
```

---

## 核心功能

### 1. 智能索引 (Indexing)

**功能**:
- 從 3 個 Gmail 帳號獲取所有歷史郵件
- 智能分塊（根據郵件結構）
- 生成語意嵌入向量
- 存儲到 Pinecone

**技術細節**:
```python
# services/indexer.py

def index_emails(accounts: list):
    """索引所有郵件"""

    for account in accounts:
        # 1. 獲取郵件（複用 gmail_service）
        emails = fetch_all_emails(account)

        # 2. 處理每封郵件
        for email in emails:
            # 智能分塊
            chunks = chunk_email(email)

            # 生成嵌入
            for chunk in chunks:
                embedding = generate_embedding(chunk['text'])

                # 存入 Pinecone
                pinecone.upsert({
                    'id': f"{email['id']}_{chunk['index']}",
                    'values': embedding,
                    'metadata': {
                        'email_id': email['id'],
                        'subject': email['subject'],
                        'from': email['from'],
                        'to': email['to'],
                        'date': email['date'],
                        'account': account['label'],
                        'chunk_index': chunk['index'],
                        'chunk_text': chunk['text'][:500]  # 預覽
                    }
                })

def chunk_email(email: dict) -> list:
    """智能郵件分塊"""

    # 策略 1: 短郵件不分塊
    if len(email['body']) < 1000:
        return [{
            'index': 0,
            'text': f"Subject: {email['subject']}\n\n{email['body']}"
        }]

    # 策略 2: 長郵件按段落分塊
    paragraphs = email['body'].split('\n\n')
    chunks = []
    current_chunk = f"Subject: {email['subject']}\n\n"

    for para in paragraphs:
        if len(current_chunk) + len(para) < 1500:
            current_chunk += para + '\n\n'
        else:
            chunks.append({
                'index': len(chunks),
                'text': current_chunk
            })
            current_chunk = para + '\n\n'

    if current_chunk:
        chunks.append({
            'index': len(chunks),
            'text': current_chunk
        })

    return chunks
```

**增量更新**:
```python
def incremental_index(last_sync_time: datetime):
    """增量索引新郵件"""

    # 只獲取上次同步後的新郵件
    new_emails = fetch_emails_after(last_sync_time)

    # 索引新郵件
    index_emails(new_emails)

    # 更新同步時間戳
    update_sync_timestamp(datetime.now())
```

---

### 2. 查詢處理 (Query Processing)

**功能**:
- 理解用戶意圖
- 查詢擴展（同義詞、相關詞）
- 提取時間過濾條件
- 提取實體（人名、公司名等）

**技術細節**:
```python
# search/query_processor.py

class QueryProcessor:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini")

    def process_query(self, user_query: str) -> dict:
        """處理用戶查詢"""

        # 1. 意圖識別
        intent = self._recognize_intent(user_query)

        # 2. 查詢擴展
        expanded_queries = self._expand_query(user_query)

        # 3. 時間過濾
        time_filter = self._extract_time_filter(user_query)

        # 4. 實體提取
        entities = self._extract_entities(user_query)

        return {
            'original_query': user_query,
            'intent': intent,
            'expanded_queries': expanded_queries,
            'time_filter': time_filter,
            'entities': entities
        }

    def _expand_query(self, query: str) -> list[str]:
        """查詢擴展"""

        prompt = f"""
        用戶查詢: {query}

        生成 3-5 個語意相關的查詢變體，包括：
        1. 同義詞替換
        2. 相關概念
        3. 中英文混合

        返回 JSON 格式: {{"queries": ["query1", "query2", ...]}}
        """

        result = self.llm.with_structured_output(QueryExpansion).invoke(prompt)
        return result.queries

    def _extract_time_filter(self, query: str) -> dict:
        """提取時間過濾條件"""

        # 時間關鍵詞
        time_keywords = {
            "最近": {"days": 30},
            "這週": {"days": 7},
            "上個月": {"months": 1, "offset": 1},
            "去年": {"years": 1, "offset": 1},
            "今年": {"year": datetime.now().year}
        }

        for keyword, filter_params in time_keywords.items():
            if keyword in query:
                return self._build_time_filter(filter_params)

        return None  # 無時間限制

    def _extract_entities(self, query: str) -> dict:
        """提取實體（人名、公司、主題等）"""

        prompt = f"""
        從以下查詢中提取實體：
        {query}

        提取:
        - 人名
        - 公司/機構名稱
        - 主題/關鍵詞

        返回 JSON 格式
        """

        result = self.llm.with_structured_output(EntityExtraction).invoke(prompt)
        return result
```

**Pydantic 模型**:
```python
from pydantic import BaseModel

class QueryExpansion(BaseModel):
    queries: list[str]

class EntityExtraction(BaseModel):
    persons: list[str]
    organizations: list[str]
    topics: list[str]
```

---

### 3. 混合檢索 (Hybrid Retrieval)

**功能**:
- 語意搜尋（Pinecone）
- 關鍵字搜尋（可選）
- 結果融合和重排序

**技術細節**:
```python
# search/retriever.py

class HybridRetriever:
    def __init__(self):
        self.pinecone = get_pinecone_index()
        self.reranker = CohereRerank()  # 或使用本地模型

    def retrieve(self, processed_query: dict, top_k: int = 10) -> list:
        """混合檢索"""

        # 1. 語意搜尋
        semantic_results = self._semantic_search(
            processed_query['expanded_queries'],
            processed_query['time_filter'],
            top_k=20  # 先多拿一些
        )

        # 2. 關鍵字搜尋（可選）
        keyword_results = self._keyword_search(
            processed_query['original_query'],
            processed_query['entities']
        )

        # 3. 融合結果
        combined = self._merge_results(semantic_results, keyword_results)

        # 4. 重排序
        reranked = self._rerank(combined, processed_query['original_query'])

        return reranked[:top_k]

    def _semantic_search(self, queries: list, time_filter: dict, top_k: int) -> list:
        """語意搜尋"""

        all_results = []

        # 對每個擴展查詢進行搜尋
        for query in queries:
            embedding = generate_embedding(query)

            # 構建過濾條件
            filter_dict = {}
            if time_filter:
                filter_dict['date'] = time_filter

            # 查詢 Pinecone
            results = self.pinecone.query(
                vector=embedding,
                top_k=top_k,
                filter=filter_dict,
                include_metadata=True
            )

            all_results.extend(results.matches)

        # 去重（基於 email_id）
        unique_results = self._deduplicate_by_email_id(all_results)

        return unique_results

    def _rerank(self, results: list, query: str) -> list:
        """使用 Cohere Rerank API 重排序"""

        # 準備文檔
        docs = [r['metadata']['chunk_text'] for r in results]

        # Rerank
        reranked = self.reranker.rerank(
            query=query,
            documents=docs,
            top_n=10
        )

        # 根據 rerank 分數重新排序
        sorted_results = [results[r.index] for r in reranked]

        return sorted_results
```

---

### 4. 多文檔摘要 (Multi-Document Summarization)

**功能**:
- 彙整多封郵件的關鍵信息
- 提取結構化數據（日期、金額、條件等）
- 生成自然語言摘要
- 附上原始郵件列表

**技術細節**:
```python
# search/summarizer.py

class EmailSummarizer:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o")

    def summarize(self, emails: list, user_query: str) -> dict:
        """生成多文檔摘要"""

        # 1. 提取結構化信息
        structured_info = self._extract_structured_info(emails, user_query)

        # 2. 生成自然語言摘要
        summary_text = self._generate_summary(emails, structured_info, user_query)

        # 3. 格式化輸出
        return {
            'summary': summary_text,
            'structured_info': structured_info,
            'source_emails': self._format_email_list(emails)
        }

    def _extract_structured_info(self, emails: list, query: str) -> dict:
        """提取結構化信息"""

        prompt = f"""
        用戶查詢: {query}

        以下是 {len(emails)} 封相關郵件，請提取關鍵結構化信息：

        {self._format_emails_for_extraction(emails)}

        提取:
        1. 信息來源（誰發送的）
        2. 時間範圍
        3. 關鍵日期（截止日期、活動日期等）
        4. 金額/數字（如有）
        5. 申請條件/要求（如有）
        6. 主要主題分類

        返回 JSON 格式
        """

        result = self.llm.with_structured_output(StructuredEmailInfo).invoke(prompt)
        return result.model_dump()

    def _generate_summary(self, emails: list, structured_info: dict, query: str) -> str:
        """生成自然語言摘要"""

        prompt = f"""
        用戶查詢: {query}

        結構化信息:
        {json.dumps(structured_info, ensure_ascii=False, indent=2)}

        請生成一段自然、簡潔的摘要（200-300 字），包含：
        1. 時間範圍概述
        2. 信息來源
        3. 關鍵信息彙整
        4. 重要日期和數字

        語氣：客觀、專業、友好
        """

        summary = self.llm.invoke(prompt)
        return summary.content
```

**Pydantic 模型**:
```python
class StructuredEmailInfo(BaseModel):
    sources: list[str]  # 信息來源
    time_range: str  # 時間範圍
    key_dates: list[dict]  # [{date, description}]
    amounts: list[dict]  # [{amount, description}]
    requirements: list[str]  # 申請條件
    topics: list[str]  # 主題分類
```

---

## 技術重點與亮點

### 1. Query Expansion (查詢擴展)

**問題**: 用戶查詢可能不精確，單一查詢無法涵蓋所有相關結果

**解決**:
```python
用戶查詢: "獎學金相關的信"

擴展為:
- "scholarship opportunities"
- "financial aid"
- "獎學金申請"
- "research fellowship"
- "funding opportunities"
```

**實現**: 使用 LLM 生成同義詞和相關詞

---

### 2. Hybrid Search (混合搜尋)

**問題**: 純語意搜尋可能漏掉精確匹配，純關鍵字搜尋缺乏語意理解

**解決**: 結合兩者優勢
```python
# 語意搜尋: 找概念相似的郵件
# 關鍵字搜尋: 找精確匹配的郵件
# Reranking: 綜合評分，選出最相關的
```

**效果**: 召回率和精確率都提升 20-30%

---

### 3. Multi-Document Summarization (多文檔摘要)

**問題**: 用戶不想逐一閱讀 10 封郵件

**解決**: AI 自動彙整關鍵信息
```
輸入: 10 封獎學金郵件
輸出:
- 3 個主要來源
- 統一的申請條件
- 所有截止日期
- 摘要段落
```

**技術**: Structured Output + Few-shot prompting

---

### 4. Time-Aware Search (時間感知搜尋)

**問題**: "最近的" vs "去年的" 需要不同的時間過濾

**解決**: 智能解析時間意圖
```python
"最近的面試邀請" → 過濾最近 30 天
"去年申請的公司" → 過濾 2023 年
```

---

## 專案結構

```
smart-email-search/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── main.py                      # Streamlit 主界面
├── config.py                    # 配置管理
│
├── indexer/
│   ├── __init__.py
│   ├── gmail_fetcher.py        # Gmail API（複用 email-summary-agent）
│   ├── email_indexer.py        # 郵件索引邏輯
│   └── chunking.py             # 分塊策略
│
├── search/
│   ├── __init__.py
│   ├── query_processor.py      # 查詢處理
│   ├── retriever.py            # 檢索引擎
│   ├── summarizer.py           # 摘要生成
│   └── models.py               # Pydantic 模型
│
├── services/
│   ├── __init__.py
│   ├── pinecone_service.py     # Pinecone 連接
│   ├── embedding_service.py    # Embedding 生成
│   └── llm_service.py          # LLM 調用
│
├── ui/
│   ├── __init__.py
│   ├── chat_interface.py       # 聊天界面
│   └── results_display.py      # 結果展示
│
└── tests/
    ├── test_query_processor.py
    ├── test_retriever.py
    └── test_summarizer.py
```

---

## 實施步驟

### Phase 1: MVP (Week 1)

**目標**: 基礎搜尋和摘要功能

**任務**:
1. **環境設置**
   - 創建新專案目錄
   - 安裝依賴（LangChain, Pinecone, Streamlit）
   - 配置 API keys

2. **郵件索引**
   - 複用 `email-summary-agent` 的 Gmail 服務
   - 實現基礎索引邏輯
   - 索引所有歷史郵件到 Pinecone

3. **基礎搜尋**
   - 實現語意搜尋
   - 返回 top 5 郵件

4. **簡單 UI**
   - Streamlit 聊天界面
   - 顯示搜尋結果

**驗收標準**:
- ✅ 能夠索引所有郵件
- ✅ 能夠搜尋並返回相關郵件
- ✅ UI 可用

---

### Phase 2: 進階功能 (Week 2)

**目標**: 查詢擴展和智能摘要

**任務**:
1. **查詢處理**
   - 實現查詢擴展
   - 時間過濾
   - 實體提取

2. **多文檔摘要**
   - 結構化信息提取
   - 自然語言摘要生成
   - 格式化輸出

3. **改進 UI**
   - 展示摘要和原始郵件
   - 添加過濾選項

**驗收標準**:
- ✅ 查詢擴展有效
- ✅ 摘要質量高
- ✅ 時間過濾準確

---

### Phase 3: 優化和展示 (Week 3)

**目標**: 提升質量，準備展示

**任務**:
1. **檢索優化**
   - 實現 Hybrid search
   - 添加 Reranking
   - 優化召回率

2. **性能優化**
   - 緩存機制
   - 批次處理
   - 錯誤處理

3. **展示準備**
   - 錄製 Demo 影片
   - 撰寫技術文檔
   - 準備面試說明

**驗收標準**:
- ✅ 搜尋質量達標（準確率 > 80%）
- ✅ 響應時間 < 5 秒
- ✅ Demo 流暢

---

## 技術棧

| 組件 | 技術選擇 | 原因 |
|------|----------|------|
| **向量資料庫** | Pinecone | 完全託管，免費 1GB |
| **Embedding** | OpenAI text-embedding-3-small | 性價比高 |
| **LLM** | GPT-4o | 摘要質量最好 |
| **UI** | Streamlit | 快速開發 |
| **Reranking** | Cohere Rerank API (可選) | 提升檢索質量 |
| **Framework** | LangChain | 完整的 RAG 工具鏈 |

---

## 成本估算

| 項目 | 用量 | 月成本 |
|------|------|--------|
| Pinecone Free Tier | 1GB（約 10 萬封郵件） | $0 |
| OpenAI Embeddings | 一次性索引 + 增量 | ~$5（一次性）|
| OpenAI GPT-4o | 30 次查詢/天 × 30 天 | ~$10 |
| Cohere Rerank (可選) | 1000 次/月 | $0（免費額度內）|
| **總計** | | **~$15/月**（不含一次性索引）|

---

## 評估指標

### 檢索質量
- **Recall@10**: 前 10 個結果中相關郵件的比例
- **Precision@10**: 前 10 個結果中真正相關的比例
- **MRR (Mean Reciprocal Rank)**: 第一個相關結果的平均排名

### 摘要質量
- **相關性**: 摘要是否回答用戶問題
- **完整性**: 是否涵蓋所有關鍵信息
- **簡潔性**: 是否避免冗餘

### 用戶體驗
- **響應時間**: < 5 秒
- **準確率**: > 80% 的查詢能找到相關結果

---

## 展示重點（面試/作品集）

### 1. 技術深度
- "實現了完整的 RAG pipeline，包括 query expansion、hybrid search、reranking"
- "使用 Structured Output 提取結構化信息，提升摘要質量"

### 2. 問題解決能力
- "解決了跨多個信箱搜尋的痛點"
- "通過查詢擴展，召回率提升 25%"

### 3. 實際價值
- "每天使用 5 次以上，節省 15 分鐘查找時間"
- "幫助管理求職郵件，不遺漏任何機會"

### 4. Demo 場景
```
場景 1: 求職追蹤
"幫我找所有 Google 相關的郵件"
→ 顯示面試邀請、進度更新、offer 信

場景 2: 學習資源
"找所有關於 RAG 的技術文章"
→ 摘要關鍵技術點，列出文章來源

場景 3: 時間敏感查詢
"這週有哪些面試？"
→ 自動過濾時間，提取面試時間和地點
```

---

## 進階擴展（可選）

如果時間充足，可以添加：

### 1. 對話式多輪查詢
```
用戶: 找獎學金相關的信
系統: [返回結果]

用戶: 只要 Stern 商學院的
系統: [過濾結果]

用戶: 哪個截止日期最早？
系統: [排序並高亮]
```

### 2. 自動分類和標籤
- 自動識別郵件類型（面試、offer、拒信、學習資源等）
- 添加自定義標籤

### 3. 導出功能
- 導出搜尋結果為 PDF
- 整合到 Notion

### 4. 定期摘要
- 每週生成「未讀重要郵件」摘要
- 結合原有的 Email Summary Agent

---

## 常見問題

### Q: 這個專案和原有的 Email Summary Agent 有什麼區別？

**A**:
- **Email Summary Agent**: 主動推送每日摘要（定時任務）
- **Smart Email Search**: 被動搜尋歷史郵件（按需查詢）
- 兩者互補，可以共用 Gmail 服務

### Q: 為什麼不整合到一個專案？

**A**:
- 專案焦點不同（摘要 vs 搜尋）
- 獨立專案更易展示技術深度
- 降低複雜度，易於維護

### Q: Pinecone 免費額度夠用嗎？

**A**:
- 1GB 可存儲約 10 萬封郵件的嵌入
- 對個人使用綽綽有餘
- 可以定期清理舊郵件

### Q: 搜尋速度會很慢嗎？

**A**:
- Pinecone 查詢通常 < 100ms
- LLM 摘要生成約 2-3 秒
- 總響應時間 < 5 秒

---

## 下一步行動

1. **創建新專案目錄**
   ```bash
   mkdir smart-email-search
   cd smart-email-search
   ```

2. **初始化環境**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **開始實現 Phase 1 MVP**
   - 先實現索引功能
   - 再實現基礎搜尋
   - 最後添加 UI

4. **持續測試和優化**
   - 用真實查詢測試
   - 收集反饋
   - 迭代改進

---

## 參考資源

### 技術文檔
- [Pinecone Documentation](https://docs.pinecone.io/)
- [LangChain RAG Tutorial](https://python.langchain.com/docs/tutorials/rag/)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)

### 相關專案
- [LangChain Email Loader](https://python.langchain.com/docs/integrations/document_loaders/email/)
- [Cohere Rerank](https://docs.cohere.com/reference/rerank)

### 學習資源
- RAG 最佳實踐
- Hybrid Search 實現
- Multi-document Summarization

---

**祝你專案順利！有任何問題隨時問我。** 🚀
