export default function Contact() {
  return (
    <section id="contacto" className="px-6 py-24">
      <div className="mx-auto max-w-7xl">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-3xl font-bold sm:text-4xl">
            <span className="bg-gradient-to-r from-accent-blue to-accent-purple bg-clip-text text-transparent">
              Contáctanos
            </span>
          </h2>
          <p className="mx-auto max-w-2xl text-text-secondary">
            Cuéntanos sobre tu proyecto y te responderemos en menos de 24 horas.
          </p>
        </div>

        <div className="grid gap-12 lg:grid-cols-2">
          {/* Form */}
          <form className="space-y-6">
            <div>
              <label htmlFor="name" className="mb-2 block text-sm font-medium">
                Nombre
              </label>
              <input
                type="text"
                id="name"
                className="w-full rounded-xl border border-card-border bg-card-bg px-4 py-3 text-white placeholder:text-text-secondary focus:border-accent-blue focus:outline-none"
                placeholder="Tu nombre"
              />
            </div>
            <div>
              <label htmlFor="email" className="mb-2 block text-sm font-medium">
                Email
              </label>
              <input
                type="email"
                id="email"
                className="w-full rounded-xl border border-card-border bg-card-bg px-4 py-3 text-white placeholder:text-text-secondary focus:border-accent-blue focus:outline-none"
                placeholder="tu@email.com"
              />
            </div>
            <div>
              <label
                htmlFor="message"
                className="mb-2 block text-sm font-medium"
              >
                Mensaje
              </label>
              <textarea
                id="message"
                rows={5}
                className="w-full resize-none rounded-xl border border-card-border bg-card-bg px-4 py-3 text-white placeholder:text-text-secondary focus:border-accent-blue focus:outline-none"
                placeholder="Cuéntanos sobre tu proyecto..."
              />
            </div>
            <button
              type="submit"
              className="w-full rounded-full bg-gradient-to-r from-accent-blue to-accent-purple py-3.5 text-base font-semibold text-white transition-opacity hover:opacity-90"
            >
              Enviar mensaje
            </button>
          </form>

          {/* Contact info */}
          <div className="flex flex-col justify-center gap-8">
            <div className="flex items-start gap-4">
              <div className="rounded-xl bg-accent-blue/10 p-3 text-accent-blue">
                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <div className="font-semibold">Email</div>
                <div className="text-text-secondary">hola@agencia-ia.com</div>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="rounded-xl bg-accent-blue/10 p-3 text-accent-blue">
                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <div>
                <div className="font-semibold">Ubicación</div>
                <div className="text-text-secondary">Ciudad de México, MX</div>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="rounded-xl bg-accent-blue/10 p-3 text-accent-blue">
                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <div className="font-semibold">Horario</div>
                <div className="text-text-secondary">Lun - Vie, 9:00 - 18:00</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
