import { useEffect, useMemo, useState } from 'react'
import { ApiError } from '../api/client'
import { writingApi } from '../api/writing'
import { ErrorState } from '../components/ui/ErrorState'
import { LoadingState } from '../components/ui/LoadingState'
import { Panel } from '../components/ui/Panel'
import { ScoreBand } from '../components/ui/ScoreBand'
import { useCountdown } from '../hooks/useCountdown'
import type { Genre, PromptSource, WritingCorrectionResult, WritingPrompt } from '../types/writing'

const DURATION_SECONDS = 40 * 60

const GENRE_LABELS: Record<Genre, string> = {
  essay: 'Essay',
  article: 'Article',
  letter: 'Letter',
  review: 'Review',
}

const GENRE_HINTS: Record<Genre, string> = {
  essay: 'Formal register — no contractions, clear intro / development / conclusion.',
  article: 'Semi-formal, engaging register — you can address the reader directly.',
  letter: 'Formal register — no contractions, proper greeting and closing.',
  review: 'Semi-formal, descriptive and evaluative — can be more personal in tone.',
}

type Phase = 'loading' | 'ready' | 'submitting' | 'result'

function countWords(text: string): number {
  return text.split(/\s+/).filter(Boolean).length
}

export function WritingPage() {
  const [prompt, setPrompt] = useState<WritingPrompt | null>(null)
  const [text, setText] = useState('')
  const [phase, setPhase] = useState<Phase>('loading')
  const [loadError, setLoadError] = useState<string | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [result, setResult] = useState<WritingCorrectionResult | null>(null)
  const timer = useCountdown(DURATION_SECONDS)

  const wordCount = useMemo(() => countWords(text), [text])

  const loadPrompt = (mode: PromptSource) => {
    setPhase('loading')
    setLoadError(null)
    setResult(null)
    setText('')
    timer.reset(DURATION_SECONDS)
    writingApi
      .getPrompt(mode)
      .then((p) => {
        setPrompt(p)
        setPhase('ready')
      })
      .catch((err: unknown) => setLoadError(err instanceof ApiError ? err.message : 'Error desconocido'))
  }

  useEffect(() => loadPrompt('fixed'), [])

  const handleSubmit = () => {
    if (!prompt) return
    setPhase('submitting')
    setSubmitError(null)
    timer.pause()
    writingApi
      .submit({
        prompt_id: prompt.id,
        genre: prompt.genre,
        title: prompt.title,
        instructions: prompt.instructions,
        text,
        duration_seconds: DURATION_SECONDS - timer.secondsLeft,
      })
      .then((r) => {
        setResult(r)
        setPhase('result')
      })
      .catch((err: unknown) => {
        setSubmitError(err instanceof ApiError ? err.message : 'Error desconocido')
        setPhase('ready')
      })
  }

  if (phase === 'loading' && !prompt) return <LoadingState label="Preparando la propuesta…" />
  if (loadError) return <ErrorState message={loadError} onRetry={() => loadPrompt('fixed')} />
  if (!prompt) return null

  const inRange = wordCount >= prompt.word_min && wordCount <= prompt.word_max
  const countColor = wordCount === 0 ? 'text-ink-faint' : inRange ? 'text-distinction' : 'text-seal'

  return (
    <div className="grid gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border border-line bg-paper-raised px-5 py-4">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-ink-soft">
            Writing · Task 4 · {GENRE_LABELS[prompt.genre]}
          </p>
          <h2 className="mt-1 font-display text-xl font-semibold">{prompt.title}</h2>
        </div>
        <div className="flex items-center gap-4">
          <div
            className={`font-mono text-2xl tabular-nums ${timer.secondsLeft <= 300 && timer.isRunning ? 'text-seal' : 'text-ink'}`}
            aria-live="polite"
          >
            {timer.formatted}
          </div>
          {!timer.isRunning && timer.secondsLeft === DURATION_SECONDS && phase === 'ready' && (
            <button
              type="button"
              onClick={timer.start}
              className="border border-ink px-3 py-1.5 font-mono text-sm uppercase tracking-wide hover:bg-ink hover:text-paper-raised"
            >
              Comenzar
            </button>
          )}
        </div>
      </div>

      {phase !== 'result' && (
        <>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => loadPrompt('fixed')}
              className="border border-line px-3 py-1 font-mono text-xs uppercase tracking-wide text-ink-soft hover:text-ink"
            >
              Otra propuesta fija
            </button>
            <button
              type="button"
              onClick={() => loadPrompt('generated')}
              className="border border-line px-3 py-1 font-mono text-xs uppercase tracking-wide text-ink-soft hover:text-ink"
            >
              Generar con IA
            </button>
          </div>

          <Panel>
            <p className="text-sm text-ink">{prompt.instructions}</p>
            <p className="mt-2 font-mono text-xs uppercase tracking-wide text-ink-faint">
              {GENRE_HINTS[prompt.genre]}
            </p>
          </Panel>

          <Panel>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={14}
              placeholder="Escribe aquí…"
              className="w-full resize-y border border-line bg-paper px-3 py-2 text-sm leading-relaxed text-ink focus:border-ink"
            />
            <div className="mt-2 flex items-center justify-between">
              <span className={`font-mono text-sm ${countColor}`}>
                {wordCount} / {prompt.word_min}-{prompt.word_max} palabras
              </span>
            </div>
          </Panel>

          {submitError && <ErrorState message={submitError} />}

          <div className="flex items-center justify-end gap-3">
            <button
              type="button"
              disabled={text.trim().length === 0 || phase === 'submitting'}
              onClick={handleSubmit}
              className="border border-seal bg-seal px-4 py-2 font-mono text-sm uppercase tracking-wide text-paper-raised transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {phase === 'submitting' ? 'Corrigiendo…' : 'Entregar redacción'}
            </button>
          </div>
        </>
      )}

      {phase === 'result' && result && <ResultView result={result} />}
    </div>
  )
}

