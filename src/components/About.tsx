const stats = [
  { value: "50+", label: "Proyectos completados" },
  { value: "98%", label: "Clientes satisfechos" },
  { value: "40%", label: "Reducción de costos promedio" },
  { value: "24/7", label: "Soporte y monitoreo" },
];

export default function About() {
  return (
    <section id="nosotros" className="px-6 py-24">
      <div className="mx-auto max-w-7xl">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          {/* Text */}
          <div>
            <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
              Sobre{" "}
              <span className="bg-gradient-to-r from-accent-blue to-accent-purple bg-clip-text text-transparent">
                Nosotros
              </span>
            </h2>
            <p className="mb-6 leading-relaxed text-text-secondary">
              Somos un equipo de expertos en inteligencia artificial y
              automatización dedicados a transformar empresas. Combinamos
              tecnología de vanguardia con un profundo entendimiento de los
              procesos de negocio para entregar soluciones que generan impacto
              real.
            </p>
            <p className="leading-relaxed text-text-secondary">
              Nuestra misión es democratizar el acceso a la IA, permitiendo que
              empresas de todos los tamaños aprovechen el poder de la
              automatización inteligente para crecer, competir y liderar en su
              industria.
            </p>
          </div>

          {/* Stats grid */}
          <div className="grid grid-cols-2 gap-4">
            {stats.map((stat) => (
              <div
                key={stat.label}
                className="rounded-2xl border border-card-border bg-card-bg p-6 text-center"
              >
                <div className="mb-1 text-3xl font-bold bg-gradient-to-r from-accent-blue to-accent-purple bg-clip-text text-transparent">
                  {stat.value}
                </div>
                <div className="text-sm text-text-secondary">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
