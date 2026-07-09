import { useCallback, useEffect, useState } from 'react'

interface SpeakOptions {
  rate?: number
  onEnd?: () => void
}

interface UseSpeechSynthesis {
  isSupported: boolean
  isSpeaking: boolean
  speak: (text: string, options?: SpeakOptions) => void
  cancel: () => void
}

export function useSpeechSynthesis(): UseSpeechSynthesis {
  const isSupported = typeof window !== 'undefined' && 'speechSynthesis' in window
  const [isSpeaking, setIsSpeaking] = useState(false)

  const speak = useCallback(
    (text: string, options?: SpeakOptions) => {
      if (!isSupported || !text.trim()) return
      window.speechSynthesis.cancel()
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = 'en-US'
      utterance.rate = options?.rate ?? 1
      utterance.onend = () => {
        setIsSpeaking(false)
        options?.onEnd?.()
      }
      utterance.onerror = () => setIsSpeaking(false)
      setIsSpeaking(true)
      window.speechSynthesis.speak(utterance)
    },
    [isSupported],
  )

  const cancel = useCallback(() => {
    if (!isSupported) return
    window.speechSynthesis.cancel()
    setIsSpeaking(false)
  }, [isSupported])

  useEffect(() => {
    return () => {
      if (isSupported) window.speechSynthesis.cancel()
    }
  }, [isSupported])

  return { isSupported, isSpeaking, speak, cancel }
}
