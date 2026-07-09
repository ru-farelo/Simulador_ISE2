import { useEffect, useRef, useState } from 'react'
import { useSpeechSynthesis } from '../../hooks/useSpeechSynthesis'

interface Props {
  text: string
  autoPlay?: boolean
}

/**
 * Renders an examiner utterance the way the real exam works: heard, not
 * read. Plays once automatically when it first appears, text stays hidden
 * until the candidate explicitly asks to see it (didn't catch it by ear).
 */
export function SpokenLine({ text, autoPlay = true }: Props) {
  const synthesis = useSpeechSynthesis()
  const [revealed, setRevealed] = useState(false)
  const hasAutoPlayed = useRef(false)

  useEffect(() => {
    if (autoPlay && synthesis.isSupported && !hasAutoPlayed.current) {
      hasAutoPlayed.current = true
      synthesis.speak(text)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => (synthesis.isSpeaking ? synthesis.cancel() : synthesis.speak(text))}
          disabled={!synthesis.isSupported}
          className="border border-line px-2 py-0.5 font-mono text-[0.65rem] uppercase tracking-wide text-ink-soft hover:text-ink disabled:cursor-not-allowed disabled:opacity-40"
        >
          {synthesis.isSpeaking ? '⏹ Detener' : '🔊 Escuchar de nuevo'}
        </button>
        {!revealed && (
          <button
            type="button"
            onClick={() => setRevealed(true)}
            className="border border-line px-2 py-0.5 font-mono text-[0.65rem] uppercase tracking-wide text-ink-soft hover:text-ink"
          >
            No lo he entendido — mostrar texto
          </button>
        )}
      </div>
      {revealed ? (
        <p className="mt-2 text-ink">{text}</p>
      ) : (
        <p className="mt-2 italic text-ink-faint">(audio)</p>
      )}
    </div>
  )
}
