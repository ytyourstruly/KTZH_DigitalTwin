"use client"

import { cn } from "@/lib/utils"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { TrendingUp, TrendingDown, Minus, Info } from "lucide-react"
import type { TelemetryPoint } from "@/lib/mock-data"

// Mini sparkline using SVG
function Sparkline({ data, color = "stroke-chart-1" }: { data: TelemetryPoint[]; color?: string }) {
  if (data.length < 2) return null
  const values = data.map((d) => d.value)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const w = 80
  const h = 24
  const padding = 2
  const points = values
    .map((v, i) => `${padding + (i / (values.length - 1)) * (w - padding * 2)},${padding + h - padding - ((v - min) / range) * (h - padding * 2)}`)
    .join(" ")

  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="overflow-hidden">
      <polyline
        points={points}
        fill="none"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        className={color}
      />
    </svg>
  )
}

interface TelemetryCardProps {
  label: string
  value: number | string
  unit: string
  delta?: number
  deltaUnit?: string
  history?: TelemetryPoint[]
  sparklineColor?: string
  status?: "normal" | "warning" | "critical" | "neutral"
  safeRange?: [number, number]
  tooltip?: string
  precision?: number
}

export function TelemetryCard({
  label,
  value,
  unit,
  delta,
  deltaUnit,
  history,
  sparklineColor,
  status = "neutral",
  safeRange,
  tooltip,
  precision = 0,
}: TelemetryCardProps) {
  const statusBorderMap = {
    normal: "border-l-status-normal",
    warning: "border-l-status-warning",
    critical: "border-l-status-critical",
    neutral: "border-l-border",
  }

  const statusTextMap = {
    normal: "text-status-normal",
    warning: "text-status-warning",
    critical: "text-status-critical",
    neutral: "text-foreground",
  }

  const displayValue = typeof value === "number"
    ? precision > 0
      ? value.toFixed(precision)
      : Math.round(value).toString()
    : value

  return (
    <div className={cn(
      "bg-card border border-border border-l-2 rounded p-3 flex flex-col gap-2 min-h-[100px]",
      statusBorderMap[status]
    )}>
      {/* Label row */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">{label}</span>
        {tooltip && (
          <TooltipProvider delayDuration={200}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Info className="w-3 h-3 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-48 text-xs font-mono">
                {tooltip}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>

      {/* Value row */}
      <div className="flex items-end justify-between gap-2">
        <div className="flex items-baseline gap-1">
          <span className={cn(
            "font-mono font-bold tabular-nums leading-none transition-all duration-500",
            statusTextMap[status],
            typeof value === "number" && Math.abs(Number(displayValue)) >= 100 ? "text-2xl" : "text-3xl"
          )}>
            {displayValue}
          </span>
          <span className="text-xs text-muted-foreground font-mono">{unit}</span>
        </div>
        {history && (
          <div className="opacity-70">
            <Sparkline data={history.slice(-20)} color={sparklineColor} />
          </div>
        )}
      </div>

      {/* Delta and safe range */}
      <div className="flex items-center justify-between">
        {delta !== undefined && (
          <div className="flex items-center gap-1">
            {delta > 0 ? (
              <TrendingUp className="w-3 h-3 text-status-warning" />
            ) : delta < 0 ? (
              <TrendingDown className="w-3 h-3 text-status-normal" />
            ) : (
              <Minus className="w-3 h-3 text-muted-foreground" />
            )}
            <span className={cn(
              "text-xs font-mono tabular-nums",
              delta > 0 ? "text-status-warning" : delta < 0 ? "text-status-normal" : "text-muted-foreground"
            )}>
              {delta > 0 ? "+" : ""}{delta}{deltaUnit ?? unit} 
            </span>
          </div>
        )}
        {safeRange && (
          <span className="text-xs text-muted-foreground font-mono ml-auto">
            Норма: {safeRange[0]}–{safeRange[1]}{unit}
          </span>
        )}
      </div>
    </div>
  )
}
