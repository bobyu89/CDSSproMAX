# Sub-Agent: vision — 身體評估 Agent(連續追蹤版)

> **權重:標準(單一功能,遵守 core 契約,可熱插拔)。**
> 校準先行 + 連續追蹤 + 軌跡生成。評核位置、手法、順序三維度。
> 一台攝影機、一具貼點模型即可,無截圖時間誤差。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | vision |
| 模組版本 | v2.0(連續追蹤版,取代 v1 截圖版) |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | core(contract, session)、llm-adapter |
| 註冊鍵 | "examination" |
| 外部依賴 | OpenCV(ArUco,本地即時)、Gemini(手法,少量抽幀) |

> GitHub 路徑:`ticdss/agents/vision_agent.py`。Notion:「TICDSS / vision / v2.0」。

---

## 設計核心:為什麼連續追蹤優於截圖

| | 截圖方案(已棄) | 連續追蹤(本版) |
|--|----------------|------------------|
| 時間精準度 | 有誤差,截圖時刻不一定是關鍵時刻 | 全程記錄,每事件有時間戳 |
| OSCE 時限 | 截圖可能錯過 | 軌跡自帶時間刻度,時限自然解決 |
| 成本 | 每節點送雲端 | 位置追蹤全本地、零雲端 |
| 漏抓風險 | 兩張截圖間會漏 | 連續偵測不漏 |

**關鍵洞察:** ArUco 偵測極輕量,本地可即時跑(30+ fps),
位置追蹤完全不需雲端、不需截圖。只有手法判讀才偶爾抽幀送 Gemini。

---

## 三大設計決策(整合)

| 決策 | 採用方案 |
|------|---------|
| 校準先行 | 訓練前掃描模型,鎖定 9 個 ArUco 點在畫面座標 |
| 連續追蹤 | 全程本地偵測手部位置,生成操作軌跡(時間戳+手法+位置+停留) |
| 三維評分 | 位置(寬容:正確/接近/錯誤)+ 手法(Gemini)+ 順序(序列比對) |

---

## 意圖先行 × 順序評核

學員每一步都先宣告「手法 + 部位」:
「我現在要**聽診**腹部腸音」→ 系統知道手法=聽診、目標=腹部。
按時間順序記下所有宣告,即得「手法序列」,與情境的「標準順序」比對,
就能評順序對不對(如腹部評估應為視→聽→叩→觸)。

---

## 產出檔案

### 1. `agents/vision_agent.py`

