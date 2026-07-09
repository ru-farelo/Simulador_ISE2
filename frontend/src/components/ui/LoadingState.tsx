interface LoadingStateProps {
  label?: string
}

export function LoadingState({ label = 'Cargando…' }: LoadingStateProps) {
  return (
    <div role="status" className="flex items-center gap-3 py-12 text-ink-soft">
      <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-seal" aria-hidden="true" />
      <span className="font-mono text-sm">{label}</span>
    </div>
  )
}
