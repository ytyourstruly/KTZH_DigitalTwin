"use client"

import { useState, useEffect } from "react"
import { useTheme } from "next-themes"
import { Train, Wifi, WifiOff, AlertTriangle, Sun, Moon, ChevronDown, Radio, LogOut } from "lucide-react"
import { cn } from "@/lib/utils"
import { LOCOMOTIVES, type LocomotiveData } from "@/lib/mock-data"

interface HeaderProps {
  selectedLoco: LocomotiveData
  onLocoChange: (loco: LocomotiveData) => void
  isLive: boolean
  onToggleLive: () => void
  username?: string
  onLogout?: () => void
  isLoggingOut?: boolean
}

function ConnectionBadge({ status }: { status: LocomotiveData["connectionStatus"] }) {
  const config = {
    online: { label: "Онлайн", icon: Wifi, className: "text-status-normal bg-status-normal-bg border-status-normal/30" },
    degraded: { label: "Нестабильная связь", icon: AlertTriangle, className: "text-status-warning bg-status-warning-bg border-status-warning/30" },
    offline: { label: "Офлайн", icon: WifiOff, className: "text-status-critical bg-status-critical-bg border-status-critical/30" },
  }
  const c = config[status]
  const Icon = c.icon
  return (
    <span className={cn("flex items-center gap-1 text-xs font-mono px-2 py-1 rounded border", c.className)}>
      <Icon className="w-3 h-3" />
      {c.label}
    </span>
  )
}

export function Header({
  selectedLoco,
  onLocoChange,
  isLive,
  onToggleLive,
  username,
  onLogout,
  isLoggingOut = false,
}: HeaderProps) {
  const { theme, setTheme } = useTheme()
  const [time, setTime] = useState("")
  const [showDropdown, setShowDropdown] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const update = () => {
      const now = new Date()
      // Kazakhstan time is UTC+6 (standard) or UTC+6 (no DST), display as UTC+6
      const kasTime = new Date(now.getTime() + (6 * 60 * 60 * 1000) - (now.getTimezoneOffset() * 60 * 1000))
      setTime(kasTime.toLocaleTimeString("en-GB", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
      }))
    }
    update()
    const interval = setInterval(update, 1000)
    return () => clearInterval(interval)
  }, [])

  return (
    <header className="flex items-center justify-between px-4 h-12 border-b border-border bg-card shrink-0">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-foreground">
          <Train className="w-4 h-4 text-accent" />
          <span className="font-mono text-sm font-semibold tracking-wide uppercase text-foreground">
            Цифровой двойник локомотива
          </span>
        </div>
        <div className="h-4 w-px bg-border hidden md:block" />
        <span className="text-xs text-muted-foreground font-mono hidden md:block">ДИСПЕТЧЕРСКАЯ КОНСОЛЬ КТЖ v2.4</span>
      </div>

      {/* Center controls */}
      <div className="flex items-center gap-2">
        {/* Locomotive selector */}
        <div className="relative">
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className="flex items-center gap-2 text-xs font-mono px-3 py-1.5 rounded border border-border bg-secondary hover:bg-muted transition-colors text-foreground"
          >
            <span className="text-muted-foreground">ТЛ:</span>
            <span className="font-semibold">{selectedLoco.id}</span>
            <ChevronDown className="w-3 h-3 text-muted-foreground" />
          </button>
          {showDropdown && (
            <div className="absolute top-full left-0 mt-1 w-64 bg-card border border-border rounded shadow-lg z-50">
              {LOCOMOTIVES.map((loco) => (
                <button
                  key={loco.id}
                  onClick={() => { onLocoChange(loco); setShowDropdown(false) }}
                  className={cn(
                    "w-full flex items-center justify-between px-3 py-2 text-xs font-mono hover:bg-muted transition-colors text-left",
                    loco.id === selectedLoco.id && "bg-muted"
                  )}
                >
                  <div>
                    <div className="font-semibold text-foreground">{loco.id}</div>
                    <div className="text-muted-foreground">{loco.model}</div>
                  </div>
                  <div className={cn(
                    "w-2 h-2 rounded-full",
                    loco.healthStatus === "normal" && "bg-status-normal",
                    loco.healthStatus === "warning" && "bg-status-warning",
                    loco.healthStatus === "critical" && "bg-status-critical",
                  )} />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Connection status */}
        <ConnectionBadge status={selectedLoco.connectionStatus} />

        {/* Time */}
        <div className="hidden lg:flex items-center gap-1.5 font-mono text-sm text-foreground bg-secondary px-3 py-1 rounded border border-border">
          <span className="text-muted-foreground text-xs">Астана</span>
          <span className="tabular-nums font-semibold">{time}</span>
        </div>
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-2">
        {/* Live / Replay toggle */}
        <button
          onClick={onToggleLive}
          className={cn(
            "flex items-center gap-1.5 text-xs font-mono px-3 py-1.5 rounded border transition-colors",
            isLive
              ? "bg-status-critical-bg border-status-critical/40 text-status-critical"
              : "bg-secondary border-border text-muted-foreground hover:text-foreground"
          )}
        >
          <Radio className={cn("w-3 h-3", isLive && "animate-blink-dot")} />
          {isLive ? "ОНЛАЙН" : "ПОВТОР"}
        </button>

        {/* Theme toggle */}
        {mounted && (
          <button
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="p-1.5 rounded border border-border bg-secondary hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
            aria-label="Toggle theme"
          >
            {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
        )}

        {username && <span className="hidden md:inline text-xs font-mono text-muted-foreground">{username}</span>}

        {onLogout && (
          <button
            onClick={onLogout}
            disabled={isLoggingOut}
            className="flex items-center gap-1.5 text-xs font-mono px-3 py-1.5 rounded border border-border bg-secondary hover:bg-muted transition-colors text-foreground disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <LogOut className="w-3 h-3" />
            {isLoggingOut ? "..." : "LOGOUT"}
          </button>
        )}
      </div>
    </header>
  )
}
