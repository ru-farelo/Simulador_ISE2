import { useEffect, useState } from 'react'
import { ApiError } from '../api/client'
import { readingApi } from '../api/reading'
import { ExerciseResultView } from '../components/reading/ExerciseResultView'
import { GapFillExerciseView } from '../components/reading/GapFillExerciseView'
import { MatchingExerciseView } from '../components/reading/MatchingExerciseView'
import { MultiSelectExerciseView } from '../components/reading/MultiSelectExerciseView'
import { TrueFalseExerciseView } from '../components/reading/TrueFalseExerciseView'
import { ErrorState } from '../components/ui/ErrorState'
import { LoadingState } from '../components/ui/LoadingState'
import { Panel } from '../components/ui/Panel'
import { ScoreBand } from '../components/ui/ScoreBand'
import { useCountdown } from '../hooks/useCountdown'
import type {
  ExamSource,
  ReadingExam,
  ReadingExamResult,
  Task1Submission,
  Task2Submission,
  Task3Submission,
} from '../types/reading'

const TOTAL_SECONDS = 60 * 60 // 30 min Task 1 + 15 min Task 2 + 15 min Task 3, as per the real paper

type Phase = 'loading' | 'ready' | 'submitting' | 'result'
type TaskNumber = 1 | 2 | 3

const emptyTask1 = (): Task1Submission => ({ exercise_a: {}, exercise_b: {}, exercise_c: {}, exercise_d: {} })
const emptyTask2 = (): Task2Submission => ({ exercise_a: {}, exercise_b: [], exercise_c: {} })
const emptyTask3 = (): Task3Submission => ({ exercise_1_5: {}, exercise_6_10: [] })

