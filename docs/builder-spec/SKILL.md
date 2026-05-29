---
name: ticdss-builder
description: >
  多模態 AI 臨床技能訓練評核系統(TICDSS)的開發加速 skill。當使用者要開發、實作、
  或擴充 TICDSS 系統的任何模組時,必須使用此 skill。觸發情境包括:
  - 「幫我做問診 Agent」、「實作身評評核」、「寫診斷評分邏輯」
  - 「建立 TICDSS 後端骨架」、「做 LLM 熱插拔層」、「實作多訊號融合」
  - 「做 RAG 個人化講義」、「實作 HRV 壓力曲線」、「DUAT 多代理人評分」
  - 提到 StageAgent 契約、Agent 註冊表、熱插拔套件、可替換模組
  - 任何涉及 TICDSS 的問診/身評/診斷/評分/融合/知識庫模組開發
  本 skill 採「母 skill + sub-agent」結構,每個 sub-agent 負責一個功能模組,
  產出的程式碼皆遵守 StageAgent 統一契約,確保所有模組可熱插拔、可獨立替換。
  即使使用者只說「幫我做 TICDSS 的某功能」,也應觸發此 skill。
---

# TICDSS Builder — 多模態 AI 臨床技能訓練評核系統開發 Skill

## 這個 Skill 是什麼

這是 TICDSS 系統的**開發加速器**。它把整個系統拆成數個功能模組,
每個模組對應一個 sub-agent。需要開發某個模組時,讀取對應的 sub-agent 規格,
即可快速產出遵守統一契約的程式碼。

## 核心設計原則

1. **全模組熱插拔**:每個功能都是可獨立替換的套件,遵守 `StageAgent` 契約。
2. **LLM 不綁定**:所有 LLM 呼叫經過 adapter 層,Gemini/Claude 可一行切換。
3. **教學式產出**:程式碼含詳細中文註解,邊產出邊解釋設計理由。
4. **契約優先**:任何模組開發前,先確認它如何符合 `core` 定義的契約。

## 系統架構總覽

```
TICDSS 後端 (Python + FastAPI)
│
├── core/                 統一契約 + 流程引擎 + 註冊表 (所有模組的基礎)
│   ├── agent_interface.py    StageAgent 抽象契約
│   ├── session_manager.py    訓練流程狀態機
│   └── registry.py           Agent 註冊表(熱插拔核心)
│
├── llm/                  LLM 熱插拔層
│   ├── llm_interface.py      統一 LLM 介面
│   ├── gemini_adapter.py     Gemini 實作
│   └── claude_adapter.py     Claude 實作
│
├── agents/               三個階段 Agent (遵守 StageAgent 契約)
│   ├── inquiry_agent.py      問診 (LQQOPERA + STT + anxiety)
│   ├── vision_agent.py       身評 (ArUco + Gemini 視覺)
│   └── diagnosis_agent.py    診斷 (推理評核)
│
├── fusion/               多訊號融合
│   └── fusion_engine.py      HRV + 語音停頓 + 表情 → 狀態分類
│
├── scoring/              評分 + 六種輸出
│   ├── realtime_scorer.py    即時評分 (60% 確定性 + 40% 語義)
│   ├── duat_verifier.py      DUAT 五代理人深度驗證
│   └── report_builder.py     六種輸出產生器
│
└── rag/                  個人化講義
    └── rag_note.py           弱點檢索 + 講義生成
```

## Sub-Agent 清單

開發各模組時,讀取 `sub-agents/` 下對應的規格檔:

