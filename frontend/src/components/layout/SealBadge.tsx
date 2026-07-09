interface SealBadgeProps {
  streakDays: number
}

export function SealBadge({ streakDays }: SealBadgeProps) {
  return (
    <div
      role="img"
      aria-label={`Racha actual: ${streakDays} ${streakDays === 1 ? 'día' : 'días'}`}
      className="relative flex h-20 w-20 shrink-0 -rotate-6 select-none items-center justify-center rounded-full border-[3px] border-seal text-seal"
    >
      <div className="absolute inset-[5px] rounded-full border border-dashed border-seal/60" />
      <div className="flex flex-col items-center leading-none">
        <span className="font-display text-2xl font-semibold">{streakDays}</span>
        <span className="mt-1 text-[0.55rem] font-semibold uppercase tracking-widest">
          {streakDays === 1 ? 'día' : 'días'}
        </span>
      </div>
    </div>
  )
}
