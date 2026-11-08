/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#e8eaee",
        paper: "#090b0f",
        surface: "#10131a",
        raised: "#161a23",
        line: "#232833",
        muted: "#8a93a3",
        accent: "#7c8bff",
        good: "#4ade80",
        warn: "#fbbf24",
        bad: "#f87171",
        // aliases kept so older class names do not break
        card: "#10131a",
        moss: "#7c8bff",
        clay: "#f87171",
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
