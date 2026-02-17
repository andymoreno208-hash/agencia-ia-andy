"use client";

import { useState } from "react";

const faqs = [
  {
    question: "¿Mis clientes sentirán que hablan con un robot?",
    answer:
      "No. Alex entiende contexto, habla de forma natural y empática, y adapta su tono a cada conversación. Tus clientes sentirán que hablan con un asesor dedicado que conoce tu negocio.",
  },
  {
    question: "¿Qué pasa si el sistema falla?",
    answer:
      "Tenemos una arquitectura con manejador de errores que nos notifica al instante para que tu operación no se detenga. Si algo sale de lo esperado, nuestro equipo interviene antes de que afecte a tu cliente.",
  },
  {
    question: "¿Necesito saber de tecnología?",
    answer:
      "Absolutamente nada. Nosotros configuramos, integramos y operamos todo. Tú solo ves los resultados: más citas agendadas, más ventas cerradas y menos horas perdidas.",
  },
];

export default function ClosingSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <section id="agendar" className="px-6 py-24">
      <div className="mx-auto max-w-3xl">
        {/* CTA */}
        <div className="mb-20 text-center">
          <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
            ¿Listo para dejar de{" "}
            <span className="bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
              perder ventas
            </span>
            ?
          </h2>
          <p className="mx-auto mb-8 max-w-xl text-text-secondary">
            En 15 minutos analizamos tu operación y te mostramos exactamente
            cuánto dinero estás dejando sobre la mesa.
          </p>
          <a
            href="https://wa.me/593959916032?text=Hola%20Alex,%20vengo%20de%20la%20web%20y%20quiero%20agendar%20mi%20auditor%C3%ADa%20de%20rentabilidad"
            target="_blank"
            rel="noopener noreferrer"
            className="animate-glow inline-block rounded-full bg-gradient-to-r from-blue-600 to-cyan-500 px-8 py-4 text-base font-semibold text-white transition-transform hover:scale-105 sm:text-lg"
          >
            Agendar Implementación
          </a>
        </div>

        {/* FAQs */}
        <div>
          <h3 className="mb-8 text-center text-2xl font-bold">
            Preguntas Frecuentes
          </h3>
          <div className="space-y-3">
            {faqs.map((faq, i) => (
              <div
                key={i}
                className="rounded-xl border border-card-border bg-card-bg"
              >
                <button
                  onClick={() => setOpenIndex(openIndex === i ? null : i)}
                  className="flex w-full items-center justify-between px-6 py-4 text-left text-sm font-medium sm:text-base"
                >
                  <span>{faq.question}</span>
                  <svg
                    className={`h-5 w-5 shrink-0 text-text-secondary transition-transform ${
                      openIndex === i ? "rotate-180" : ""
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>
                {openIndex === i && (
                  <div className="border-t border-card-border px-6 py-4 text-sm leading-relaxed text-text-secondary">
                    {faq.answer}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
