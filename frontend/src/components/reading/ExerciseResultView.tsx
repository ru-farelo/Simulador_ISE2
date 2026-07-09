import type { ExerciseResult } from '../../types/reading'

export function ExerciseResultView({ result }: { result: ExerciseResult }) {
  return (
    <div className="border border-line p-4">
      <div className="flex items-center justify-between">
        <h4 className="font-mono text-xs uppercase tracking-wide text-ink-soft">{result.label}</h4>
        <span className="font-mono text-sm">
          {result.correct_count}/{result.total_count}
        </span>
      </div>
      <ul className="mt-3 grid gap-2">
        {result.items.map((item) => (
          <li key={item.id} className="flex items-start gap-2 text-sm">
            <span className={item.correct ? 'text-distinction' : 'text-fail'} aria-hidden="true">
              {item.correct ? '✓' : '✗'}
            </span>
            <span>
              <span className="mr-1 font-mono text-ink-faint">{item.id}</span>
              {!item.correct && item.expected && (
                <span className="text-ink-soft">Esperado: {item.expected}. </span>
              )}
              {item.comment && <span className="text-ink-soft">{item.comment}</span>}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
