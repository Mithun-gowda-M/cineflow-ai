import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "CINEFLOW AI — Your AI. Your Story. Your Cinema.",
  description:
    "International-grade, local-first AI video production studio. Transform raw footage and photos into festival-worthy cinematic stories with intelligent scene detection, beat-synced cuts, and multi-track rendering.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-cine-black text-gray-100 antialiased selection:bg-cine-gold-500/30 selection:text-cine-gold-300">
        <Navbar />
        <main className="min-h-[calc(100vh-4rem)]">{children}</main>
      </body>
    </html>
  );
}

