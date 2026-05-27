# DUAT Pipeline 設計文件

對應 Protocol §四（DUAT 系統設計）。**程式碼變更前先讀本文與 Protocol。**

## 五 Agent 流水線

```
                ┌─────────────────────────────────────────┐
                │  O-Agent  (主控/狀態機, FastAPI)         │
                │  - 維護 Session.phase                    │
                │  - 排程 LQQOPERA 八維度 + PE 雙軌        │
                └─────┬──────────────────────────────┬────┘
                      │                              │
              對每個 rubric item                   全程
                      │                              │
            ┌─────────▼─────────┐         ┌─────────▼─────────┐
            │  E-Agent (Gemini)  │         │  M-Agent (規則+LLM)│
            │  唯一接 RAG         │         │  跨 session 漂移   │
            │  輸出 Evidence     │         │  override rate     │
            │  Bundle (JSON)     │         └────────────────────┘
            └─────────┬─────────┘
                      │
              Evidence Bundle
                      │
          ┌───────────┴───────────┐
          │                       │
   ┌──────▼──────┐         ┌──────▼──────┐
   │  S-Agent     │         │  A-Agent    │
   │  (Claude 4.7)│         │  (Gemini)   │
   │  CoT 評分    │         │  對抗審查   │
   │  → score     │         │  → advocate │
   └──────┬──────┘         └──────┬──────┘
          │                       │
          └──────────┬────────────┘
                     │
            ┌────────▼────────┐
            │ Consensus       │
            │ Arbiter (規則)  │
            │ → accept/flag/  │
            │   force_human   │
            └────────┬────────┘
                     │
              寫入 duat_scores
              寫入 audit_events (JSONL)
              送 Langfuse trace
```

## Consensus Arbiter 三層規則（對應 Protocol §四.(三) 表二）

```python
def arbitrate(e_confidence: float, s_score: int,
              a_advocate_score: float) -> ArbiterDecision:
    """
    e_confidence:     E-Agent RAG 信心（餘弦相似度加權平均, 0-1）
    s_score:          S-Agent 評分（0-5）
    a_advocate_score: A-Agent 對抗顯著度（0-1）

    閾值將於 Phase 1 Pilot 後依 override rate 校正。
    """
    # Layer 1: 高信心 + 無對抗 → 直接接受
    if e_confidence >= 0.8 and a_advocate_score < 0.3:
        return ArbiterDecision(action="accept", confidence="high")

    # Layer 2: 中等信心或輕度對抗 → 標 Uncertainty Flag
    if e_confidence >= 0.5 and a_advocate_score < 0.5:
        return ArbiterDecision(action="flag", confidence="medium",
                               flag_reason="moderate_uncertainty")

    # Layer 3: 低信心或強對抗 → 強制人工裁決
    return ArbiterDecision(action="force_human", confidence="low",
                           flag_reason="low_confidence_or_strong_advocate")
```

**Override rate 監控**：M-Agent 持續計算每個 rubric item 的「人工 modify/reject 比率」，
若連續超過 30%，自動通知考站主任並暫停該條目的自動評分。

## Evidence Bundle JSON Schema（E-Agent 輸出）

```json
{
  "rubric_item_id": "lqqopera.location",
  "evidence_segments": [
    {
      "transcript_id": "uuid",
      "start_ms": 12340,
      "end_ms": 18900,
      "speaker": "student",
      "text": "請問您痛的位置是哪裡？",
      "relevance_score": 0.92
    }
  ],
  "rag_hits": [
    {
      "chunk_id": "biblio_chunk_123",
      "source": "Seidel et al. 2019, Ch.4",
      "cosine_similarity": 0.84,
      "rerank_score": 0.91
    }
  ],
  "confidence": 0.87,
  "extraction_notes": "學員主動詢問位置與放射路徑，符合 Location 維度全部子標準"
}
```

## S-Agent / A-Agent 輸入規範

兩者**只**收到 Evidence Bundle + Rubric Item Spec，**絕不**收到整場逐字稿。
這是 Protocol §四.(六) Context Window 最小化原則的強制要求。
