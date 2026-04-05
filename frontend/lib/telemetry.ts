"use client"

import type {
  Alert,
  HealthFactor,
  LocomotiveData,
  Recommendation,
  TelemetryPoint,
} from "@/lib/mock-data"

export type HealthStatus = "normal" | "warning" | "critical"

export interface TelemetryRaw {
  speed?: number | null
  fuel_level?: number | null
  engine_temp?: number | null
  oil_pressure?: number | null
  voltage?: number | null
  current?: number | null
}

export interface TelemetryMetric {
  value?: number | null
  unit: string
  label_ru: string
  norm_min?: number | null
  norm_max?: number | null
  status: "normal" | "warning" | "critical" | "unknown"
}

export interface TelemetryAlert {
  severity: "critical" | "attention" | "info"
  subsystem: string
  message: string
}

export interface TelemetryRecommendation {
  priority: "high" | "medium" | "low"
  urgency_ru: string
  action_ru: string
  reason_ru: string
}

export interface TelemetryTopFactor {
  key: string
  label: string
  impact_pct: number
  severity: "normal" | "warning" | "critical" | "unknown"
}

export interface TelemetryLive {
  timestamp: string
  locomotive_id: string
  locomotive_uuid?: string | null
  mode?: string | null
  health_hint?: string | null
  error_codes?: string[]
  health_index: number
  health_status: "normal" | "attention" | "critical"
  raw: TelemetryRaw
  metrics: Record<string, TelemetryMetric>
  trends?: Record<string, number | null>
  top_factors?: TelemetryTopFactor[]
  alerts?: TelemetryAlert[]
  recommendations?: TelemetryRecommendation[]
}

export interface ChartData {
  health: TelemetryPoint[]
  speed: TelemetryPoint[]
  brakePressure: TelemetryPoint[]
  tractionTemp: TelemetryPoint[]
  voltage: TelemetryPoint[]
  current: TelemetryPoint[]
}

export interface TelemetryMapped {
  loco: LocomotiveData
  alerts: Alert[]
  recommendations: Recommendation[]
  healthFactors: HealthFactor[]
}

export type ConnectionStatus = "online" | "degraded" | "offline"

const RAW_API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
const API_BASE = RAW_API_BASE.endsWith("/api/v1")
  ? RAW_API_BASE
  : `${RAW_API_BASE}/api/v1`
const WS_BASE = process.env.NEXT_PUBLIC_WS_BASE_URL ?? API_BASE.replace(/^http/, "ws")

export const TELEMETRY_LATEST_URL = `${API_BASE}/telemetry/latest`
export const TELEMETRY_WS_URL = `${WS_BASE}/telemetry/stream`

function toTimeLabel(timestamp: string): string {
  const d = new Date(timestamp)
  if (Number.isNaN(d.getTime())) {
    return new Date().toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit", second: "2-digit" })
  }
  return d.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit", second: "2-digit" })
}

function mapHealthStatus(status: TelemetryLive["health_status"]): HealthStatus {
  return status === "attention" ? "warning" : status
}

function findMetric(metrics: Record<string, TelemetryMetric>, matcher: RegExp): TelemetryMetric | undefined {
  const direct = Object.values(metrics).find((m) => matcher.test(m.label_ru))
  return direct
}

export function applyTelemetryToCharts(
  prev: ChartData,
  payload: TelemetryLive,
): ChartData {
  const time = toTimeLabel(payload.timestamp)
  const pushPoint = (series: TelemetryPoint[], value: number | null | undefined) => {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return series
    }
    const next = [...series, { time, value }]
    return next.length > 120 ? next.slice(-120) : next
  }

  return {
    health: pushPoint(prev.health, payload.health_index),
    speed: pushPoint(prev.speed, payload.raw?.speed ?? null),
    brakePressure: pushPoint(prev.brakePressure, payload.raw?.oil_pressure ?? null),
    tractionTemp: pushPoint(prev.tractionTemp, payload.raw?.engine_temp ?? null),
    voltage: pushPoint(prev.voltage, payload.raw?.voltage ?? null),
    current: pushPoint(prev.current, payload.raw?.current ?? null),
  }
}

export function mapTelemetryToDashboard(
  payload: TelemetryLive,
  base: LocomotiveData,
  connectionStatus: ConnectionStatus,
): TelemetryMapped {
  const metrics = payload.metrics ?? {}
  const speedMetric = metrics.speed ?? findMetric(metrics, /Скорост/i)
  const brakeMetric = metrics.brake_pressure ?? findMetric(metrics, /Давлен.*тормоз/i)
  const tractionMetric = metrics.engine_temp ?? findMetric(metrics, /Температур.*тяг/i)

  const speedLimit = speedMetric?.norm_max ?? base.speedLimit
  const brakeNorm: [number, number] = [
    brakeMetric?.norm_min ?? base.brakePressureNormal[0],
    brakeMetric?.norm_max ?? base.brakePressureNormal[1],
  ]
  const tractionLimit = tractionMetric?.norm_max ?? base.tractionTempLimit

  const loco: LocomotiveData = {
    ...base,
    id: payload.locomotive_id || base.id,
    healthScore: Math.round(payload.health_index),
    healthStatus: mapHealthStatus(payload.health_status),
    speed: Math.round(payload.raw?.speed ?? base.speed),
    speedLimit,
    fuelLevel: Math.round((payload.raw?.fuel_level ?? base.fuelLevel) * 10) / 10,
    brakePressure: Math.round((payload.raw?.oil_pressure ?? base.brakePressure) * 100) / 100,
    brakePressureNormal: brakeNorm,
    tractionTemp: Math.round((payload.raw?.engine_temp ?? base.tractionTemp) * 10) / 10,
    tractionTempLimit: tractionLimit,
    voltage: Math.round((payload.raw?.voltage ?? base.voltage) * 10) / 10,
    currentAmps: Math.round(payload.raw?.current ?? base.currentAmps),
    connectionStatus,
  }

  const alerts: Alert[] = (payload.alerts ?? []).map((alert, idx) => ({
    id: `live-${payload.timestamp}-${idx}`,
    timestamp: toTimeLabel(payload.timestamp),
    severity: alert.severity === "attention" ? "warning" : alert.severity,
    source: alert.subsystem,
    message: alert.message,
  }))

  const recommendations: Recommendation[] = (payload.recommendations ?? []).map((rec, idx) => ({
    id: `rec-${payload.timestamp}-${idx}`,
    priority: rec.priority,
    action: rec.action_ru,
    reason: rec.reason_ru,
    eta: rec.urgency_ru,
  }))

  const healthFactors: HealthFactor[] = (payload.top_factors ?? []).map((f) => {
    const impact = Math.round(f.impact_pct)
    const trend = impact < -1 ? "up" : impact > 1 ? "down" : "stable"
    return {
      name: f.label,
      impact,
      trend,
    }
  })

  return { loco, alerts, recommendations, healthFactors }
}
