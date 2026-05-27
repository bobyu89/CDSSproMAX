# Keyboard Shortcuts

Currently active on the **練習 (`/practice`)** flow. Tap `?` in the page header for an in-app reminder popover.

| Shortcut | Action | Notes |
|---|---|---|
| `Alt + →` *or* `Ctrl + →` | 進入下一步 | Only when the current step is "complete" (e.g. interview has ≥ 1 turn, diagnosis has content). Ignored when focus is inside an input/textarea/select. |
| `Alt + ←` *or* `Ctrl + ←` | 回上一步 | Symptom 步驟無上一步可回。Ignored when focus is inside an editable element. |
| `Esc` | 中止練習 | Only triggers the 離開確認 dialog when mid-session (`sessionId` exists and step is not `symptom` / `summary`). If the shortcut help popover is open, `Esc` closes it instead. |

## Completion gate for `Alt+→`

The "step complete" check lives in `apps/web/app/practice/page.tsx`:

| Step | Considered complete when… |
|---|---|
| `symptom` | a session exists (`sessionId !== null`) |
| `system` | a body system is selected |
| `interview` | at least one Q/A turn recorded |
| `pe` | at least one PE selection made |
| `diagnosis` | the serialized diagnosis is set |

If the user tries to fast-forward past an incomplete step, the keystroke is silently ignored — they need to fill the step normally.

## Not yet bound

- 提交 / 送出 (Enter shortcuts inside step components handle this already where appropriate)
- OSCE mode does **not** honour these shortcuts — the timer drives step transitions there to keep exam semantics deterministic.
