"use client";

import { useEffect, useRef } from "react";
import type { MarkerDetection } from "@ticdss/shared-types";

interface Props {
  /** Latest detections this tick. */
  detections: MarkerDetection[];
  /** Frame dims so we can size the SVG viewbox correctly. */
  frameW: number;
  frameH: number;
  /** How long a trail dot stays before fading out (ms). */
  trailLifetimeMs?: number;
}

interface TrailPoint {
  arucoId: number;
  x: number;
  y: number;
  ts: number;
  matched: boolean;
}

/**
 * Decaying ghost trail of marker centers — used by the calibration page
 * to visualise marker stability. A perfectly fixed marker shows a tight
 * cluster; a flickering or moving marker leaves a smear.
 *
 * Renders an absolutely-positioned SVG on top of the camera preview.
 * Each new detection appends a point; points fade linearly to zero
 * opacity over ``trailLifetimeMs``.
 *
 * No external charting lib — pure SVG + a single ref-stored buffer.
 */
export function MarkerHeatmap({
  detections,
  frameW,
  frameH,
  trailLifetimeMs = 6000,
}: Props) {
  const trailRef = useRef<TrailPoint[]>([]);
  const tickRef = useRef<number>(0);
  const svgRef = useRef<SVGSVGElement>(null);

  // Append the new detections to the trail buffer on every render.
  useEffect(() => {
    const now = performance.now();
    for (const d of detections) {
      trailRef.current.push({
        arucoId: d.arucoId,
        x: d.centerX,
        y: d.centerY,
        ts: now,
        matched: d.region !== null,
      });
    }
    // Cap memory: drop everything older than 2× lifetime
    const cutoff = now - trailLifetimeMs * 2;
    trailRef.current = trailRef.current.filter((p) => p.ts >= cutoff);
  }, [detections, trailLifetimeMs]);

  // Drive an animation loop that redraws fading dots. We bump a state
  // counter via requestAnimationFrame so React re-renders the SVG.
  useEffect(() => {
    let raf = 0;
    const draw = () => {
      // Force re-render by toggling a ref-driven attribute. The SVG
      // reads trailRef.current on every render but we need to schedule
      // re-renders. Easiest: poke a data attribute on the SVG element.
      if (svgRef.current) {
        tickRef.current = (tickRef.current + 1) % 100000;
        svgRef.current.setAttribute("data-tick", String(tickRef.current));
      }
      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, []);

  if (frameW === 0 || frameH === 0) return null;

  const now = performance.now();
  const points = trailRef.current;

  return (
    <svg
      ref={svgRef}
      className="absolute inset-0 w-full h-full pointer-events-none"
      viewBox={`0 0 ${frameW} ${frameH}`}
      preserveAspectRatio="xMidYMid meet"
      aria-hidden="true"
    >
      {points.map((p, i) => {
        const age = now - p.ts;
        if (age >= trailLifetimeMs) return null;
        const opacity = 1 - age / trailLifetimeMs;
        const radius = Math.max(3, frameW / 200) * (0.4 + 0.6 * opacity);
        const fill = p.matched ? "#10b981" : "#A1887F";
        return (
          <circle
            key={`${p.arucoId}-${p.ts}-${i}`}
            cx={p.x}
            cy={p.y}
            r={radius}
            fill={fill}
            opacity={opacity * 0.55}
          />
        );
      })}
    </svg>
  );
}
