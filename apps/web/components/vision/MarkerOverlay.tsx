"use client";

import type { MarkerDetection } from "@ticdss/shared-types";

interface Props {
  detections: MarkerDetection[];
  frameW: number;
  frameH: number;
}

/**
 * SVG overlay that draws marker bounding boxes + region labels on top of
 * the camera preview. Renders inside an absolutely-positioned container
 * that matches the video element's aspect ratio.
 */
export function MarkerOverlay({ detections, frameW, frameH }: Props) {
  if (frameW === 0 || frameH === 0) return null;
  return (
    <svg
      className="absolute inset-0 w-full h-full pointer-events-none"
      viewBox={`0 0 ${frameW} ${frameH}`}
      preserveAspectRatio="xMidYMid meet"
      aria-hidden="true"
    >
      {detections.map((d) => {
        if (d.corners.length === 0) return null;
        const path = d.corners
          .map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`)
          .join(" ") + " Z";
        const matched = d.region !== null;
        const stroke = matched ? "#10b981" /* emerald */ : "#A1887F" /* brand */;
        return (
          <g key={d.arucoId}>
            <path
              d={path}
              fill="none"
              stroke={stroke}
              strokeWidth={Math.max(2, frameW / 320)}
              strokeLinejoin="round"
              opacity={0.9}
            />
            <circle cx={d.centerX} cy={d.centerY} r={4} fill={stroke} />
            <text
              x={d.centerX}
              y={d.centerY - 10}
              fontSize={Math.max(14, frameW / 50)}
              fontWeight="700"
              textAnchor="middle"
              fill="#fff"
              stroke="#000"
              strokeWidth={3}
              paintOrder="stroke"
              style={{ fontFamily: "Manrope, sans-serif" }}
            >
              #{d.arucoId}{d.region ? ` · ${d.region}` : ""}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
