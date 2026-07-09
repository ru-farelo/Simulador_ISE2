import { useEffect, useState } from 'react'
import { ApiError } from '../api/client'
import { listeningApi } from '../api/listening'
import { speakingApi } from '../api/speaking'
import { ChatTranscript } from '../components/speaking/ChatTranscript'
import { SpokenLine } from '../components/speaking/SpokenLine'
import { VoiceOrTextInput } from '../components/speaking/VoiceOrTextInput'
import { ErrorState } from '../components/ui/ErrorState'
import { LoadingState } from '../components/ui/LoadingState'
import { Panel } from '../components/ui/Panel'
import { ScoreBand } from '../components/ui/ScoreBand'
import { useSpeechSynthesis } from '../hooks/useSpeechSynthesis'
import type { ConversationTurn, PartName, SpeakingCorrectionResult } from '../types/speaking'
import type { ListeningPassage, PassageSource } from '../types/speaking'

type TaskKey = 'topic' | 'collaborative' | 'conversation' | 'listening'

const TASK_LABELS: Record<TaskKey, string> = {
  topic: 'Topic',
  collaborative: 'Collaborative',
  conversation: 'Conversation',
  listening: 'Listening',
}

export function SpeakingPage() {
  const [activeTask, setActiveTask] = useState<TaskKey>('topic')
  const [transcripts, setTranscripts] = useState<Record<TaskKey, ConversationTurn[]>>({
    topic: [],
    collaborative: [],
    conversation: [],
    listening: [],
  })
  const [correcting, setCorrecting] = useState(false)
  const [correctError, setCorrectError] = useState<string | null>(null)
  const [result, setResult] = useState<SpeakingCorrectionResult | null>(null)

  const setTranscript = (task: TaskKey, turns: ConversationTurn[]) =>
    setTranscripts((prev) => ({ ...prev, [task]: turns }))

  const runCorrection = (scope: TaskKey | 'all') => {
    const parts = (scope === 'all' ? (Object.keys(transcripts) as TaskKey[]) : [scope])
      .map((task) => ({ task_name: task as PartName, transcript: transcripts[task] }))
      .filter((p) => p.transcript.length > 0)

    if (parts.length === 0) return

    setCorrecting(true)
    setCorrectError(null)
    setResult(null)
    speakingApi
      .correct({ parts, duration_seconds: 0 })
      .then(setResult)
      .catch((err: unknown) => setCorrectError(err instanceof ApiError ? err.message : 'Error desconocido'))
      .finally(() => setCorrecting(false))
  }

  const anyTranscript = Object.values(transcripts).some((t) => t.length > 0)

  return (
    <div className="grid gap-6">
      <div className="border border-line bg-paper-raised px-5 py-4">
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-ink-soft">Speaking &amp; Listening</p>
        <h2 className="mt-1 font-display text-xl font-semibold">Sesión de 20 minutos, 4 partes</h2>
      </div>

      <nav className="flex flex-wrap gap-1 border-b border-line" aria-label="Partes de Speaking &amp; Listening">
        {(Object.keys(TASK_LABELS) as TaskKey[]).map((task) => (
          <button
            key={task}
            type="button"
            onClick={() => setActiveTask(task)}
            className={`border-b-2 px-4 py-2 font-mono text-sm uppercase tracking-wide ${
              activeTask === task ? 'border-seal text-seal' : 'border-transparent text-ink-soft hover:text-ink'
            }`}
          >
            {TASK_LABELS[task]}
            {transcripts[task].length > 0 && <span className="ml-1 text-distinction">●</span>}
          </button>
        ))}
      </nav>

      <div className={activeTask === 'topic' ? '' : 'hidden'}>
        <TopicTaskView transcript={transcripts.topic} setTranscript={(t) => setTranscript('topic', t)} />
      </div>
      <div className={activeTask === 'collaborative' ? '' : 'hidden'}>
        <CollaborativeTaskView
          transcript={transcripts.collaborative}
          setTranscript={(t) => setTranscript('collaborative', t)}
        />
      </div>
      <div className={activeTask === 'conversation' ? '' : 'hidden'}>
        <ConversationTaskView
          transcript={transcripts.conversation}
          setTranscript={(t) => setTranscript('conversation', t)}
        />
      </div>
      <div className={activeTask === 'listening' ? '' : 'hidden'}>
        <ListeningTaskView transcript={transcripts.listening} setTranscript={(t) => setTranscript('listening', t)} />
      </div>

      <div className="flex flex-wrap items-center justify-end gap-3 border-t border-line pt-5">
        <button
          type="button"
          disabled={transcripts[activeTask].length === 0 || correcting}
          onClick={() => runCorrection(activeTask)}
          className="border border-line px-4 py-2 font-mono text-sm uppercase tracking-wide text-ink-soft hover:text-ink disabled:cursor-not-allowed disabled:opacity-40"
        >
          Corregir esta parte
        </button>
        <button
          type="button"
          disabled={!anyTranscript || correcting}
          onClick={() => runCorrection('all')}
          className="border border-seal bg-seal px-4 py-2 font-mono text-sm uppercase tracking-wide text-paper-raised hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {correcting ? 'Corrigiendo…' : 'Corregir las 4 partes'}
        </button>
      </div>

      {correctError && <ErrorState message={correctError} />}
      {result && <SpeakingResultView result={result} />}
    </div>
  )
}

