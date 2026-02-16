export default function CTA() {
  return (
    <section className="px-6 py-24">
      <div className="mx-auto max-w-4xl overflow-hidden rounded-3xl bg-gradient-to-r from-accent-blue to-accent-purple p-[1px]">
        <div className="rounded-3xl bg-background px-8 py-16 text-center sm:px-16">
          <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
            Listo para transformar tu empresa?
          </h2>
          <p className="mx-auto mb-8 max-w-xl text-text-secondary">
            Agenda una consulta gratuita y descubre cómo la inteligencia
            artificial puede impulsar tu negocio al siguiente nivel.
          </p>
          <a
            href="#contacto"
            className="inline-block rounded-full bg-gradient-to-r from-accent-blue to-accent-purple px-8 py-3.5 text-base font-semibold text-white transition-opacity hover:opacity-90"
          >
            Agenda tu consulta gratis
          </a>
        </div>
      </div>
    </section>
  );
}
