const testimonials = [
  {
    name: "Dra. Lucía Paredes",
    role: "Directora, Clínica Dental Sonríe",
    quote:
      "Antes perdíamos el 60% de los leads de Instagram. Desde que Alex responde en segundos, llenamos la agenda sin que mi recepcionista toque el teléfono.",
  },
  {
    name: "Roberto Cevallos",
    role: "Gerente Comercial, Inmobiliaria Prado",
    quote:
      "Un lead de un departamento de $120K nos escribió a las 11pm. Alex lo calificó, le mostró opciones y agendó visita para las 9am. Cerramos esa venta.",
  },
  {
    name: "Valentina Ruiz",
    role: "Fundadora, Agencia Digital Impulso",
    quote:
      "Gestiono la pauta de 8 clientes. Alex me ahorra 4 horas diarias de seguimiento y mis clientes ven más citas agendadas. Todos ganamos.",
  },
];

export default function Testimonials() {
  return (
    <section id="testimonios" className="px-6 py-24">
      <div className="mx-auto max-w-7xl">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
            Negocios que ya{" "}
            <span className="bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
              dejaron de perder ventas
            </span>
          </h2>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {testimonials.map((t) => (
            <div
              key={t.name}
              className="rounded-2xl border border-card-border bg-card-bg p-6"
            >
              <svg
                className="mb-4 h-8 w-8 text-cyan-500/40"
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
