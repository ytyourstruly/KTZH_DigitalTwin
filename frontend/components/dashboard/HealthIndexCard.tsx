"use client"

import { cn } from "@/lib/utils"
import type { LocomotiveData } from "@/lib/mock-data"
import { HEALTH_FACTORS } from "@/lib/mock-data"
import { TrendingUp, TrendingDown, Minus } from "lucide-react"

interface HealthGaugeProps {
  score: number
  status: LocomotiveData["healthStatus"]
}

function HealthGauge({ score, status }: HealthGaugeProps) {
  // Arc sweeps 300° — from 120° to 420° (i.e. 120° → 60°)
  // R=50, cx=64, cy=52. Bottom of arc: cy + R = 102.
  // ViewBox height = 108 gives 6px clearance below + room for end-cap strokeWidth=10.
  const R = 50
  const cx = 64
  const cy = 54

  const colorMap = {
    normal: "stroke-status-normal",
    warning: "stroke-status-warning",
    critical: "stroke-status-critical",
  }

  // Convert polar to cartesian (0° = top/north)
  function polarToCartesian(angle: number) {
    const rad = ((angle - 90) * Math.PI) / 180
    return {
      x: cx + R * Math.cos(rad),
      y: cy + R * Math.sin(rad),
    }
  }

  function arcPath(startAngle: number, endAngle: number) {
    const s = polarToCartesian(startAngle)
    const e = polarToCartesian(endAngle)
    const largeArc = endAngle - startAngle > 180 ? 1 : 0
    return `M ${s.x} ${s.y} A ${R} ${R} 0 ${largeArc} 1 ${e.x} ${e.y}`
  }

  // Track: 120° → 420° (300° sweep)
  const trackPath = arcPath(120, 420)
  // Fill: proportional score, minimum visible stub at 2° so 0 doesn't look broken
  const fillEndAngle = 120 + Math.max((score / 100) * 300, score === 0 ? 0 : 2)
  const fillPath = arcPath(120, fillEndAngle)

  // Tick marks at 0 / 25 / 50 / 75 / 100
  const tickAngles = [0, 25, 50, 75, 100].map((val) => 120 + (val / 100) * 300)

  return (
    <svg viewBox="0 0 128 108" className="w-full max-w-[180px] mx-auto overflow-visible">
      {/* Track arc */}
      <path
        d={trackPath}
        fill="none"
        strokeWidth="10"
        strokeLinecap="round"
        className="stroke-secondary"
      />
      {/* Fill arc */}
      <path
        d={fillPath}
        fill="none"
        strokeWidth="10"
        strokeLinecap="round"
        className={cn("transition-all duration-1000", colorMap[status])}
      />
      {/* Tick marks */}
      {tickAngles.map((angle, i) => {
        const innerR = R - 7
        const outerR = R + 3
        const rad = ((angle - 90) * Math.PI) / 180
        const x1 = cx + innerR * Math.cos(rad)
        const y1 = cy + innerR * Math.sin(rad)
        const x2 = cx + outerR * Math.cos(rad)
        const y2 = cy + outerR * Math.sin(rad)
        return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} className="stroke-border" strokeWidth="1.2" />
      })}
      {/* Score — vertically centred in the arc's visual "bowl" */}
      <text
        x={cx}
        y={cy + 4}
        textAnchor="middle"
        dominantBaseline="middle"
        className="fill-foreground font-mono font-bold"
        fontSize="24"
      >
        {score}
      </text>
      <text
        x={cx}
        y={cy + 20}
        textAnchor="middle"
        dominantBaseline="middle"
        className="fill-muted-foreground"
        fontSize="9"
        fontFamily="monospace"
      >
        / 100
      </text>
    </svg>
  )
}

interface HealthIndexCardProps {
  loco: LocomotiveData
}

export function HealthIndexCard({ loco }: HealthIndexCardProps) {
  const statusLabel = {
    normal: "Нормально",
    warning: "Внимание",
    critical: "Критично",
  }

  const statusClass = {
    normal: "text-status-normal bg-status-normal-bg border-status-normal/40",
    warning: "text-status-warning bg-status-warning-bg border-status-warning/40",
    critical: "text-status-critical bg-status-critical-bg border-status-critical/40",
  }

  return (
    <div className="bg-card border border-border rounded p-4 flex flex-col gap-3 h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-muted-foreground font-mono uppercase tracking-wider">Индекс состояния</div>
          <div className="text-sm font-semibold text-foreground">Общее состояние системы</div>
        </div>
        <span className={cn(
          "text-xs font-mono font-semibold px-2 py-1 rounded border",
          statusClass[loco.healthStatus]
        )}>
          {statusLabel[loco.healthStatus]}
        </span>
      </div>

      {/* Gauge */}
      <HealthGauge score={loco.healthScore} status={loco.healthStatus} />

      {/* Explanation */}
      <p className="text-xs text-muted-foreground leading-relaxed border-t border-border pt-2">
        Индекс состояния зависит от температуры тяги, отклонения давления тормоза и скачков тока.
      </p>

      {/* Contributing factors */}
      <div className="space-y-1.5">
        <div className="text-xs font-mono text-muted-foreground uppercase tracking-wider">Основные факторы влияния</div>
        {HEALTH_FACTORS.map((factor) => (
          <div key={factor.name} className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1.5 min-w-0">
              {factor.trend === "up" && <TrendingUp className="w-3 h-3 text-status-critical shrink-0" />}
              {factor.trend === "down" && <TrendingDown className="w-3 h-3 text-status-normal shrink-0" />}
              {factor.trend === "stable" && <Minus className="w-3 h-3 text-muted-foreground shrink-0" />}
              <span className="text-xs text-foreground truncate">{factor.name}</span>
            </div>
            <span className={cn(
              "text-xs font-mono font-semibold tabular-nums shrink-0",
              factor.impact < -5 ? "text-status-critical" : factor.impact < -2 ? "text-status-warning" : "text-muted-foreground"
            )}>
              {factor.impact}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
