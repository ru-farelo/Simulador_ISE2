interface ErrorStateProps {
  message: string
  onRetry?: () => void
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div role="alert" className="border border-fail bg-fail/5 px-5 py-4">
      <p className="font-semibold text-fail">No se ha podido completar la solicitud</p>
      <p className="mt-1 text-sm text-ink-soft">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 border border-fail px-3 py-1 font-mono text-sm uppercase tracking-wide text-fail transition-colors hover:bg-fail hover:text-paper-raised"
        >
          Reintentar
        </button>
      )}
    </div>
  )
}
