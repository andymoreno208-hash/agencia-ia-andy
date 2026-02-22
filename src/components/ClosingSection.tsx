"use client";

import { useState } from "react";

const MAKE_WEBHOOK_URL =
  "https://hook.us2.make.com/9w1yeaphxiqhfet166r6bre15roh2ldz";

const faqs = [
  {
    question: "¿Mis clientes sentirán que hablan con un robot?",
    answer:
      "No. Vanguard usa modelos avanzados que entienden contexto, manejan modismos locales y negocian como tu mejor closer. Filtramos curiosos para que tú solo hables con los que tienen la tarjeta en la mano.",
  },
  {
    question: "¿Qué pasa si el sistema falla?",
    answer:
      "Infraestructura monitoreada 24/7 con alertas en tiempo real. Si Meta o OpenAI presentan intermitencias, nuestro equipo interviene antes de que pierdas un solo lead.",
  },
  {
    question: "¿Necesito saber de tecnología?",
    answer:
      "Cero. Vanguard Scale maneja toda la arquitectura técnica: webhooks, Google Calendar, CRM. Tú solo recibes leads calificados y te presentas a cerrar.",
  },
];

export default function ClosingSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const [nombre, setNombre] = useState("");
  const [telefono, setTelefono] = useState("");
  const [empleados, setEmpleados] = useState("");
  const [horas, setHoras] = useState("");
  const [loading, setLoading] = useState(false);
  
  // Nuevo Estado: Controla si mostramos el formulario o el calendario
  const [step, setStep] = useState<"formulario" | "calendario">("formulario");
  const [fugaCalculada, setFugaCalculada] = useState("");

  async function handleSubmitAuditoria(e: React.FormEvent) {
    e.preventDefault();
    if (!nombre.trim() || !telefono.trim() || !empleados || !horas) {
      alert("Por favor completa todos los campos para calcular tu auditoría.");
      return;
    }

    // Lógica de Negocio: Cálculo de Fuga de Capital (Burn Rate)
    const burnRateCalculado = Number(empleados) * Number(horas) * 25 * 4;
    setFugaCalculada(`$${burnRateCalculado.toLocaleString()}`);

    setLoading(true);
    try {
      const res = await fetch(MAKE_WEBHOOK_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nombre: nombre.trim(),
          telefono: telefono.trim(),
          empleados: empleados,
          horas_perdidas: horas,
          estatus: "En Calificación",
          facturacion: burnRateCalculado, // <-- NÚMERO CRUDO PARA LOOKER STUDIO
        }),
      });
      if (!res.ok) throw new Error("Error al enviar");
      
      // EL CIERRE MAESTRO: Cambiamos la vista en lugar de lanzar un alert
      setStep("calendario");
      
    } catch {
      alert("Hubo un error al enviar. Intenta de nuevo o contáctanos por WhatsApp.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section id="agendar" className="px-6 py-24">
      <div className="mx-auto max-w-3xl">
        
        {step === "formulario" ? (
          <div className="mb-20 text-center animate-fade-in">
            <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
              Cada hora sin Vanguard es{" "}
              <span className="bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
                revenue que no vuelve
              </span>
            </h2>
            <p className="mx-auto mb-8 max-w-xl text-text-secondary">
              Calcula cuánto dinero estás quemando por lentitud operativa y solicita tu plan de rescate inmediato.
            </p>
            
            <form
              onSubmit={handleSubmitAuditoria}
              className="mx-auto grid max-w-2xl grid-cols-1 gap-4 sm:grid-cols-2"
            >
              <div className="col-span-1">
                <input
                  type="text"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  placeholder="Tu nombre completo"
                  className="w-full rounded-xl border border-card-border bg-card-bg px-4 py-3 text-white placeholder:text-text-secondary focus:border-cyan-500 focus:outline-none"
                  required
                />
              </div>
              <div className="col-span-1">
                <input
                  type="tel"
                  value={telefono}
                  onChange={(e) => setTelefono(e.target.value)}
                  placeholder="WhatsApp (con código de país)"
                  className="w-full rounded-xl border border-card-border bg-card-bg px-4 py-3 text-white placeholder:text-text-secondary focus:border-cyan-500 focus:outline-none"
                  required
                />
              </div>
              <div className="col-span-1">
                <input
                  type="number"
                  value={empleados}
                  onChange={(e) => setEmpleados(e.target.value)}
                  placeholder="Nº de empleados"
                  className="w-full rounded-xl border border-card-border bg-card-bg px-4 py-3 text-white placeholder:text-text-secondary focus:border-cyan-500 focus:outline-none"
                  required
                />
              </div>
              <div className="col-span-1">
                <input
                  type="number"
                  value={horas}
                  onChange={(e) => setHoras(e.target.value)}
                  placeholder="Horas perdidas/semana"
                  className="w-full rounded-xl border border-card-border bg-card-bg px-4 py-3 text-white placeholder:text-text-secondary focus:border-cyan-500 focus:outline-none"
                  required
                />
              </div>
              <div className="col-span-1 sm:col-span-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="animate-glow w-full rounded-xl bg-gradient-to-r from-blue-600 to-cyan-500 py-4 text-lg font-bold text-white transition-transform hover:scale-[1.02] disabled:opacity-70"
                >
                  {loading ? "Calculando Impacto..." : "Solicitar Auditoría de Fuga"}
                </button>
              </div>
            </form>
          </div>
        ) : (
          <div className="mb-20 text-center animate-fade-in-up">
            <h3 className="text-3xl font-bold text-white mb-2">
              Fuga Detectada: <span className="text-red-500 font-mono">{fugaCalculada}</span> USD/mes
            </h3>
            <p className="text-gray-400 text-lg mb-8">
              Tu infraestructura actual está quemando capital. Agenda tu consultoría estratégica para tapar la fuga antes de que escale.
            </p>
            
            <div className="w-full rounded-xl overflow-hidden border border-card-border shadow-2xl bg-card-bg">
              <iframe
                src={`https://calendly.com/andymoreno208/30min?hide_event_type_details=1&hide_gdpr_banner=1&background_color=0f172a&text_color=ffffff&primary_color=06b6d4&name=${encodeURIComponent(nombre)}`}
                width="100%"
                height="650"
                frameBorder="0"
              ></iframe>
            </div>
          </div>
        )}

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