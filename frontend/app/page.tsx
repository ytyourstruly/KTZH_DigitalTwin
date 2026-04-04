"use client"

import { useState, useEffect, useCallback } from "react"
import { Header } from "@/components/dashboard/Header"
import { TrainStatusPanel } from "@/components/dashboard/TrainStatusPanel"
import { HealthIndexCard } from "@/components/dashboard/HealthIndexCard"
import { TelemetryCard } from "@/components/dashboard/TelemetryCard"
import { AlertsPanel } from "@/components/dashboard/AlertsPanel"
import { TrendChartsSection } from "@/components/dashboard/TrendChartsSection"
import { RouteStrip } from "@/components/dashboard/RouteStrip"
import { RecommendationsPanel } from "@/components/dashboard/RecommendationsPanel"
import { LOCOMOTIVES, ALERTS, CHART_DATA, type LocomotiveData } from "@/lib/mock-data"
import { cn } from "@/lib/utils"

export default function DashboardPage() {
  const [selectedLoco, setSelectedLoco] = useState<LocomotiveData>(LOCOMOTIVES[0])
  const [isLive, setIsLive] = useState(true)

  // Simulate live telemetry tick — small random drift each second
  const [liveData, setLiveData] = useState(selectedLoco)

  const tick = useCallback(() => {
    if (!isLive) return
    setLiveData((prev) => {
      const jitter = (range: number) => (Math.random() - 0.5) * range
      const newSpeed = Math.max(0, Math.min(prev.speedLimit, prev.speed + jitter(4)))
      const newTemp = Math.max(20, Math.min(110, prev.tractionTemp + jitter(1.5)))
      const newPressure = Math.max(0, Math.min(8, prev.brakePressure + jitter(0.15)))
      const newVoltage = Math.max(20, Math.min(30, prev.voltage + jitter(0.2)))
      const newFuel = Math.max(0, prev.fuelLevel - Math.random() * 0.02)

      return {
        ...prev,
        speed: Math.round(newSpeed),
        tractionTemp: Math.round(newTemp * 10) / 10,
        brakePressure: Math.round(newPressure * 100) / 100,
        voltage: Math.round(newVoltage * 10) / 10,
        fuelLevel: Math.round(newFuel * 10) / 10,
        healthScore: Math.max(
          0,
          Math.min(
            100,
            prev.healthScore +
              (newTemp > 90 ? -0.5 : 0) +
              (newPressure < 4.5 ? -0.5 : 0.1)
          )
        ),
        healthStatus:
          prev.healthScore < 50 ? "critical" : prev.healthScore < 70 ? "warning" : "normal",
      }
    })
  }, [isLive])

  useEffect(() => {
    const interval = setInterval(tick, 2000)
    return () => clearInterval(interval)
  }, [tick])

  // Sync when user switches locomotive
  useEffect(() => {
    setLiveData(selectedLoco)
  }, [selectedLoco])

  // Compute deltas for telemetry cards
  const speedHistory = CHART_DATA.speed
  const prevSpeed = speedHistory.length > 4 ? speedHistory[speedHistory.length - 5].value : liveData.speed
  const speedDelta = Math.round(liveData.speed - prevSpeed)

  const prevTemp = CHART_DATA.tractionTemp.length > 4
    ? CHART_DATA.tractionTemp[CHART_DATA.tractionTemp.length - 5].value
    : liveData.tractionTemp
  const tempDelta = Math.round((liveData.tractionTemp - prevTemp) * 10) / 10

  const prevPressure = CHART_DATA.brakePressure.length > 4
    ? CHART_DATA.brakePressure[CHART_DATA.brakePressure.length - 5].value
    : liveData.brakePressure
  const pressureDelta = Math.round((liveData.brakePressure - prevPressure) * 100) / 100

  const fuelPercent = Math.max(0, Math.min(100, liveData.fuelLevel))
  const fuelStatus = fuelPercent > 60 ? "normal" : fuelPercent > 30 ? "warning" : "critical"
  const fuelValueClass = fuelStatus === "normal"
    ? "text-status-normal"
    : fuelStatus === "warning"
    ? "text-status-warning"
    : "text-status-critical"
  const fuelBorderClass = fuelStatus === "normal"
    ? "border-l-status-normal"
    : fuelStatus === "warning"
    ? "border-l-status-warning"
    : "border-l-status-critical"

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-background">
      {/* Header */}
      <Header
        selectedLoco={liveData}
        onLocoChange={setSelectedLoco}
        isLive={isLive}
        onToggleLive={() => setIsLive((v) => !v)}
      />

      {/* Main dashboard grid */}
      <main className="flex-1 overflow-y-auto p-3 min-h-0">
        <div className="grid grid-cols-12 gap-3 min-h-full">

          {/* Row 1 — Train visual + Health Index + Telemetry row */}
          {/* Train status panel — 3 cols */}
          <div className="col-span-12 md:col-span-4 lg:col-span-3 row-span-2">
            <TrainStatusPanel loco={liveData} />
          </div>

          {/* Health Index — 3 cols */}
          <div className="col-span-12 md:col-span-4 lg:col-span-3 row-span-2">
            <HealthIndexCard loco={liveData} />
          </div>

          {/* Telemetry cards — 6 cols, 2 rows worth */}
          <div className="col-span-12 lg:col-span-6 grid grid-cols-2 md:grid-cols-3 gap-3">
            <TelemetryCard
              label="Скорость"
              value={liveData.speed}
              unit="км/ч"
              delta={speedDelta}
              history={CHART_DATA.speed}
              sparklineColor="stroke-chart-2"
              status={
                liveData.speed > liveData.speedLimit * 0.95
                  ? "critical"
                  : liveData.speed > liveData.speedLimit * 0.8
                  ? "warning"
                  : "normal"
              }
              tooltip="Текущая скорость. Лимит зависит от участка пути."
            />
            <div className={cn(
              "bg-card border border-border rounded p-3 flex flex-col gap-2 min-h-[100px] border-l-2",
              fuelBorderClass
            )}>
              <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">Уровень топлива</span>
              <div className="flex-1 flex flex-col justify-center">
                <div className={cn("text-3xl font-mono font-bold tabular-nums", fuelValueClass)}>
                  {liveData.fuelLevel}%
                </div>
                <div className="text-xs text-muted-foreground font-mono mt-2">
                  {Math.round((liveData.fuelLevel / 100) * 10000)} / 10000 л
                </div>
              </div>
            </div>
            <TelemetryCard
              label="Расход топлива"
              value={liveData.fuelRate}
              unit="л/ч"
              delta={2}
              sparklineColor="stroke-chart-3"
              status={liveData.fuelRate > 160 ? "warning" : "normal"}
              tooltip="Расход топлива. Повышенный расход может указывать на проблемы нагрузки."
            />
            <TelemetryCard
              label="Давление тормоза"
              value={liveData.brakePressure}
              unit="бар"
              delta={pressureDelta}
              precision={2}
              history={CHART_DATA.brakePressure}
              sparklineColor="stroke-chart-1"
              status={
                liveData.brakePressure < liveData.brakePressureNormal[0]
                  ? "critical"
                  : liveData.brakePressure > liveData.brakePressureNormal[1]
                  ? "warning"
                  : "normal"
              }
              safeRange={liveData.brakePressureNormal}
              tooltip="Давление в тормозной магистрали. Должно быть в допустимых пределах."
            />
            <TelemetryCard
              label="Температура тяги"
              value={liveData.tractionTemp}
              unit="°C"
              delta={tempDelta}
              history={CHART_DATA.tractionTemp}
              sparklineColor="stroke-chart-4"
              status={
                liveData.tractionTemp >= liveData.tractionTempLimit
                  ? "critical"
                  : liveData.tractionTemp >= liveData.tractionTempLimit * 0.9
                  ? "warning"
                  : "normal"
              }
              safeRange={[0, liveData.tractionTempLimit]}
              tooltip="Температура тягового мотора. Приближение к лимиту активирует тепловую защиту."
            />
            <TelemetryCard
              label="Напряжение"
              value={liveData.voltage}
              unit="В"
              delta={0.1}
              precision={1}
              history={CHART_DATA.voltage}
              sparklineColor="stroke-chart-5"
              status={liveData.voltage < 23 ? "warning" : "normal"}
              safeRange={[22, 28]}
              tooltip="Напряжение батареи/генератора. Низкое напряжение указывает на проблемы генератора."
            />
          </div>

          {/* Row 2 — second row of telemetry (fills height) */}
          <div className="col-span-12 lg:col-span-6 grid grid-cols-2 md:grid-cols-3 gap-3">
            <TelemetryCard
              label="Ток нагрузки"
              value={Math.round(liveData.currentAmps)}
              unit="А"
              delta={8}
              history={CHART_DATA.current}
              sparklineColor="stroke-chart-5"
              status={liveData.currentAmps > 400 ? "warning" : "normal"}
              safeRange={[0, 450]}
              tooltip="Электрический ток от тяговых моторов и вспомогательных систем."
            />
            <div className="col-span-1 md:col-span-2 bg-card border border-border rounded p-3 flex flex-col gap-1 justify-center">
              <div className="text-xs font-mono text-muted-foreground uppercase tracking-wider">Прогресс маршрута</div>
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-foreground font-semibold">{liveData.routeProgress}%</span>
                <span className="text-muted-foreground">{liveData.distanceCovered} / {liveData.totalDistance} км</span>
              </div>
              <div className="h-2 bg-secondary rounded-full overflow-hidden mt-1">
                <div
                  className="h-full bg-chart-1 rounded-full transition-all duration-1000"
                  style={{ width: `${liveData.routeProgress}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-xs font-mono mt-1">
                <span className="text-muted-foreground">Начало</span>
                <span className="text-status-warning">Следующая: {liveData.nextStation} ({liveData.nextStationKm} км)</span>
                <span className="text-muted-foreground">Конец</span>
              </div>
            </div>
          </div>

          {/* Row 3 — Alerts + Recommendations side by side */}
          <div className="col-span-12 md:col-span-7 lg:col-span-8" style={{ minHeight: "260px" }}>
            <AlertsPanel alerts={ALERTS} />
          </div>
          <div className="col-span-12 md:col-span-5 lg:col-span-4" style={{ minHeight: "260px" }}>
            <RecommendationsPanel />
          </div>

          {/* Row 4 — Trend charts full width */}
          <div className="col-span-12">
            <TrendChartsSection />
          </div>

          {/* Row 5 — Route strip full width */}
          <div className="col-span-12">
            <RouteStrip loco={liveData} />
          </div>

        </div>
      </main>
    </div>
  )
}
