import { useEffect, useState } from 'react'
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition'

interface Props {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  disabled?: boolean
  placeholder?: string
  sendLabel?: string
  rows?: number
}

export function VoiceOrTextInput({
  value,
  onChange,
  onSend,
  disabled = false,
  placeholder = 'Escribe tu respuesta…',
  sendLabel = 'Enviar',
  rows = 3,
}: Props) {
  const [mode, setMode] = useState<'text' | 'voice'>('text')
  const recognition = useSpeechRecognition()

  useEffect(() => {
    if (mode === 'voice' && recognition.transcript) {
      onChange(recognition.transcript)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recognition.transcript])

  return (
    <div className="grid gap-2">
      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={() => setMode('text')}
          className={`border px-3 py-1 font-mono text-xs uppercase tracking-wide ${
            mode === 'text' ? 'border-seal text-seal' : 'border-line text-ink-soft hover:text-ink'
          }`}
        >
          Texto
        </button>
        <button
          type="button"
          onClick={() => setMode('voice')}
          disabled={!recognition.isSupported}
          className={`border px-3 py-1 font-mono text-xs uppercase tracking-wide disabled:cursor-not-allowed disabled:opacity-40 ${
            mode === 'voice' ? 'border-seal text-seal' : 'border-line text-ink-soft hover:text-ink'
          }`}
        >
          Voz{!recognition.isSupported && ' (no soportado)'}
        </button>

        {mode === 'voice' && (
          <button
            type="button"
            onClick={recognition.isListening ? recognition.stop : recognition.start}
            className={`ml-2 border px-3 py-1 font-mono text-xs uppercase tracking-wide ${
              recognition.isListening ? 'border-seal bg-seal text-paper-raised' : 'border-line text-ink-soft hover:text-ink'
            }`}
          >
            {recognition.isListening ? '● Grabando…' : '🎙 Hablar'}
          </button>
        )}
      </div>

      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        placeholder={placeholder}
        className="w-full resize-y border border-line bg-paper px-3 py-2 text-sm text-ink focus:border-ink"
      />

      <div className="flex justify-end">
        <button
          type="button"
          disabled={disabled || value.trim().length === 0}
          onClick={onSend}
          className="border border-seal bg-seal px-4 py-1.5 font-mono text-xs uppercase tracking-wide text-paper-raised transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {sendLabel}
        </button>
      </div>
    </div>
  )
}
