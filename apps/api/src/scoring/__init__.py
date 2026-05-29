"""TICDSS 評分層 (Builder realtime-scorer + duat-flow).

- realtime.py     System 1 即時評分(練習模式)
- duat/           System 2 深度驗證(O→E‖S→A→M)+ 驗證層
"""

from src.scoring.realtime import realtime_score

__all__ = ["realtime_score"]
