import { useCallback, useEffect, useRef, useState } from 'react'

// The Web Speech API has no stable TypeScript lib types across browsers,
// so this hook deliberately types the recognizer as `any` at the boundary.
type SpeechRecognitionInstance = any

function getRecognitionConstructor(): (new () => SpeechRecognitionInstance) | undefined {
  if (typeof window === 'undefined') return undefined
  return (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition
}

interface UseSpeechRecognition {
  isSupported: boolean
  isListening: boolean
  transcript: string
  start: () => void
  stop: () => void
  reset: () => void
}

export function useSpeechRecognition(): UseSpeechRecognition {
  const RecognitionCtor = getRecognitionConstructor()
  const isSupported = Boolean(RecognitionCtor)

  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null)
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')

  useEffect(() => {
    if (!RecognitionCtor) return

    const recognition = new RecognitionCtor()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'en-US'

    recognition.onresult = (event: any) => {
      let combined = ''
      for (let i = 0; i < event.results.length; i++) {
        combined += event.results[i][0].transcript
      }
      setTranscript(combined)
    }
    recognition.onend = () => setIsListening(false)

    recognitionRef.current = recognition

    return () => {
      recognition.onresult = null
      recognition.onend = null
      recognition.abort()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const start = useCallback(() => {
    if (!recognitionRef.current) return
    setTranscript('')
    recognitionRef.current.start()
    setIsListening(true)
  }, [])

  const stop = useCallback(() => {
    recognitionRef.current?.stop()
    setIsListening(false)
  }, [])

  const reset = useCallback(() => setTranscript(''), [])

  return { isSupported, isListening, transcript, start, stop, reset }
}
