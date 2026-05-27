# TICDSS Web — UI Flow

A short field guide to how the Next.js front-end is wired. Backend work belongs in `apps/api/`; this doc only covers `apps/web/`.

## Routes

| Path | Purpose | Role |
|---|---|---|
| `/login` | Login form (參與者代碼 + 密碼). On success populates `authStore` and redirects by role. | public |
| `/home` | Landing page for students/teachers — quick links to 練習、OSCE、歷史。 | participant |
| `/practice` | Multi-step practice flow (主訴 → 系統 → 問診 → 身體評估 → 鑑別診斷 → 回饋). | student |
| `/osce` | Three-station timed exam mode. Reuses Practice step components. | student |
| `/history` | List of past sessions with expandable DUAT scoring detail. | student / teacher |
| `/admin` | Admin dashboard (總覽 / 學員 / 案例). | admin |

## State machine — `cdssStore`

The Zustand store `apps/web/lib/cdssStore.ts` drives the multi-step flows.

```
phase (implicit, via currentStep):

  symptom  → system  → interview → pe → diagnosis → summary
   (choose)   (pick    (LQQOPERA   (PE   (3 dx       (DUAT
              system)   chat)      pick) rows)        feedback)
```

Key fields:

- `mode: "practice" | "osce"` — chooses time-limit + feedback semantics.
- `sessionId` — set when a session is created via `POST /sessions`. Until set, the user is "pre-session" and Esc / Home don't trigger the abandon dialog.
- `currentStep` — drives which `Step*` component renders.
- `interviewTurns`, `peSelections`, `diagnosis` — per-step content; also used by the practice page to gate `Alt+→` (must be "complete").

Transitions are always user-driven via `setStep()`. There is no auto-advance except OSCE's per-step timer running out (`apps/web/app/osce/page.tsx` → `handleTimeUp`).

`resetSteps()` clears all step content but keeps `sessionId`. `reset()` clears everything (called when leaving mid-session).

## API fallback pattern

All read endpoints in `apps/web/lib/api.ts` follow this pattern:

```ts
try {
  return await request<...>("/path");
} catch {
  return MOCK_VALUE;
}
```

This means **the UI always renders something**, even when the backend is offline. Mocks live in `apps/web/lib/mock.ts` and are shaped to match the eventual API response.

Write endpoints (`createSession`, `gradeItem`, `createParticipant`, `toggleCaseWithheld`, `completeSession`) do **not** fall back — failures bubble as `ApiError` so the caller can show a toast / inline error.

`appendTranscript` is the one exception: it fabricates a local transcript object on failure so the practice flow never breaks if the API is down.

## Color tokens

Defined in `apps/web/tailwind.config.*` (theme extension). Semantic meanings:

| Token | Hex (approx) | Meaning |
|---|---|---|
| `brand-500` | #A1887F | Primary action / focus ring base (practice mode CTA, links, active tab) |
| `brand-600` | #6f5a52 | Stronger accent — used for the **OSCE** confirm button and active-tab text (slightly darker for emphasis) |
| `brand-100` | very light brand | Card borders, hover surfaces |
| `bg`, `bg-surface`, `bg-muted` | warm off-white | Page → card → input ramp |
| `ink`, `ink-soft`, `ink-muted` | text ramp | Strong → secondary → tertiary text |
| `danger`, `danger-soft` | red | Abandon / destructive actions, error states |
| `emerald-*` | green | Success (e.g. "已完成", arbiter accept), positive deltas |
| `amber-*` | amber | "標記" arbiter decisions, warnings |
| `rose-*` | rose | "人工裁決", force-human flags |

Don't mix `brand-500` and `brand-600` casually — `500` is the default; `600` is reserved for places where the visual weight needs to step up (notably OSCE-mode controls).

## Drafts (localStorage)

Practice steps auto-save text drafts to `localStorage` keyed by `ticdss-draft-{sessionId}-{step}`:

- `ticdss-draft-{sessionId}-diagnosis` — JSON of the three diagnosis rows.
- `ticdss-draft-{sessionId}-interview` — the free-text question input.

Drafts are cleared on successful step submission. The key includes `sessionId`, so different sessions don't collide.
