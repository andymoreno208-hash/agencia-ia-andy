const plans = [
  {
    name: "Tier Básico",
    price: 1500,
    highlight: false,
    subtitle:
      "Setup inicial de $1,500 USD. Suscripción mensual de $500 USD por mantenimiento de servidores y optimización.",
    features: [
      "Intercepción de leads 24/7 en WhatsApp",
      "Calificación automática de presupuesto",
      "Agendamiento directo en tu calendario",
      "Sincronización básica con CRM",
      "Setup en 7 días hábiles",
    ],
  },
  {
    name: "Súper Flujo SaaS Modular RAG",
    price: 3000,
    highlight: true,
    subtitle:
      "Setup inicial de $3,000 USD. Suscripción mensual de $500 USD por mantenimiento y optimización del motor IA.",
    features: [
      "Todo lo del Tier Básico +",
      "Agente IA Multi-Tenant",
      "Memoria infinita en PostgreSQL",
      "Búsqueda avanzada de documentos (RAG)",
      "Resolución de objeciones técnicas al instante",
    ],
  },
];

export default function Pricing() {
  return (
    <section id="planes" className="px-6 py-24">
      <div className="mx-auto max-w-5xl">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
            Infraestructura y{" "}
            <span className="bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
              Escalabilidad
            </span>
          </h2>
          <p className="mx-auto max-w-2xl text-text-secondary">
            Pagas el setup y una mensualidad que cubre el mantenimiento.
            Vanguard opera como tu empleado senior desde el día uno.
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
                  El Estándar Corporativo
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
                <div className="mt-3 inline-flex items-center rounded-full border border-emerald-500/40 bg-emerald-500/15 px-3 py-1.5 text-xs font-bold text-emerald-300 shadow-sm">
                  -$500 USD de crédito por Auditoría aplicada
                </div>
                <div className="mt-3 text-sm leading-relaxed text-text-secondary">
                  {plan.subtitle}
                </div>
              </div>

              <ul className="mb-6 flex-1 space-y-3">
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

              {/* Caja riesgo cero: justo encima del botón */}
              <div className="mb-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 shadow-inner">
                <p className="text-center text-sm font-semibold leading-relaxed text-emerald-200">
                  Inversión con Riesgo Cero: El costo de esta auditoría se descuenta íntegramente de tu setup final si decides implementar con nosotros.
                </p>
              </div>
              <a
                href="https://calendly.com/andymoreno208/30min"
                target="_blank"
                rel="noopener noreferrer"
                className={`block w-full rounded-full py-3.5 text-center text-sm font-semibold transition-transform hover:scale-[1.02] ${
                  plan.highlight
                    ? "animate-glow bg-gradient-to-r from-blue-600 to-cyan-500 text-white"
                    : "border border-white/10 text-white hover:border-white/25"
                }`}
              >
                Agendar Auditoría ($500)
              </a>
            </div>
          ))}
        </div>

        {/* Scarcity notice */}
        <div className="mt-10 rounded-xl border border-yellow-500/20 bg-yellow-500/5 px-6 py-4 text-center text-sm leading-relaxed text-yellow-200/90 sm:text-base">
          &#x26A0;&#xFE0F; Aviso de Capacidad: Para garantizar la estabilidad de la infraestructura RAG en nuestros clientes activos, actualmente
          solo aceptamos 4 nuevos despliegues por mes. Agenda tu auditoría antes de
          que se llenen los cupos.
        </div>
      </div>
    </section>
  );
}
