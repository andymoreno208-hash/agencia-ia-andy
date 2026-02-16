const projects = [
  {
    title: "Automatización de Atención al Cliente",
    category: "Chatbot IA",
    description:
      "Implementamos un chatbot inteligente para una empresa de e-commerce que redujo los tiempos de respuesta en un 80% y aumentó la satisfacción del cliente.",
  },
  {
    title: "Optimización de Supply Chain",
    category: "Automatización",
    description:
      "Sistema de predicción de demanda con ML que optimizó el inventario de una cadena retail, reduciendo costos de almacenamiento en un 35%.",
  },
  {
    title: "Dashboard de Analítica Predictiva",
    category: "Analítica",
    description:
      "Plataforma de Business Intelligence con modelos predictivos para una fintech, mejorando la precisión de sus proyecciones financieras en un 60%.",
  },
];

export default function Portfolio() {
  return (
    <section id="portfolio" className="px-6 py-24">
      <div className="mx-auto max-w-7xl">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
            Casos de{" "}
            <span className="bg-gradient-to-r from-accent-blue to-accent-purple bg-clip-text text-transparent">
              Éxito
            </span>
          </h2>
          <p className="mx-auto max-w-2xl text-text-secondary">
            Resultados reales que hablan por sí solos. Así es como hemos
            transformado negocios con IA.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <div
              key={project.title}
              className="group overflow-hidden rounded-2xl border border-card-border bg-card-bg transition-colors hover:border-accent-purple/30"
            >
              {/* Placeholder image area */}
              <div className="flex h-48 items-center justify-center bg-gradient-to-br from-accent-blue/10 to-accent-purple/10">
                <span className="rounded-full border border-white/10 px-4 py-1.5 text-sm text-text-secondary">
                  {project.category}
                </span>
              </div>
              <div className="p-6">
                <h3 className="mb-2 text-lg font-semibold">{project.title}</h3>
                <p className="text-sm leading-relaxed text-text-secondary">
                  {project.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
