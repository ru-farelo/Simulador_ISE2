import type { LearningReviewResult } from '../../types/learning'

export function ReviewFeedback({
  result,
  onNext,
  hideNext = false,
  label,
}: {
  result: LearningReviewResult
  onNext: () => void
  hideNext?: boolean
  label?: string
}) {
  return (
    <div className={`border p-4 ${result.correct ? 'border-distinction bg-distinction/5' : 'border-seal bg-seal/5'}`}>
      <p className={`font-mono text-xs uppercase tracking-wide ${result.correct ? 'text-distinction' : 'text-seal'}`}>
        {label ? `${label} · ` : ''}
        {result.correct ? '✓ Correcto' : '✗ Incorrecto'}
      </p>
      <p className="mt-2 text-sm text-ink">{result.feedback}</p>
      {result.corrected_answer && (
        <p className="mt-2 text-sm text-ink-soft">
          <span className="font-mono text-xs uppercase tracking-wide text-ink-faint">Respuesta modelo: </span>
          {result.corrected_answer}
        </p>
      )}
      <p className="mt-3 font-mono text-xs text-ink-faint">
        Próxima repetición en {result.interval_days} día{result.interval_days === 1 ? '' : 's'} · racha:{' '}
        {result.repetitions}
      </p>
      {!hideNext && (
        <button
          type="button"
          onClick={onNext}
          className="mt-4 border border-ink px-4 py-1.5 font-mono text-xs uppercase tracking-wide hover:bg-ink hover:text-paper-raised"
        >
          Siguiente
        </button>
      )}
    </div>
  )
}