function SpeakingResultView({ result }: { result: SpeakingCorrectionResult }) {
  return (
    <div className="grid gap-6">
      <Panel title="Resultado">
        <div className="flex flex-wrap items-center gap-4">
          <span className="font-display text-4xl text-ink">{Math.round(result.score)}</span>
          <ScoreBand band={result.band} />
        </div>
        <p className="mt-3 text-ink-soft">{result.summary}</p>
      </Panel>

      <div className="grid gap-4 sm:grid-cols-2">
        <Panel title="Estructura">
          <p className="text-sm text-ink-soft">{result.structure_comment}</p>
        </Panel>
        <Panel title="Gramática">
          <p className="text-sm text-ink-soft">{result.grammar_comment}</p>
        </Panel>
        <Panel title="Fluidez">
          <p className="text-sm text-ink-soft">{result.fluency_comment}</p>
        </Panel>
        <Panel title="Interacción">
          <p className="text-sm text-ink-soft">{result.interaction_comment}</p>
        </Panel>
      </div>

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
    </div>
  )
}

function TopicTaskView({
  transcript,
  setTranscript,
}: {
  transcript: ConversationTurn[]
  setTranscript: (t: ConversationTurn[]) => void
}) {
  const [phase, setPhase] = useState<'prep' | 'chatting' | 'done'>(transcript.length > 0 ? 'chatting' : 'prep')
  const [topic, setTopic] = useState('AI in Language Learning')
  const [notes, setNotes] = useState('')
  const [draft, setDraft] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendTurn = (candidateText: string) => {
    const newHistory = [...transcript, { role: 'candidate' as const, text: candidateText }]
    setTranscript(newHistory)
    setDraft('')
    setLoading(true)
    setError(null)
    speakingApi
      .postTurn('topic', { history: newHistory, context: { topic, notes } })
      .then((res) => {
        setTranscript([...newHistory, { role: 'examiner', text: res.examiner_text }])
        setPhase(res.task_complete ? 'done' : 'chatting')
      })
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Error desconocido'))
      .finally(() => setLoading(false))
  }

  if (phase === 'prep') {
    return (
      <Panel title="Prepara tu Topic">
        <label className="block text-sm text-ink-soft" htmlFor="topic-title">
          Topic
        </label>
        <input
          id="topic-title"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          className="mt-1 w-full border border-line bg-paper px-3 py-1.5 text-sm text-ink focus:border-ink"
        />
        <label className="mt-4 block text-sm text-ink-soft" htmlFor="topic-notes">
          Notas / puntos clave (opcional)
        </label>
        <textarea
          id="topic-notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={3}
          placeholder="Idea general, diferentes puntos de vista, tu opinión, conclusión…"
          className="mt-1 w-full border border-line bg-paper px-3 py-1.5 text-sm text-ink focus:border-ink"
        />
        <p className="mt-4 text-sm text-ink-soft">
          Cuando estés listo, habla o escribe tu presentación completa (≈2 minutos) y entrégala. El examinador te
          hará preguntas sobre lo que has dicho.
        </p>
        <div className="mt-3">
          <VoiceOrTextInput
            value={draft}
            onChange={setDraft}
            onSend={() => sendTurn(draft)}
            sendLabel="Entregar mi presentación"
            rows={6}
            placeholder="Today I'd like to talk about…"
            disabled={loading}
          />
        </div>
        {loading && <LoadingState label="El examinador está pensando…" />}
        {error && <ErrorState message={error} />}
      </Panel>
    )
  }

  return (
    <div className="grid gap-4">
      <Panel title={`Topic: ${topic}`}>
        <ChatTranscript turns={transcript} />
      </Panel>
      {phase === 'chatting' && (
        <Panel>
          <VoiceOrTextInput value={draft} onChange={setDraft} onSend={() => sendTurn(draft)} disabled={loading} />
          {loading && <LoadingState label="El examinador está pensando…" />}
          {error && <ErrorState message={error} />}
        </Panel>
      )}
      {phase === 'done' && (
        <p className="font-mono text-xs uppercase tracking-wide text-distinction">Tarea completada</p>
      )}
    </div>
  )
}

