export default function ResultsSection() {
  return (
    <section id="resultados" className="px-6 py-24">
      <div className="mx-auto max-w-7xl">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            Resultados
          </h2>
          <p className="mx-auto max-w-2xl text-lg text-white/80">
            Facturación verificable. Citas agendadas. Infraestructura que
            demuestra su ROI desde el día uno.
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-2">
          {/* Stripe/Payoneer placeholder */}
          <div className="overflow-hidden rounded-2xl border border-white/10 bg-card-bg transition-all hover:border-cyan-500/30">
            <div className="border-b border-white/5 bg-white/[0.02] px-6 py-4">
              <h3 className="font-semibold text-white">
                Facturación Stripe / Payoneer
              </h3>
              <p className="text-sm text-white/60">
                Capturas de pantalla de ingresos procesados
              </p>
            </div>
            <div className="flex aspect-[16/9] items-center justify-center bg-gradient-to-br from-slate-900/80 to-slate-800/50 p-8">
              <div className="flex flex-col items-center gap-4 text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-white/5 ring-2 ring-dashed ring-white/20">
                  <svg
                    className="h-8 w-8 text-white/40"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                    />
                  </svg>
                </div>
                <p className="text-sm font-medium text-white/70">
                  Placeholder: Captura de Stripe / Payoneer
                </p>
                <p className="text-xs text-white/50">
                  Añade screenshots de facturación para social proof
                </p>
              </div>
            </div>
          </div>

          {/* Calendly appointments placeholder */}
          <div className="overflow-hidden rounded-2xl border border-white/10 bg-card-bg transition-all hover:border-cyan-500/30">
            <div className="border-b border-white/5 bg-white/[0.02] px-6 py-4">
              <h3 className="font-semibold text-white">
                Reportes de Citas Calendly
              </h3>
              <p className="text-sm text-white/60">
                Citas agendadas por la infraestructura IA
              </p>
            </div>
            <div className="flex aspect-[16/9] items-center justify-center bg-gradient-to-br from-slate-900/80 to-slate-800/50 p-8">
              <div className="flex flex-col items-center gap-4 text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-white/5 ring-2 ring-dashed ring-white/20">
                  <svg
                    className="h-8 w-8 text-white/40"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                    />
                  </svg>
                </div>
                <p className="text-sm font-medium text-white/70">
                  Placeholder: Reporte Calendly
                </p>
                <p className="text-xs text-white/50">
                  Añade capturas de citas agendadas automáticamente
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-12 text-center">
          <a
            href="https://calendly.com/andymoreno208/30min"
            target="_blank"
            rel="noopener noreferrer"
            className="cta-primary animate-glow inline-block rounded-full px-8 py-4 text-base font-semibold text-white transition-transform hover:scale-105"
          >
            Agendar Auditoría de Escalamiento
          </a>
        </div>
      </div>
    </section>
  );
}
