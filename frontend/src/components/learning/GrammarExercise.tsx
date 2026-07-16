import { useState } from 'react'
import { learningApi } from '../../api/learning'
import { ApiError } from '../../api/client'
import { ErrorState } from '../ui/ErrorState'
import { LoadingState } from '../ui/LoadingState'
import { Panel } from '../ui/Panel'
import type { DueGrammarItem, LearningReviewResult } from '../../types/learning'
import { ReviewFeedback } from './ReviewFeedback'

export function GrammarExercise({ item, onDone }: { item: DueGrammarItem; onDone: () => void }) {
  const [answer, setAnswer] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<LearningReviewResult | null>(null)

  const submit = () => {
    setSubmitting(true)
    setError(null)
    learningApi
      .review(item.item_id, { answer, prompt: item.prompt_sentence })
      .then(setResult)
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Error desconocido'))
      .finally(() => setSubmitting(false))
  }

  return (
    <Panel title={`Gramática · ${item.structure}`}>
      <p className="text-sm text-ink-soft">{item.instructions}</p>
      <p className="mt-3 border border-line bg-paper px-3 py-2 text-ink">{item.prompt_sentence}</p>
      <p className="mt-2 text-sm text-ink-faint">Regla: {item.hint}</p>

      {!result && (
        <div className="mt-4 grid gap-2">
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            rows={3}
            placeholder="Reescribe la frase…"
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
      {result && <div className="mt-4"><ReviewFeedback result={result} onNext={onDone} /></div>}
    </Panel>
  )
}
