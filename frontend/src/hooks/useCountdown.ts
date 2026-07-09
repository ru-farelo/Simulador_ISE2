import { useEffect, useState } from 'react'

export function useCountdown(initialSeconds: number) {
  const [secondsLeft, setSecondsLeft] = useState(initialSeconds)
  const [isRunning, setIsRunning] = useState(false)

  useEffect(() => {
    if (!isRunning) return

    const id = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          setIsRunning(false)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(id)
  }, [isRunning])

  const start = () => setIsRunning(true)
  const pause = () => setIsRunning(false)
  const reset = (seconds: number = initialSeconds) => {
    setSecondsLeft(seconds)
    setIsRunning(false)
  }

  const minutes = Math.floor(secondsLeft / 60)
  const seconds = secondsLeft % 60
  const formatted = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`

  return {
    secondsLeft,
    isRunning,
    isExpired: secondsLeft === 0,
    formatted,
    start,
    pause,
    reset,
  }
}
