const plans = [
  {
    name: "El Filtro de Leads",
    price: 500,
    highlight: false,
    subtitle:
      "Setup inicial de $500 USD + $97 USD/mes (Cubre servidores, consumo de IA y mantenimiento técnico).",
    features: [
      "Alex en WhatsApp 24/7",
      "Calificación automática de leads",
      "Filtrado de curiosos vs. compradores",
      "Sincronización básica con CRM",
      "Respuesta en 3 segundos",
    ],
  },
  {
    name: "La Oficina Autónoma",
    price: 900,
    highlight: true,
    subtitle:
      "Setup inicial de $900 USD + $149 USD/mes (Cubre servidores, consumo ilimitado de IA, integraciones CRM y 1 ajuste de prompt mensual).",
    features: [
      "Todo lo del plan anterior",
      "CRM completo en Airtable",
      "Agendamiento inteligente en Google Calendar",
      "Cancelación y reagendamiento automático",
      "Recuperación de leads fríos (follow-up)",
      "Persecución implacable de carritos abandonados",
    ],
  },
];

export default function Pricing() {
  return (
    <section id="planes" className="px-6 py-24">
      <div className="mx-auto max-w-5xl">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
            Planes de{" "}
            <span className="bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
              Implementación
            </span>
          </h2>
          <p className="mx-auto max-w-2xl text-text-secondary">
            Pagas el setup y una mensualidad que cubre toda la infraestructura.
            Alex trabaja para ti desde el día uno.
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-2">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative flex flex-col rounded-2xl border p-8 sm:p-10 ${
                plan.highlight
                  ? "border-cyan-500/40 bg-gradient-to-b from-cyan-500/5 to-blue-600/5 shadow-lg shadow-cyan-500/10"
                  : "border-card-border bg-card-bg"
              }`}
            >
              {plan.highlight && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-blue-600 to-cyan-500 px-4 py-1 text-xs font-semibold text-white">
                  Recomendado
                </div>
              )}

              <div className="mb-8">
                <h3 className="mb-3 text-2xl font-bold">{plan.name}</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
                    ${plan.price}
                  </span>
                  <span className="text-text-secondary">USD / Setup</span>
                </div>
                <div className="mt-2 text-sm leading-relaxed text-text-secondary">
                  {plan.subtitle}
                </div>
              </div>

              <ul className="mb-8 flex-1 space-y-3">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-3 text-sm">
                    <svg
                      className="mt-0.5 h-5 w-5 shrink-0 text-cyan-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    <span className="text-text-secondary">{feature}</span>
                  </li>
                ))}
              </ul>

              <a
                href="#agendar"
                className={`w-full rounded-full py-3.5 text-center text-sm font-semibold transition-transform hover:scale-[1.02] ${
                  plan.highlight
                    ? "animate-glow bg-gradient-to-r from-blue-600 to-cyan-500 text-white"
                    : "border border-white/10 text-white hover:border-white/25"
                }`}
              >
                Agendar Implementación
              </a>
            </div>
          ))}
        </div>

        {/* Scarcity notice */}
        <div className="mt-10 rounded-xl border border-yellow-500/20 bg-yellow-500/5 px-6 py-4 text-center text-sm leading-relaxed text-yellow-200/90 sm:text-base">
          &#x26A0;&#xFE0F; Aviso de Capacidad: Para garantizar una respuesta en
          3 segundos a todos los clientes de nuestra infraestructura, actualmente
          solo aceptamos 4 nuevos setups por mes. Agenda tu auditoría antes de
          que se llenen los cupos.
        </div>
      </div>
    </section>
  );
}
