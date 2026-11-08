"use client";

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

type Theme = "dark" | "light";

interface ThemeContext {
  theme: Theme;
  toggle: () => void;
}

const Ctx = createContext<ThemeContext>({ theme: "dark", toggle: () => undefined });

export function useTheme() {
  return useContext(Ctx);
}

/** Reads the persisted theme or falls back to system preference. */
function resolveTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  const saved = localStorage.getItem("cp-theme");
  if (saved === "light" || saved === "dark") return saved;
  return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

function applyTheme(theme: Theme, animate: boolean) {
  const root = document.documentElement;
  root.classList.remove("dark", "light");
  root.classList.add(theme);
  if (animate) {
    root.classList.add("theme-ready");
  }
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>("dark");

  useEffect(() => {
    const t = resolveTheme();
    setTheme(t);
    applyTheme(t, false);
    // Allow transitions only after the first paint so there is no flash.
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        document.documentElement.classList.add("theme-ready");
      });
    });
  }, []);

  const toggle = useCallback(() => {
    setTheme((prev) => {
      const next: Theme = prev === "dark" ? "light" : "dark";
      localStorage.setItem("cp-theme", next);
      applyTheme(next, true);
      return next;
    });
  }, []);

  return <Ctx.Provider value={{ theme, toggle }}>{children}</Ctx.Provider>;
}

