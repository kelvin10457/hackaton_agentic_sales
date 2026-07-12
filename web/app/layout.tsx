import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: {
    default: "Futuro Academy",
    template: "%s · Futuro Academy",
  },
  description:
    "Educación financiera con un agente de IA supervisado: capta, califica y educa prospectos — un humano aprueba cada comunicación.",
};

export const viewport: Viewport = {
  themeColor: "#031B4E",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" className={inter.variable}>
      <body className="font-sans">{children}</body>
    </html>
  );
}
