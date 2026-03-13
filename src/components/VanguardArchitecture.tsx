const superFlujoPilares = [
  {
    numero: "01",
    title: "Inyector RAG",
    subtitle: "Memoria Perfecta",
    description:
      "Tu infraestructura aprende de cada documento, FAQ y caso de éxito. RAG multi-tenant garantiza que cada cliente corporativo tenga su base de conocimiento aislada. Cero confusión entre inmobiliarias, clínicas o agencias.",
    icon: (
      <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
      </svg>
    ),
  },
  {
    numero: "02",
    title: "Reloj Maestro",
    subtitle: "Cero No-Shows",
    description:
      "Integración nativa con Google Calendar. El flujo lee tu disponibilidad en tiempo real, envía recordatorios automáticos y rellena huecos con reagendamientos inteligentes. Tu agenda se optimiza sola.",
    icon: (
      <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    numero: "03",
    title: "Dóberman de Ventas",
    subtitle: "Calificación Implacable",
    description:
      "Preguntas de poder, detección de presupuesto y urgencia. El bot filtra curiosos antes de que consuman tu tiempo. Solo los prospectos calificados llegan a tu calendario. Eficiencia operativa brutal.",
    icon: (
      <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
  },
];

export default function VanguardArchitecture() {
  return (
    <section id="super-flujo" className="px-6 py-24">
      <div className="mx-auto max-w-7xl">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">
            El{" "}
            <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              Súper Flujo
            </span>
          </h2>
          <p className="mx-auto max-w-2xl text-lg text-white/80">
            Tres pilares técnicos que convierten tu WhatsApp en una máquina de
            ventas B2B autónoma. Infraestructura multi-tenant lista para escalar.
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-3">
          {superFlujoPilares.map((pilar) => (
            <div
              key={pilar.title}
              className="group relative overflow-hidden rounded-2xl border border-white/10 bg-card-bg p-8 transition-all hover:border-cyan-500/40 hover:shadow-[0_0_30px_rgba(0,217,255,0.1)]"
            >
              <div className="absolute right-4 top-4 text-5xl font-bold text-white/5">
                {pilar.numero}
              </div>
              <div className="relative">
                <div className="mb-5 inline-flex rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20 p-3 text-cyan-400 ring-1 ring-cyan-500/20">
                  {pilar.icon}
                </div>
                <h3 className="mb-1 text-xl font-bold text-white">
                  {pilar.title}
                </h3>
                <p className="mb-4 text-sm font-medium text-cyan-400">
                  {pilar.subtitle}
                </p>
                <p className="text-sm leading-relaxed text-white/80">
                  {pilar.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
