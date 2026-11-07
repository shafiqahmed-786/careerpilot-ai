import type { Metadata } from "next";
import { Outfit, Source_Serif_4 } from "next/font/google";

import { AppHeader } from "@/components/AppHeader";

import "./globals.css";

const outfit = Outfit({ subsets: ["latin"], variable: "--font-outfit" });
const sourceSerif = Source_Serif_4({ subsets: ["latin"], variable: "--font-serif" });

export const metadata: Metadata = {
  title: "CareerPilot AI",
  description: "Your career goal. A personalized roadmap. Measurable progress.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${outfit.variable} ${sourceSerif.variable} font-sans antialiased`}>
        <AppHeader />
        {children}
      </body>
    </html>
  );
}
