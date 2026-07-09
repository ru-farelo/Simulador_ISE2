import type { TrueFalseExercise } from '../../types/reading'

interface Props {
  exercise: TrueFalseExercise
  value: Record<string, boolean>
  onChange: (value: Record<string, boolean>) => void
}

export function TrueFalseExerciseView({ exercise, value, onChange }: Props) {
  return (
    <div>
      <p className="text-sm text-ink-soft">{exercise.instructions}</p>
      <div className="mt-3 grid gap-3">
        {exercise.statements.map((statement) => (
          <div
            key={statement.id}
            className="flex flex-wrap items-center justify-between gap-3 border border-line bg-paper px-3 py-2"
          >
            <span className="flex-1 text-sm">{statement.text}</span>
            <div className="flex gap-1">
              {([true, false] as const).map((boolValue) => {
                const isSelected = value[statement.id] === boolValue
                return (
                  <button
                    key={String(boolValue)}
                    type="button"
                    onClick={() => onChange({ ...value, [statement.id]: boolValue })}
                    className={`border px-3 py-1 font-mono text-xs uppercase tracking-wide ${
                      isSelected ? 'border-seal bg-seal text-paper-raised' : 'border-line text-ink-soft hover:text-ink'
                    }`}
                  >
                    {boolValue ? 'True' : 'False'}
                  </button>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