function CollaborativeTaskView({
  transcript,
  setTranscript,
}: {
  transcript: ConversationTurn[]
  setTranscript: (t: ConversationTurn[]) => void
}) {
  const [phase, setPhase] = useState<'idle' | 'chatting' | 'done'>(transcript.length > 0 ? 'chatting' : 'idle')
  const [draft, setDraft] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const start = () => {
    setLoading(true)
    setError(null)
    speakingApi
      .postTurn('collaborative', { history: [], context: {} })
      .then((res) => {
        setTranscript([{ role: 'examiner', text: res.examiner_text }])
        setPhase('chatting')
      })
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Error desconocido'))
      .finally(() => setLoading(false))
  }

  const sendTurn = (candidateText: string) => {
    const newHistory = [...transcript, { role: 'candidate' as const, text: candidateText }]
    setTranscript(newHistory)
    setDraft('')
    setLoading(true)
    setError(null)
    speakingApi
      .postTurn('collaborative', { history: newHistory, context: {} })
      .then((res) => {
        setTranscript([...newHistory, { role: 'examiner', text: res.examiner_text }])
        setPhase(res.task_complete ? 'done' : 'chatting')
      })
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Error desconocido'))
      .finally(() => setLoading(false))
  }

  if (phase === 'idle') {
    return (
      <Panel title="Collaborative task">
        <p className="text-sm text-ink-soft">
          El examinador te planteará un dilema o una opinión breve. Tu trabajo es hacerle preguntas para sacarle
          información — los roles están invertidos respecto al Topic task.
        </p>
        <button
          type="button"
          onClick={start}
          disabled={loading}
          className="mt-4 border border-ink px-4 py-2 font-mono text-sm uppercase tracking-wide hover:bg-ink hover:text-paper-raised disabled:cursor-not-allowed disabled:opacity-40"
        >
          {loading ? 'Cargando…' : 'Empezar'}
        </button>
        {error && <ErrorState message={error} />}
      </Panel>
    )
  }

  return (
    <div className="grid gap-4">
      <Panel title="Collaborative task">
        <ChatTranscript turns={transcript} />
      </Panel>
      {phase === 'chatting' && (
        <Panel>
          <VoiceOrTextInput
            value={draft}
            onChange={setDraft}
            onSend={() => sendTurn(draft)}
            disabled={loading}
            placeholder="Pregunta al examinador…"
          />
          {loading && <LoadingState label="El examinador está pensando…" />}
          {error && <ErrorState message={error} />}
        </Panel>
      )}
      {phase === 'done' && (
        <p className="font-mono text-xs uppercase tracking-wide text-distinction">Tarea completada</p>
      )}
    </div>
  )
}

