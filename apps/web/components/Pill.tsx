import type { ArbiterAction } from "@ticdss/shared-types";

const STYLES: Record<ArbiterAction, { bg: string; text: string; label: string }> =
  {
    accept: {
      bg: "bg-emerald-50",
      text: "text-emerald-700",
      label: "通過 Accept",
    },
    flag: {
      bg: "bg-amber-50",
      text: "text-amber-700",
      label: "標記 Flag",
    },
    force_human: {
      bg: "bg-rose-50",
      text: "text-rose-700",
      label: "人工裁決 Force human",
    },
  };

export function ArbiterPill({
  action,
}: {
  action: ArbiterAction | null;
}) {
  if (!action) {
    return (
      <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
        未裁決
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
