import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Invest Immo Paris — Analyse de stratégies",
  description: "Comparaison de stratégies d'investissement immobilier à Paris",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className="min-h-screen bg-slate-50">{children}</body>
    </html>
  );
}
