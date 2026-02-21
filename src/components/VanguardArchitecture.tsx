const benefits = [
  {
    title: "CRM Automático",
    description:
      "Guarda el perfil completo y presupuesto del lead en Airtable sin tocar el teclado. Nombre, empresa, necesidad y nivel de urgencia, todo organizado automáticamente.",
    icon: (
      <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
      </svg>
    ),
  },
  {
    title: "Agendamiento Inteligente",
    description:
      "Lee tu Google Calendar en tiempo real y agenda o cancela citas sin intervención humana. El prospecto elige horario y recibe confirmación instantánea.",
    icon: (
      <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    title: "Persecución Implacable",
    description:
      "Retoma la conversación automáticamente con los leads que dejaron de responder. Vanguard ejecuta follow-up sistemático hasta cerrar la cita o descartar al curioso.",
    icon: (
      <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    ),
  },
];

export default function VanguardArchitecture() {
  return (
    <section id="vanguard" className="px-6 py-24">
      <div className="mx-auto max-w-7xl">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
            La arquitectura de{" "}
            <span className="bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
              Vanguard
            </span>
          </h2>
          <p className="mx-auto max-w-2xl text-text-secondary">
            No es un chatbot genérico. Vanguard es infraestructura de ventas autónoma
            que opera las 24 horas para que tú cierres más y operes menos.
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-3">
          {benefits.map((b) => (
            <div
              key={b.title}
              className="group rounded-2xl border border-card-border bg-card-bg p-8 transition-all hover:border-cyan-500/30 hover:shadow-lg hover:shadow-cyan-500/5"
            >
              <div className="mb-5 inline-flex rounded-xl bg-gradient-to-br from-blue-600/10 to-cyan-500/10 p-3 text-cyan-400">
                {b.icon}
              </div>
              <h3 className="mb-3 text-xl font-semibold">{b.title}</h3>
              <p className="text-sm leading-relaxed text-text-secondary">
                {b.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
