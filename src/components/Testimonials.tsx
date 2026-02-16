const testimonials = [
  {
    name: "María González",
    role: "CEO, TechRetail",
    quote:
      "Gracias a Agencia IA, automatizamos el 70% de nuestras tareas de atención al cliente. El ROI se vio en el primer mes.",
  },
  {
    name: "Carlos Mendoza",
    role: "Director de Operaciones, LogiPro",
    quote:
      "La implementación de IA en nuestra cadena de suministro fue impecable. Redujimos errores y costos significativamente.",
  },
  {
    name: "Ana Ramírez",
    role: "Fundadora, FinData",
    quote:
      "El equipo entiende tanto de tecnología como de negocio. Nos entregaron una solución que realmente transformó nuestros procesos.",
  },
];

export default function Testimonials() {
  return (
    <section id="testimonios" className="px-6 py-24">
      <div className="mx-auto max-w-7xl">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
            Lo que dicen nuestros{" "}
            <span className="bg-gradient-to-r from-accent-blue to-accent-purple bg-clip-text text-transparent">
              Clientes
            </span>
          </h2>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {testimonials.map((t) => (
            <div
              key={t.name}
              className="rounded-2xl border border-card-border bg-card-bg p-6"
            >
              {/* Quote icon */}
              <svg
                className="mb-4 h-8 w-8 text-accent-purple/40"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10H14.017zM0 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151C7.546 6.068 5.983 8.789 5.983 11h4v10H0z" />
              </svg>
              <p className="mb-6 leading-relaxed text-text-secondary">
                &ldquo;{t.quote}&rdquo;
              </p>
              <div>
                <div className="font-semibold">{t.name}</div>
                <div className="text-sm text-text-secondary">{t.role}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
