import { useEffect, useState } from 'react'
import { ApiError } from '../api/client'
import { learningApi } from '../api/learning'
import { plannerApi } from '../api/planner'
import { reinforcementApi } from '../api/reinforcement'
import { FillerExercise } from '../components/learning/FillerExercise'
import { GrammarExercise } from '../components/learning/GrammarExercise'
import { PronunciationExercise } from '../components/learning/PronunciationExercise'
import { ReinforcementExercise } from '../components/learning/ReinforcementExercise'
import { VocabExercise } from '../components/learning/VocabExercise'
import { ErrorState } from '../components/ui/ErrorState'
import { LoadingState } from '../components/ui/LoadingState'
import { Panel } from '../components/ui/Panel'
import type { DueItem, LearningItemType, VocabCategoryFilter } from '../types/learning'
import type { PlannerToday } from '../types/planner'
import type { DueReinforcementItem } from '../types/reinforcement'

type TabKey = 'vocab' | 'grammar' | 'filler' | 'connector' | 'pronunciation'
type BlockKey = 'learning' | 'reinforcement'
type VocabFilterKey = 'all' | VocabCategoryFilter

const VOCAB_FILTERS: { key: VocabFilterKey; label: string }[] = [
  { key: 'all', label: 'Todos' },
  { key: 'thematic', label: 'Temático' },
  { key: 'general', label: 'General (NGSL)' },
]

const TABS: { key: TabKey; label: string }[] = [
  { key: 'vocab', label: 'Vocabulario' },
  { key: 'grammar', label: 'Gramática' },
  { key: 'filler', label: 'Fillers' },
  { key: 'connector', label: 'Conectores' },
  { key: 'pronunciation', label: 'Pronunciación' },
]

function Badge({ count }: { count: number }) {
  if (count === 0) return null
  return (
    <span className="ml-1.5 rounded-full bg-seal px-1.5 py-0.5 text-[0.65rem] font-semibold text-paper-raised">
      {count}
    </span>
  )
}

