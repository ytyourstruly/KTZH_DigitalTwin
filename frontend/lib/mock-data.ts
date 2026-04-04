export type AlertSeverity = "warning" | "critical" | "info" | "resolved"

export interface Alert {
  id: string
  timestamp: string
  severity: AlertSeverity
  source: string
  message: string
}

export interface TelemetryPoint {
  time: string
  value: number
}

export interface HealthFactor {
  name: string
  impact: number
  trend: "up" | "down" | "stable"
}

export interface RouteStation {
  id: string
  name: string
  km: number
  status: "passed" | "current" | "next" | "upcoming" | "restricted"
  restriction?: number
}

export interface LocomotiveData {
  id: string
  name: string
  model: string
  healthScore: number
  healthStatus: "normal" | "warning" | "critical"
  speed: number
  speedLimit: number
  fuelLevel: number
  fuelRate: number
  brakePressure: number
  brakePressureNormal: [number, number]
  tractionTemp: number
  tractionTempLimit: number
  voltage: number
  currentAmps: number
  connectionStatus: "online" | "degraded" | "offline"
  routeProgress: number
  distanceCovered: number
  totalDistance: number
  nextStation: string
  nextStationKm: number
}

// Locomotives
export const LOCOMOTIVES: LocomotiveData[] = [
  {
    id: "ТЛ-4471",
    name: 'ТЛ-4471 "Карагвнда"',
    model: "Д65 Дизель",
    healthScore: 73,
    healthStatus: "warning",
    speed: 112,
    speedLimit: 120,
    fuelLevel: 61,
    fuelRate: 142,
    brakePressure: 4.1,
    brakePressureNormal: [4.5, 6.5],
    tractionTemp: 88,
    tractionTempLimit: 95,
    voltage: 24.2,
    currentAmps: 312,
    connectionStatus: "online",
    routeProgress: 29,
    distanceCovered: 90,
    totalDistance: 315,
    nextStation: "Акколь",
    nextStationKm: 20,
  },
  {
    id: "ТЛ-8810",
    name: 'ТЛ-8810 "Алмас"',
    model: "ЭП20 Электрический",
    healthScore: 91,
    healthStatus: "normal",
    speed: 0,
    speedLimit: 160,
    fuelLevel: 88,
    fuelRate: 0,
    brakePressure: 5.8,
    brakePressureNormal: [4.5, 6.5],
    tractionTemp: 42,
    tractionTempLimit: 100,
    voltage: 25.0,
    currentAmps: 18,
    connectionStatus: "online",
    routeProgress: 100,
    distanceCovered: 315,
    totalDistance: 315,
    nextStation: "Кокшетау-1",
    nextStationKm: 0,
  },
  {
    id: "ТЛ-3302",
    name: 'ТЛ-3302 "Спутник"',
    model: "Д49 Дизель",
    healthScore: 42,
    healthStatus: "critical",
    speed: 68,
    speedLimit: 100,
    fuelLevel: 23,
    fuelRate: 188,
    brakePressure: 3.2,
    brakePressureNormal: [4.5, 6.5],
    tractionTemp: 101,
    tractionTempLimit: 95,
    voltage: 22.1,
    currentAmps: 481,
    connectionStatus: "degraded",
    routeProgress: 13,
    distanceCovered: 40,
    totalDistance: 315,
    nextStation: "Шортанды",
    nextStationKm: 38,
  },
]

export const HEALTH_FACTORS: HealthFactor[] = [
  { name: "Температура тягового мотора", impact: -12, trend: "up" },
  { name: "Отклонение давления тормоза", impact: -8, trend: "up" },
  { name: "Колебание напряжения", impact: -4, trend: "stable" },
  { name: "Снижение КПД топлива", impact: -2, trend: "stable" },
  { name: "События пробуксовки колёс", impact: -1, trend: "down" },
]

