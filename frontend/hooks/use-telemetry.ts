"use client"

import { useEffect, useRef, useState } from "react"
import {
  TELEMETRY_LATEST_URL,
  TELEMETRY_WS_URL,
  applyTelemetryToCharts,
  mapTelemetryToDashboard,
  type ChartData,
  type ConnectionStatus,
  type TelemetryLive,
} from "@/lib/telemetry"
import {
  ALERTS,
  CHART_DATA,
  HEALTH_FACTORS,
  LOCOMOTIVES,
  RECOMMENDATIONS,
  type Alert,
  type HealthFactor,
  type LocomotiveData,
  type Recommendation,
} from "@/lib/mock-data"

interface TelemetryState {
  loco: LocomotiveData
  alerts: Alert[]
  recommendations: Recommendation[]
  healthFactors: HealthFactor[]
  chartData: ChartData
}

interface TelemetryStatus {
  loading: boolean
  wsConnected: boolean
  lastMessageAt: number | null
}

const DEFAULT_STATE: TelemetryState = {
  loco: LOCOMOTIVES[0],
  alerts: ALERTS,
  recommendations: RECOMMENDATIONS,
  healthFactors: HEALTH_FACTORS,
  chartData: CHART_DATA,
}

function resolveConnectionStatus(status: TelemetryStatus): ConnectionStatus {
  if (status.wsConnected) return "online"
  if (status.lastMessageAt) return "degraded"
  return "offline"
}

export function useTelemetry(baseLoco: LocomotiveData, enabled: boolean) {
  const [state, setState] = useState<TelemetryState>(() => ({
    ...DEFAULT_STATE,
    loco: baseLoco,
  }))
  const [status, setStatus] = useState<TelemetryStatus>({
    loading: true,
    wsConnected: false,
    lastMessageAt: null,
  })

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectRef = useRef<number | null>(null)
  const backoffRef = useRef(1000)
  const lastPayloadRef = useRef<TelemetryLive | null>(null)

  const applyPayload = (payload: TelemetryLive) => {
    lastPayloadRef.current = payload
    setState((prev) => {
      const chartData = applyTelemetryToCharts(prev.chartData, payload)
      const connectionStatus = resolveConnectionStatus({
        ...status,
        wsConnected: status.wsConnected,
        lastMessageAt: Date.now(),
      })
      const mapped = mapTelemetryToDashboard(payload, baseLoco, connectionStatus)
      return {
        loco: mapped.loco,
        alerts: mapped.alerts,
        recommendations: mapped.recommendations,
        healthFactors: mapped.healthFactors,
        chartData,
      }
    })
    setStatus((prev) => ({
      ...prev,
      loading: false,
      lastMessageAt: Date.now(),
    }))
  }

  useEffect(() => {
    let cancelled = false

    const loadLatest = async () => {
      try {
        const res = await fetch(TELEMETRY_LATEST_URL, { credentials: "include" })
        if (!res.ok) {
          throw new Error(`latest failed: ${res.status}`)
        }
        const data = (await res.json()) as TelemetryLive | null
        if (cancelled || !data) {
          return
        }
        applyPayload(data)
      } catch {
        setStatus((prev) => ({ ...prev, loading: false }))
      }
    }

    void loadLatest()

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!enabled) return

    const connect = () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      const ws = new WebSocket(TELEMETRY_WS_URL)
      wsRef.current = ws

      ws.onopen = () => {
        backoffRef.current = 1000
        setStatus((prev) => ({ ...prev, wsConnected: true }))
      }
      ws.onmessage = (event) => {
        if (!enabled) return
        try {
          const data = JSON.parse(event.data) as TelemetryLive
          applyPayload(data)
        } catch {
          // ignore malformed payloads
        }
      }
      ws.onclose = () => {
        setStatus((prev) => ({ ...prev, wsConnected: false }))
        if (!enabled) return
        const timeout = backoffRef.current
        backoffRef.current = Math.min(backoffRef.current * 1.6, 10000)
        if (reconnectRef.current) {
          window.clearTimeout(reconnectRef.current)
        }
        reconnectRef.current = window.setTimeout(connect, timeout)
      }
      ws.onerror = () => {
        ws.close()
      }
    }

    connect()

    return () => {
      if (reconnectRef.current) {
        window.clearTimeout(reconnectRef.current)
      }
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [enabled])

  useEffect(() => {
    const payload = lastPayloadRef.current
    if (!payload) {
      setState((prev) => ({ ...prev, loco: baseLoco }))
      return
    }
    const connectionStatus = resolveConnectionStatus(status)
    const mapped = mapTelemetryToDashboard(payload, baseLoco, connectionStatus)
    setState((prev) => ({
      ...prev,
      loco: mapped.loco,
      alerts: mapped.alerts,
      recommendations: mapped.recommendations,
      healthFactors: mapped.healthFactors,
    }))
  }, [baseLoco])

  return { state, status }
}
