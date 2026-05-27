// Mock data for UI development before backend endpoints exist.
import type {
  DuatScore,
  HandoutResponse,
  Rubric,
  SessionRecord,
  Transcript,
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

export const MOCK_TRANSCRIPTS: Record<string, Transcript[]> = {
  "sess-001": [
    {
      id: "tr-001",
      sessionId: "sess-001",
      speaker: "student",
      text: "您好，請問今天哪裡不舒服？",
      audioPath: null,
      startedMs: 0,
      endedMs: 2500,
      createdAt: "2026-05-27T08:30:05Z",
    },
    {
      id: "tr-002",
      sessionId: "sess-001",
      speaker: "patient",
      text: "我胸口悶悶的，已經痛了快一個小時。",
      audioPath: null,
      startedMs: 3000,
      endedMs: 7200,
      createdAt: "2026-05-27T08:30:12Z",
    },
    {
      id: "tr-003",
      sessionId: "sess-001",
      speaker: "student",
      text: "請問疼痛的位置主要在哪裡？會不會延伸到別的地方？",
      audioPath: null,
      startedMs: 8000,
      endedMs: 12500,
      createdAt: "2026-05-27T08:30:20Z",
    },
    {
      id: "tr-004",
      sessionId: "sess-001",
      speaker: "patient",
      text: "在胸口正中央這邊，有時候會延伸到左手臂內側。",
      audioPath: null,
      startedMs: 13000,
      endedMs: 18000,
      createdAt: "2026-05-27T08:30:28Z",
    },
    {
      id: "tr-005",
      sessionId: "sess-001",
      speaker: "student",
      text: "這種痛的感覺像什麼？是刺痛、悶痛還是壓迫感？",
      audioPath: null,
      startedMs: 19000,
      endedMs: 23500,
      createdAt: "2026-05-27T08:30:36Z",
    },
    {
      id: "tr-006",
      sessionId: "sess-001",
      speaker: "patient",
      text: "像有人壓在胸口上一樣，悶悶緊緊的。",
      audioPath: null,
      startedMs: 24000,
      endedMs: 28000,
      createdAt: "2026-05-27T08:30:44Z",
    },
  ],
  "sess-002": [],
  "sess-003": [],
};

// ─── Admin / participant mocks ───────────────────────────────────────────

export interface MockParticipant {
  id: string;
  code: string;
  name: string;
  role: "student" | "teacher" | "admin";
  sessionCount: number;
  meanScore: number;
  lastLoginAt: string;
}

export const MOCK_PARTICIPANTS: MockParticipant[] = [
  {
    id: "stu-2025-001",
    code: "P001",
    name: "王雅雯",
    role: "student",
    sessionCount: 12,
    meanScore: 4.3,
    lastLoginAt: "2026-05-27T08:30:00Z",
  },
  {
    id: "stu-2025-014",
    code: "P002",
    name: "陳柏宇",
    role: "student",
    sessionCount: 9,
    meanScore: 3.8,
    lastLoginAt: "2026-05-26T14:10:00Z",
  },
  {
    id: "stu-2025-022",
    code: "P003",
    name: "林思妤",
    role: "student",
    sessionCount: 15,
    meanScore: 4.6,
    lastLoginAt: "2026-05-27T09:05:00Z",
  },
  {
    id: "stu-2025-031",
    code: "P004",
    name: "張詠淳",
    role: "student",
    sessionCount: 7,
    meanScore: 3.5,
    lastLoginAt: "2026-05-25T16:42:00Z",
  },
  {
    id: "stu-2025-045",
    code: "P005",
    name: "黃彥廷",
    role: "student",
    sessionCount: 11,
    meanScore: 4.1,
    lastLoginAt: "2026-05-27T07:15:00Z",
  },
  {
    id: "tea-2025-001",
    code: "T001",
    name: "吳玟臻 老師",
    role: "teacher",
    sessionCount: 0,
    meanScore: 0,
    lastLoginAt: "2026-05-27T10:00:00Z",
  },
  {
    id: "adm-2025-001",
    code: "A001",
    name: "系統管理員",
    role: "admin",
    sessionCount: 0,
    meanScore: 0,
    lastLoginAt: "2026-05-27T11:20:00Z",
  },
];

export interface MockAdminDashboard {
  totalParticipants: number;
  totalSessions: number;
  meanScore: number;
  completionRate: number; // 0-1
  perParticipantScores: { code: string; name: string; meanScore: number }[];
}

export const MOCK_ADMIN_DASHBOARD: MockAdminDashboard = {
  totalParticipants: 5,
  totalSessions: 54,
  meanScore: 4.06,
  completionRate: 0.83,
  perParticipantScores: MOCK_PARTICIPANTS.filter((p) => p.role === "student").map(
    (p) => ({ code: p.code, name: p.name, meanScore: p.meanScore }),
  ),
};

export const MOCK_ADVOCATE_REPORTS: Record<string, string> = {
  "ds-001":
    "S-Agent 給予 5 分，依據完整定位與輻射敘述。對抗審查無顯著反例，建議接受。",
  "ds-003":
    "S-Agent 給予 3 分，然而學生並未追問 0-10 數值量表，可能高估。建議標記給人工複核。",
  "ds-005":
    "證據不足且雙評分歧異過大（S=2, A=0.7），E-Agent 信心 0.42 偏低，強制人工裁決。",
};

// ─── 個人講義 Mock ──────────────────────────────────────────────────────

function buildMockHrv(): HandoutResponse["hrv"] {
  const points: HandoutResponse["hrv"] = [];
  // 18 minutes, sample every 18 seconds → 60 points
  for (let i = 0; i < 60; i++) {
    const tMin = +(i * 0.3).toFixed(2);
    // baseline 78bpm, stress dip RMSSD between min 6 and 12
    const stressful = tMin >= 6 && tMin <= 12;
    const hr = Math.round(
      78 + (stressful ? 14 : 4) + Math.sin(i / 4) * 3 + (Math.random() - 0.5) * 4,
    );
    const rmssd = Math.max(
      8,
      Math.round(
        (stressful ? 16 : 42) + Math.cos(i / 3) * 5 + (Math.random() - 0.5) * 6,
      ),
    );
    let phase: string | null = null;
    if (tMin < 3) phase = "Intro";
    else if (tMin < 9) phase = "Inquiry";
    else if (tMin < 14) phase = "PE";
    else phase = "Diagnosis";
    points.push({ tMin, hr, rmssd, phase });
  }
  return points;
}

function buildMockFlow(): HandoutResponse["flow"] {
  const out: HandoutResponse["flow"] = [];
  for (let i = 0; i < 18; i++) {
    const tMin = i;
    // challenge ramps up; skill grows slower
    const challenge = +(2 + (i / 18) * 2.5 + Math.sin(i / 2) * 0.4).toFixed(2);
    const skill = +(1.8 + (i / 18) * 2.2 + Math.cos(i / 3) * 0.3).toFixed(2);
    const diff = challenge - skill;
    let zone: "flow" | "anxiety" | "boredom" | "apathy";
    if (Math.abs(diff) < 0.5) zone = challenge > 3 ? "flow" : "apathy";
    else if (diff >= 0.5) zone = "anxiety";
    else zone = "boredom";
    out.push({ tMin, challenge, skill, zone });
  }
  return out;
}

export const MOCK_HANDOUT: HandoutResponse = {
  sessionId: "sess-001",
  caseTitle: "CASE-01 急性胸痛 — 冠心症疑似",
  caseCode: "CASE-01",
  mode: "exam",
  completedAt: "2026-05-27T08:48:12Z",
  totalScore: 3.88,
  radar: [
    { axis: "Location", label: "位置", score: 5 },
    { axis: "Quality", label: "性質", score: 4 },
    { axis: "Quantity", label: "強度", score: 3 },
    { axis: "Onset", label: "發作", score: 5 },
    { axis: "Precipitating", label: "誘發/緩解", score: 4 },
    { axis: "Extension", label: "放射", score: 4 },
    { axis: "Relieving", label: "緩解因子", score: 3 },
    { axis: "Associated", label: "伴隨症狀", score: 3 },
  ],
  hrv: buildMockHrv(),
  flow: buildMockFlow(),
  mindmap: [
    { id: "n0", label: "急性胸痛", kind: "root", parentId: null,
      description: "62 歲男性突發胸痛，鑑別冠心症、主動脈剝離、肺栓塞。" },
    { id: "n1", label: "LQQOPERA 八向度", kind: "key_concept", parentId: "n0",
      description: "標準症狀問診框架，確保資訊完整。" },
    { id: "n2", label: "Quantity 強度量化不足", kind: "weakness", parentId: "n1",
      description: "未使用 0-10 數值量表詢問，導致嚴重度判斷不明。" },
    { id: "n3", label: "Associated 漏問", kind: "weakness", parentId: "n1",
      description: "未詢問冒冷汗、噁心、放射至左臂等冠心症關聯症狀。" },
    { id: "n4", label: "鑑別診斷邏輯", kind: "key_concept", parentId: "n0",
      description: "STEMI vs NSTEMI vs 不穩定型心絞痛分層思考。" },
    { id: "n5", label: "HEART Score 應用", kind: "action", parentId: "n4",
      description: "下次練習嘗試套用 HEART score 進行風險分層。" },
    { id: "n6", label: "壓力管理", kind: "key_concept", parentId: "n0",
      description: "HRV 顯示第 6-12 分鐘進入焦慮區，需練習臨床冷靜。" },
    { id: "n7", label: "深呼吸 box breathing", kind: "action", parentId: "n6",
      description: "4-4-4-4 呼吸法可降低交感神經興奮。" },
    { id: "n8", label: "證據參考", kind: "reference", parentId: "n4",
      description: "AHA/ACC 2023 NSTEMI 指引。" },
    { id: "n9", label: "UpToDate 章節", kind: "reference", parentId: "n1",
      description: "Evaluation of acute chest pain in the ED (2025)." },
    { id: "n10", label: "下次練習目標", kind: "action", parentId: "n0",
      description: "重點補強 Quantity / Associated / Relieving 三向度。" },
    { id: "n11", label: "Csikszentmihalyi 心流", kind: "reference", parentId: "n6",
      description: "挑戰-技能比例維持在 ±0.5 範圍內可進入心流。" },
  ],
  studyNotes: [
    {
      id: "sn1",
      heading: "1. 急性胸痛鑑別診斷重點",
      body: "胸痛三大致命鑑別：(1) ACS（STEMI/NSTEMI/UA）— 壓迫感、冒冷汗、放射至左臂或下顎；(2) 主動脈剝離 — 撕裂痛、放射至背、兩側血壓不對稱；(3) 肺栓塞 — 銳痛、呼吸困難、SpO₂ 下降。問診時務必同時排除這三項。",
      citations: ["AHA/ACC 2023 NSTEMI Guideline", "UpToDate 2025 Acute Chest Pain"],
    },
    {
      id: "sn2",
      heading: "2. Quantity 量化技巧",
      body: "本次評分中 Quantity 僅得 3 分。建議使用 0-10 數值評估量表（NRS），並追問「最痛時幾分？現在幾分？」以建立疼痛軌跡。對於 ACS 病人，疼痛強度與心肌缺血程度未必成正比，但仍是重要追蹤指標。",
      citations: ["IASP Pain Assessment 2020"],
    },
    {
      id: "sn3",
      heading: "3. Associated 症狀關鍵詞",
      body: "ACS 高風險伴隨症狀：冒冷汗（diaphoresis）、噁心嘔吐、呼吸困難、頭暈、瀕死感（sense of doom）。下次練習至少問三項。",
      citations: ["Braunwald Heart Disease 12e Ch.59"],
    },
    {
      id: "sn4",
      heading: "4. 壓力與表現曲線",
      body: "HRV 監測顯示你在第 6-12 分鐘時 RMSSD 從 42ms 驟降至 16ms，進入焦慮區。建議在 PE 階段前進行 box breathing（吸 4 秒、憋 4 秒、吐 4 秒、停 4 秒）以恢復副交感神經張力。",
      citations: ["Thayer & Lane 2009 Neuroscience & Biobehavioral Reviews"],
    },
  ],
  discussion: [
    { id: "d1", question: "本案例中你最先排除哪一項致命鑑別？依據是什麼？",
      why: "檢驗學生是否具備系統化排除邏輯，避免錨定偏誤。" },
    { id: "d2", question: "若病人 troponin 第一次陰性，你下一步會做什麼？",
      why: "測試對 serial troponin 與 HEART score 流程的掌握度。" },
    { id: "d3", question: "你在 PE 階段感到緊張嗎？HRV 顯示明顯壓力反應。",
      why: "引導學生意識生理回饋並建立自我調節習慣。" },
    { id: "d4", question: "若這位病人實際為主動脈剝離，你的問診遺漏會造成什麼後果？",
      why: "強化 worst-case-scenario 思考，培養臨床警覺。" },
  ],
  spacedRepetition: [
    {
      id: "sr1",
      dimension: "Quantity 強度量化",
      reviewDates: ["2026-05-29", "2026-06-02", "2026-06-10", "2026-06-26"],
      rationale: "依 Ebbinghaus 1-3-7-15 間隔，鞏固 NRS 量表使用習慣。",
    },
    {
      id: "sr2",
      dimension: "Associated 伴隨症狀",
      reviewDates: ["2026-05-29", "2026-06-02", "2026-06-10", "2026-06-26"],
      rationale: "練習至少問三項冠心症關聯症狀。",
    },
    {
      id: "sr3",
      dimension: "Relieving 緩解因子",
      reviewDates: ["2026-05-30", "2026-06-03", "2026-06-11", "2026-06-27"],
      rationale: "建立硝化甘油試驗的問診慣性。",
    },
  ],
  selfAssessment: null,
  confidence: {
    predictedScore: null,
    actualScore: 3.88,
    gap: null,
  },
  phaseBoundaries: [
    { tMin: 3, label: "Inquiry 開始" },
    { tMin: 9, label: "PE 開始" },
    { tMin: 14, label: "Diagnosis" },
  ],
};

