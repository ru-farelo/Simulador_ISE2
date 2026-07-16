import { useEffect, useState } from 'react'
import { ApiError } from '../../api/client'
import { learningApi } from '../../api/learning'
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition'
import { useSpeechSynthesis } from '../../hooks/useSpeechSynthesis'
import type { DuePronunciationItem, LearningReviewResult } from '../../types/learning'
import { ErrorState } from '../ui/ErrorState'
import { LoadingState } from '../ui/LoadingState'
import { Panel } from '../ui/Panel'
import { ReviewFeedback } from './ReviewFeedback'

export function PronunciationExercise({ item, onDone }: { item: DuePronunciationItem; onDone: () => void }) {
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<LearningReviewResult | null>(null)
  const synthesis = useSpeechSynthesis()
  const recognition = useSpeechRecognition()

  useEffect(() => {
    synthesis.cancel()
    recognition.reset()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [item.item_id])

  const submit = (transcript: string) => {
    if (!transcript.trim()) return
    setSubmitting(true)
    setError(null)
    learningApi
      .review(item.item_id, { answer: transcript })
      .then(setResult)
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Error desconocido'))
      .finally(() => setSubmitting(false))
  }

  const stopAndSubmit = () => {
    recognition.stop()
    submit(recognition.transcript)
  }

  return (
    <Panel title={`Pronunciación · ${item.category}`}>
      <p className="text-lg leading-relaxed text-ink">{item.sentence}</p>
      <p className="mt-2 text-sm text-ink-faint">Foco: {item.tip}</p>

      <p className="mt-3 text-xs text-ink-faint">
        Nota: esto compara el texto que reconoce el navegador con la frase objetivo — no analiza tu fonética real, así
        que un acento marcado o una palabra transcrita de forma distinta pueden dar falsos negativos o positivos.
      </p>

      {!result && (
        <div className="mt-4 grid gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => synthesis.speak(item.sentence)}
              disabled={synthesis.isSpeaking || !synthesis.isSupported}
              className="border border-ink px-4 py-2 font-mono text-sm uppercase tracking-wide hover:bg-ink hover:text-paper-raised disabled:cursor-not-allowed disabled:opacity-40"
            >
              {synthesis.isSpeaking ? 'Reproduciendo…' : '▶ Escuchar'}
            </button>
            {!synthesis.isSupported && <span className="text-xs text-seal">Tu navegador no soporta TTS.</span>}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={recognition.isListening ? stopAndSubmit : recognition.start}
              disabled={!recognition.isSupported || submitting}
              className={`border px-4 py-2 font-mono text-sm uppercase tracking-wide disabled:cursor-not-allowed disabled:opacity-40 ${
                recognition.isListening ? 'border-seal bg-seal text-paper-raised' : 'border-ink hover:bg-ink hover:text-paper-raised'
              }`}
            >
              {recognition.isListening ? '⏹ Detener y enviar' : '🎙 Repetir la frase'}
            </button>
            {!recognition.isSupported && (
              <span className="text-xs text-seal">Tu navegador no soporta reconocimiento de voz.</span>
            )}
          </div>

          {recognition.transcript && (
            <p className="border border-line bg-paper px-3 py-2 text-sm text-ink-soft">
              Reconocido: “{recognition.transcript}”
            </p>
          )}
        </div>
      )}

      {submitting && <LoadingState label="Comparando…" />}
      {error && <ErrorState message={error} onRetry={() => submit(recognition.transcript)} />}
      {result && <div className="mt-4"><ReviewFeedback result={result} onNext={onDone} /></div>}
    </Panel>
  )
}
