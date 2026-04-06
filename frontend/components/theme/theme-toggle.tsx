"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";

export function ThemeToggle() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted) {
    return (
      <button className="flex h-11 w-11 items-center justify-center rounded-2xl border border-black/10 bg-white text-black/70 shadow-sm dark:border-white/10 dark:bg-neutral-900 dark:text-white/70">
        <Sun className="h-5 w-5" />
      </button>
    );
  }

  const currentTheme = theme === "system" ? resolvedTheme : theme;
  const isDark = currentTheme === "dark";

  return (
    <button
      onClick={() => setTheme(isDark ? "light" : "dark")}
      aria-label={isDark ? "Cambiar a modo claro" : "Cambiar a modo oscuro"}
      title={isDark ? "Modo claro" : "Modo oscuro"}
      className="flex h-11 w-11 items-center justify-center rounded-2xl border border-black/10 bg-white text-black/80 shadow-sm transition hover:scale-[1.03] hover:shadow-md dark:border-white/10 dark:bg-neutral-900 dark:text-white/80"
    >
      {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </button>
  );
}