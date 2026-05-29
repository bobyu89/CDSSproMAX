"""
身體評估 Agent(連續追蹤版) (Builder vision.md / v2.0)
=======================================================
校準先行 + 連續追蹤 + 軌跡生成。評核位置、手法、順序三維度。
位置追蹤全本地(ArUco),無截圖時間誤差;只有手法判讀才抽幀送 Gemini。

實作備註:
- cv2/numpy 採延遲載入(方法內 import),OpenCV 未安裝時 module 仍可被 import。
- ANATOMY_MARKERS 沿用 builder 規格的 9 點 + 鄰接表;production 可改接
  src.vision.anatomy_map 的 15 點(follow-up,不影響契約)。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass

from src.core.contract import StageAgent, StageScore
from src.llm.router import call_llm

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

    timestamp: float
    technique: str
    target: str
    position_score: float
    dwell: float = 0.0
    technique_ok: bool | None = None


class VisionAgentV2(StageAgent):
    stage_name = "examination"
    rubric_version = "v2.0"

    def on_enter(self, session):
        session.scratch["vision"] = {
            "calibrated": False,
            "marker_map": {},
            "trajectory": [],
            "current": None,
            "t0": time.time(),
        }
        return {"hint": "請先讓攝影機掃描模型完成校準,再開始操作"}

    # ── 校準階段 ──
    def calibrate(self, session, frame_b64):
        frame = self._decode(frame_b64)
        corners, ids = self._detect(frame)
        marker_map = {}
        if ids is not None:
            for marker_id, corner in zip(ids.flatten(), corners):
                center = corner[0].mean(axis=0)
                marker_map[int(marker_id)] = center.tolist()
        st = session.scratch["vision"]
        st["marker_map"] = marker_map
        st["calibrated"] = len(marker_map) >= 9
        return {"calibrated": st["calibrated"], "found": len(marker_map)}

    # ── 連續追蹤主迴圈 ──
    async def handle_input(self, session, payload):
        st = session.scratch["vision"]
        kind = payload.get("kind")

        if kind == "declare":  # 意圖先行:宣告手法 + 部位
            st["current"] = {
                "technique": payload["technique"],
                "target": payload["target"],
                "start": time.time(),
            }
            return {"ack": f"開始{payload['technique']}{payload['target']}"}

        if kind == "frame" and st["current"]:  # 連續幀追蹤(本地、即時)
            frame = self._decode(payload["frame"])
            occluded = self._detect_occluded(frame)
            target_id = self._resolve(st["current"]["target"])
            st["current"]["last_score"] = self._score_position(target_id, occluded)
            return {"tracking": True}

        if kind == "complete" and st["current"]:  # 封存操作事件
            cur = st["current"]
            event = TrajectoryEvent(
                timestamp=round(cur["start"] - st["t0"], 1),
                technique=cur["technique"],
                target=cur["target"],
                position_score=cur.get("last_score", 0.0),
                dwell=round(time.time() - cur["start"], 1),
            )
            # 手法判讀(位置對才檢查,抽一幀送 Gemini)
            if event.position_score >= 0.5 and payload.get("frame"):
                try:
                    resp = await call_llm(
                        "vision",
                        prompt=f"學員正在{cur['technique']}{cur['target']},"
                        f"判斷手法是否正確,回傳JSON:"
                        f'{{"correct":true/false,"comment":"..."}}',
                        image_b64=payload["frame"],
                        session=session,
                        json_mode=True,
                    )
                    event.technique_ok = self._tech_ok(resp.text)
                except Exception:  # noqa: BLE001 — 手法判讀失敗不可中斷
                    event.technique_ok = None
            st["trajectory"].append(event)
            st["current"] = None
            return {"event_logged": True, "trajectory_len": len(st["trajectory"])}

        return {}

    # ── 三維評分:位置 + 手法 + 順序 ──
    def score(self, session):
        traj = session.scratch["vision"]["trajectory"]
        if not traj:
            return StageScore(stage="examination", raw_score=0)

        pos = sum(e.position_score for e in traj) / len(traj)
        checked = [e for e in traj if e.technique_ok is not None]
        tech = (
            sum(1 for e in checked if e.technique_ok) / len(checked) if checked else 1.0
        )
        seq = self._sequence_score(session, traj)
        raw = (pos * 0.4 + tech * 0.3 + seq * 0.3) * 100

        return StageScore(
            stage="examination",
            raw_score=round(raw, 1),
            sub_items={
                "position": round(pos * 100, 1),
                "technique": round(tech * 100, 1),
                "sequence": round(seq * 100, 1),
                "trajectory": [vars(e) for e in traj],
            },
            weak_points=self._collect_weak(traj, seq),
            signals=[],
        )

    def on_exit(self, session):
        n = len(session.scratch["vision"]["trajectory"])
        return {"summary": f"身評完成,軌跡含 {n} 個操作事件"}

    # ── 內部方法 ──
    def _sequence_score(self, session, traj):
        actual = [e.technique for e in traj]
        standard = session.scratch.get("standard_sequence")
        if not standard:
            return 1.0
        return self._lcs_ratio(actual, standard)

    def _lcs_ratio(self, a, b):
        m, n = len(a), len(b)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                dp[i][j] = (
                    dp[i - 1][j - 1] + 1
                    if a[i - 1] == b[j - 1]
                    else max(dp[i - 1][j], dp[i][j - 1])
                )
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
            if name in target or target in name:
                return mid
        return None

    # ── ArUco(延遲載入 cv2) ──
    def _aruco(self):
        import cv2.aruco as aruco

        return aruco

    def _detect(self, frame):
        aruco = self._aruco()
        d = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
        corners, ids, _ = aruco.detectMarkers(frame, d)
        return corners, ids

    def _detect_occluded(self, frame):
        _, ids = self._detect(frame)
        visible = set(ids.flatten()) if ids is not None else set()
        return set(ANATOMY_MARKERS.keys()) - visible

    def _score_position(self, target_id, occluded):
        if target_id is None:
            return 0.0
        if target_id in occluded:  # 手遮住目標 marker = 摸對位置
            return 1.0
        if any(a in occluded for a in ADJACENCY.get(target_id, [])):
            return 0.5  # 摸到鄰近區域(寬容)
        return 0.0

    def _tech_ok(self, txt):
        try:
            return json.loads(txt).get("correct", False)
        except Exception:  # noqa: BLE001
            return False

    def _decode(self, frame_b64):
        import cv2
        import numpy as np

        data = __import__("base64").b64decode(frame_b64.split(",")[-1])
        arr = np.frombuffer(data, np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
