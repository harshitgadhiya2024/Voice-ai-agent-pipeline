"use client";

import { useEffect, useRef } from "react";
import type { VoiceStatus } from "@/types";

interface AudioVisualizerProps {
  analyser: AnalyserNode | null;
  status: VoiceStatus;
  height?: number;
}

const COLOR_FOR_STATUS: Record<VoiceStatus, string> = {
  idle: "#4b5563",
  listening: "#2dd4bf",
  thinking: "#a78bfa",
  speaking: "#f59e0b",
};

const BAR_COUNT = 48;
const BAR_GAP = 3;

export function AudioVisualizer({
  analyser,
  status,
  height = 80,
}: AudioVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let dataArray: Uint8Array | null = null;
    if (analyser) {
      dataArray = new Uint8Array(analyser.frequencyBinCount);
    }

    const resize = () => {
      const ratio = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      const cssW = Math.max(1, rect.width);
      canvas.width = Math.floor(cssW * ratio);
      canvas.height = Math.floor(height * ratio);
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    };
    resize();
    window.addEventListener("resize", resize);

    const draw = () => {
      const rect = canvas.getBoundingClientRect();
      const w = Math.max(1, rect.width);
      const h = Math.max(1, height);
      ctx.clearRect(0, 0, w, h);

      const color = COLOR_FOR_STATUS[status];
      const totalGap = BAR_GAP * (BAR_COUNT - 1);
      const barWidth = Math.max(0, (w - totalGap) / BAR_COUNT);

      if (barWidth < 0.5) {
        rafRef.current = requestAnimationFrame(draw);
        return;
      }

      if (analyser && dataArray) {
        analyser.getByteFrequencyData(dataArray);
      }

      for (let i = 0; i < BAR_COUNT; i++) {
        let v = 0;
        if (analyser && dataArray) {
          const idx = Math.floor((i / BAR_COUNT) * dataArray.length);
          v = dataArray[idx] / 255;
        } else {
          v = 0.05 + Math.abs(Math.sin(Date.now() / 600 + i * 0.3)) * 0.08;
        }
        const barH = Math.max(2, v * h * 0.95);
        const x = i * (barWidth + BAR_GAP);
        const y = (h - barH) / 2;
        ctx.fillStyle = color;
        const radius = Math.max(
          0,
          Math.min(3, barWidth / 2, barH / 2),
        );
        roundRect(ctx, x, y, barWidth, barH, radius);
        ctx.fill();
      }

      rafRef.current = requestAnimationFrame(draw);
    };
    rafRef.current = requestAnimationFrame(draw);

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      window.removeEventListener("resize", resize);
    };
  }, [analyser, status, height]);

  return (
    <canvas
      ref={canvasRef}
      className="w-full min-w-[120px]"
      style={{ height: `${height}px` }}
    />
  );
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  if (w <= 0 || h <= 0) return;

  const radius = Math.max(0, Math.min(r, w / 2, h / 2));
  if (radius <= 0) {
    ctx.rect(x, y, w, h);
    return;
  }

  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.arcTo(x + w, y, x + w, y + h, radius);
  ctx.arcTo(x + w, y + h, x, y + h, radius);
  ctx.arcTo(x, y + h, x, y, radius);
  ctx.arcTo(x, y, x + w, y, radius);
  ctx.closePath();
}
