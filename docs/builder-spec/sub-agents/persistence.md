# Sub-Agent: persistence — 資料持久化(PostgreSQL 表結構)

> **權重:基礎設施層(資料持久化,支撐所有累積型功能)。**
> 定義完整 SQL 表結構。雙層隱私:個人帳戶層(可識別)+ 研究層(去識別化)。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | persistence |
| 模組版本 | v1.0 |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 資料庫 | PostgreSQL |
| 相依模組 | core |
| 被依賴模組 | case-generator、duat-memory、rag-note、concurrency-manager、輸出 |

> GitHub 路徑:`ticdss/db/schema.sql`、`ticdss/db/repository.py`。
> Notion:「TICDSS / persistence / v1.0」。

---

## 三大設計決策

| 決策 | 採用方案 |
|------|---------|
| 資料庫 | PostgreSQL(完整、多人、上線用) |
| 詳細度 | 分層:摘要永久存;原始訊號時序可選存,設保留期 |
| 隱私架構 | 雙層:個人帳戶層(可識別)+ 研究層(去識別化) |

---

## 雙層隱私架構

> 同時滿足:學員有完整個人歷程(M-Agent/卡片需要)、
> 研究者有合乎倫理的去識別化資料。符合 IRB 精神,利於論文與商業化。

```
個人帳戶層(可識別)
  學員本人存取完整資料:影像參照、HRV 原值、訓練歷程
  以 student_id 關聯,本人可見

研究層(去識別化)
  管理者存取:移除姓名/學號,僅留訓練表現與訊號
  以 anon_id 關聯,供群體分析
  原始生物資料須去識別化後才進此層
```

---

## 完整表結構

### `db/schema.sql`

```sql
-- ═══ 個人帳戶層(可識別) ═══

-- 學員
CREATE TABLE students (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT,                    -- 可識別,僅本人/授權可見
    email           TEXT UNIQUE,
    current_level   INTEGER DEFAULT 1,       -- 當前混淆難度等級
    total_sessions  INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- 案例庫(case-generator 使用)
CREATE TABLE scenarios (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic           TEXT NOT NULL,
    confusion_level INTEGER NOT NULL,         -- 1/2/3
    status          TEXT NOT NULL DEFAULT 'draft',  -- draft/approved/rejected
    content         JSONB NOT NULL,           -- 序列化 Scenario
    qc_result       JSONB,                    -- AI 自檢結果
    reject_reason   TEXT,
    reviewed_by     UUID,                     -- 審核專家
    created_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_scenarios_pick ON scenarios(status, topic, confusion_level);

-- 訓練紀錄(摘要,永久存)
CREATE TABLE sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID REFERENCES students(id),
    scenario_id     UUID REFERENCES scenarios(id),
    mode            TEXT NOT NULL,            -- practice/exam
    confusion_level INTEGER,
    composite_score NUMERIC(5,2),             -- 綜合表現指數
    phase_scores    JSONB,                    -- 各階段 StageScore 摘要
    llm_cost        NUMERIC(8,4),             -- 本次 LLM 成本
    experimental    BOOLEAN DEFAULT false,    -- 是否用實驗性案例
    started_at      TIMESTAMPTZ DEFAULT now(),
    ended_at        TIMESTAMPTZ
);
CREATE INDEX idx_sessions_student ON sessions(student_id, started_at);

-- DUAT 分析(M-Agent 歷程比對要讀)
CREATE TABLE duat_analyses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID REFERENCES sessions(id),
    student_id      UUID REFERENCES students(id),
    analysis        JSONB NOT NULL,           -- A-Agent 弱點/錯誤模式/原因
    narrative       TEXT,                     -- M-Agent 個人化敘事
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- 弱點累積(哪個知識點犯錯幾次)
CREATE TABLE weak_points (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID REFERENCES students(id),
    topic           TEXT NOT NULL,            -- 弱點主題(對應永久卡)
    hit_count       INTEGER DEFAULT 1,        -- 累計犯錯次數
    last_session_id UUID REFERENCES sessions(id),
    last_seen       TIMESTAMPTZ DEFAULT now(),
    UNIQUE(student_id, topic)                 -- 同主題累加而非新增
);

-- Zettelkasten 卡片(rag-note 累積)
CREATE TABLE zettel_cards (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id      UUID REFERENCES students(id),
    card_type       TEXT NOT NULL,            -- permanent/training
    topic           TEXT NOT NULL,
    content         TEXT NOT NULL,            -- Obsidian markdown
    links           JSONB,                    -- 連結的其他卡片
    created_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_cards_student ON zettel_cards(student_id, card_type, topic);

-- ═══ 原始訊號(量大,可設保留期,個人帳戶層) ═══

CREATE TABLE signal_timeseries (
    id              BIGSERIAL PRIMARY KEY,
    session_id      UUID REFERENCES sessions(id),
    signal_type     TEXT NOT NULL,            -- hrv/pause/expression/fusion_state
    timestamp       NUMERIC(8,2),             -- 相對訓練開始秒數
    payload         JSONB,                    -- 該訊號的原始值與標籤
    retain_until    DATE                      -- 保留期限,過期可清
);
CREATE INDEX idx_signals_session ON signal_timeseries(session_id, signal_type);

-- ═══ 成本記錄(concurrency CostGuard) ═══

CREATE TABLE cost_records (
    id              BIGSERIAL PRIMARY KEY,
    student_id      UUID REFERENCES students(id),
    session_id      UUID REFERENCES sessions(id),
    service         TEXT,                     -- llm/tts/vision
    cost_usd        NUMERIC(8,4),
    used_fallback   BOOLEAN DEFAULT false,
    recorded_at     TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_cost_daily ON cost_records(student_id, recorded_at);

-- ═══ 研究層(去識別化視圖) ═══

-- 去識別化視圖:移除可識別欄位,以 anon_id 取代
CREATE VIEW research_sessions AS
SELECT
    md5(s.student_id::text) AS anon_id,       -- 去識別化雜湊
    s.scenario_id, s.mode, s.confusion_level,
    s.composite_score, s.phase_scores,
    s.started_at, s.ended_at
FROM sessions s;
-- 管理者透過此視圖做群體研究,看不到姓名/email
```