export const ALERTS: Alert[] = [
  {
    id: "a1",
    timestamp: "14:32:11",
    severity: "critical",
    source: "Тормозная система",
    message: "Давление тормоза ниже безопасного уровня — текущее: 4.1 бар (мин: 4.5 бар)",
  },
  {
    id: "a2",
    timestamp: "14:29:45",
    severity: "warning",
    source: "Тяговый мотор",
    message: "Температура тяги растёт аномально — 88°C приближается к лимиту 95°C",
  },
  {
    id: "a3",
    timestamp: "14:25:03",
    severity: "warning",
    source: "Электрическая система",
    message: "Обнаружено колебание напряжения — отклонение ±0.8V за последние 5 минут",
  },
  {
    id: "a4",
    timestamp: "14:18:30",
    severity: "info",
    source: "Топливная система",
    message: "Расход топлива повышен — 142 л/ч против ожидаемых 128 л/ч",
  },
  {
    id: "a5",
    timestamp: "14:10:55",
    severity: "resolved",
    source: "Датчики колёс",
    message: "Событие пробуксовки колеса устранено — тяговый контроль восстановлен",
  },
  {
    id: "a6",
    timestamp: "13:58:12",
    severity: "resolved",
    source: "Система климата",
    message: "Температура кабины нормализована после периода повышения на 4 минуты",
  },
]

export const ROUTE_STATIONS: RouteStation[] = [
  { id: "s1", name: "Астана-Нурлы Жол", km: 0, status: "passed" },
  { id: "s2", name: "Шортанды", km: 78, status: "passed" },
  { id: "s3", name: "Акколь", km: 110, status: "next" },
  { id: "s4", name: "Макинка", km: 185, status: "upcoming", restriction: 60 },
  { id: "s5", name: "Курорт-Боровое", km: 245, status: "upcoming" },
  { id: "s6", name: "Кокшетау-1", km: 315, status: "upcoming" },
]

// Seeded pseudo-random number generator for deterministic chart data
function seededRandom(seed: number): () => number {
  return () => {
    seed = (seed * 9301 + 49297) % 233280
    return seed / 233280
  }
}

// Generate chart history (60 points = 15 min at 15s intervals)
// Uses deterministic seeded random to avoid SSR/client hydration mismatch
function generateHistory(
  base: number,
  variance: number,
  drift: number = 0,
  points: number = 60,
  seed: number = 12345
): TelemetryPoint[] {
  const random = seededRandom(seed)
  // Use fixed base time to avoid Date.now() mismatch
  const baseTime = new Date("2026-04-04T14:30:00Z")
  return Array.from({ length: points }, (_, i) => {
    const t = new Date(baseTime.getTime() - (points - 1 - i) * 15000)
    const noiseAmp = variance * 0.4
    const noise = (random() - 0.5) * noiseAmp
    const driftVal = drift * (i / points)
    const val = Math.max(0, base + driftVal + noise + Math.sin(i * 0.3) * variance * 0.3)
    return {
      time: t.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
      value: Math.round(val * 10) / 10,
    }
  })
}

export const CHART_DATA = {
  health: generateHistory(73, 5, -3, 60, 11111),
  speed: generateHistory(108, 12, 4, 60, 22222),
  brakePressure: generateHistory(4.4, 0.4, -0.3, 60, 33333),
  tractionTemp: generateHistory(82, 5, 6, 60, 44444),
  voltage: generateHistory(24.2, 0.6, 0, 60, 55555),
  current: generateHistory(305, 30, 7, 60, 66666),
}

export const RECOMMENDATIONS = [
  {
    id: "r1",
    priority: "high" as const,
    action: "Снизить нагрузку тяги на 15%",
    reason: "Температура мотора приближается к лимиту. Снижение нагрузки уменьшит тепловыделение.",
    eta: "Немедленно",
  },
  {
    id: "r2",
    priority: "high" as const,
    action: "Проверить тормозную систему на Балхаше",
    reason: "Дав��ение тормоза постоянно на 9% ниже нижнего лимита. Требуется проверка вручную.",
    eta: "22 км / ~12 мин",
  },
  {
    id: "r3",
    priority: "medium" as const,
    action: "Мониторить температуру 3 минуты",
    reason: "Если температура превысит 92°C перед Балхашом, применить протокол аварийного охлаждения.",
    eta: "Текущая операция",
  },
  {
    id: "r4",
    priority: "low" as const,
    action: "Записать событие напряжения для техническoго обслуживания",
    reason: "Прерывистые скачки напряжения указывают на возможный износ щёток генератора.",
    eta: "На следующем депо",
  },
]
