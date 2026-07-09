import type { MultiSelectExercise } from '../../types/reading'

interface Props {
  exercise: MultiSelectExercise
  value: string[]
  onChange: (value: string[]) => void
}

export function MultiSelectExerciseView({ exercise, value, onChange }: Props) {
  const toggle = (id: string) => {
    if (value.includes(id)) {
      onChange(value.filter((v) => v !== id))
    } else if (value.length < exercise.select_count) {
      onChange([...value, id])
    }
  }

  return (
    <div>
      <p className="text-sm text-ink-soft">
        {exercise.instructions} ({value.length}/{exercise.select_count} seleccionadas)
      </p>
      <div className="mt-3 grid gap-2">
        {exercise.options.map((opt) => {
          const checked = value.includes(opt.id)
          const disabled = !checked && value.length >= exercise.select_count
          return (
            <label
              key={opt.id}
              className={`flex items-center gap-3 border px-3 py-2 text-sm ${
                checked ? 'border-seal' : 'border-line'
              } ${disabled ? 'opacity-50' : 'cursor-pointer'}`}
            >
              <input type="checkbox" checked={checked} disabled={disabled} onChange={() => toggle(opt.id)} />
              <span>{opt.text}</span>
            </label>
          )
        })}
      </div>
    </div>
  )
}