function ConversationTaskView({
  transcript,
  setTranscript,
}: {
  transcript: ConversationTurn[]
  setTranscript: (t: ConversationTurn[]) => void
}) {
  const [phase, setPhase] = useState<'idle' | 'chatting' | 'done'>(transcript.length > 0 ? 'chatting' : 'idle')
  const [topic, setTopic] = useState<string | null>(null)
  const [draft, setDraft] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const start = () => {
    setLoading(true)
    setError(null)
    speakingApi
      .getConversationTopic()
      .then(({ topic: chosen }) => {
        setTopic(chosen)
        return speakingApi.postTurn('conversation', { history: [], context: { topic: chosen } })
      })
      .then((res) => {
        setTranscript([{ role: 'examiner', text: res.examiner_text }])
        setPhase('chatting')
      })
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Error desconocido'))
      .finally(() => setLoading(false))
  }

  const sendTurn = (candidateText: string) => {
    if (!topic) return
    const newHistory = [...transcript, { role: 'candidate' as const, text: candidateText }]
    setTranscript(newHistory)
    setDraft('')
    setLoading(true)
    setError(null)
    speakingApi
      .postTurn('conversation', { history: newHistory, context: { topic } })
      .then((res) => {
        setTranscript([...newHistory, { role: 'examiner', text: res.examiner_text }])
        setPhase(res.task_complete ? 'done' : 'chatting')
      })
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Error desconocido'))
      .finally(() => setLoading(false))
  }

  if (phase === 'idle') {
    return (
      <Panel title="Conversation task">
        <p className="text-sm text-ink-soft">
          El examinador elegirá un tema (medio ambiente, sociedad, valores, trabajo, educación, tecnología, salud o
          viajes) y mantendrá una breve conversación contigo.
        </p>
        <button
          type="button"
          onClick={start}
          disabled={loading}
          className="mt-4 border border-ink px-4 py-2 font-mono text-sm uppercase tracking-wide hover:bg-ink hover:text-paper-raised disabled:cursor-not-allowed disabled:opacity-40"
        >
          {loading ? 'Cargando…' : 'Empezar'}
        </button>
        {error && <ErrorState message={error} />}
      </Panel>
    )
  }

  return (
    <div className="grid gap-4">
      <Panel title={`Conversation: ${topic ?? ''}`}>
        <ChatTranscript turns={transcript} />
      </Panel>
      {phase === 'chatting' && (
        <Panel>
          <VoiceOrTextInput value={draft} onChange={setDraft} onSend={() => sendTurn(draft)} disabled={loading} />
          {loading && <LoadingState label="El examinador está pensando…" />}
          {error && <ErrorState message={error} />}
        </Panel>
      )}
      {phase === 'done' && (
        <p className="font-mono text-xs uppercase tracking-wide text-distinction">Tarea completada</p>
      )}
    </div>
  )
}

