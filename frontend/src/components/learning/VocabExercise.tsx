import { useState } from 'react'
import { learningApi } from '../../api/learning'
import { ApiError } from '../../api/client'
import { ErrorState } from '../ui/ErrorState'
import { LoadingState } from '../ui/LoadingState'
import { Panel } from '../ui/Panel'
import type { DueVocabItem, LearningReviewResult } from '../../types/learning'
import { ReviewFeedback } from './ReviewFeedback'

export function VocabExercise({ item, onDone }: { item: DueVocabItem; onDone: () => void }) {
  if (item.phase === 'flashcard') return <VocabFlashcard item={item} onDone={onDone} />
  return <VocabProduction item={item} onDone={onDone} />
}

type CardSide = 'front' | 'back'

function VocabFlashcard({ item, onDone }: { item: DueVocabItem; onDone: () => void }) {
  const [side, setSide] = useState<CardSide>('front')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<LearningReviewResult | null>(null)

  const flip = () => {
    if (side === 'front') setSide('back')
  }

  const rate = (knew: boolean) => {
    setSubmitting(true)
    setError(null)
    learningApi
      .review(item.item_id, { self_rating: knew ? 'known' : 'unknown' })
      .then(setResult)
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Error desconocido'))
      .finally(() => setSubmitting(false))
  }

  return (
    <Panel title={`Vocabulario · ${item.category === 'general' ? 'General (NGSL)' : item.category}`}>
      {!result && (
        <div
          role="button"
          tabIndex={0}
          onClick={flip}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && flip()}
          aria-label={side === 'front' ? 'Mostrar definición y ejemplo' : undefined}
          className={`grid min-h-[10rem] place-items-center border border-line bg-paper px-6 py-10 text-center ${
            side === 'front' ? 'cursor-pointer hover:border-ink' : ''
          }`}
        >
          {side === 'front' && <p className="font-display text-3xl text-ink">{item.term}</p>}

          {side === 'back' && (
            <div className="grid w-full gap-3 text-center">
              <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">{item.term}</p>
              <p className="font-display text-3xl font-semibold text-seal">{item.translation_es}</p>
              <p className="text-left italic text-ink-soft">{item.example}</p>
            </div>
          )}
        </div>
      )}

      {side === 'front' && !result && (
        <p className="mt-2 text-center font-mono text-xs uppercase tracking-wide text-ink-faint">
          Toca la tarjeta para ver la traducción
        </p>
      )}

      {side === 'back' && !result && (
        <div className="mt-4 flex justify-end gap-2">
          <button
            type="button"
            disabled={submitting}
            onClick={() => rate(false)}
            className="border border-seal px-4 py-1.5 font-mono text-xs uppercase tracking-wide text-seal hover:bg-seal hover:text-paper-raised disabled:cursor-not-allowed disabled:opacity-40"
          >
            No la sabía
          </button>
          <button
            type="button"
            disabled={submitting}
            onClick={() => rate(true)}
            className="border border-distinction px-4 py-1.5 font-mono text-xs uppercase tracking-wide text-distinction hover:bg-distinction hover:text-paper-raised disabled:cursor-not-allowed disabled:opacity-40"
          >
            La sabía
          </button>
        </div>
      )}

      {submitting && <LoadingState label="Guardando…" />}
      {error && <ErrorState message={error} onRetry={() => rate(true)} />}
      {result && <div className="mt-4"><ReviewFeedback result={result} onNext={onDone} /></div>}
    </Panel>
  )
}

function VocabProduction({ item, onDone }: { item: DueVocabItem; onDone: () => void }) {
  const [answer, setAnswer] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<LearningReviewResult | null>(null)

  const submit = () => {
    setSubmitting(true)
    setError(null)
    learningApi
      .review(item.item_id, { answer })
      .then(setResult)
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Error desconocido'))
      .finally(() => setSubmitting(false))
  }

  return (
    <Panel title={`Vocabulario · ${item.category === 'general' ? 'General (NGSL)' : item.category}`}>
      <p className="text-lg leading-relaxed text-ink">{item.sentence}</p>
      <p className="mt-2 text-sm text-ink-faint">Pista: {item.hint}</p>

      {!result && (
        <div className="mt-4 grid gap-2">
          <input
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && answer.trim() && submit()}
            placeholder="Escribe la palabra que falta…"
            autoFocus
            className="w-full border border-line bg-paper px-3 py-2 text-sm text-ink focus:border-ink"
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