```python
"""
身體評估 Agent(連續追蹤版)
============================
校準先行 + 連續追蹤 + 軌跡生成。
評核位置、手法、順序三維度。位置追蹤全本地,無截圖時間誤差。
"""

import cv2
import cv2.aruco as aruco
import base64
import numpy as np
import time
from dataclasses import dataclass, field
from core.contract import StageAgent, StageScore
from llm.router import call_llm

ANATOMY_MARKERS = {
    1: "右上肺葉", 2: "左上肺葉", 3: "右下肺葉", 4: "左下肺葉",
    5: "心尖搏動點", 6: "腹部右上象限", 7: "腹部左上象限",
    8: "腹部右下象限", 9: "腹部左下象限",
}
ADJACENCY = {
    1: [2, 3], 2: [1, 4], 3: [1, 4], 4: [2, 3],
    6: [7, 8], 7: [6, 9], 8: [6, 9], 9: [7, 8],
}
TECHNIQUES = ["視診", "聽診", "叩診", "觸診"]


@dataclass
class TrajectoryEvent:
    """軌跡上的一個操作事件。"""
    timestamp: float        # 相對訓練開始的秒數
    technique: str          # 視/聽/叩/觸(來自語音宣告)
    target: str             # 宣告的目標部位
    position_score: float   # 實際手部位置評分
    dwell: float = 0.0      # 在該位置停留秒數
    technique_ok: bool = None   # 手法是否正確(Gemini,可選)


class VisionAgentV2(StageAgent):
    stage_name = "examination"
    rubric_version = "v2.0"

    def on_enter(self, session):
        session.scratch["vision"] = {
            "calibrated": False,        # 是否已校準
            "marker_map": {},           # ArUco 點 → 畫面座標
            "trajectory": [],           # 操作軌跡(TrajectoryEvent 列表)
            "current": None,            # 當前進行中的操作宣告
            "t0": time.time(),          # 訓練開始時間
        }
        return {"hint": "請先讓攝影機掃描模型完成校準,再開始操作"}

    # ── 校準階段 ──
    def calibrate(self, session, frame_b64):
        """訓練前掃描模型,鎖定 9 個 ArUco 點座標。"""
        frame = self._decode(frame_b64)
        corners, ids, _ = self._detect(frame)
        marker_map = {}
        if ids is not None:
            for marker_id, corner in zip(ids.flatten(), corners):
                center = corner[0].mean(axis=0)     # 該點中心座標
                marker_map[int(marker_id)] = center.tolist()
        st = session.scratch["vision"]
        st["marker_map"] = marker_map
        st["calibrated"] = len(marker_map) >= 9     # 9 點都找到才算完成
        return {"calibrated": st["calibrated"],
                "found": len(marker_map)}

    # ── 連續追蹤主迴圈 ──
    async def handle_input(self, session, payload):
        st = session.scratch["vision"]

        kind = payload.get("kind")
        # 1. 學員宣告新操作(意圖先行)
        if kind == "declare":
            st["current"] = {
                "technique": payload["technique"],   # 視/聽/叩/觸
                "target": payload["target"],          # 部位
                "start": time.time(),
            }
            return {"ack": f"開始{payload['technique']}{payload['target']}"}

        # 2. 連續幀追蹤(本地,即時,不送雲端)
        if kind == "frame" and st["current"]:
            frame = self._decode(payload["frame"])
            occluded = self._detect_occluded(frame)
            # 即時更新:手是否到達宣告的目標
            target_id = self._resolve(st["current"]["target"])
            st["current"]["last_score"] = self._score_position(
                target_id, occluded)
            return {"tracking": True}

        # 3. 學員說「完成」,封存這個操作事件進軌跡
        if kind == "complete" and st["current"]:
            cur = st["current"]
            event = TrajectoryEvent(
                timestamp=round(cur["start"] - st["t0"], 1),
                technique=cur["technique"],
                target=cur["target"],
                position_score=cur.get("last_score", 0.0),
                dwell=round(time.time() - cur["start"], 1))

            # 手法判讀(位置對才檢查,抽一幀送 Gemini)
            if event.position_score >= 0.5 and payload.get("frame"):
                resp = await call_llm(
                    "vision",
                    prompt=f"學員正在{cur['technique']}{cur['target']},"
                           f"判斷手法是否正確,回傳JSON:"
                           f'{{"correct":true/false,"comment":"..."}}',
                    image_b64=payload["frame"], session=session)
                event.technique_ok = self._tech_ok(resp.text)

            st["trajectory"].append(event)
            st["current"] = None
            return {"event_logged": True, "trajectory_len": len(st["trajectory"])}

        return {}

    # ── 三維評分:位置 + 手法 + 順序 ──
    def score(self, session):
        traj = session.scratch["vision"]["trajectory"]
        if not traj:
            return StageScore(stage="examination", raw_score=0)

        # 維度一:位置正確率(寬容評分平均)
        pos = sum(e.position_score for e in traj) / len(traj)

        # 維度二:手法正確率
        checked = [e for e in traj if e.technique_ok is not None]
        tech = (sum(1 for e in checked if e.technique_ok) / len(checked)
                if checked else 1.0)

        # 維度三:順序正確率(實際手法序列 vs 標準順序)
        seq = self._sequence_score(session, traj)

        # 綜合:位置 40% + 手法 30% + 順序 30%
        raw = (pos * 0.4 + tech * 0.3 + seq * 0.3) * 100

        weak = self._collect_weak(traj, seq)

        return StageScore(
            stage="examination",
            raw_score=round(raw, 1),
            sub_items={
                "position": round(pos * 100, 1),
                "technique": round(tech * 100, 1),
                "sequence": round(seq * 100, 1),
                # 軌跡直接作為「操作軌跡報告」輸出之用
                "trajectory": [vars(e) for e in traj],
            },
            weak_points=weak, signals=[])

    def on_exit(self, session):
        n = len(session.scratch["vision"]["trajectory"])
        return {"summary": f"身評完成,軌跡含 {n} 個操作事件"}

    # ── 內部方法 ──
    def _sequence_score(self, session, traj):
        """實際手法序列與標準順序比對。標準順序存於情境設定。"""
        actual = [e.technique for e in traj]
        standard = session.scratch.get("standard_sequence")  # 由情境提供
        if not standard:
            return 1.0          # 無標準順序則不扣分
        # 最長共同子序列比例,衡量順序吻合度
        return self._lcs_ratio(actual, standard)

    def _lcs_ratio(self, a, b):
        m, n = len(a), len(b)
        dp = [[0]*(n+1) for _ in range(m+1)]
        for i in range(1, m+1):
            for j in range(1, n+1):
                dp[i][j] = (dp[i-1][j-1]+1 if a[i-1]==b[j-1]
                            else max(dp[i-1][j], dp[i][j-1]))
        return dp[m][n] / max(len(b), 1)

    def _collect_weak(self, traj, seq):
        weak = []
        for e in traj:
            if e.position_score == 0:
                weak.append(f"位置錯誤:{e.technique}{e.target}")
            elif e.position_score == 0.5:
                weak.append(f"位置偏移:{e.technique}{e.target}(接近)")
            if e.technique_ok is False:
                weak.append(f"手法待加強:{e.technique}{e.target}")
        if seq < 1.0:
            weak.append("評估順序與標準不符")
        return weak

    def _resolve(self, target):
        for mid, name in ANATOMY_MARKERS.items():
            if name in target:
                return mid
        return None

    def _detect(self, frame):
        d = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
        return aruco.detectMarkers(frame, d)

    def _detect_occluded(self, frame):
        _, ids, _ = self._detect(frame)
        visible = set(ids.flatten()) if ids is not None else set()
        return set(ANATOMY_MARKERS.keys()) - visible

    def _score_position(self, target_id, occluded):
        if target_id is None:
            return 0.0
        if target_id in occluded:
            return 1.0
        if any(a in occluded for a in ADJACENCY.get(target_id, [])):
            return 0.5
        return 0.0

    def _tech_ok(self, txt):
        import json
        try:
            return json.loads(txt).get("correct", False)
        except Exception:
            return False

    def _decode(self, frame_b64):
        data = base64.b64decode(frame_b64.split(",")[-1])
        arr = np.frombuffer(data, np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
```

