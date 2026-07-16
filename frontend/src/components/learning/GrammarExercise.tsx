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

  const [phase2Answer, setPhase2Answer] = useState('')
  const [phase2Submitting, setPhase2Submitting] = useState(false)
  const [phase2Error, setPhase2Error] = useState<string | null>(null)
  const [phase2Result, setPhase2Result] = useState<LearningReviewResult | null>(null)

  const submit = () => {
    setSubmitting(true)
    setError(null)
    learningApi
      .review(item.item_id, { answer, prompt: item.prompt_sentence })
      .then(setResult)
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Error desconocido'))
      .finally(() => setSubmitting(false))
  }

  const submitPhase2 = () => {
    if (!result?.phase2) return
    setPhase2Submitting(true)
    setPhase2Error(null)
    learningApi
      .review(item.item_id, { answer: phase2Answer, phase: '2', phase2_topic: result.phase2.topic })
      .then(setPhase2Result)
      .catch((err: unknown) => setPhase2Error(err instanceof ApiError ? err.message : 'Error desconocido'))
      .finally(() => setPhase2Submitting(false))
  }

  const phase2Pending = Boolean(result?.phase2) && !phase2Result

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

      {result && (
        <div className="mt-4">
          <ReviewFeedback result={result} onNext={onDone} hideNext={phase2Pending} label={result.phase2 ? 'Fase 1' : undefined} />
        </div>
      )}

      {phase2Pending && result?.phase2 && (
        <div className="mt-4 border border-seal/40 bg-seal/5 p-4">
          <p className="font-mono text-xs uppercase tracking-wide text-seal">Fase 2 · Producción libre</p>
          <p className="mt-2 text-sm text-ink-soft">{result.phase2.instructions}</p>
          <div className="mt-3 grid gap-2">
            <textarea
              value={phase2Answer}
              onChange={(e) => setPhase2Answer(e.target.value)}
              rows={3}
              placeholder="Escribe desde cero…"
              autoFocus
              className="w-full resize-y border border-line bg-paper px-3 py-2 text-sm text-ink focus:border-ink"
            />
            <div className="flex justify-end">
              <button
                type="button"
                disabled={phase2Submitting || phase2Answer.trim().length === 0}
                onClick={submitPhase2}
                className="border border-seal bg-seal px-4 py-1.5 font-mono text-xs uppercase tracking-wide text-paper-raised disabled:cursor-not-allowed disabled:opacity-40"
              >
                {phase2Submitting ? 'Corrigiendo…' : 'Comprobar'}
              </button>
            </div>
          </div>
          {phase2Submitting && <LoadingState label="Corrigiendo…" />}
          {phase2Error && <ErrorState message={phase2Error} onRetry={submitPhase2} />}
        </div>
      )}

      {phase2Result && (
        <div className="mt-4">
          <ReviewFeedback result={phase2Result} onNext={onDone} label="Fase 2" />
        </div>
      )}
    </Panel>
  )
}
