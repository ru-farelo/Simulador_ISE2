import { useState } from 'react'
import { ApiError } from '../../api/client'
import { reinforcementApi } from '../../api/reinforcement'
import type { DueReinforcementItem, ReinforcementReviewResult } from '../../types/reinforcement'
import { ErrorState } from '../ui/ErrorState'
import { LoadingState } from '../ui/LoadingState'
import { Panel } from '../ui/Panel'

export function ReinforcementExercise({ item, onDone }: { item: DueReinforcementItem; onDone: () => void }) {
  const [answer, setAnswer] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ReinforcementReviewResult | null>(null)

  const submit = () => {
    setSubmitting(true)
    setError(null)
    reinforcementApi
      .review(item.id, { answer })
      .then(setResult)
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Error desconocido'))
      .finally(() => setSubmitting(false))
  }

  return (
    <Panel title={`Refuerzo · ${item.error_category}`}>
      <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">
        {item.is_real ? 'De una de tus sesiones reales' : 'Variante generada del mismo patrón'}
      </p>
      <p className="mt-2 text-sm text-ink-soft">
        Esta frase contiene uno de tus errores recurrentes. Encuéntralo y corrígelo tú mismo.
      </p>
      <p className="mt-3 border border-line bg-paper px-3 py-2 text-ink">{item.example_sentence}</p>

      {!result && (
        <div className="mt-4 grid gap-2">
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            rows={2}
            placeholder="Reescribe la frase corrigiendo el error…"
            autoFocus
            className="w-full resize-y border border-line bg-paper px-3 py-2 text-sm text-ink focus:border-ink"
          />
          <div className="flex justify-end">
            <button
              type="button"
              disabled={submitting || answer.trim().length === 0}
              onClick={submit}
              className="border border-seal bg-seal px-4 py-1.5 font-mono text-xs uppercase tracking-wide text-paper-raised disabled:cursor-not-allowed disabled:opacity-40"
            >
              {submitting ? 'Corrigiendo…' : 'Comprobar'}
            </button>
          </div>
        </div>
      )}

      {submitting && <LoadingState label="Corrigiendo…" />}
      {error && <ErrorState message={error} onRetry={submit} />}

      {result && (
        <div className={`mt-4 border p-4 ${result.correct ? 'border-distinction bg-distinction/5' : 'border-seal bg-seal/5'}`}>
          <p className={`font-mono text-xs uppercase tracking-wide ${result.correct ? 'text-distinction' : 'text-seal'}`}>
            {result.correct ? '✓ Correcto' : '✗ Incorrecto'}
          </p>
          <p className="mt-2 text-sm text-ink">{result.feedback}</p>
          <p className="mt-2 text-sm text-ink-soft">
            <span className="font-mono text-xs uppercase tracking-wide text-ink-faint">Corrección de referencia: </span>
            {result.corrected_sentence}
          </p>
          <p className="mt-3 font-mono text-xs text-ink-faint">
            Próxima repetición en {result.interval_days} día{result.interval_days === 1 ? '' : 's'} · racha:{' '}
            {result.repetitions}
          </p>
          <button
            type="button"
            onClick={onDone}
            className="mt-4 border border-ink px-4 py-1.5 font-mono text-xs uppercase tracking-wide hover:bg-ink hover:text-paper-raised"
          >
            Siguiente
          </button>
        </div>
      )}
    </Panel>
  )
}
