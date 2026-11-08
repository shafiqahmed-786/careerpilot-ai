import type { Metadata } from "next";
import { Inter } from "next/font/google";

import "./globals.css";
import { ThemeProvider } from "@/lib/theme";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "CareerPilot AI",
  description: "AI career intelligence: understand your skills, plan your learning, get mentored as you progress.",
};

/** Blocking inline script — runs before React hydrates so the correct theme
 *  class is set on <html> before the first paint. Prevents any flash. */
const themeScript = `
(function(){
  try {
    var s = localStorage.getItem('cp-theme');
    var t = (s === 'light' || s === 'dark') ? s
          : (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
    document.documentElement.classList.add(t);
  } catch(e){}
})();
`.trim();

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* eslint-disable-next-line @next/next/no-sync-scripts */}
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className={`${inter.variable} font-sans antialiased`}>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
