"use client"

import { useState } from "react"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
} from "recharts"
import { cn } from "@/lib/utils"
import { CHART_DATA } from "@/lib/mock-data"
import type { ChartData } from "@/lib/telemetry"

type TimeRange = "1m" | "5m" | "15m"

const TIME_RANGE_POINTS: Record<TimeRange, number> = {
  "1m": 4,
  "5m": 20,
  "15m": 60,
}

function ChartTooltipContent({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-popover border border-border rounded p-2 shadow-lg">
      <div className="text-xs text-muted-foreground font-mono mb-1">{label}</div>
      {payload.map((p: any) => (
        <div key={p.name} className="flex items-center gap-2 text-xs font-mono">
          <div className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-muted-foreground">{p.name}:</span>
          <span className="font-semibold text-foreground tabular-nums">
            {typeof p.value === "number" ? p.value.toFixed(1) : p.value}
          </span>
        </div>
      ))}
    </div>
  )
}

interface MiniChartProps {
  title: string
  data: { time: string; value: number }[]
  dataKey: string
  color: string
  unit: string
  referenceLines?: { value: number; label: string; color?: string }[]
  secondaryData?: { time: string; value: number }[]
  secondaryKey?: string
  secondaryColor?: string
  timeRange: TimeRange
}

function MiniChart({
  title,
  data,
  dataKey,
  color,
  unit,
  referenceLines,
  secondaryData,
  secondaryKey,
  secondaryColor,
  timeRange,
}: MiniChartProps) {
  const points = TIME_RANGE_POINTS[timeRange]

  const primarySliced = data.slice(-points)
  const mergedData = secondaryData
    ? primarySliced.map((d, i) => ({
        ...d,
        ...(secondaryData[secondaryData.length - points + i] ?? {}),
        time: d.time,
      }))
    : primarySliced

  return (
    <div className="bg-card border border-border rounded p-3 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">{title}</span>
        <span className="text-xs font-mono text-muted-foreground">{unit}</span>
      </div>
      <div className="h-36">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={mergedData} margin={{ top: 4, right: 4, bottom: 0, left: -16 }}>
            <CartesianGrid strokeDasharray="2 4" className="stroke-border" opacity={0.5} />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 9, fontFamily: "monospace" }}
              className="fill-muted-foreground"
              tickLine={false}
              axisLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fontSize: 9, fontFamily: "monospace" }}
              className="fill-muted-foreground"
              tickLine={false}
              axisLine={false}
              width={30}
            />
            <Tooltip content={<ChartTooltipContent />} />
            {referenceLines?.map((ref) => (
              <ReferenceLine
                key={ref.value}
                y={ref.value}
                stroke={ref.color ?? "#ef4444"}
                strokeDasharray="3 3"
                strokeWidth={1}
                label={{ value: ref.label, fill: ref.color ?? "#ef4444", fontSize: 8, fontFamily: "monospace", position: "right", offset: 4 }}
              />
            ))}
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              strokeWidth={1.5}
              dot={false}
              activeDot={{ r: 3, fill: color }}
              name={dataKey}
            />
            {secondaryKey && secondaryColor && (
              <Line
                type="monotone"
                dataKey={secondaryKey}
                stroke={secondaryColor}
                strokeWidth={1.5}
                dot={false}
                activeDot={{ r: 3, fill: secondaryColor }}
                name={secondaryKey}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

interface TrendChartsSectionProps {
  chartData?: ChartData
}

export function TrendChartsSection({ chartData = CHART_DATA }: TrendChartsSectionProps) {
  const [timeRange, setTimeRange] = useState<TimeRange>("5m")

  // Merge pressure + temp data
  const pressureTempData = chartData.brakePressure.map((d, i) => ({
    time: d.time,
    "Давление тормоза": d.value,
    "Температура тяги": chartData.tractionTemp[i]?.value ?? 0,
  }))

  const electricalData = chartData.voltage.map((d, i) => ({
    time: d.time,
    "Напряжение": d.value,
    "Ток (×0.1)": (chartData.current[i]?.value ?? 0) * 0.1,
  }))

  return (
    <div className="bg-card border border-border rounded p-4 flex flex-col gap-3">
      {/* Header + time range */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">Анализ трендов</span>
        <div className="flex items-center gap-1">
          {(["1m", "5m", "15m"] as TimeRange[]).map((r) => (
            <button
              key={r}
              onClick={() => setTimeRange(r)}
              className={cn(
                "text-xs font-mono px-2 py-1 rounded transition-colors",
                timeRange === r
                  ? "bg-secondary text-foreground font-semibold"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
              )}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      {/* Charts grid */}
      <div className="grid grid-cols-2 gap-3">
        <MiniChart
          title="Индекс состояния"
          data={chartData.health}
          dataKey="value"
          color="var(--color-chart-1)"
          unit="балл"
          timeRange={timeRange}
          referenceLines={[{ value: 60, label: "Пред.", color: "var(--color-status-warning)" }]}
        />
        <MiniChart
          title="Скорость"
          data={chartData.speed}
          dataKey="value"
          color="var(--color-chart-2)"
          unit="км/ч"
          timeRange={timeRange}
          referenceLines={[{ value: 120, label: "Лимит", color: "var(--color-status-critical)" }]}
        />
        <div className="bg-card border border-border rounded p-3 flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">Давление / Температура</span>
          </div>
          <div className="h-36">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={pressureTempData.slice(-TIME_RANGE_POINTS[timeRange])}
                margin={{ top: 4, right: 4, bottom: 0, left: -16 }}
              >
                <CartesianGrid strokeDasharray="2 4" className="stroke-border" opacity={0.5} />
                <XAxis dataKey="time" tick={{ fontSize: 9, fontFamily: "monospace" }} className="fill-muted-foreground" tickLine={false} axisLine={false} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 9, fontFamily: "monospace" }} className="fill-muted-foreground" tickLine={false} axisLine={false} width={30} />
                <Tooltip content={<ChartTooltipContent />} />
                <Legend wrapperStyle={{ fontSize: "9px", fontFamily: "monospace" }} />
                <Line type="monotone" dataKey="Давление тормоза" stroke="var(--color-chart-3)" strokeWidth={1.5} dot={false} activeDot={{ r: 3 }} />
                <Line type="monotone" dataKey="Температура тяги" stroke="var(--color-chart-4)" strokeWidth={1.5} dot={false} activeDot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="bg-card border border-border rounded p-3 flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">Электрическая система</span>
          </div>
          <div className="h-36">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={electricalData.slice(-TIME_RANGE_POINTS[timeRange])}
                margin={{ top: 4, right: 4, bottom: 0, left: -16 }}
              >
                <CartesianGrid strokeDasharray="2 4" className="stroke-border" opacity={0.5} />
                <XAxis dataKey="time" tick={{ fontSize: 9, fontFamily: "monospace" }} className="fill-muted-foreground" tickLine={false} axisLine={false} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 9, fontFamily: "monospace" }} className="fill-muted-foreground" tickLine={false} axisLine={false} width={30} />
                <Tooltip content={<ChartTooltipContent />} />
                <Legend wrapperStyle={{ fontSize: "9px", fontFamily: "monospace" }} />
                <Line type="monotone" dataKey="Напряжение" stroke="var(--color-chart-1)" strokeWidth={1.5} dot={false} activeDot={{ r: 3 }} />
                <Line type="monotone" dataKey="Ток (×0.1)" stroke="var(--color-chart-5)" strokeWidth={1.5} dot={false} activeDot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  )
}