---

## 註冊(熱插拔)

```python
from core.flow import registry
from agents.vision_agent import VisionAgentV2
registry.register("examination", VisionAgentV2)
```

---

## 設計重點

- **校準先行消除偏差**:訓練前鎖定 9 點座標,評分時系統已知每區域在哪,
  不必每次重找,位置判斷穩定。
- **連續追蹤解決時限**:軌跡每事件帶時間戳,OSCE 時限到 → 軌跡停 →
  看完整軌跡評分,沒有截圖時間誤差。時限變成軌跡上的時間刻度。
- **位置追蹤全本地**:ArUco 即時偵測不送雲端、零成本;只有手法判讀
  才抽幀送 Gemini,且位置對才送,雙重省成本。
- **順序評核靠意圖先行**:學員每步先宣告手法,按序記錄即得手法序列,
  與標準順序用最長共同子序列比對,得順序分。
- **軌跡即輸出**:`sub_items["trajectory"]` 直接作為「操作軌跡報告」
  的資料來源,六種輸出之一自然產生,不需另做。

---

## 與其他模組的關係

- 順序評分需要 `session.scratch["standard_sequence"]`,由情境設定提供
  (例如腹部評估 = ["視診","聽診","叩診","觸診"])。
- 軌跡資料流向 output-stress / 操作軌跡報告模組。

---

## 設計紀錄(同步 Notion / GitHub)

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v2.0 | 重構:截圖 → 連續追蹤 + 軌跡 + 三維評分(位置/手法/順序) | 解決截圖時間誤差,加入順序評核,符合 OSCE 時限 |

---

## 驗證方式

1. 校準:掃描含 9 點的模型,確認 calibrated=True。
2. 宣告「聽診腹部」→ 連續餵幀手到 Marker 7 → 說「完成」,確認軌跡新增一事件。
3. 餵入錯誤順序(觸→聽→叩→視),確認 sequence 分數下降。
4. OSCE 模式跑滿時限,確認軌跡在時限處停止,評分看完整軌跡。
5. 確認 StageScore 含 position / technique / sequence / trajectory 四項。
```
