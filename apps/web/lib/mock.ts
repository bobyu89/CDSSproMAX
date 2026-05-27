// Mock data for UI development before backend endpoints exist.
import type {
  DuatScore,
  Rubric,
  SessionRecord,
} from "@ticdss/shared-types";

export const MOCK_SESSIONS: SessionRecord[] = [
  {
    id: "sess-001",
    participantId: "stu-2025-001",
    caseId: "CASE-01",
    mode: "exam",
    phase: "diagnosis",
    startedAt: "2026-05-27T08:30:00Z",
    endedAt: "2026-05-27T08:48:12Z",
  },
  {
    id: "sess-002",
    participantId: "stu-2025-014",
    caseId: "CASE-04",
    mode: "practice",
    phase: "review",
    startedAt: "2026-05-26T14:10:00Z",
    endedAt: "2026-05-26T14:32:45Z",
  },
  {
    id: "sess-003",
    participantId: "stu-2025-022",
    caseId: "CASE-07",
    mode: "practice",
    phase: "inquiry",
    startedAt: "2026-05-27T09:05:00Z",
    endedAt: null,
  },
];

export const MOCK_CASE_TITLES: Record<string, string> = {
  "CASE-01": "CASE-01 急性胸痛 — 冠心症疑似",
  "CASE-04": "CASE-04 腹痛 — 闌尾炎",
  "CASE-07": "CASE-07 呼吸困難 — 氣喘急性發作",
};

export const MOCK_DUAT_SCORES: Record<string, DuatScore[]> = {
  "sess-001": [
    {
      id: "ds-001",
      sessionId: "sess-001",
      rubricItemId: "lqqopera.location",
      eConfidence: 0.92,
      sScore: 5,
      aAdvocateScore: 0.88,
      arbiterDecision: "accept",
      arbiterConfidence: "high",
      finalScore: 5,
      graderAction: null,
      graderReason: null,
    },
    {
      id: "ds-002",
      sessionId: "sess-001",
      rubricItemId: "lqqopera.quality",
      eConfidence: 0.81,
      sScore: 4,
      aAdvocateScore: 0.72,
      arbiterDecision: "accept",
      arbiterConfidence: "high",
      finalScore: 4,
      graderAction: null,
      graderReason: null,
    },
    {
      id: "ds-003",
      sessionId: "sess-001",
      rubricItemId: "lqqopera.quantity",
      eConfidence: 0.55,
      sScore: 3,
      aAdvocateScore: 0.45,
      arbiterDecision: "flag",
      arbiterConfidence: "medium",
      finalScore: 3,
      graderAction: null,
      graderReason: null,
    },
    {
      id: "ds-004",
      sessionId: "sess-001",
      rubricItemId: "lqqopera.onset",
      eConfidence: 0.88,
      sScore: 5,
      aAdvocateScore: 0.91,
      arbiterDecision: "accept",
      arbiterConfidence: "high",
      finalScore: 5,
      graderAction: null,
      graderReason: null,
    },
    {
      id: "ds-005",
      sessionId: "sess-001",
      rubricItemId: "lqqopera.precipitating",
      eConfidence: 0.42,
      sScore: 2,
      aAdvocateScore: 0.7,
      arbiterDecision: "force_human",
      arbiterConfidence: "low",
      finalScore: null,
      graderAction: null,
      graderReason: null,
    },
    {
      id: "ds-006",
      sessionId: "sess-001",
      rubricItemId: "lqqopera.extension",
      eConfidence: 0.78,
      sScore: 4,
      aAdvocateScore: 0.65,
      arbiterDecision: "accept",
      arbiterConfidence: "medium",
      finalScore: 4,
      graderAction: null,
      graderReason: null,
    },
    {
      id: "ds-007",
      sessionId: "sess-001",
      rubricItemId: "lqqopera.relieving",
      eConfidence: 0.6,
      sScore: 3,
      aAdvocateScore: 0.4,
      arbiterDecision: "flag",
      arbiterConfidence: "medium",
      finalScore: 3,
      graderAction: null,
      graderReason: null,
    },
    {
      id: "ds-008",
      sessionId: "sess-001",
      rubricItemId: "lqqopera.associated_symptoms",
      eConfidence: 0.9,
      sScore: 5,
      aAdvocateScore: 0.85,
      arbiterDecision: "accept",
      arbiterConfidence: "high",
      finalScore: 5,
      graderAction: null,
      graderReason: null,
    },
  ],
  "sess-002": [],
  "sess-003": [],
};

const LQQOPERA_DIMENSIONS: Record<string, string> = {
  "lqqopera.location": "Location 位置",
  "lqqopera.quality": "Quality 性質",
  "lqqopera.quantity": "Quantity 程度",
  "lqqopera.onset": "Onset 發作",
  "lqqopera.precipitating": "Precipitating 誘發/緩解",
  "lqqopera.extension": "Extension 擴散",
  "lqqopera.relieving": "Relieving 緩解",
  "lqqopera.associated_symptoms": "Associated 伴隨症狀",
};

export function dimensionLabel(rubricItemId: string): string {
  return LQQOPERA_DIMENSIONS[rubricItemId] ?? rubricItemId;
}

export const MOCK_RUBRIC: Rubric = {
  rubricId: "rubric.lqqopera.v1",
  type: "lqqopera",
  version: "1.0.0",
  items: [
    {
      id: "lqqopera.location",
      dimension: "Location 位置",
      weight: 1,
      maxScore: 5,
      criteria: [
        { level: 5, descriptor: "完整描述疼痛位置與分區" },
        { level: 3, descriptor: "僅描述大致部位" },
        { level: 0, descriptor: "未詢問" },
      ],
    },
    {
      id: "lqqopera.quality",
      dimension: "Quality 性質",
      weight: 1,
      maxScore: 5,
      criteria: [
        { level: 5, descriptor: "明確區分壓迫/刺痛/灼熱等" },
        { level: 3, descriptor: "粗略描述" },
        { level: 0, descriptor: "未詢問" },
      ],
    },
    {
      id: "lqqopera.onset",
      dimension: "Onset 發作",
      weight: 1,
      maxScore: 5,
      criteria: [
        { level: 5, descriptor: "詳細詢問發作時間與情境" },
        { level: 3, descriptor: "僅問何時開始" },
        { level: 0, descriptor: "未詢問" },
      ],
    },
  ],
};

export const MOCK_EVIDENCE: Record<
  string,
  { speaker: "student" | "patient"; text: string }[]
> = {
  "ds-001": [
    { speaker: "student", text: "請問您的疼痛主要在哪個位置？" },
    { speaker: "patient", text: "在胸口正中央，有時候會延伸到左手臂。" },
  ],
  "ds-002": [
    { speaker: "student", text: "這個痛是怎樣的感覺？刺痛還是壓迫感？" },
    { speaker: "patient", text: "像有人壓在胸口上一樣悶悶的。" },
  ],
  "ds-003": [
    { speaker: "student", text: "痛的程度大概多少？" },
    { speaker: "patient", text: "蠻痛的。" },
  ],
};

export const MOCK_ADVOCATE_REPORTS: Record<string, string> = {
  "ds-001":
    "S-Agent 給予 5 分，依據完整定位與輻射敘述。對抗審查無顯著反例，建議接受。",
  "ds-003":
    "S-Agent 給予 3 分，然而學生並未追問 0-10 數值量表，可能高估。建議標記給人工複核。",
  "ds-005":
    "證據不足且雙評分歧異過大（S=2, A=0.7），E-Agent 信心 0.42 偏低，強制人工裁決。",
};
