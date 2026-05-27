"""Personal handout (個人講義) — Wave-4 reflective debrief vertical slice.

Pipeline:
  DB (scores, physio, observations, self-assessment, confidence prediction)
    → aggregator (radar, HRV timeseries, flow curve, spaced repetition)
    → generators (Claude study notes / discussion, Gemini mindmap)
    → HandoutResponse (cached in sessions.generated_handout_json)
"""
