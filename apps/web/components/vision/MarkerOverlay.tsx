"use client";

import type { MarkerDetection } from "@ticdss/shared-types";

interface Props {
  detections: MarkerDetection[];
  frameW: number;
  frameH: number;
  /** Calibration mode — render very large IDs + region labels with high-
   *  contrast background pills so they're legible from across the room. */
  largeIds?: boolean;
}

/**
 * SVG overlay drawn on top of the live camera feed.
 *
 * - Normal mode: 2-3 px stroke + small label next to each marker box.
 * - Large-ID mode (calibration): thick stroke + giant centered ID + region
 *   chip with rounded background, so the operator can tell which marker
 *   is at which physical location without reading tiny text.
 */
export function MarkerOverlay({ detections, frameW, frameH, largeIds = false }: Props) {
  if (frameW === 0 || frameH === 0) return null;

  const idFontPx = largeIds
    ? Math.max(48, Math.round(frameW / 14))
    : Math.max(14, Math.round(frameW / 50));
  const regionFontPx = largeIds
    ? Math.max(20, Math.round(frameW / 38))
    : Math.max(12, Math.round(frameW / 60));
  const strokeWidth = largeIds
    ? Math.max(4, Math.round(frameW / 220))
    : Math.max(2, Math.round(frameW / 320));

  return (
    <svg
      className="absolute inset-0 w-full h-full pointer-events-none"
      viewBox={`0 0 ${frameW} ${frameH}`}
      preserveAspectRatio="xMidYMid meet"
      aria-hidden="true"
    >
      {detections.map((d) => {
        if (d.corners.length === 0) return null;
        const path =
          d.corners
            .map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`)
            .join(" ") + " Z";
        const matched = d.region !== null;
        const stroke = matched ? "#10b981" /* emerald */ : "#A1887F" /* brand */;
        const fillBg = matched ? "#10b981" : "#A1887F";
        const idText = `#${d.arucoId}`;
        // Pill width estimated from text length — generous padding for legibility.
        const pillW =
          idFontPx * (idText.length * 0.6) + (largeIds ? 32 : 16);
        const pillH = idFontPx + (largeIds ? 16 : 8);
        const pillX = d.centerX - pillW / 2;
        const pillY = d.centerY - pillH / 2;

        return (
          <g key={`${d.arucoId}-${d.centerX.toFixed(0)}`}>
            {/* Marker outline */}
            <path
              d={path}
              fill="none"
              stroke={stroke}
              strokeWidth={strokeWidth}
              strokeLinejoin="round"
              opacity={0.92}
            />

            {/* Large-ID mode — bold pill at marker center */}
            {largeIds ? (
              <>
                <rect
                  x={pillX}
                  y={pillY}
                  width={pillW}
                  height={pillH}
                  rx={pillH / 2}
                  fill={fillBg}
                  opacity={0.92}
                />
                <text
                  x={d.centerX}
                  y={d.centerY + idFontPx * 0.34}
                  fontSize={idFontPx}
                  fontWeight="800"
                  textAnchor="middle"
                  fill="#fff"
                  style={{ fontFamily: "Manrope, sans-serif" }}
                >
                  {idText}
                </text>
                {d.region && (
                  <g>
                    <rect
                      x={d.centerX - regionFontPx * (d.region.length * 0.55)}
                      y={pillY + pillH + 6}
                      width={regionFontPx * (d.region.length * 1.1)}
                      height={regionFontPx + 10}
                      rx={6}
                      fill="rgba(0,0,0,0.78)"
                    />
                    <text
                      x={d.centerX}
                      y={pillY + pillH + 6 + regionFontPx * 0.85}
                      fontSize={regionFontPx}
                      fontWeight="700"
                      textAnchor="middle"
                      fill="#fff"
                      style={{ fontFamily: "Manrope, ui-monospace, monospace" }}
                    >
                      {d.region}
                    </text>
                  </g>
                )}
              </>
            ) : (
              <>
                <circle cx={d.centerX} cy={d.centerY} r={4} fill={stroke} />
                <text
                  x={d.centerX}
                  y={d.centerY - 10}
                  fontSize={idFontPx}
                  fontWeight="700"
                  textAnchor="middle"
                  fill="#fff"
                  stroke="#000"
                  strokeWidth={3}
                  paintOrder="stroke"
                  style={{ fontFamily: "Manrope, sans-serif" }}
                >
                  {idText}
                  {d.region ? ` · ${d.region}` : ""}
                </text>
              </>
            )}
          </g>
        );
      })}
    </svg>
  );
}