function ListeningTaskView({
  setTranscript,
}: {
  transcript: ConversationTurn[]
  setTranscript: (t: ConversationTurn[]) => void
}) {
  const [passage, setPassage] = useState<ListeningPassage | null>(null)
  const [phase, setPhase] = useState<'loading' | 'ready' | 'done'>('loading')
  const [loadError, setLoadError] = useState<string | null>(null)
  const [playCount, setPlayCount] = useState(0)
  const [rate, setRate] = useState(1)
  const [generalAnswer, setGeneralAnswer] = useState('')
  const [detailAnswer, setDetailAnswer] = useState('')
  const [generalSubmitted, setGeneralSubmitted] = useState(false)
  const synthesis = useSpeechSynthesis()

  const load = (mode: PassageSource) => {
    setPhase('loading')
    setLoadError(null)
    setPlayCount(0)
    setGeneralAnswer('')
    setDetailAnswer('')
    setGeneralSubmitted(false)
    setTranscript([])
    listeningApi
      .getPassage(mode)
      .then((p) => {
        setPassage(p)
        setPhase('ready')
      })
      .catch((err: unknown) => setLoadError(err instanceof ApiError ? err.message : 'Error desconocido'))
  }

  useEffect(() => {
    if (!passage) load('fixed')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const play = () => {
    if (!passage || playCount >= 2) return
    synthesis.speak(passage.text, { rate, onEnd: () => setPlayCount((c) => c + 1) })
  }

  const submitGeneral = () => {
    if (!passage) return
    setTranscript([
      { role: 'examiner', text: passage.general_question },
      { role: 'candidate', text: generalAnswer },
    ])
    setGeneralSubmitted(true)
  }

  const submitDetail = () => {
    if (!passage) return
    setTranscript([
      { role: 'examiner', text: passage.general_question },
      { role: 'candidate', text: generalAnswer },
      { role: 'examiner', text: passage.detail_question },
      { role: 'candidate', text: detailAnswer },
    ])
    setPhase('done')
  }

  if (phase === 'loading' && !passage) return <LoadingState label="Preparando el audio…" />
  if (loadError) return <ErrorState message={loadError} onRetry={() => load('fixed')} />
  if (!passage) return null

  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => load('fixed')}
          className="border border-line px-3 py-1 font-mono text-xs uppercase tracking-wide text-ink-soft hover:text-ink"
        >
          Otro audio fijo
        </button>
        <button
          type="button"
          onClick={() => load('generated')}
          className="border border-line px-3 py-1 font-mono text-xs uppercase tracking-wide text-ink-soft hover:text-ink"
        >
          Generar con IA
        </button>
      </div>

      <Panel title={passage.topic}>
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={play}
            disabled={playCount >= 2 || synthesis.isSpeaking || !synthesis.isSupported}
            className="border border-ink px-4 py-2 font-mono text-sm uppercase tracking-wide hover:bg-ink hover:text-paper-raised disabled:cursor-not-allowed disabled:opacity-40"
          >
            {synthesis.isSpeaking ? 'Reproduciendo…' : `▶ Reproducir (${playCount}/2)`}
          </button>
          {synthesis.isSpeaking && (
            <button
              type="button"
              onClick={synthesis.cancel}
              className="border border-seal px-4 py-2 font-mono text-sm uppercase tracking-wide text-seal hover:bg-seal hover:text-paper-raised"
            >
              ⏹ Detener
            </button>
          )}
          <label className="flex items-center gap-2 font-mono text-xs uppercase tracking-wide text-ink-soft">
            Velocidad
            <select
              value={rate}
              onChange={(e) => setRate(Number(e.target.value))}
              className="border border-line bg-paper px-2 py-1"
            >
              <option value={0.75}>0.75×</option>
              <option value={1}>1×</option>
              <option value={1.25}>1.25×</option>
            </select>
          </label>
          {!synthesis.isSupported && (
            <span className="text-xs text-seal">Tu navegador no soporta síntesis de voz.</span>
          )}
        </div>
        {playCount === 0 && (
          <p className="mt-3 text-sm text-ink-faint">
            Puedes tomar notas mientras escuchas. Tras la primera escucha aparecerá la pregunta general.
          </p>
        )}
      </Panel>

      {playCount >= 1 && (
        <Panel title="Pregunta general (tras la 1ª escucha)">
          <SpokenLine text={passage.general_question} />
          <div className="mt-3">
            <VoiceOrTextInput
              value={generalAnswer}
              onChange={setGeneralAnswer}
              onSend={submitGeneral}
              disabled={generalSubmitted}
              sendLabel="Confirmar respuesta"
            />
          </div>
        </Panel>
      )}

      {playCount >= 2 && generalSubmitted && (
        <Panel title="Pregunta de detalle (tras la 2ª escucha)">
          <SpokenLine text={passage.detail_question} />
          <div className="mt-3">
            <VoiceOrTextInput
              value={detailAnswer}
              onChange={setDetailAnswer}
              onSend={submitDetail}
              disabled={phase === 'done'}
              sendLabel="Confirmar respuesta"
              rows={4}
            />
          </div>
        </Panel>
      )}

      {phase === 'done' && (
        <p className="font-mono text-xs uppercase tracking-wide text-distinction">Tarea completada</p>
      )}
    </div>
  )
}
