// Mirrors docs/architecture/rubric-schema.md.

export type RubricType = "lqqopera" | "pe";

export interface RubricCriterion {
  level: number;
  descriptor: string;
}

export interface RubricItem {
  id: string;
  dimension: string;
  weight: number;
  maxScore: number;
  criteria: RubricCriterion[];
  evidenceAnchors?: string[];

  // PE-only (used by Wave 1.5 Vision Agent)
  bodyRegion?: string;
  expectedAction?: string;
  minDurationSeconds?: number;
}

export interface Rubric {
  rubricId: string;
  type: RubricType;
  version: string;
  items: RubricItem[];
}

export const LQQOPERA_ITEM_IDS = [
  "lqqopera.location",
  "lqqopera.quality",
  "lqqopera.quantity",
  "lqqopera.onset",
  "lqqopera.precipitating",
  "lqqopera.extension",
  "lqqopera.relieving",
  "lqqopera.associated_symptoms",
] as const;

export type LqqoperaItemId = (typeof LQQOPERA_ITEM_IDS)[number];
