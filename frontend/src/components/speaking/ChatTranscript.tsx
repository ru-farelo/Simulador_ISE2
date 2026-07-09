import { SpokenLine } from './SpokenLine'
import type { ConversationTurn } from '../../types/speaking'

export function ChatTranscript({ turns }: { turns: ConversationTurn[] }) {
  return (
    <div className="flex flex-col gap-3">
      {turns.map((turn, idx) => (
        <div key={idx} className={`flex ${turn.role === 'candidate' ? 'justify-end' : 'justify-start'}`}>
          <div
            className={`max-w-[85%] border px-4 py-2 text-sm ${
              turn.role === 'candidate' ? 'border-seal/40 bg-paper' : 'border-line bg-paper-raised'
            }`}
          >
            <span className="mb-1 block font-mono text-[0.65rem] uppercase tracking-wide text-ink-faint">
              {turn.role === 'examiner' ? 'Examinador' : 'Tú'}
            </span>
            {turn.role === 'examiner' ? <SpokenLine text={turn.text} /> : <p className="text-ink">{turn.text}</p>}
          </div>
        </div>
      ))}
    </div>
  )
}
