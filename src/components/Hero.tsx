export default function Hero() {
  return (
    <section className="relative flex min-h-screen items-center justify-center overflow-hidden px-6 pt-20">
      {/* Background grid */}
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
        <h1 className="mb-6 text-4xl font-bold leading-tight tracking-tight sm:text-5xl md:text-6xl lg:text-7xl">
          ¿Cuántas ventas perdiste esta semana por{" "}
          <span className="bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
            no responder a tiempo
          </span>{" "}
          en WhatsApp?
        </h1>

        <p className="mx-auto mb-10 max-w-2xl text-lg text-text-secondary sm:text-xl">
          Conoce a Alex, tu nuevo socio de IA. Responde en 3 segundos, filtra a
          los curiosos y agenda citas de alto valor directamente en tu
          calendario. 24/7.
        </p>

        <a
          href="#agendar"
          className="animate-glow inline-block rounded-full bg-gradient-to-r from-blue-600 to-cyan-500 px-8 py-4 text-base font-semibold text-white transition-transform hover:scale-105 sm:text-lg"
        >
          Agendar mi Auditoría de Rentabilidad (15 min)
        </a>
      </div>
    </section>
  );
}
