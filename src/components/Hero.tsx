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
          Gana más dinero reduciendo costos operativos
        </div>

        <h1 className="mb-6 text-4xl font-bold leading-tight tracking-tight sm:text-5xl md:text-6xl lg:text-7xl">
          Escala tu rentabilidad con{" "}
          <span className="bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
            Max
          </span>
          , tu nuevo socio de IA
        </h1>

        <p className="mx-auto mb-10 max-w-2xl text-lg text-text-secondary sm:text-xl">
          Automatizamos el 80% de tus tareas operativas para que te enfoques en
          cerrar ventas. Sin empleados extra, sin errores humanos.
        </p>

        <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <a
            href="#contacto"
            className="animate-glow rounded-full bg-gradient-to-r from-blue-600 to-cyan-500 px-8 py-3.5 text-base font-semibold text-white transition-transform hover:scale-105"
          >
            Conocer a Max
          </a>
          <a
            href="#max-servicios"
            className="rounded-full border border-white/10 px-8 py-3.5 text-base font-semibold text-white transition-colors hover:border-white/25"
          >
            Ver qué hace Max
          </a>
        </div>
      </div>
    </section>
  );
}
