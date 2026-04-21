"use client";

type CounterButtonProps = {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
};

export function CounterButton({ label, value, onChange, min = 0 }: CounterButtonProps) {
  const increment = () => onChange(value + 1);
  const decrement = () => {
    if (value > min) onChange(value - 1);
  };

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium text-[var(--muted)] uppercase tracking-widest">
        {label}
      </label>
      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={decrement}
          className="flex min-h-[44px] min-w-[44px] h-14 w-14 items-center justify-center rounded-2xl bg-[var(--card-strong)] text-2xl font-bold ring-1 ring-black/10 dark:ring-white/10 hover:bg-red-500/10 hover:text-red-400 transition active:scale-95"
          aria-label={`Reducir ${label}`}
        >
          −
        </button>
        <span className="w-20 text-center text-4xl font-black tracking-tight">
          {value}
        </span>
        <button
          type="button"
          onClick={increment}
          className="flex min-h-[44px] min-w-[44px] h-14 w-14 items-center justify-center rounded-2xl bg-[var(--egg)] text-2xl font-bold text-[var(--primary-strong)] ring-1 ring-black/10 dark:ring-white/10 hover:brightness-105 transition active:scale-95"
          aria-label={`Aumentar ${label}`}
        >
          +
        </button>
      </div>
    </div>
  );
}