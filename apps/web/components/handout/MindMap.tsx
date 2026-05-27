"use client";

import { useMemo, useState } from "react";
import type { MindMapKind, MindMapNode } from "@ticdss/shared-types";
import { Network } from "lucide-react";

interface Props {
  nodes: MindMapNode[];
}

interface LaidOutNode extends MindMapNode {
  x: number;
  y: number;
  childIds: string[];
}

// Vertical tree layout — left root, children fanned to the right.
function layout(nodes: MindMapNode[]): { laid: Map<string, LaidOutNode>; w: number; h: number } {
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const childMap = new Map<string | null, string[]>();
  nodes.forEach((n) => {
    const arr = childMap.get(n.parentId) ?? [];
    arr.push(n.id);
    childMap.set(n.parentId, arr);
  });

  // depth (root = 0)
  const depth = new Map<string, number>();
  function computeDepth(id: string, d: number) {
    depth.set(id, d);
    (childMap.get(id) ?? []).forEach((c) => computeDepth(c, d + 1));
  }
  const roots = childMap.get(null) ?? [];
  roots.forEach((r) => computeDepth(r, 0));

  // assign y positions to leaves of each depth bucket — simple by-depth column layout.
  // Group nodes by depth, evenly space along y.
  const byDepth = new Map<number, string[]>();
  nodes.forEach((n) => {
    const d = depth.get(n.id) ?? 0;
    const arr = byDepth.get(d) ?? [];
    arr.push(n.id);
    byDepth.set(d, arr);
  });

  const colWidth = 240;
  const rowHeight = 56;
  const laid = new Map<string, LaidOutNode>();
  const maxDepth = Math.max(...Array.from(byDepth.keys()));

  let maxRows = 0;
  byDepth.forEach((ids) => {
    if (ids.length > maxRows) maxRows = ids.length;
  });

  byDepth.forEach((ids, d) => {
    const totalH = ids.length * rowHeight;
    const offsetY = (maxRows * rowHeight - totalH) / 2;
    ids.forEach((id, i) => {
      laid.set(id, {
        ...(byId.get(id) as MindMapNode),
        x: 40 + d * colWidth,
        y: offsetY + i * rowHeight + rowHeight / 2 + 20,
        childIds: childMap.get(id) ?? [],
      });
    });
  });

  return {
    laid,
    w: 40 + (maxDepth + 1) * colWidth + 40,
    h: maxRows * rowHeight + 60,
  };
}

const KIND_COLORS: Record<MindMapKind, { fill: string; stroke: string; text: string }> = {
  root: { fill: "#6f5a52", stroke: "#5b483f", text: "#FFFFFF" },
  key_concept: { fill: "#A1887F", stroke: "#6f5a52", text: "#FFFFFF" },
  weakness: { fill: "#fee2e2", stroke: "#dc2626", text: "#7f1d1d" },
  action: { fill: "#d1fae5", stroke: "#059669", text: "#064e3b" },
  reference: { fill: "#D7CCC8", stroke: "#A1887F", text: "#3a2f29" },
};

const KIND_LABEL: Record<MindMapKind, string> = {
  root: "案例",
  key_concept: "核心概念",
  weakness: "弱項",
  action: "行動",
  reference: "參考",
};

export function MindMap({ nodes }: Props) {
  const { laid, w, h } = useMemo(() => layout(nodes), [nodes]);
  const [selected, setSelected] = useState<string | null>(nodes[0]?.id ?? null);

  const selectedNode = selected ? laid.get(selected) : null;

  return (
    <section className="bg-white border border-subtle rounded-xl p-6 shadow-sm">
      <h2 className="text-lg font-bold text-ink mb-1 flex items-center gap-2">
        <Network size={18} className="text-brand-500" /> 學習心智圖
      </h2>
      <p className="text-xs text-ink-muted mb-4">
        點擊節點查看說明。顏色：棕＝核心概念、紅＝弱項、綠＝行動建議、米＝參考。
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_280px] gap-4">
        <div className="overflow-auto border border-faint rounded-lg bg-bg-surface">
          <svg
            width={w}
            height={h}
            viewBox={`0 0 ${w} ${h}`}
            className="block min-w-full"
            role="img"
            aria-label="學習心智圖"
          >
            {/* edges */}
            {Array.from(laid.values()).map((n) =>
              n.childIds.map((cid) => {
                const child = laid.get(cid);
                if (!child) return null;
                const x1 = n.x + 90;
                const y1 = n.y;
                const x2 = child.x - 90;
                const y2 = child.y;
                const midX = (x1 + x2) / 2;
                return (
                  <path
                    key={`${n.id}-${cid}`}
                    d={`M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`}
                    stroke="#D7CCC8"
                    strokeWidth={1.4}
                    fill="none"
                  />
                );
              }),
            )}
            {/* nodes */}
            {Array.from(laid.values()).map((n) => {
              const c = KIND_COLORS[n.kind];
              const isSel = selected === n.id;
              return (
                <g
                  key={n.id}
                  transform={`translate(${n.x - 90}, ${n.y - 18})`}
                  onClick={() => setSelected(n.id)}
                  style={{ cursor: "pointer" }}
                >
                  <rect
                    width={180}
                    height={36}
                    rx={8}
                    fill={c.fill}
                    stroke={isSel ? "#2f2a26" : c.stroke}
                    strokeWidth={isSel ? 2.5 : 1.2}
                  />
                  <text
                    x={90}
                    y={22}
                    textAnchor="middle"
                    fill={c.text}
                    fontSize={12}
                    fontWeight={600}
                  >
                    {n.label.length > 14 ? n.label.slice(0, 14) + "…" : n.label}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        <aside className="bg-bg-surface rounded-lg p-4 border border-faint">
          {selectedNode ? (
            <div>
              <span
                className="inline-block px-2 py-0.5 rounded-full text-[10px] uppercase tracking-widest font-bold mb-2"
                style={{
                  background: KIND_COLORS[selectedNode.kind].fill,
                  color: KIND_COLORS[selectedNode.kind].text,
                }}
              >
                {KIND_LABEL[selectedNode.kind]}
              </span>
              <h3 className="text-base font-bold text-ink mb-2">
                {selectedNode.label}
              </h3>
              <p className="text-xs text-ink-soft leading-relaxed">
                {selectedNode.description ?? "（無說明）"}
              </p>
            </div>
          ) : (
            <p className="text-xs text-ink-muted">點擊節點查看說明</p>
          )}
        </aside>
      </div>
    </section>
  );
}

export default MindMap;
