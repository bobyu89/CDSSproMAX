# Audit Log 規格

對應 Protocol §四.(七)。每筆評分事件必須完整可追溯。

## JSONL 格式（一筆一行）

```json
{
  "event_id": "uuid",
  "session_id": "uuid",
  "rubric_item_id": "lqqopera.location",
  "timestamp": "2026-05-27T10:32:14.123Z",
  "event_type": "duat.score_computed",
  "evidence_bundle": { ... },
  "s_agent": {
    "model": "claude-opus-4-7",
    "prompt_hash": "sha256:...",
    "cot_reasoning": "...",
    "raw_score": 4
  },
  "a_agent": {
    "model": "gemini-3.5-flash",
    "prompt_hash": "sha256:...",
    "advocate_report": "...",
    "advocate_score": 0.2
  },
  "arbiter": {
    "decision": "accept",
    "confidence": "high",
    "thresholds_version": "v1.0"
  },
  "grader": {
    "participant_id": "uuid",
    "action": "accept",
    "final_score": 4,
    "modify_reason": null,
    "timestamp": "2026-05-27T10:35:02.456Z"
  }
}
```

## 事件類型 (event_type)

- `session.started`
- `transcript.appended`
- `duat.e_extracted`
- `duat.s_scored`
- `duat.a_reviewed`
- `duat.arbiter_decided`
- `duat.score_computed`（完整一輪結束）
- `grader.action`
- `mdrift.alert`（M-Agent 偵測到 override rate > 30%）

## 儲存

- 即時寫入 `audit_logs/{session_id}.jsonl`
- DB 表 `audit_events` 同時索引（查詢用）
- M-Agent 從 JSONL 統計 override rate
