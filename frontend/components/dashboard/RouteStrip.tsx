"use client"

import { cn } from "@/lib/utils"
import { ROUTE_STATIONS } from "@/lib/mock-data"
import type { LocomotiveData } from "@/lib/mock-data"
import { AlertTriangle, MapPin, Navigation } from "lucide-react"

interface RouteStripProps {
  loco: LocomotiveData
}

export function RouteStrip({ loco }: RouteStripProps) {
  const currentKm = loco.distanceCovered
  const totalKm = ROUTE_STATIONS[ROUTE_STATIONS.length - 1].km
  const startStation = ROUTE_STATIONS[0]
  const endStation = ROUTE_STATIONS[ROUTE_STATIONS.length - 1]

  const passedStations = ROUTE_STATIONS.filter((s) => s.km < currentKm)
  const nextStation = ROUTE_STATIONS.find((s) => s.status === "next")
  const currentSectionStart = passedStations[passedStations.length - 1]
  const currentSectionEnd = nextStation || ROUTE_STATIONS.find((s) => s.km >= currentKm)

  return (
    <div className="bg-card border border-border rounded p-4 flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Navigation className="w-4 h-4 text-accent" />
          <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
            Маршрут: {startStation?.name ?? "Начало"} → {endStation?.name ?? "Конец"}
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono text-muted-foreground">
          <span className="font-semibold text-foreground">{loco.distanceCovered}</span>
          <span>/</span>
          <span>{loco.totalDistance} км</span>
        </div>
      </div>

      {/* Overall progress bar */}
      <div className="relative h-2 bg-secondary rounded-full overflow-hidden">
        <div
          className="h-full bg-status-normal rounded-full transition-all duration-1000"
          style={{ width: `${(currentKm / loco.totalDistance) * 100}%` }}
        />
      </div>

      {/* Railway track diagram */}
      <div className="relative py-10 px-2 border border-border/40 rounded bg-muted/20">
        {/* Main track rails - top and bottom */}
        <div className="absolute top-1/3 left-0 right-0 h-px bg-gradient-to-r from-foreground/30 via-foreground/50 to-foreground/30" />
        <div className="absolute top-1/3 translate-y-2 left-0 right-0 h-px bg-gradient-to-r from-foreground/30 via-foreground/50 to-foreground/30" />

        {/* Sleepers/ties across track */}
        <div className="absolute inset-0 flex items-center justify-between px-4" style={{ top: "32%", height: "8px" }}>
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={i} className="w-px h-2 bg-foreground/15" />
          ))}
        </div>

        {/* Station markers and labels */}
        <div className="relative flex items-center justify-between px-4 space-y-0">
          {ROUTE_STATIONS.slice(0, 6).map((station, idx) => {
            const posPercent = (station.km / totalKm) * 100
            const isPassed = station.km < currentKm
            const isCurrent = Math.abs(station.km - currentKm) < 30
            const isNext = station.status === "next"
            const hasRestriction = !!station.restriction

            return (
              <div
                key={station.id}
                className="relative flex flex-col items-center"
                style={{ width: `calc(100% / 6)` }}
              >
                {/* Station marker circle - positioned on track */}
                <div style={{ height: "32px" }} className="flex items-center justify-center w-full">
                  <div className={cn(
                    "relative z-10 w-5 h-5 rounded-full border-2 transition-all",
                    isPassed && "bg-status-normal border-status-normal shadow-lg shadow-status-normal/50",
                    isNext && "bg-status-warning border-status-warning ring-2 ring-status-warning/40 scale-125",
                    isCurrent && !isPassed && !isNext && "bg-foreground/40 border-foreground/60 animate-pulse",
                    !isPassed && !isNext && !isCurrent && "bg-card border-border",
                  )}>
                    {isNext && (
                      <div className="absolute inset-0 animate-blink-dot rounded-full border-2 border-status-warning" />
                    )}
                  </div>
                </div>

                {/* Restriction indicator - positioned above track */}
                {hasRestriction && (
                  <div className="absolute top-0 left-1/2 -translate-x-1/2 z-20">
                    <AlertTriangle className="w-3.5 h-3.5 text-status-warning fill-status-warning-bg" />
                  </div>
                )}

                {/* Station name and km - positioned below track */}
                <div className="text-center pt-2" style={{ minHeight: "48px" }}>
                  <div className={cn(
                    "text-xs font-mono font-semibold truncate px-1 leading-tight",
                    isNext ? "text-status-warning" : isPassed ? "text-foreground" : "text-foreground/60",
                  )}>
                    {station.name}
                  </div>
                  <div className="text-xs text-muted-foreground font-mono tabular-nums mt-0.5">
                    {station.km} км
                  </div>
                  {hasRestriction && (
                    <div className="text-xs font-mono text-status-warning font-semibold tabular-nums mt-1 bg-status-warning-bg px-1 py-0.5 rounded">
                      {station.restriction} км/ч
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Current position and operational info */}
      <div className="grid grid-cols-2 gap-3 pt-2 border-t border-border">
        <div>
          <div className="text-xs text-muted-foreground font-mono uppercase tracking-wider">Текущий перегон</div>
          <div className="text-sm font-semibold text-foreground font-mono mt-1">
            {currentSectionStart?.name ?? "Начало"} → {currentSectionEnd?.name ?? "Конец"}
          </div>
          <div className="text-xs text-muted-foreground font-mono mt-0.5">
            Пройдено {currentKm - (currentSectionStart?.km ?? 0)} из {(currentSectionEnd?.km ?? totalKm) - (currentSectionStart?.km ?? 0)} км
          </div>
        </div>
        <div>
          <div className="flex items-center gap-2 mb-1">
            <MapPin className="w-3 h-3 text-status-warning shrink-0" />
            <div className="text-xs text-muted-foreground font-mono uppercase tracking-wider">Следующая станция</div>
          </div>
          <div className="text-sm font-semibold text-status-warning font-mono">
            {loco.nextStation}
          </div>
          <div className="text-xs text-muted-foreground font-mono mt-0.5">
            {loco.nextStationKm} км | ПВП: ≈ {Math.round((loco.nextStationKm / Math.max(loco.speed, 1)) * 60)} мин
          </div>
        </div>
      </div>

      {/* Speed and restriction info */}
      <div className="grid grid-cols-2 gap-3 pt-2 border-t border-border">
        <div>
          <div className="text-xs text-muted-foreground font-mono uppercase tracking-wider">Текущая скорость</div>
          <div className="font-mono text-lg font-bold text-foreground tabular-nums">
            {loco.speed} <span className="text-xs text-muted-foreground">км/ч</span>
          </div>
          <div className="text-xs text-muted-foreground font-mono mt-0.5">
            Лимит: {loco.speedLimit} км/ч
          </div>
        </div>
        <div>
          <div className="text-xs text-muted-foreground font-mono uppercase tracking-wider">Расстояние до конца</div>
          <div className="font-mono text-lg font-bold text-foreground tabular-nums">
            {loco.totalDistance - loco.distanceCovered} <span className="text-xs text-muted-foreground">км</span>
          </div>
          <div className="text-xs text-muted-foreground font-mono mt-0.5">
            ПВП в конец маршрута: ≈ {Math.round(((loco.totalDistance - loco.distanceCovered) / Math.max(loco.speed, 1)) * 60)} мин
          </div>
        </div>
      </div>
    </div>
  )
}
