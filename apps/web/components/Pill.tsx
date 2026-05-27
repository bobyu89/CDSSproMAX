import type { ArbiterAction } from "@ticdss/shared-types";

// Traffic-light semantics are kept for arbiter status — green/amber/rose are
// universally readable. The "no decision yet" pill uses the warm beige palette.
const STYLES: Record<ArbiterAction, { bg: string; text: string; label: string }> =
  {
    accept: {
      bg: "bg-emerald-50",
      text: "text-emerald-700",
      label: "通過",
    },
    flag: {
      bg: "bg-amber-50",
      text: "text-amber-700",
      label: "需確認",
    },
    force_human: {
      bg: "bg-rose-50",
      text: "text-rose-700",
      label: "人工裁決",
    },
  };

export function ArbiterPill({
  action,
}: {
  action: ArbiterAction | null;
}) {
  if (!action) {
    return (
      <span className="inline-flex items-center rounded-full bg-bg-surface px-2.5 py-0.5 text-xs font-medium text-ink-muted">
        尚未裁決
      </span>
    );
  }
  const style = STYLES[action];
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${style.bg} ${style.text}`}
    >
      {style.label}
    </span>
  );
}
