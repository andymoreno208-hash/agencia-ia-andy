import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import ModalProvider from "@/components/ModalProvider";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Alex IA | Tu Socio de Ventas con Inteligencia Artificial",
  description:
    "Alex responde en 3 segundos, filtra curiosos y agenda citas de alto valor en tu calendario. Automatización de WhatsApp para clínicas, inmobiliarias y agencias en Ecuador.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ModalProvider>{children}</ModalProvider>
      </body>
    </html>
  );
}
