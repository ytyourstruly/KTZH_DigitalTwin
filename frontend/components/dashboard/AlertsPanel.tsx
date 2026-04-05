"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { AlertTriangle, Info, CheckCircle, XCircle, Clock } from "lucide-react"
import type { Alert, AlertSeverity } from "@/lib/mock-data"

const SEVERITY_CONFIG: Record<AlertSeverity, {
  icon: React.ElementType
  label: string
  className: string
  rowClass: string
}> = {
  critical: {
    icon: XCircle,
    label: "Критично",
    className: "text-status-critical bg-status-critical-bg border-status-critical/40",
    rowClass: "border-l-status-critical bg-status-critical-bg/40",
  },
  warning: {
    icon: AlertTriangle,
    label: "Внимание",
    className: "text-status-warning bg-status-warning-bg border-status-warning/40",
    rowClass: "border-l-status-warning",
  },
  info: {
    icon: Info,
    label: "Инфо",
    className: "text-chart-1 bg-secondary border-chart-1/30",
    rowClass: "border-l-chart-1",
  },
  resolved: {
    icon: CheckCircle,
    label: "Устранено",
    className: "text-muted-foreground bg-muted border-border",
    rowClass: "border-l-border opacity-60",
  },
}

type FilterType = "all" | AlertSeverity

interface AlertsPanelProps {
  alerts: Alert[]
}

export function AlertsPanel({ alerts }: AlertsPanelProps) {
  const [filter, setFilter] = useState<FilterType>("all")

  const filters: { key: FilterType; label: string; count: number }[] = [
    { key: "all", label: "Все", count: alerts.length },
    { key: "critical", label: "Критично", count: alerts.filter((a) => a.severity === "critical").length },
    { key: "warning", label: "Внимание", count: alerts.filter((a) => a.severity === "warning").length },
    { key: "resolved", label: "Устранено", count: alerts.filter((a) => a.severity === "resolved").length },
  ]

  const filtered = filter === "all" ? alerts : alerts.filter((a) => a.severity === filter)

  const unresolved = alerts.filter((a) => a.severity !== "resolved").length

  return (
    <div className="bg-card border border-border rounded flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">Активные предупреждения</span>
          {unresolved > 0 && (
            <span className="text-xs font-mono font-bold px-1.5 py-0.5 rounded bg-status-critical-bg text-status-critical border border-status-critical/40">
              {unresolved}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3 text-muted-foreground" />
          <span className="text-xs text-muted-foreground font-mono">Живая лента</span>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-1 px-4 py-2 border-b border-border">
        {filters.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={cn(
              "flex items-center gap-1 text-xs font-mono px-2 py-1 rounded transition-colors",
              filter === f.key
                ? "bg-secondary text-foreground font-semibold"
                : "text-muted-foreground hover:text-foreground hover:bg-muted"
            )}
          >
            {f.label}
            <span className={cn(
              "text-xs rounded px-1 tabular-nums",
              filter === f.key ? "text-foreground" : "text-muted-foreground"
            )}>
              {f.count}
            </span>
          </button>
        ))}
      </div>

      {/* Alert list */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {filtered.length === 0 ? (
          <div className="flex items-center justify-center h-20 text-xs text-muted-foreground font-mono">
            Нет предупреждений в этой категории
          </div>
        ) : (
          <div className="divide-y divide-border">
            {filtered.map((alert) => {
              const cfg = SEVERITY_CONFIG[alert.severity]
              const Icon = cfg.icon
              return (
                <div
                  key={alert.id}
                  className={cn(
                    "flex gap-3 px-4 py-3 border-l-2 transition-colors hover:bg-muted/30",
                    cfg.rowClass
                  )}
                >
                  <Icon className={cn("w-4 h-4 mt-0.5 shrink-0", SEVERITY_CONFIG[alert.severity].className.split(" ")[0])} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 mb-0.5">
                      <div className="flex items-center gap-2">
                        <span className={cn(
                          "text-xs font-mono font-semibold px-1.5 py-0.5 rounded border",
                          cfg.className
                        )}>
                          {cfg.label}
                        </span>
                        <span className="text-xs text-muted-foreground font-mono">{alert.source}</span>
                      </div>
                      <span className="text-xs text-muted-foreground font-mono tabular-nums shrink-0">{alert.timestamp}</span>
                    </div>
                    <p className="text-xs text-foreground leading-relaxed">{alert.message}</p>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
