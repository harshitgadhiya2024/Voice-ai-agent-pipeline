import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Toaster } from "sonner";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Voice AI Demo Studio — 8 production-grade agents",
  description:
    "Real estate, restaurant, e-commerce, recruitment, hotel, banking, debt collection, and travel Voice AI demos — built on LangGraph + Sarvam + Groq.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.className} min-h-dvh overflow-x-hidden bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-zinc-900 via-zinc-950 to-black text-zinc-100 antialiased`}
      >
        {children}
        <Toaster
          theme="dark"
          richColors
          position="top-right"
          closeButton
        />
      </body>
    </html>
  );
}
