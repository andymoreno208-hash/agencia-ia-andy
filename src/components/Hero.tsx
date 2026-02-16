export default function Hero() {
  return (
    <section className="relative flex min-h-screen items-center justify-center overflow-hidden px-6 pt-20">
      {/* Background grid pattern */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      {/* Glow */}
      <div className="pointer-events-none absolute top-1/4 left-1/2 h-[500px] w-[500px] -translate-x-1/2 rounded-full bg-accent-purple/20 blur-[120px]" />

      <div className="relative z-10 mx-auto max-w-4xl text-center">
        <div className="mb-6 inline-block rounded-full border border-accent-blue/30 bg-accent-blue/10 px-4 py-1.5 text-sm text-accent-blue">
          Automatización empresarial con IA
        </div>

        <h1 className="mb-6 text-4xl font-bold leading-tight tracking-tight sm:text-5xl md:text-6xl lg:text-7xl">
          Transformamos tu negocio con{" "}
          <span className="bg-gradient-to-r from-accent-blue to-accent-purple bg-clip-text text-transparent">
            Inteligencia Artificial
          </span>
        </h1>

        <p className="mx-auto mb-10 max-w-2xl text-lg text-text-secondary sm:text-xl">
          Automatizamos procesos, reducimos costos y potenciamos la toma de
          decisiones de tu empresa con soluciones de IA a medida.
        </p>

        <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <a
            href="#contacto"
            className="rounded-full bg-gradient-to-r from-accent-blue to-accent-purple px-8 py-3.5 text-base font-semibold text-white transition-opacity hover:opacity-90"
          >
            Agenda una consulta gratis
          </a>
          <a
            href="#servicios"
            className="rounded-full border border-white/10 px-8 py-3.5 text-base font-semibold text-white transition-colors hover:border-white/25"
          >
            Ver servicios
          </a>
        </div>
      </div>
    </section>
  );
}
