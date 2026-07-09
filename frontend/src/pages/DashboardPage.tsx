import { useEffect, useState } from 'react'
import { dashboardApi } from '../api/dashboard'
import { ApiError } from '../api/client'
import { ErrorState } from '../components/ui/ErrorState'
import { LoadingState } from '../components/ui/LoadingState'
import { Panel } from '../components/ui/Panel'
import type { DashboardSummary } from '../types/dashboard'

const SKILL_LABELS: Record<string, string> = {
  reading: 'Reading',
  writing: 'Writing',
  speaking: 'Speaking & Listening',
}

const DAY_LABELS = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb']

export function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    setError(null)
    dashboardApi
      .getSummary()
      .then(setSummary)
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Error desconocido'))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  if (loading) return <LoadingState label="Cargando panel de control…" />
  if (error) return <ErrorState message={error} onRetry={load} />
  if (!summary) return null

  return (
    <div className="grid gap-6">
      <Panel title="Semana en curso">
        <div className="grid grid-cols-7 gap-2">
          {summary.weekly_activity.map((day) => {
            const date = new Date(`${day.date}T00:00:00`)
            const isToday = date.toDateString() === new Date().toDateString()
            return (
              <div
                key={day.date}
                className={`flex flex-col items-center gap-2 border p-3 ${isToday ? 'border-seal' : 'border-line'}`}
              >
                <span className="font-mono text-xs text-ink-soft">{DAY_LABELS[date.getDay()]}</span>
                <span className="font-display text-lg">{date.getDate()}</span>
                <div className="flex min-h-[0.4rem] flex-wrap justify-center gap-1">
                  {day.skills_practiced.map((skill) => (
                    <span
                      key={skill}
                      title={SKILL_LABELS[skill] ?? skill}
                      className="h-1.5 w-1.5 rounded-full bg-seal"
                    />
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </Panel>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Object.entries(summary.skill_progress).map(([skill, progress]) => (
          <Panel key={skill} title={SKILL_LABELS[skill] ?? skill}>
            <p className="font-display text-3xl text-ink">
              {progress.avg_score !== null ? Math.round(progress.avg_score) : '—'}
            </p>
            <p className="mt-1 font-mono text-xs text-ink-soft">
              {progress.sessions} {progress.sessions === 1 ? 'sesión' : 'sesiones'}
            </p>
          </Panel>
        ))}
      </div>

      <Panel title="Errores recurrentes">
        {summary.top_error_categories.length === 0 ? (
          <p className="text-ink-soft">
            Todavía no hay suficientes datos. Completa una sesión para empezar a ver patrones.
          </p>
        ) : (
          <ul className="divide-y divide-line">
            {summary.top_error_categories.map((item) => (
              <li key={item.category} className="flex items-center justify-between py-2">
                <span>{item.category}</span>
                <span className="font-mono text-sm text-ink-soft">×{item.count}</span>
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  )
}