| Sub-Agent 規格檔 | 負責模組 | 觸發語句範例 |
|-----------------|---------|-------------|
| `core.md` | 契約、session、流程引擎、註冊表 | 「建立骨架」、「定義契約」 |
| `llm-adapter.md` | LLM 熱插拔層(任務路由+備援+成本) | 「做 LLM 切換層」 |
| `inquiry.md` | 問診 Agent(LQQOPERA+混合檢核) | 「做問診」 |
| `voice-output.md` | TTS 語音(ElevenLabs+anxiety 語氣) | 「做語音」 |
| `avatar-presenter.md` | 虛擬病人形象(三段式可替換) | 「做虛擬病人」 |
| `vision.md` | 身評 Agent(連續追蹤+軌跡+三維評分) | 「做身評」 |
| `diagnosis.md` | 診斷 Agent(三診斷+危急度排序) | 「做診斷」 |
| `signal-hrv.md` | HRV 訊號採集(每迴圈正念建基準) | 「做 HRV」 |
| `signal-pause.md` | 語音停頓採集(混合判斷) | 「做停頓偵測」 |
| `signal-expression.md` | 臉部表情採集(本地 FER+Gemini) | 「做表情辨識」 |
| `fusion-classifier.md` | 三訊號融合(加權投票+防抖) | 「做融合分類」 |
| `realtime-scorer.md` | 即時評分(60%確定+40%語義) | 「做即時評分」 |
| `duat-flow.md` | DUAT 協調流程(O→E‖S→A→M) | 「做 DUAT 流程」 |
| `duat-agents.md` | DUAT 五代理(O/E/S/A/M) | 「做深度驗證代理」 |
| `output.md` | 五種輸出+協調者(共用真相來源) | 「做輸出」、「雷達圖」、「壓力曲線」 |
| `rag-note.md` | 個人化講義(Zettelkasten 雙卡) | 「做 RAG 講義」、「卡片筆記」 |
| `scenario-schema.md` | 情境案例結構(情境契約,高權重) | 「定義案例」、「情境結構」 |
| `case-generator.md` | 模擬案例生成(AI生成→專家審核) | 「生成案例」、「做案例生成」 |
| `concurrency-manager.md` | 併發與成本管理(基礎設施,設計預留) | 「多人併發」、「過載」、「成本控制」 |
| `persistence.md` | 資料持久化(PostgreSQL 全表+雙層隱私) | 「資料庫」、「表結構」、「SQL」 |
| `knowledge-base.md` | 知識庫(StatPearls+自建,按疾病分類) | 「知識庫」、「文獻庫」、「StatPearls」 |
| `transition.md` | 過渡期(問診摘要+預載身評標準) | 「過渡期」、「階段轉換」 |
| `roles-access.md` | 角色權限(學員/審核者/管理者) | 「角色」、「權限」、「管理者模式」 |
| `dev-tools.md` | 開發者除錯工具層(雙重安全開關) | 「開發者模式」、「除錯」、「測試工具」 |

> 共 24 個規格檔,涵蓋完整系統。所有產出皆遵守 core 契約,可熱插拔。
> scenario-schema 為情境契約(高權重),三軌 Agent 與 case-generator 皆依賴它。
> concurrency-manager 為基礎設施層,**設計預留**,prototype 不實作,多人上線前再實作。
> persistence 為資料持久化層,支撐 M-Agent 歷程、rag-note 卡片累積、成本記錄等累積型功能。
> knowledge-base 以 StatPearls 結構化文獻為主來源,按疾病分類,供 rag-note 檢索。
> roles-access 三種角色(學員/審核者/管理者),一帳號一角色,權限最小化,教師可擴充。
> dev-tools 為獨立除錯工具層(非角色),與角色正交,雙重安全開關(開發者帳號 AND 非正式環境)。

## 六種評分輸出(scoring 模組產出)

每次訓練結束後,系統產出以下六種輸出:

1. **自然語言評語** — 整體表現的文字總結
2. **雷達圖** — 問診/身評/診斷/溝通四維度視覺化
3. **弱點分析** — 條列本次最需改進的項目
4. **重點提示** — 最需要注意的單一關鍵問題
5. **RAG 個人化講義** — 依弱點從知識庫生成的學習材料
6. **HRV 壓力曲線** — 依生理監測產出的壓力時序預測圖

## 開發流程

1. 先讀 `sub-agents/core.md`,建立契約與骨架(其他模組的基礎)。
2. 再讀 `sub-agents/llm-adapter.md`,建立 LLM 熱插拔層。
3. 然後依需求讀取各 Agent 與功能模組的規格檔。
4. 每個模組產出後,確認它遵守 `StageAgent` 契約,即可熱插拔。

## 開發順序建議

```
階段一(骨架):  core → llm-adapter
階段二(三軌):  inquiry → vision → diagnosis
階段三(智慧):  fusion → scoring
階段四(回饋):  rag-note
```
