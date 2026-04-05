"use client"

import { cn } from "@/lib/utils"
import { RECOMMENDATIONS, type Recommendation } from "@/lib/mock-data"
import { AlertTriangle, ArrowRight, ChevronRight, Zap, Info } from "lucide-react"

const PRIORITY_CONFIG = {
  high: {
    label: "Высокий",
    className: "text-status-critical bg-status-critical-bg border-status-critical/40",
    borderClass: "border-l-status-critical",
    icon: AlertTriangle,
  },
  medium: {
    label: "Средний",
    className: "text-status-warning bg-status-warning-bg border-status-warning/40",
    borderClass: "border-l-status-warning",
    icon: Zap,
  },
  low: {
    label: "Низкий",
    className: "text-muted-foreground bg-muted border-border",
    borderClass: "border-l-border",
    icon: Info,
  },
}

interface RecommendationsPanelProps {
  recommendations?: Recommendation[]
}

export function RecommendationsPanel({ recommendations = RECOMMENDATIONS }: RecommendationsPanelProps) {
  return (
    <div className="bg-card border border-border rounded flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">Рекомендации</span>
        <span className="text-xs font-mono text-muted-foreground">Помощник диспетчера</span>
      </div>

      {/* Recommendation list */}
      <div className="flex-1 overflow-y-auto min-h-0 divide-y divide-border">
        {recommendations.map((rec) => {
          const cfg = PRIORITY_CONFIG[rec.priority]
          const Icon = cfg.icon
          return (
            <div
              key={rec.id}
              className={cn(
                "flex gap-3 px-4 py-3 border-l-2 hover:bg-muted/30 transition-colors",
                cfg.borderClass
              )}
            >
              <Icon className={cn("w-3.5 h-3.5 mt-0.5 shrink-0", cfg.className.split(" ")[0])} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2 mb-0.5">
                  <span className={cn(
                    "text-xs font-mono font-semibold px-1.5 py-0.5 rounded border",
                    cfg.className
                  )}>
                    {cfg.label}
                  </span>
                  <span className="text-xs text-muted-foreground font-mono">{rec.eta}</span>
                </div>
                <div className="flex items-start gap-1 mt-1">
                  <ChevronRight className="w-3 h-3 mt-0.5 text-foreground/40 shrink-0" />
                  <p className="text-xs font-semibold text-foreground">{rec.action}</p>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed mt-0.5 ml-4">{rec.reason}</p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
