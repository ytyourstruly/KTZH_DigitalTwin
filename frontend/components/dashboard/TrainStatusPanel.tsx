"use client"

import { cn } from "@/lib/utils"
import type { LocomotiveData } from "@/lib/mock-data"

// SVG locomotive silhouette
function LocomotiveSVG({ isMoving }: { isMoving: boolean }) {
  return (
    <svg
      viewBox="0 0 320 90"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="w-full h-full"
      aria-label="Locomotive silhouette"
    >
      {/* Main body */}
      <rect x="30" y="28" width="230" height="36" rx="4" className="fill-foreground/10 stroke-foreground/30" strokeWidth="1" />

      {/* Cab section */}
      <path d="M220 28 L240 14 L270 14 L280 28 Z" className="fill-foreground/15 stroke-foreground/30" strokeWidth="1" />

      {/* Cab windows */}
      <rect x="244" y="17" width="14" height="9" rx="1" className="fill-foreground/5 stroke-foreground/40" strokeWidth="0.8" />
      <rect x="262" y="17" width="12" height="9" rx="1" className="fill-foreground/5 stroke-foreground/40" strokeWidth="0.8" />

      {/* Body windows / vents */}
      <rect x="60" y="33" width="28" height="14" rx="1" className="fill-foreground/5 stroke-foreground/20" strokeWidth="0.8" />
      <rect x="96" y="33" width="28" height="14" rx="1" className="fill-foreground/5 stroke-foreground/20" strokeWidth="0.8" />
      <rect x="132" y="33" width="22" height="14" rx="1" className="fill-foreground/5 stroke-foreground/20" strokeWidth="0.8" />

      {/* Nose / front plow */}
      <path d="M30 34 L18 38 L18 54 L30 58 Z" className="fill-foreground/15 stroke-foreground/30" strokeWidth="1" />

      {/* Front headlights */}
      <circle cx="16" cy="42" r="3" className={cn("fill-status-warning", isMoving ? "opacity-90" : "opacity-30")} />
      <circle cx="16" cy="52" r="2.5" className={cn("fill-status-warning", isMoving ? "opacity-70" : "opacity-20")} />

      {/* Undercarriage */}
      <rect x="25" y="63" width="238" height="5" rx="1" className="fill-foreground/20" />

      {/* Bogies - front */}
      <rect x="36" y="63" width="50" height="7" rx="2" className="fill-foreground/25 stroke-foreground/20" strokeWidth="0.5" />
      {/* Front wheels */}
      <circle
        cx="48" cy="72" r="8"
        className={cn("fill-foreground/10 stroke-foreground/40", isMoving && "animate-wheel-spin")}
        strokeWidth="1.5"
        style={{ transformOrigin: "48px 72px" }}
      />
      <circle cx="48" cy="72" r="3" className="fill-foreground/20" />
      <circle cx="48" cy="72" r="1" className="fill-foreground/40" />
      <line x1="48" y1="64" x2="48" y2="80" className="stroke-foreground/20" strokeWidth="1" />
      <line x1="40" y1="72" x2="56" y2="72" className="stroke-foreground/20" strokeWidth="1" />

      <circle
        cx="74" cy="72" r="8"
        className={cn("fill-foreground/10 stroke-foreground/40", isMoving && "animate-wheel-spin")}
        strokeWidth="1.5"
        style={{ transformOrigin: "74px 72px" }}
      />
      <circle cx="74" cy="72" r="3" className="fill-foreground/20" />
      <circle cx="74" cy="72" r="1" className="fill-foreground/40" />
      <line x1="74" y1="64" x2="74" y2="80" className="stroke-foreground/20" strokeWidth="1" />
      <line x1="66" y1="72" x2="82" y2="72" className="stroke-foreground/20" strokeWidth="1" />

      {/* Bogies - rear */}
      <rect x="200" y="63" width="50" height="7" rx="2" className="fill-foreground/25 stroke-foreground/20" strokeWidth="0.5" />
      <circle
        cx="212" cy="72" r="8"
        className={cn("fill-foreground/10 stroke-foreground/40", isMoving && "animate-wheel-spin")}
        strokeWidth="1.5"
        style={{ transformOrigin: "212px 72px" }}
      />
      <circle cx="212" cy="72" r="3" className="fill-foreground/20" />
      <circle cx="212" cy="72" r="1" className="fill-foreground/40" />
      <line x1="212" y1="64" x2="212" y2="80" className="stroke-foreground/20" strokeWidth="1" />
      <line x1="204" y1="72" x2="220" y2="72" className="stroke-foreground/20" strokeWidth="1" />

      <circle
        cx="238" cy="72" r="8"
        className={cn("fill-foreground/10 stroke-foreground/40", isMoving && "animate-wheel-spin")}
        strokeWidth="1.5"
        style={{ transformOrigin: "238px 72px" }}
      />
      <circle cx="238" cy="72" r="3" className="fill-foreground/20" />
      <circle cx="238" cy="72" r="1" className="fill-foreground/40" />
      <line x1="238" y1="64" x2="238" y2="80" className="stroke-foreground/20" strokeWidth="1" />
      <line x1="230" y1="72" x2="246" y2="72" className="stroke-foreground/20" strokeWidth="1" />

      {/* Exhaust stack */}
      <rect x="100" y="20" width="6" height="9" rx="1" className="fill-foreground/20 stroke-foreground/20" strokeWidth="0.5" />
      <rect x="115" y="18" width="6" height="11" rx="1" className="fill-foreground/20 stroke-foreground/20" strokeWidth="0.5" />

      {/* Coupling rear */}
      <rect x="266" y="42" width="12" height="6" rx="1" className="fill-foreground/30 stroke-foreground/20" strokeWidth="0.5" />

      {/* Stripe accent */}
      <rect x="30" y="56" width="230" height="2" rx="1" className="fill-accent/60" />
    </svg>
  )
}

