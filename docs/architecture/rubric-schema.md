# Rubric JSON Schema

LQQOPERA + PE 雙軌 Rubric 的機器可讀規格。對應 Protocol §四.(四)。

## Rubric 結構

```json
{
  "rubric_id": "lqqopera.v1",
  "type": "lqqopera",
  "version": "1.0.0",
  "items": [
    {
      "id": "lqqopera.location",
      "dimension": "Location",
      "weight": 1.0,
      "max_score": 5,
      "criteria": [
        {
          "level": 5,
          "descriptor": "主動詢問痛點位置，並追問放射路徑與相對位置"
        },
        {
          "level": 3,
          "descriptor": "詢問痛點位置但未追問放射或相對位置"
        },
        {
          "level": 1,
          "descriptor": "僅提及痛點，未明確詢問位置"
        },
        {
          "level": 0,
          "descriptor": "完全未詢問位置維度"
        }
      ],
      "evidence_anchors": [
        "位置", "哪裡", "放射", "傳到", "延伸"
      ]
    }
  ]
}
```

## LQQOPERA 八維度（id 命名）

- `lqqopera.location`
- `lqqopera.quality`
- `lqqopera.quantity`
- `lqqopera.onset`
- `lqqopera.precipitating`
- `lqqopera.extension`
- `lqqopera.relieving`
- `lqqopera.associated_symptoms`

## PE Rubric Item 範例

```json
{
  "id": "pe.lung.auscultation.right_lower",
  "dimension": "Auscultation",
  "body_region": "right_lower_lung",
  "weight": 1.0,
  "max_score": 5,
  "criteria": [...],
  "expected_action": "auscultation",
  "min_duration_seconds": 3.0
}
```

`expected_action` 與 `min_duration_seconds` 是給 Wave 1.5 Vision Agent 用的，
Wave 1 階段先存著不評。
