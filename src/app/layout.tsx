import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import ModalProvider from "@/components/ModalProvider";
import VanguardBubble from "@/components/VanguardBubble"; 
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Vanguard Scale | Infraestructura IA que Escala tu Operación Comercial",
  description: "Vanguard responde en 3 segundos, filtra curiosos y agenda citas de alto valor en tu calendario.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <ModalProvider>
          {children}
        </ModalProvider>
        {/* Aquí liberamos oficialmente al Dóberman */}
        <VanguardBubble />
      </body>
    </html>
  );
}