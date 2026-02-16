export default function CTA() {
  return (
    <section className="px-6 py-24">
      <div className="mx-auto max-w-4xl overflow-hidden rounded-3xl bg-gradient-to-r from-blue-600 to-cyan-500 p-[1px]">
        <div className="rounded-3xl bg-background px-8 py-16 text-center sm:px-16">
          <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
            Deja que Max trabaje por ti
          </h2>
          <p className="mx-auto mb-8 max-w-xl text-text-secondary">
            Gana más dinero reduciendo costos operativos. Agenda una consulta
            gratuita y descubre cómo Max puede transformar tu negocio.
          </p>
          <a
            href="#contacto"
            className="animate-glow inline-block rounded-full bg-gradient-to-r from-blue-600 to-cyan-500 px-8 py-3.5 text-base font-semibold text-white transition-transform hover:scale-105"
          >
            Conocer a Max
          </a>
        </div>
      </div>
    </section>
  );
}
