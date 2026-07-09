import type { ReactNode } from 'react'

interface PanelProps {
  title?: string
  children: ReactNode
  className?: string
}

export function Panel({ title, children, className = '' }: PanelProps) {
  return (
    <section className={`border border-line bg-paper-raised p-5 ${className}`}>
      {title && <h2 className="mb-4 font-mono text-xs uppercase tracking-[0.2em] text-ink-soft">{title}</h2>}
      {children}
    </section>
  )
}
