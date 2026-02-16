"use client";

import { useOpenChat } from "./ModalProvider";

const plans = [
  {
    name: "Starter",
    setup: 200,
    monthly: 87,
    popular: false,
    features: [
      "CRM Básico",
      "Hasta 8 usuarios",
      "Automatización de WhatsApp",
    ],
  },
  {
    name: "Growth",
    setup: 300,
    monthly: 207,
    popular: true,
    features: [
      "CRM + IA",
      "Recuperación de carritos",
      "Agendamiento en Calendar",
      "Hasta 12 usuarios",
    ],
  },
  {
    name: "Genius",
    setup: 600,
    monthly: 857,
    popular: false,
    features: [
      "IA Predictiva",
      "Integración ERP/Airtable",
      "Análisis de datos avanzado",
    ],
  },
];

export default function Pricing() {
  const openChat = useOpenChat();

  return (
    <section id="planes" className="px-6 py-24">
      <div className="mx-auto max-w-7xl">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
            Planes de{" "}
            <span className="bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
              Inversión
            </span>
          </h2>
          <p className="mx-auto max-w-2xl text-text-secondary">
            Elige el plan que mejor se adapte a tu negocio. Todos incluyen a Max
            trabajando 24/7 para que ganes más reduciendo costos operativos.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative flex flex-col rounded-2xl border p-8 ${
                plan.popular
                  ? "border-cyan-500/40 bg-gradient-to-b from-cyan-500/5 to-blue-600/5 shadow-lg shadow-cyan-500/10"
                  : "border-card-border bg-card-bg"
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-blue-600 to-cyan-500 px-4 py-1 text-xs font-semibold text-white">
                  Más Popular
                </div>
              )}

              <div className="mb-6">
                <h3 className="mb-2 text-xl font-bold">{plan.name}</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
                    ${plan.monthly}
                  </span>
                  <span className="text-text-secondary">/mes</span>
                </div>
                <div className="mt-1 text-sm text-text-secondary">
                  Setup: ${plan.setup} USD (único pago)
                </div>
              </div>

              <ul className="mb-8 flex-1 space-y-3">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-3 text-sm">
                    <svg
                      className="h-5 w-5 shrink-0 text-cyan-400"
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

              <button
                onClick={openChat}
                className={`w-full rounded-full py-3 text-sm font-semibold transition-transform hover:scale-[1.02] ${
                  plan.popular
                    ? "animate-glow bg-gradient-to-r from-blue-600 to-cyan-500 text-white"
                    : "border border-white/10 text-white hover:border-white/25"
                }`}
              >
                Empezar con {plan.name}
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
