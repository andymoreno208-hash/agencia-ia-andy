export default function ScreenshotCards() {
  return (
    <section id="capturas" className="px-6 py-16">
      <div className="mx-auto max-w-5xl">
        <div className="mb-12 text-center">
          <h2 className="mb-3 text-2xl font-bold sm:text-3xl">
            Prueba visual
          </h2>
          <p className="mx-auto max-w-xl text-text-secondary">
            Conversaciones en tiempo real y resultados verificables
          </p>
        </div>

        <div className="grid items-start gap-6 sm:gap-8 lg:grid-cols-2">
          {/* WhatsApp */}
          <div className="h-fit overflow-hidden rounded-2xl border border-white/10 bg-card-bg transition-all hover:border-cyan-500/30">
            <div className="border-b border-white/5 bg-white/[0.02] px-5 py-4">
              <h3 className="font-semibold text-white">WhatsApp</h3>
              <p className="text-sm text-text-secondary">
                Capturas de conversaciones con el agente IA
              </p>
            </div>
            <div className="bg-gradient-to-br from-slate-900/80 to-slate-800/50 p-6">
              <img
                src="/capturas/whatsapp.png"
                alt="Captura de WhatsApp con conversaciones reales"
                className="w-full h-auto object-cover rounded-xl shadow-2xl border border-gray-800"
                loading="lazy"
              />
            </div>
          </div>

          {/* Evidencia */}
          <div className="h-fit overflow-hidden rounded-2xl border border-white/10 bg-card-bg transition-all hover:border-cyan-500/30">
            <div className="border-b border-white/5 bg-white/[0.02] px-5 py-4">
              <h3 className="font-semibold text-white">Evidencia</h3>
              <p className="text-sm text-text-secondary">
                Facturación, citas agendadas y métricas
              </p>
            </div>
            <div className="bg-gradient-to-br from-slate-900/80 to-slate-800/50 p-6">
              <img
                src="/capturas/supabase.png"
                alt="Captura de Supabase con evidencia verificable"
                className="w-full h-auto object-cover rounded-xl shadow-2xl border border-gray-800"
                loading="lazy"
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
