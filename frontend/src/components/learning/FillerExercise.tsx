import { useState } from 'react'
import { learningApi } from '../../api/learning'
import { ApiError } from '../../api/client'
import { useCountdown } from '../../hooks/useCountdown'
import { ErrorState } from '../ui/ErrorState'
import { LoadingState } from '../ui/LoadingState'
import { Panel } from '../ui/Panel'
import { VoiceOrTextInput } from '../speaking/VoiceOrTextInput'
import type { DueFillerItem, LearningReviewResult } from '../../types/learning'
import { ReviewFeedback } from './ReviewFeedback'

export function FillerExercise({ item, onDone }: { item: DueFillerItem; onDone: () => void }) {
  const [phase, setPhase] = useState<'ready' | 'answering'>('ready')
  const [answer, setAnswer] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<LearningReviewResult | null>(null)
  const countdown = useCountdown(item.time_limit_seconds)

  const label = item.type === 'filler' ? 'Filler' : 'Conector'

  const begin = () => {
    setPhase('answering')
    countdown.reset(item.time_limit_seconds)
    countdown.start()
  }

  const submit = () => {
    countdown.pause()
    setSubmitting(true)
    setError(null)
    learningApi
      .review(item.item_id, { answer, prompt: item.opener })
      .then(setResult)
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Error desconocido'))
      .finally(() => setSubmitting(false))
  }

  return (
    <Panel title={`${label} · ${item.category}`}>
      <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">Objetivo</p>
      <p className="mt-1 text-lg text-seal">{item.target}</p>
      <p className="mt-1 text-sm text-ink-faint">{item.hint}</p>

      <p className="mt-4 border border-line bg-paper px-3 py-2 text-ink">{item.opener}</p>

      {phase === 'ready' && !result && (
        <button
          type="button"
          onClick={begin}
          className="mt-4 border border-ink px-4 py-2 font-mono text-sm uppercase tracking-wide hover:bg-ink hover:text-paper-raised"
        >
          Empezar ({item.time_limit_seconds}s)
        </button>
      )}

      {phase === 'answering' && !result && (
        <div className="mt-4 grid gap-2">
          <p
            className={`font-mono text-sm ${countdown.isExpired ? 'text-seal' : 'text-ink-soft'}`}
            aria-live="polite"
          >
            {countdown.isExpired ? '¡Tiempo! Termina tu frase y envíala.' : `Tiempo: ${countdown.formatted}`}
          </p>
          <VoiceOrTextInput
            value={answer}
            onChange={setAnswer}
            onSend={submit}
            disabled={submitting}
            placeholder="Continúa el argumento usando el objetivo…"
            sendLabel="Enviar"
          />
        </div>
      )}

      {submitting && <LoadingState label="Corrigiendo…" />}
      {error && <ErrorState message={error} onRetry={submit} />}
      {result && <div className="mt-4"><ReviewFeedback result={result} onNext={onDone} /></div>}
    </Panel>
  )
}
