"use client"

import * as React from "react"
import { AlertTriangle, CheckCircle2, Info, X } from "lucide-react"

import { cn } from "@/lib/utils"

type ToastTipo = "success" | "error" | "info"

interface ToastItem {
  id: number
  tipo: ToastTipo
  titulo: string
  descripcion?: string
}

interface ToastContextValue {
  toast: (t: Omit<ToastItem, "id">) => void
}

const ToastContext = React.createContext<ToastContextValue | null>(null)

export function useToast() {
  const ctx = React.useContext(ToastContext)
  if (!ctx) throw new Error("useToast debe usarse dentro de <ToastProvider>")
  return ctx
}

const ICONOS: Record<ToastTipo, React.ElementType> = {
  success: CheckCircle2,
  error: AlertTriangle,
  info: Info,
}

const ESTILOS: Record<ToastTipo, string> = {
  success: "border-emerald-200 [&>svg]:text-emerald-600",
  error: "border-red-200 [&>svg]:text-red-600",
  info: "border-futuro-accent/30 [&>svg]:text-futuro-accent",
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = React.useState<ToastItem[]>([])
  const contador = React.useRef(0)

  const cerrar = React.useCallback((id: number) => {
    setItems((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const toast = React.useCallback(
    (t: Omit<ToastItem, "id">) => {
      const id = ++contador.current
      setItems((prev) => [...prev.slice(-2), { ...t, id }])
      window.setTimeout(() => cerrar(id), 4500)
    },
    [cerrar]
  )

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      {/* Región viva: los lectores de pantalla anuncian cada toast */}
      <div
        aria-live="polite"
        role="status"
        className="pointer-events-none fixed bottom-4 right-4 z-[60] flex w-[min(360px,calc(100vw-2rem))] flex-col gap-2"
      >
        {items.map((t) => {
          const Icono = ICONOS[t.tipo]
          return (
            <div
              key={t.id}
              className={cn(
                "pointer-events-auto grid animate-toast-in grid-cols-[auto_1fr_auto] items-start gap-2.5 rounded-xl border bg-card p-3 shadow-lg",
                ESTILOS[t.tipo]
              )}
            >
              <Icono className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
              <div className="min-w-0">
                <p className="text-sm font-semibold text-foreground">{t.titulo}</p>
                {t.descripcion && (
                  <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">
                    {t.descripcion}
                  </p>
                )}
              </div>
              <button
                type="button"
                onClick={() => cerrar(t.id)}
                aria-label="Cerrar notificación"
                className="rounded-md p-1 text-muted-foreground transition-colors duration-150 hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <X className="size-3.5" aria-hidden="true" />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}