function ResultView({ result }: { result: WritingCorrectionResult }) {
  return (
    <div className="grid gap-6">
      <Panel title="Resultado">
        <div className="flex flex-wrap items-center gap-4">
          <ScoreBand band={result.band} />
          <span className="font-mono text-sm text-ink-soft">{result.word_count} palabras</span>
        </div>
        <p className="mt-3 text-ink-soft">{result.summary}</p>
      </Panel>

      <Panel title="Puntos fuertes">
        <ul className="grid gap-2">
          {result.strengths.map((strength, idx) => (
            <li key={idx} className="flex gap-2 text-sm text-ink">
              <span className="text-distinction" aria-hidden="true">
                ✓
              </span>
              <span>{strength}</span>
            </li>
          ))}
        </ul>
      </Panel>

      {result.errors.length > 0 && (
        <Panel title="Errores detectados">
          <ul className="grid gap-4">
            {result.errors.map((err, idx) => (
              <li key={idx} className="border border-line p-4">
                <p className="font-mono text-xs uppercase tracking-wide text-seal">{err.category}</p>
                <p className="mt-2 text-sm text-ink">
                  <span className="text-ink-faint line-through">{err.excerpt}</span>
                  {' → '}
                  <span className="font-semibold text-distinction">{err.correction}</span>
                </p>
                <p className="mt-1 text-sm text-ink-soft">{err.explanation}</p>
              </li>
            ))}
          </ul>
        </Panel>
      )}

      <Panel title="Frase modelo reescrita">
        <p className="text-sm text-ink-faint line-through">{result.model_sentence.original}</p>
        <p className="mt-2 text-sm font-semibold text-distinction">{result.model_sentence.rewritten}</p>
        <p className="mt-2 text-sm text-ink-soft">{result.model_sentence.explanation}</p>
      </Panel>
    </div>
  )
}
