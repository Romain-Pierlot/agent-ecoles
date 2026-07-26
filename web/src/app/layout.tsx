// Remplacement de src/app/layout.tsx — chargement des polices de la refonte.
// Newsreader (sérif éditorial) + Hanken Grotesk (UI + chiffres) + Schibsted
// Grotesk (lettre de notation). Baloo / Figtree / Caveat / Geist retirés
// (Caveat = plus aucun manuscrit dans la refonte). Si des composants pas
// encore migrés lisent encore --font-baloo & co, les alias transitionnels
// de globals.css les font pointer vers les nouvelles polices.

import type { Metadata } from "next";
import Script from "next/script";
import { Newsreader, Hanken_Grotesk, Schibsted_Grotesk } from "next/font/google";
import { TopBar } from "@/components/TopBar";
import { Footer } from "@/components/Footer";
import "./globals.css";

const newsreader = Newsreader({
  variable: "--font-newsreader",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  style: ["normal", "italic"],
});

const hanken = Hanken_Grotesk({
  variable: "--font-hanken",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

const schibsted = Schibsted_Grotesk({
  variable: "--font-schibsted",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

export const metadata: Metadata = {
  title: "agent-ecoles",
  description: "Agent conversationnel d'aide au choix de collège — test local",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="fr"
      className={`${newsreader.variable} ${hanken.variable} ${schibsted.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <TopBar />
        {children}
        <Footer />
        {process.env.NEXT_PUBLIC_UMAMI_WEBSITE_ID && (
          <Script
            src={process.env.NEXT_PUBLIC_UMAMI_SRC}
            data-website-id={process.env.NEXT_PUBLIC_UMAMI_WEBSITE_ID}
            strategy="afterInteractive"
          />
        )}
      </body>
    </html>
  );
}
