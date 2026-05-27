"""ArUco marker ID → 解剖位置 對應表（半身假人）.

15 個標籤覆蓋 NP OSCE 常用評估部位。每張 A4 列印一個 marker
（約 5 × 5 cm，DICT_4X4_50），貼在假人對應位置。

對應表必須與 PE rubric 的 `body_region` 欄位同步：
  例如 rubric "pe.lung.auscultation.right_lower" 的 body_region =
  "right_lower_lung" 必須匹配某個 marker 的 region。
"""

from __future__ import annotations

from enum import Enum
from typing import NamedTuple


class AnatomyRegion(str, Enum):
    """半身假人標準解剖位置（snake_case 對齊 rubric body_region 欄位）"""

    # 心血管
    PMI = "pmi"  # 心尖搏動點
    AORTIC = "aortic_area"  # 主動脈瓣聽診區（右胸骨第二肋）
    PULMONIC = "pulmonic_area"  # 肺動脈瓣（左胸骨第二肋）
    ERBS_POINT = "erbs_point"  # Erb's point（左胸骨第三肋）
    TRICUSPID = "tricuspid_area"  # 三尖瓣（左胸骨下緣）
    # NOTE: MITRAL ≈ PMI — for OSCE scoring purposes the二尖瓣 listening
    # point is the same physical location as PMI, so we don't allocate
    # a separate ArUco marker. Rubric items targeting "mitral_area"
    # should treat detection of PMI as the matching region. Kept in the
    # enum for completeness so future rubrics can name it explicitly.
    MITRAL = "mitral_area"

    # 頸部
    JVP = "jvp"  # 頸靜脈壓
    CAROTID_R = "carotid_right"
    CAROTID_L = "carotid_left"

    # 肺
    LUNG_RIGHT_UPPER = "right_upper_lung"
    LUNG_LEFT_UPPER = "left_upper_lung"
    LUNG_RIGHT_LOWER = "right_lower_lung"
    LUNG_LEFT_LOWER = "left_lower_lung"

    # 腹部四象限
    ABD_RUQ = "abdomen_ruq"  # 右上 — 含肝/膽
    ABD_LUQ = "abdomen_luq"  # 左上 — 含脾/胃
    ABD_RLQ = "abdomen_rlq"  # 右下 — 含闌尾/McBurney
    ABD_LLQ = "abdomen_llq"  # 左下


class MarkerSpec(NamedTuple):
    """單個 marker 的元資料 — 給校準 UI / PDF 生成用"""

    aruco_id: int
    region: AnatomyRegion
    label_zh: str
    print_hint: str  # 貼附位置的口語說明


# ArUco DICT_4X4_50 提供 50 個 marker，我們用 ID 1-16。
# 順序刻意按解剖區塊分組，方便列印時對齊。
ANATOMY_MARKERS: dict[int, MarkerSpec] = {
    1: MarkerSpec(1, AnatomyRegion.PMI, "心尖搏動點", "左鎖骨中線 × 第五肋間"),
    2: MarkerSpec(2, AnatomyRegion.AORTIC, "主動脈瓣區", "右胸骨第二肋間"),
    3: MarkerSpec(3, AnatomyRegion.PULMONIC, "肺動脈瓣區", "左胸骨第二肋間"),
    4: MarkerSpec(4, AnatomyRegion.ERBS_POINT, "Erb's point", "左胸骨第三肋間"),
    5: MarkerSpec(5, AnatomyRegion.TRICUSPID, "三尖瓣區", "左胸骨下緣（劍突旁）"),
    6: MarkerSpec(6, AnatomyRegion.JVP, "頸靜脈壓", "右側胸鎖乳突肌中段"),
    7: MarkerSpec(7, AnatomyRegion.CAROTID_R, "右頸動脈", "右胸鎖乳突肌前緣"),
    8: MarkerSpec(8, AnatomyRegion.CAROTID_L, "左頸動脈", "左胸鎖乳突肌前緣"),
    9: MarkerSpec(9, AnatomyRegion.LUNG_RIGHT_UPPER, "右上肺葉", "右鎖骨下方第二肋間"),
    10: MarkerSpec(10, AnatomyRegion.LUNG_LEFT_UPPER, "左上肺葉", "左鎖骨下方第二肋間"),
    11: MarkerSpec(11, AnatomyRegion.LUNG_RIGHT_LOWER, "右下肺葉", "右側第八肋間腋中線"),
    12: MarkerSpec(12, AnatomyRegion.LUNG_LEFT_LOWER, "左下肺葉", "左側第八肋間腋中線"),
    13: MarkerSpec(13, AnatomyRegion.ABD_RUQ, "腹部右上象限", "肋緣下右鎖骨中線"),
    14: MarkerSpec(14, AnatomyRegion.ABD_LUQ, "腹部左上象限", "肋緣下左鎖骨中線"),
    15: MarkerSpec(15, AnatomyRegion.ABD_RLQ, "腹部右下象限", "右髂前上棘與臍連線中點（McBurney）"),
    16: MarkerSpec(16, AnatomyRegion.ABD_LLQ, "腹部左下象限", "左下腹"),
}


# Reverse lookup: region → aruco_id
ANATOMY_REGIONS: dict[AnatomyRegion, int] = {
    spec.region: aid for aid, spec in ANATOMY_MARKERS.items()
}


def marker_to_region(aruco_id: int) -> AnatomyRegion | None:
    spec = ANATOMY_MARKERS.get(aruco_id)
    return spec.region if spec else None


def region_to_marker(region: AnatomyRegion) -> int | None:
    return ANATOMY_REGIONS.get(region)
