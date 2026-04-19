"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

/** Swap this src when your final Loom embed URL is ready */
const LOOM_EMBED_SRC =
  "https://www.loom.com/embed/8d0764c0e97745f793f6a44afa25b7b7";

const CALENDLY_HREF = "https://calendly.com/andymoreno208/30min";

const topContent = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2,
      delayChildren: 0.05,
    },
  },
};

const topItem = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] as const },
  },
};

export default function Hero() {
  return (
    <section className="relative min-h-screen overflow-hidden bg-[#050505] pt-24 pb-20 lg:pt-28">
      {/* Center-top radial backlight */}
      <div
        className="pointer-events-none absolute left-1/2 top-0 h-[min(75vh,680px)] w-[min(110vw,960px)] -translate-x-1/2 rounded-full bg-gradient-to-b from-violet-600/30 via-indigo-600/25 to-transparent blur-3xl opacity-20"
        aria-hidden
      />

      {/* Subtle grid */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.035]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)",
          backgroundSize: "56px 56px",
        }}
      />

      <div className="relative z-10 mx-auto max-w-6xl px-6">
        <motion.div
          className="flex flex-col items-center text-center"
          variants={topContent}
          initial="hidden"
          animate="visible"
        >
          <motion.div variants={topItem}>
            <div className="mb-6 inline-flex items-center justify-center rounded-full border border-white/10 bg-white/[0.05] px-4 py-1.5 text-xs font-medium text-zinc-300 shadow-[0_0_28px_rgba(124,58,237,0.18)] backdrop-blur-md sm:text-sm">
              🟢 Infraestructura Operativa | Latencia {"<"} 1.2s
            </div>
          </motion.div>

          <motion.h1
            variants={topItem}
            className="mb-6 max-w-4xl text-4xl font-bold leading-[1.08] tracking-tight sm:text-5xl md:text-6xl lg:text-7xl"
          >
            <span className="bg-gradient-to-r from-white via-purple-200 to-purple-500 bg-clip-text text-transparent">
              Infraestructura RAG de Latencia Cero para B2B
            </span>
          </motion.h1>

          <motion.p
            variants={topItem}
            className="mb-10 max-w-2xl text-base leading-relaxed text-gray-400 sm:text-lg"
          >
            Deje de perder leads. Diseñamos y desplegamos motores de IA
            privados y arquitecturas n8n que automatizan su ciclo de ventas en
            48 horas.
          </motion.p>

          <motion.div
            variants={topItem}
            className="flex w-full flex-col items-center justify-center gap-3 sm:flex-row sm:gap-4"
          >
            <motion.a
              href={CALENDLY_HREF}
              target="_blank"
              rel="noopener noreferrer"
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.98 }}
              className="inline-flex w-full min-w-[240px] items-center justify-center rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-8 py-4 text-base font-semibold text-white shadow-[0_0_32px_rgba(124,58,237,0.45),0_0_64px_rgba(79,70,229,0.2)] transition-shadow hover:shadow-[0_0_40px_rgba(124,58,237,0.55)] sm:w-auto"
            >
              Solicitar Auditoría ($500)
            </motion.a>
            <a
              href="#super-flujo"
              className="group inline-flex w-full min-w-[240px] items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/[0.05] px-6 py-4 text-base font-medium text-zinc-200 backdrop-blur-md transition-colors hover:border-white/20 hover:bg-white/[0.08] sm:w-auto"
            >
              Ver Arquitectura
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </a>
          </motion.div>
        </motion.div>

        {/* Loom — premium window + bento badges */}
        <motion.div
          className="relative mx-auto mt-14 w-full max-w-5xl"
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: 0.7,
            delay: 1.15,
            ease: [0.22, 1, 0.36, 1],
          }}
        >
          {/* Bento badges — overlap video frame edges */}
          <div
            className="pointer-events-none absolute -left-1 top-2 z-20 sm:left-0 sm:top-4 md:-left-2"
            aria-hidden
          >
            <div className="pointer-events-auto rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2 text-[11px] font-medium text-zinc-100 shadow-lg backdrop-blur-md sm:text-xs">
              🔌 API WhatsApp: Conectada
            </div>
          </div>
          <div
            className="pointer-events-none absolute -right-1 top-2 z-20 sm:right-0 sm:top-4 md:-right-2"
            aria-hidden
          >
            <div className="pointer-events-auto rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2 text-[11px] font-medium text-zinc-100 shadow-lg backdrop-blur-md sm:text-xs">
              🗄️ Memoria Supabase: 100%
            </div>
          </div>
          <div
            className="pointer-events-none absolute -bottom-1 right-2 z-20 sm:bottom-3 sm:right-4 md:right-2"
            aria-hidden
          >
            <div className="pointer-events-auto rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2 text-[11px] font-medium text-zinc-100 shadow-lg backdrop-blur-md sm:text-xs">
              ⚡ OpenAI: 1.1s latency
            </div>
          </div>

          <div
            className="overflow-hidden rounded-2xl bg-white/5 shadow-[0_0_80px_rgba(168,85,247,0.15)] ring-1 ring-white/10 backdrop-blur-xl"
          >
            {/* Minimal browser / window chrome */}
            <div className="flex items-center gap-2 border-b border-white/10 bg-black/20 px-4 py-3">
              <div className="flex gap-1.5">
                <span className="h-3 w-3 rounded-full bg-red-500/80" />
                <span className="h-3 w-3 rounded-full bg-amber-500/80" />
                <span className="h-3 w-3 rounded-full bg-emerald-500/80" />
              </div>
              <div className="ml-2 flex-1 truncate rounded-md bg-white/5 px-3 py-1 text-left text-[11px] text-zinc-500 sm:text-xs">
                vanguardscale.com · demo en vivo
              </div>
            </div>

            <div className="aspect-video w-full bg-black/40">
              <iframe
                src={LOOM_EMBED_SRC}
                title="Vanguard Scale — demo Loom"
                allowFullScreen
                className="h-full w-full"
              />
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
