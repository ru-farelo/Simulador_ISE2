import type { MatchingExercise } from '../../types/reading'

interface Props {
  exercise: MatchingExercise
  value: Record<string, string>
  onChange: (value: Record<string, string>) => void
}

export function MatchingExerciseView({ exercise, value, onChange }: Props) {
  return (
    <div>
      <p className="text-sm text-ink-soft">{exercise.instructions}</p>
      <div className="mt-3 grid gap-3">
        {exercise.items.map((item) => (
          <div key={item.id} className="flex flex-wrap items-center gap-3 border border-line bg-paper px-3 py-2">
            <span className="flex-1 text-sm">{item.text}</span>
            <select
              value={value[item.id] ?? ''}
              onChange={(e) => onChange({ ...value, [item.id]: e.target.value })}
              className="border border-line bg-paper-raised px-2 py-1 font-mono text-sm"
            >
              <option value="" disabled>
                —
              </option>
              {exercise.options.map((opt) => (
                <option key={opt.id} value={opt.id}>
                  {opt.id} — {opt.text}
                </option>
              ))}
            </select>
          </div>
        ))}
      </div>
    </div>
  )
}