// Moving track strip 
function TrackStrip({ isMoving }: { isMoving: boolean }) {
  return (
    <div className="relative w-full h-6 overflow-hidden">
      {/* Rails */}
      <div className="absolute top-1.5 left-0 right-0 h-0.5 bg-foreground/20 rounded" />
      <div className="absolute bottom-1.5 left-0 right-0 h-0.5 bg-foreground/20 rounded" />
      {/* Sleepers - scrolling when moving */}
      <div className={cn("flex absolute inset-y-0", isMoving && "animate-track-scroll")} style={{ width: "200%" }}>
        {Array.from({ length: 40 }, (_, i) => (
          <div key={i} className="flex flex-col justify-between" style={{ minWidth: "24px" }}>
            <div className="w-0.5 h-full mx-auto bg-foreground/15 rounded" />
          </div>
        ))}
      </div>
    </div>
  )
}

interface TrainStatusPanelProps {
  loco: LocomotiveData
}

export function TrainStatusPanel({ loco }: TrainStatusPanelProps) {
  const isMoving = loco.speed > 0

  const statusConfig = {
    normal: { label: "Движется" as const, className: "text-status-normal bg-status-normal-bg border-status-normal/40" },
    warning: { label: "Внимание" as const, className: "text-status-warning bg-status-warning-bg border-status-warning/40" },
    critical: { label: "Критично" as const, className: "text-status-critical bg-status-critical-bg border-status-critical/40" },
  }

  const displayStatus = !isMoving
    ? { label: "Остановлен", className: "text-muted-foreground bg-muted border-border" }
    : statusConfig[loco.healthStatus]

  return (
    <div className="bg-card border border-border rounded p-4 flex flex-col gap-3 h-full">
      {/* Title row */}
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-muted-foreground font-mono uppercase tracking-wider">Тяговый локомотив</div>
          <div className="text-sm font-semibold text-foreground font-mono">{loco.id}</div>
        </div>
        <div className="text-right">
          <div className="text-xs text-muted-foreground font-mono">{loco.model}</div>
          <span className={cn(
            "inline-block mt-1 text-xs font-mono px-2 py-0.5 rounded border font-semibold",
            displayStatus.className
          )}>
            {displayStatus.label}
          </span>
        </div>
      </div>

      {/* Track strip - top */}
      <TrackStrip isMoving={isMoving} />

      {/* Train visual */}
      <div className={cn(
        "relative flex-1 flex items-center justify-center py-2",
        isMoving && "animate-train-float"
      )}>
        <LocomotiveSVG isMoving={isMoving} />
      </div>

      {/* Track strip - bottom */}
      <TrackStrip isMoving={isMoving} />

      {/* Speed and metrics */}
      <div className="grid grid-cols-3 gap-2 pt-1 border-t border-border">
        <div className="text-center">
          <div className="font-mono text-2xl font-bold text-foreground tabular-nums leading-none">
            {loco.speed}
          </div>
          <div className="text-xs text-muted-foreground font-mono mt-0.5">км/ч</div>
        </div>
        <div className="text-center border-x border-border">
          <div className="font-mono text-sm font-semibold text-foreground tabular-nums leading-none mt-1">
            {loco.speedLimit}
          </div>
          <div className="text-xs text-muted-foreground font-mono mt-0.5">Лимит км/ч</div>
        </div>
        <div className="text-center">
          <div className="font-mono text-sm font-semibold text-foreground tabular-nums leading-none mt-1">
            {loco.distanceCovered}
          </div>
          <div className="text-xs text-muted-foreground font-mono mt-0.5">Пройдено км</div>
        </div>
      </div>

      {/* Speed bar */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs font-mono text-muted-foreground">
          <span>0</span>
          <span>Скорость</span>
          <span>{loco.speedLimit}</span>
        </div>
        <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
          <div
            className={cn(
              "h-full rounded-full transition-all duration-1000",
              loco.speed / loco.speedLimit > 0.9 ? "bg-status-critical" :
              loco.speed / loco.speedLimit > 0.7 ? "bg-status-warning" : "bg-status-normal"
            )}
            style={{ width: `${(loco.speed / loco.speedLimit) * 100}%` }}
          />
        </div>
      </div>
    </div>
  )
}
