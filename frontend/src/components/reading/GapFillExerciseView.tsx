import type { GapFillExercise } from '../../types/reading'

interface Props {
  exercise: GapFillExercise
  value: Record<string, string>
  onChange: (value: Record<string, string>) => void
}

export function GapFillExerciseView({ exercise, value, onChange }: Props) {
  return (
    <div>
      <p className="text-sm text-ink-soft">{exercise.instructions}</p>
      <div className="mt-3 grid gap-3">
        {exercise.items.map((item) => (
          <div key={item.id}>
            <p className="text-sm">{item.text}</p>
            <input
              type="text"
              value={value[item.id] ?? ''}
              onChange={(e) => onChange({ ...value, [item.id]: e.target.value })}
              className="mt-1 w-full border border-line bg-paper px-3 py-1.5 text-sm focus:border-ink"
            />
          </div>
        ))}
      </div>
    </div>
  )
}