export function ReadingPage() {
  const [exam, setExam] = useState<ReadingExam | null>(null)
  const [activeTask, setActiveTask] = useState<TaskNumber>(1)
  const [phase, setPhase] = useState<Phase>('loading')
  const [loadError, setLoadError] = useState<string | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [result, setResult] = useState<ReadingExamResult | null>(null)

  const [t1, setT1] = useState<Task1Submission>(emptyTask1())
  const [t2, setT2] = useState<Task2Submission>(emptyTask2())
  const [t3, setT3] = useState<Task3Submission>(emptyTask3())

  const timer = useCountdown(TOTAL_SECONDS)

  const loadExam = (mode: ExamSource) => {
    setPhase('loading')
    setLoadError(null)
    setResult(null)
    setActiveTask(1)
    setT1(emptyTask1())
    setT2(emptyTask2())
    setT3(emptyTask3())
    timer.reset(TOTAL_SECONDS)
    readingApi
      .getExam(mode)
      .then((e) => {
        setExam(e)
        setPhase('ready')
      })
      .catch((err: unknown) => setLoadError(err instanceof ApiError ? err.message : 'Error desconocido'))
  }

  useEffect(() => loadExam('fixed'), [])

  const handleSubmit = () => {
    if (!exam) return
    setPhase('submitting')
    setSubmitError(null)
    timer.pause()
    readingApi
      .submit({
        exam_id: exam.id,
        task1: t1,
        task2: t2,
        task3: t3,
        duration_seconds: TOTAL_SECONDS - timer.secondsLeft,
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

  if (phase === 'loading' && !exam) return <LoadingState label="Preparando el examen…" />
  if (loadError) return <ErrorState message={loadError} onRetry={() => loadExam('fixed')} />
  if (!exam) return null

  return (
    <div className="grid gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border border-line bg-paper-raised px-5 py-4">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-ink-soft">Reading &amp; Writing</p>
          <h2 className="mt-1 font-display text-xl font-semibold">Task 1, 2 y 3</h2>
        </div>
        <div className="flex items-center gap-4">
          <div
            className={`font-mono text-2xl tabular-nums ${timer.secondsLeft <= 300 && timer.isRunning ? 'text-seal' : 'text-ink'}`}
            aria-live="polite"
          >
            {timer.formatted}
          </div>
          {!timer.isRunning && timer.secondsLeft === TOTAL_SECONDS && phase === 'ready' && (
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
              onClick={() => loadExam('fixed')}
              className="border border-line px-3 py-1 font-mono text-xs uppercase tracking-wide text-ink-soft hover:text-ink"
            >
              Examen real (Julio)
            </button>
            <button
              type="button"
              onClick={() => loadExam('generated')}
              className="border border-line px-3 py-1 font-mono text-xs uppercase tracking-wide text-ink-soft hover:text-ink"
            >
              Generar con IA
            </button>
          </div>

          <nav className="flex gap-1 border-b border-line" aria-label="Tareas de Reading">
            {([1, 2, 3] as const).map((n) => (
              <button
                key={n}
                type="button"
                onClick={() => setActiveTask(n)}
                className={`border-b-2 px-4 py-2 font-mono text-sm uppercase tracking-wide ${
                  activeTask === n ? 'border-seal text-seal' : 'border-transparent text-ink-soft hover:text-ink'
                }`}
              >
                Task {n}
              </button>
            ))}
          </nav>

          {activeTask === 1 && (
            <Task1View task={exam.task1} value={t1} onChange={setT1} />
          )}
          {activeTask === 2 && (
            <Task2View task={exam.task2} value={t2} onChange={setT2} />
          )}
          {activeTask === 3 && (
            <Task3View task={exam.task3} value={t3} onChange={setT3} />
          )}

          {submitError && <ErrorState message={submitError} />}

          <div className="flex items-center justify-end gap-3 border-t border-line pt-5">
            <button
              type="button"
              disabled={phase === 'submitting'}
              onClick={handleSubmit}
              className="border border-seal bg-seal px-4 py-2 font-mono text-sm uppercase tracking-wide text-paper-raised transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {phase === 'submitting' ? 'Corrigiendo…' : 'Entregar examen completo'}
            </button>
          </div>
        </>
      )}

      {phase === 'result' && result && <ResultView result={result} />}
    </div>
  )
}

function Task1View({
  task,
  value,
  onChange,
}: {
  task: ReadingExam['task1']
  value: Task1Submission
  onChange: (v: Task1Submission) => void
}) {
  return (
    <div className="grid gap-6">
      <Panel title={task.title}>
        <div className="grid gap-4">
          {task.paragraphs.map((p) => (
            <p key={p.id} className="text-sm leading-relaxed text-ink">
              <span className="mr-2 font-mono text-ink-faint">{p.id}.</span>
              {p.text}
            </p>
          ))}
        </div>
      </Panel>
      <Panel title="A — Match the titles">
        <MatchingExerciseView
          exercise={task.exercise_a}
          value={value.exercise_a}
          onChange={(v) => onChange({ ...value, exercise_a: v })}
        />
      </Panel>
      <Panel title="B — Vocabulary">
        <GapFillExerciseView
          exercise={task.exercise_b}
          value={value.exercise_b}
          onChange={(v) => onChange({ ...value, exercise_b: v })}
        />
      </Panel>
      <Panel title="C — True or False">
        <TrueFalseExerciseView
          exercise={task.exercise_c}
          value={value.exercise_c}
          onChange={(v) => onChange({ ...value, exercise_c: v })}
        />
      </Panel>
      <Panel title="D — Complete the sentences">
        <GapFillExerciseView
          exercise={task.exercise_d}
          value={value.exercise_d}
          onChange={(v) => onChange({ ...value, exercise_d: v })}
        />
      </Panel>
    </div>
  )
}

function Task2View({
  task,
  value,
  onChange,
}: {
  task: ReadingExam['task2']
  value: Task2Submission
  onChange: (v: Task2Submission) => void
}) {
  return (
    <div className="grid gap-6">
      <Panel title={task.title}>
        <div className="grid gap-4">
          {task.texts.map((t) => (
            <div key={t.id}>
              <p className="mb-1 font-mono text-xs uppercase tracking-wide text-ink-faint">Text {t.id}</p>
              <p className="whitespace-pre-line text-sm leading-relaxed text-ink">{t.text}</p>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="A — Which text?">
        <MatchingExerciseView
          exercise={task.exercise_a}
          value={value.exercise_a}
          onChange={(v) => onChange({ ...value, exercise_a: v })}
        />
      </Panel>
      <Panel title="B — True statements">
        <MultiSelectExerciseView
          exercise={task.exercise_b}
          value={value.exercise_b}
          onChange={(v) => onChange({ ...value, exercise_b: v })}
        />
      </Panel>
      <Panel title="C — Summary notes">
        <GapFillExerciseView
          exercise={task.exercise_c}
          value={value.exercise_c}
          onChange={(v) => onChange({ ...value, exercise_c: v })}
        />
      </Panel>
    </div>
  )
}

function Task3View({
  task,
  value,
  onChange,
}: {
  task: ReadingExam['task3']
  value: Task3Submission
  onChange: (v: Task3Submission) => void
}) {
  return (
    <div className="grid gap-6">
      <Panel title={task.title}>
        <div className="grid gap-4">
          {task.texts.map((t) => (
            <div key={t.id}>
              <p className="mb-1 font-mono text-xs uppercase tracking-wide text-ink-faint">Text {t.id}</p>
              <p className="whitespace-pre-line text-sm leading-relaxed text-ink">{t.text}</p>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="1-5 — Which text?">
        <MatchingExerciseView
          exercise={task.exercise_1_5}
          value={value.exercise_1_5}
          onChange={(v) => onChange({ ...value, exercise_1_5: v })}
        />
      </Panel>
      <Panel title="6-10 — True statements">
        <MultiSelectExerciseView
          exercise={task.exercise_6_10}
          value={value.exercise_6_10}
          onChange={(v) => onChange({ ...value, exercise_6_10: v })}
        />
      </Panel>
    </div>
  )
}

function ResultView({ result }: { result: ReadingExamResult }) {
  return (
    <div className="grid gap-6">
      <Panel title="Resultado global">
        <div className="flex flex-wrap items-center gap-4">
          <span className="font-display text-4xl text-ink">{Math.round(result.overall_score)}</span>
          <ScoreBand band={result.band} />
        </div>
        <p className="mt-3 text-ink-soft">{result.summary}</p>
      </Panel>

      {result.tasks.map((task) => (
        <Panel key={task.task_number} title={`Task ${task.task_number} — ${task.title} (${task.correct_count}/${task.total_count})`}>
          <div className="grid gap-4">
            {task.exercises.map((ex) => (
              <ExerciseResultView key={ex.label} result={ex} />
            ))}
          </div>
        </Panel>
      ))}

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