### `db/repository.py` — 資料存取層(摘要)

```python
"""
資料存取層
==========
封裝各模組的讀寫,模組不直接寫 SQL。
個人帳戶層用 student_id;研究層查 research_* 視圖。
"""

class Repository:
    def save_session(self, session, composite_score):
        """訓練結束:存摘要(分數、各階段、成本)。"""
        ...

    def save_signals(self, session_id, signals, retain_days=90):
        """存原始訊號時序,設保留期(預設 90 天)。"""
        ...

    def upsert_weak_point(self, student_id, topic, session_id):
        """弱點累加:同主題 hit_count +1,而非新增。"""
        ...

    def get_student_history(self, student_id, limit=3):
        """M-Agent 用:取近 N 次 DUAT 分析供歷程比對。"""
        ...

    def save_card(self, student_id, card):
        """rag-note 用:存永久卡/訓練卡。"""
        ...

    def daily_cost(self, student_id):
        """CostGuard 用:查今日累計成本。"""
        ...

    def purge_expired_signals(self):
        """定期清理:刪除過保留期的原始訊號。"""
        ...
```

---

## 各模組如何對接

```
case-generator   → scenarios(批次生成、審核、抽案例)
sessions         ← 訓練結束寫摘要
duat-memory      → duat_analyses + get_student_history(歷程比對)
weak_points      ← 各 StageScore 弱點,同主題累加
rag-note         → zettel_cards(永久卡累積靠 topic 關聯)
signal-*         → signal_timeseries(原始訊號,設保留期)
concurrency      → cost_records + daily_cost(成本守門)
研究/管理者       → research_sessions 視圖(去識別化)
```

---

## 設計重點

- **分層存儲控大小**:摘要(分數/弱點/卡片)永久存,量小;原始訊號時序
  量大,進獨立表設 `retain_until`,過期由 `purge_expired_signals` 清。
- **雙層隱私**:個人帳戶層以 student_id 關聯(本人可見完整);研究層用
  `research_sessions` 視圖,md5 去識別化,管理者看不到姓名。符合 IRB。
- **弱點/卡片累加靠 UNIQUE**:weak_points 用 `UNIQUE(student_id, topic)`
  確保同弱點累加 hit_count 而非新增,實現「犯錯幾次」累積。
- **M-Agent 歷程有家了**:duat_analyses 存每次分析,get_student_history
  供 M-Agent 比對進步/老問題——之前懸空的「累積」功能現在落地。
- **成本記錄支撐 CostGuard**:cost_records 讓 concurrency 能查每日花費,
  實現成本守門。
- **Repository 隔離 SQL**:各模組透過 Repository 讀寫,不直接寫 SQL,
  未來換資料庫或調結構,只改 Repository。

---

## 設計紀錄

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v1.0 | 初版:PostgreSQL 全表 + 雙層隱私 + 分層存儲 | 落地所有累積型功能;對接隱私/研究需求 |

---

## 驗證方式

1. 訓練結束,確認 sessions 寫入摘要、signal_timeseries 寫入原始訊號帶保留期。
2. 同一弱點主題第二次出現,確認 weak_points 的 hit_count 累加為 2 而非新增列。
3. M-Agent 呼叫 get_student_history,確認取得過去 DUAT 分析。
4. 查 research_sessions 視圖,確認看不到 name/email,僅去識別化 anon_id。
5. purge_expired_signals 確認刪除過 retain_until 的訊號,不動摘要。
6. CostGuard 查 daily_cost,確認正確加總今日 cost_records。
```
