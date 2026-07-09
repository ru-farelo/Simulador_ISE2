import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { dashboardApi } from '../../api/dashboard'
import { SealBadge } from './SealBadge'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', end: true, comingSoon: false },
  { to: '/reading', label: 'Reading', end: false, comingSoon: false },
  { to: '/writing', label: 'Writing', end: false, comingSoon: false },
  { to: '/speaking', label: 'Speaking & Listening', end: false, comingSoon: false },
]

export function AppShell() {
  const [streakDays, setStreakDays] = useState(0)

  useEffect(() => {
    dashboardApi
      .getSummary()
      .then((summary) => setStreakDays(summary.streak_days))
      .catch(() => setStreakDays(0))
  }, [])

  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col px-6 py-8">
      <header className="flex items-start justify-between gap-6 border-b-2 border-ink pb-6">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.3em] text-ink-soft">
            Trinity College London · ISE II
          </p>
          <h1 className="mt-1 font-display text-3xl font-semibold text-ink">Dossier de examen</h1>
        </div>
        <SealBadge streakDays={streakDays} />
      </header>

      <nav className="mt-6 flex flex-wrap gap-1 border-b border-line" aria-label="Secciones de práctica">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            aria-disabled={item.comingSoon}
            onClick={(e) => item.comingSoon && e.preventDefault()}
            className={({ isActive }) =>
              [
                'px-4 py-2 font-mono text-sm uppercase tracking-wide transition-colors border-b-2',
                isActive ? 'border-seal text-seal' : 'border-transparent text-ink-soft hover:text-ink',
                item.comingSoon ? 'cursor-default opacity-40 hover:text-ink-soft' : '',
              ].join(' ')
            }
          >
            {item.label}
            {item.comingSoon && <span className="ml-1.5 text-[0.65rem] normal-case">(pronto)</span>}
          </NavLink>
        ))}
      </nav>

      <main className="mt-8 flex-1">
        <Outlet />
      </main>

      <footer className="mt-12 border-t border-line pt-4 font-mono text-xs text-ink-faint">
        Simulador Trinity ISE II — práctica personal
      </footer>
    </div>
  )
}
