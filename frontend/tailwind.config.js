/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Each color is defined as an RGB channel variable so Tailwind's
        // opacity modifiers (e.g. bg-accent/10) work correctly.
        ink:     ({ opacityValue }) => opacityValue !== undefined ? `rgba(var(--color-ink-rgb), ${opacityValue})` : "rgb(var(--color-ink-rgb))",
        paper:   ({ opacityValue }) => opacityValue !== undefined ? `rgba(var(--color-paper-rgb), ${opacityValue})` : "rgb(var(--color-paper-rgb))",
        surface: ({ opacityValue }) => opacityValue !== undefined ? `rgba(var(--color-surface-rgb), ${opacityValue})` : "rgb(var(--color-surface-rgb))",
        raised:  ({ opacityValue }) => opacityValue !== undefined ? `rgba(var(--color-raised-rgb), ${opacityValue})` : "rgb(var(--color-raised-rgb))",
        line:    ({ opacityValue }) => opacityValue !== undefined ? `rgba(var(--color-line-rgb), ${opacityValue})` : "rgb(var(--color-line-rgb))",
        muted:   ({ opacityValue }) => opacityValue !== undefined ? `rgba(var(--color-muted-rgb), ${opacityValue})` : "rgb(var(--color-muted-rgb))",
        accent:  ({ opacityValue }) => opacityValue !== undefined ? `rgba(var(--color-accent-rgb), ${opacityValue})` : "rgb(var(--color-accent-rgb))",
        good:    ({ opacityValue }) => opacityValue !== undefined ? `rgba(var(--color-good-rgb), ${opacityValue})` : "rgb(var(--color-good-rgb))",
        warn:    ({ opacityValue }) => opacityValue !== undefined ? `rgba(var(--color-warn-rgb), ${opacityValue})` : "rgb(var(--color-warn-rgb))",
        bad:     ({ opacityValue }) => opacityValue !== undefined ? `rgba(var(--color-bad-rgb), ${opacityValue})` : "rgb(var(--color-bad-rgb))",
        // aliases kept so older class names do not break
        card: ({ opacityValue }) => opacityValue !== undefined ? `rgba(var(--color-surface-rgb), ${opacityValue})` : "rgb(var(--color-surface-rgb))",
        moss: ({ opacityValue }) => opacityValue !== undefined ? `rgba(var(--color-accent-rgb), ${opacityValue})` : "rgb(var(--color-accent-rgb))",
        clay: ({ opacityValue }) => opacityValue !== undefined ? `rgba(var(--color-bad-rgb), ${opacityValue})` : "rgb(var(--color-bad-rgb))",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
        serif: ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      keyframes: {
        fadeIn: { from: { opacity: "0", transform: "translateY(4px)" }, to: { opacity: "1", transform: "none" } },
        shimmer: { "100%": { transform: "translateX(100%)" } },
        dots: { "0%, 80%, 100%": { opacity: "0.2" }, "40%": { opacity: "1" } },
      },
      animation: {
        "fade-in": "fadeIn 0.25s ease-out both",
        dots: "dots 1.2s infinite ease-in-out",
      },
    },
  },
  plugins: [],
};
