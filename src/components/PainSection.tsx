export default function PainSection() {
  return (
    <section className="px-6 py-24">
      <div className="mx-auto max-w-4xl">
        <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-8 sm:p-12">
          <h2 className="mb-6 text-center text-3xl font-bold sm:text-4xl">
            El costo de{" "}
            <span className="text-red-400">no actuar</span>
          </h2>

          <div className="space-y-6 text-base leading-relaxed text-text-secondary sm:text-lg">
            <p>
              Inviertes en Meta Ads. Los leads llegan. Pero tu equipo tarda{" "}
              <span className="font-semibold text-white">
                2, 5 o hasta 12 horas en responder
              </span>
              . Para cuando contestan, ese lead ya habló con tu competencia y
              cerró con ellos.
            </p>

            <p>
              Cada lead que se enfría es dinero que{" "}
              <span className="font-semibold text-white">
                ya pagaste en publicidad
              </span>{" "}
              y que nunca vas a recuperar. No es un problema de marketing. Es un
              problema de{" "}
              <span className="font-semibold text-white">
                velocidad de respuesta
              </span>
              .
            </p>

            <p>
              Las clínicas, inmobiliarias y agencias que ya operan con Vanguard
              responden en{" "}
              <span className="font-semibold text-cyan-400">3 segundos</span>,
              califican al lead automáticamente y agendan la cita antes de que el
              prospecto cierre la pantalla.
            </p>
          </div>

          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            <div className="rounded-xl border border-red-500/10 bg-background/50 p-4 text-center">
              <div className="text-3xl font-bold text-red-400">78%</div>
              <div className="mt-1 text-sm text-text-secondary">
                de leads compran al primero que responde
              </div>
            </div>
            <div className="rounded-xl border border-red-500/10 bg-background/50 p-4 text-center">
              <div className="text-3xl font-bold text-red-400">5 min</div>
              <div className="mt-1 text-sm text-text-secondary">
                máximo antes de que el lead se enfríe
              </div>
            </div>
            <div className="rounded-xl border border-red-500/10 bg-background/50 p-4 text-center">
              <div className="text-3xl font-bold text-red-400">$0</div>
              <div className="mt-1 text-sm text-text-secondary">
                recuperas de un lead que no contestaste
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
