// ECCRP Root Layout
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ECCRP — Election Compliance & Candidate Readiness Platform",
  description: "India's premier AI-powered election compliance platform for candidates, parties, lawyers, and consultants.",
  keywords: ["election compliance", "India elections", "candidate eligibility", "MCC", "affidavit", "ECI"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
