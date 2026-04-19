"use client";

import dynamic from "next/dynamic";
import { Suspense } from "react";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

const SPLINE_SCENE =
  "https://prod.spline.design/6Wq1Q7YGyM-iab9i/scene.splinecode";

const Spline = dynamic(() => import("@splinetool/react-spline"), {
  ssr: false,
  loading: () => (
    <div
      className="flex h-full min-h-[280px] w-full items-center justify-center rounded-3xl bg-gradient-to-br from-indigo-950/30 via-[#050505] to-violet-950/20 lg:min-h-[520px]"
      aria-hidden
    >
      <div className="h-10 w-10 animate-pulse rounded-full border-2 border-white/10 border-t-indigo-400" />
    </div>
  ),
});

const container = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2,
      delayChildren: 0.06,
    },
  },
};

const item = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] as const },
  },
};

const floatTransition = {
  y: {
    duration: 5,
    repeat: Infinity,
    ease: "easeInOut" as const,
  },
};

function SplineCanvas() {
  return (
    <div className="absolute inset-0 hidden lg:block">
      <Suspense
        fallback={
          <div className="flex h-full min-h-[520px] w-full items-center justify-center">
            <div className="h-10 w-10 animate-pulse rounded-full border-2 border-white/10 border-t-indigo-400" />
          </div>
        }
      >
        <Spline
          scene={SPLINE_SCENE}
          className="!absolute inset-0 !h-full !w-full scale-[1.02]"
        />
      </Suspense>
    </div>
  );
}

export default function Hero() {
  return (
    <section className="relative min-h-screen overflow-hidden bg-[#050505] pt-24 pb-16 lg:pt-28">
      {/* Subtle grid + ambient glow */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,.12) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.12) 1px, transparent 1px)",
          backgroundSize: "56px 56px",
        }}
      />
      <div className="pointer-events-none absolute -top-32 right-0 h-[420px] w-[420px] rounded-full bg-violet-600/15 blur-[120px]" />
      <div className="pointer-events-none absolute bottom-0 left-1/4 h-[320px] w-[320px] rounded-full bg-indigo-600/10 blur-[100px]" />

      <div className="relative z-10 mx-auto grid max-w-7xl grid-cols-1 items-center gap-12 px-6 lg:grid-cols-2 lg:gap-10">
        {/* Left: copy + CTAs */}
        <motion.div
          className="flex max-w-xl flex-col text-left"
          variants={container}
          initial="hidden"
          animate="visible"
        >
          <motion.div variants={item}>
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.05] px-4 py-1.5 text-xs font-medium text-zinc-300 shadow-[0_0_24px_rgba(124,58,237,0.15)] backdrop-blur-md sm:text-sm">
              🟢 Infraestructura Operativa | Latencia {"<"} 1.2s
            </div>
          </motion.div>

          <motion.h1
            variants={item}
            className="mb-5 text-4xl font-bold leading-[1.05] tracking-tight text-white sm:text-5xl md:text-6xl lg:text-[3.35rem] xl:text-7xl"
          >
            Infraestructura{" "}
            <span className="bg-gradient-to-r from-indigo-300 via-violet-400 to-fuchsia-400 bg-clip-text text-transparent">
              RAG
            </span>{" "}
            de Latencia{" "}
            <span className="bg-gradient-to-r from-emerald-300 via-cyan-300 to-indigo-300 bg-clip-text text-transparent">
              Cero
            </span>{" "}
            para B2B
          </motion.h1>

          <motion.p
            variants={item}
            className="mb-9 max-w-lg text-base leading-relaxed text-gray-400 sm:text-lg"
          >
            Deje de perder leads. Diseñamos y desplegamos motores de IA
            privados y arquitecturas n8n que automatizan su ciclo de ventas en
            48 horas.
          </motion.p>

          <motion.div
            variants={item}
            className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4"
          >
            <motion.a
              href="https://calendly.com/andymoreno208/30min"
              target="_blank"
              rel="noopener noreferrer"
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.98 }}
              className="inline-flex items-center justify-center rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-8 py-4 text-base font-semibold text-white shadow-[0_0_32px_rgba(124,58,237,0.45),0_0_64px_rgba(79,70,229,0.2)] transition-shadow hover:shadow-[0_0_40px_rgba(124,58,237,0.55)]"
            >
              Solicitar Auditoría ($500)
            </motion.a>
            <a
              href="#super-flujo"
              className="group inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/[0.05] px-6 py-4 text-base font-medium text-zinc-200 backdrop-blur-md transition-colors hover:border-white/20 hover:bg-white/[0.08]"
            >
              Ver Arquitectura
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </a>
          </motion.div>
        </motion.div>

        {/* Right: Spline + floating cards */}
        <div className="relative mx-auto w-full max-w-xl lg:mx-0 lg:max-w-none">
          {/* Mobile-only backdrop when Spline is hidden */}
          <div
            className="pointer-events-none absolute inset-0 rounded-3xl bg-gradient-to-br from-indigo-950/50 via-transparent to-violet-950/30 lg:hidden"
            aria-hidden
          />

          <SplineCanvas />

          <div className="relative min-h-[300px] w-full lg:min-h-[560px]">
            {/* Top right card */}
            <motion.div
              className="absolute right-2 top-6 z-20 max-w-[220px] rounded-2xl border border-white/10 bg-white/[0.05] p-3.5 shadow-xl backdrop-blur-md sm:right-4 sm:top-10 sm:max-w-[260px] sm:p-4"
              animate={{ y: [0, -10, 0] }}
              transition={{ ...floatTransition, delay: 0 }}
            >
              <div className="flex items-center gap-2.5">
                <span
                  className="h-2 w-2 shrink-0 rounded-full bg-[#00FF00] shadow-[0_0_12px_#00FF00]"
                  aria-hidden
                />
                <span className="text-sm font-medium text-zinc-100">
                  API WhatsApp Conectada
                </span>
              </div>
            </motion.div>

            {/* Bottom left card */}
            <motion.div
              className="absolute bottom-10 left-2 z-20 max-w-[240px] rounded-2xl border border-white/10 bg-white/[0.05] p-3.5 shadow-xl backdrop-blur-md sm:bottom-14 sm:left-4 sm:max-w-[280px] sm:p-4"
              animate={{ y: [0, -10, 0] }}
              transition={{ ...floatTransition, delay: 0.6 }}
            >
              <p className="text-sm font-medium text-zinc-100">
                Vector Database Sync…{" "}
                <span className="bg-gradient-to-r from-emerald-300 to-cyan-300 bg-clip-text font-semibold text-transparent">
                  100%
                </span>
              </p>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
}
