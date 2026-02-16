const maxServices = [
  {
    title: "Ventas en Piloto Automático",
    description:
      "Chatbots con IA que califican leads y cierran ventas 24/7. Max trabaja mientras tú descansas.",
    icon: (
      <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    title: "Agendamiento Inteligente",
    description:
      "Sincronización total con calendarios para que Max agende tus citas sin que muevas un dedo.",
    icon: (
      <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    title: "Cerebro Operativo",
    description:
      "Automatización de CRMs y tareas repetitivas para maximizar tu rentabilidad. Menos costos, más ganancias.",
    icon: (
      <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
  },
];

export default function MaxServices() {
  return (
    <section id="max-servicios" className="px-6 py-24">
      <div className="mx-auto max-w-7xl">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
            ¿Qué puede hacer{" "}
            <span className="bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
              Max
            </span>{" "}
            por tu negocio?
          </h2>
          <p className="mx-auto max-w-2xl text-text-secondary">
            Max es tu socio de IA que trabaja 24/7 para que ganes más dinero
            reduciendo costos operativos.
          </p>
        </div>

        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {maxServices.map((service) => (
            <div
              key={service.title}
              className="group rounded-2xl border border-card-border bg-card-bg p-8 transition-all hover:border-cyan-500/30 hover:shadow-lg hover:shadow-cyan-500/5"
            >
              <div className="mb-5 inline-flex rounded-xl bg-gradient-to-br from-blue-600/10 to-cyan-500/10 p-3 text-cyan-400">
                {service.icon}
              </div>
              <h3 className="mb-3 text-xl font-semibold">{service.title}</h3>
              <p className="text-sm leading-relaxed text-text-secondary">
                {service.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
