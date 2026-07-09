import type { Band } from '../../types/reading'

const BAND_STYLES: Record<Band, string> = {
  Distinction: 'text-distinction border-distinction',
  Merit: 'text-merit border-merit',
  Pass: 'text-pass border-pass',
  'Not yet': 'text-fail border-fail',
}

export function ScoreBand({ band }: { band: Band }) {
  return (
    <span
      className={`inline-block border px-2 py-0.5 font-mono text-xs uppercase tracking-wider ${BAND_STYLES[band]}`}
    >
      {band}
    </span>
  )
}