export function PracticePage() {
  const [block, setBlock] = useState<BlockKey>('learning')
  const [activeTab, setActiveTab] = useState<TabKey>('vocab')
  const [vocabFilter, setVocabFilter] = useState<VocabFilterKey>('all')
  const [plan, setPlan] = useState<PlannerToday | null>(null)

  useEffect(() => {
    plannerApi
      .getToday()
      .then(setPlan)
      .catch(() => setPlan(null))
  }, [])

  const dueCount = (type: string) => plan?.blocks.find((b) => b.type === type)?.due_count ?? 0
  const reinforcementDue = dueCount('reinforcement')
  const learningDue = plan ? plan.total_due - reinforcementDue : 0

  return (
    <div className="grid gap-6">
      <div className="border border-line bg-paper-raised px-5 py-4">
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-ink-soft">Práctica diaria</p>
        <h2 className="mt-1 font-display text-xl font-semibold">
          {block === 'learning' ? 'Bloque 1 · Aprendizaje' : 'Bloque 2 · Refuerzo'}
        </h2>
        <p className="mt-1 text-sm text-ink-soft">
          {block === 'learning'
            ? 'Producción activa: escribe, transforma o habla — nunca elijas de una lista.'
            : 'Tus propios errores recurrentes, detectados automáticamente de tus sesiones — sin pistas.'}
        </p>
      </div>

      {plan && (
        <Panel title="Plan de hoy">
          <p className="text-sm text-ink">{plan.suggestion}</p>
        </Panel>
      )}

      <div className="flex gap-1">
        <button
          type="button"
          onClick={() => setBlock('learning')}
          className={`border px-4 py-1.5 font-mono text-xs uppercase tracking-wide ${
            block === 'learning' ? 'border-seal text-seal' : 'border-line text-ink-soft hover:text-ink'
          }`}
        >
          Aprendizaje
          <Badge count={learningDue} />
        </button>
        <button
          type="button"
          onClick={() => setBlock('reinforcement')}
          className={`border px-4 py-1.5 font-mono text-xs uppercase tracking-wide ${
            block === 'reinforcement' ? 'border-seal text-seal' : 'border-line text-ink-soft hover:text-ink'
          }`}
        >
          Refuerzo
          <Badge count={reinforcementDue} />
        </button>
      </div>

      {block === 'learning' && (
        <>
          <nav className="flex flex-wrap gap-1 border-b border-line" aria-label="Tipo de práctica">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => setActiveTab(tab.key)}
                className={`border-b-2 px-4 py-2 font-mono text-sm uppercase tracking-wide ${
                  activeTab === tab.key ? 'border-seal text-seal' : 'border-transparent text-ink-soft hover:text-ink'
                }`}
              >
                {tab.label}
                <Badge count={dueCount(tab.key)} />
              </button>
            ))}
          </nav>

          {activeTab === 'vocab' && (
            <div className="flex flex-wrap gap-1" aria-label="Filtro de vocabulario">
              {VOCAB_FILTERS.map((f) => (
                <button
                  key={f.key}
                  type="button"
                  onClick={() => setVocabFilter(f.key)}
                  className={`border px-3 py-1 font-mono text-xs uppercase tracking-wide ${
                    vocabFilter === f.key ? 'border-seal text-seal' : 'border-line text-ink-soft hover:text-ink'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          )}

          <PracticeQueue
            key={`${activeTab}:${activeTab === 'vocab' ? vocabFilter : 'all'}`}
            itemType={activeTab}
            category={activeTab === 'vocab' && vocabFilter !== 'all' ? vocabFilter : undefined}
          />
        </>
      )}

      {block === 'reinforcement' && <ReinforcementQueue />}
    </div>
  )
}

function ReinforcementQueue() {
  const [items, setItems] = useState<DueReinforcementItem[] | null>(null)
  const [index, setIndex] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const load = () => {
    setItems(null)
    setError(null)
    setIndex(0)
    reinforcementApi
      .getDue(5)
      .then(setItems)
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Error desconocido'))
  }

  useEffect(load, [])

  if (error) return <ErrorState message={error} onRetry={load} />
  if (!items) return <LoadingState label="Buscando errores para reforzar…" />
  if (items.length === 0) {
    return (
      <div className="border border-line bg-paper-raised px-5 py-8 text-center">
        <p className="text-ink-soft">
          No hay nada pendiente de refuerzo ahora mismo. Este bloque se rellena solo a partir de los errores que
          Claude detecta en tus sesiones de Reading, Writing y Speaking.
        </p>
        <button
          type="button"
          onClick={load}
          className="mt-3 border border-line px-3 py-1 font-mono text-xs uppercase tracking-wide text-ink-soft hover:text-ink"
        >
          Comprobar de nuevo
        </button>
      </div>
    )
  }
  if (index >= items.length) {
    return (
      <div className="border border-distinction bg-distinction/5 px-5 py-8 text-center">
        <p className="text-distinction">Ronda completada — {items.length} error(es) repasado(s).</p>
        <button
          type="button"
          onClick={load}
          className="mt-3 border border-ink px-4 py-1.5 font-mono text-xs uppercase tracking-wide hover:bg-ink hover:text-paper-raised"
        >
          Repasar más
        </button>
      </div>
    )
  }

  const current = items[index]
  return (
    <div className="grid gap-3">
      <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">
        {index + 1} / {items.length}
      </p>
      <ReinforcementExercise key={current.id} item={current} onDone={() => setIndex((i) => i + 1)} />
    </div>
  )
}

function PracticeQueue({
  itemType,
  category,
}: {
  itemType: LearningItemType
  category?: VocabCategoryFilter
}) {
  const [items, setItems] = useState<DueItem[] | null>(null)
  const [index, setIndex] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const load = () => {
    setItems(null)
    setError(null)
    setIndex(0)
    learningApi
      .getDue(itemType, 5, category)
      .then(setItems)
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : 'Error desconocido'))
  }

  useEffect(load, [itemType, category])

  if (error) return <ErrorState message={error} onRetry={load} />
  if (!items) return <LoadingState label="Preparando ejercicios…" />
  if (items.length === 0) {
    return (
      <div className="border border-line bg-paper-raised px-5 py-8 text-center">
        <p className="text-ink-soft">No hay ítems pendientes de repaso ahora mismo para este tipo.</p>
        <button
          type="button"
          onClick={load}
          className="mt-3 border border-line px-3 py-1 font-mono text-xs uppercase tracking-wide text-ink-soft hover:text-ink"
        >
          Comprobar de nuevo
        </button>
      </div>
    )
  }
  if (index >= items.length) {
    return (
      <div className="border border-distinction bg-distinction/5 px-5 py-8 text-center">
        <p className="text-distinction">Ronda completada — {items.length} ítem(s) repasado(s).</p>
        <button
          type="button"
          onClick={load}
          className="mt-3 border border-ink px-4 py-1.5 font-mono text-xs uppercase tracking-wide hover:bg-ink hover:text-paper-raised"
        >
          Repasar más
        </button>
      </div>
    )
  }

  const current = items[index]
  const advance = () => setIndex((i) => i + 1)

  return (
    <div className="grid gap-3">
      <p className="font-mono text-xs uppercase tracking-wide text-ink-faint">
        {index + 1} / {items.length}
      </p>
      {current.type === 'vocab' && <VocabExercise key={current.item_id} item={current} onDone={advance} />}
      {current.type === 'grammar' && <GrammarExercise key={current.item_id} item={current} onDone={advance} />}
      {(current.type === 'filler' || current.type === 'connector') && (
        <FillerExercise key={current.item_id} item={current} onDone={advance} />
      )}
      {current.type === 'pronunciation' && (
        <PronunciationExercise key={current.item_id} item={current} onDone={advance} />
      )}
    </div>
  )
}
