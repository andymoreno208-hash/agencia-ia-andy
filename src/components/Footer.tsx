export default function Footer() {
  return (
    <footer className="border-t border-white/5 px-6 py-12">
      <div className="mx-auto max-w-7xl">
        <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
          <a href="#" className="text-xl font-bold tracking-tight">
            <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              Vanguard
            </span>{" "}
            Scale
          </a>

          <ul className="flex gap-6">
            <li>
              <a
                href="#super-flujo"
                className="text-sm text-white/70 transition-colors hover:text-white"
              >
                El Súper Flujo
              </a>
            </li>
            <li>
              <a
                href="#resultados"
                className="text-sm text-white/70 transition-colors hover:text-white"
              >
                Resultados
              </a>
            </li>
            <li>
              <a
                href="#planes"
                className="text-sm text-white/70 transition-colors hover:text-white"
              >
                Planes
              </a>
            </li>
            <li>
              <a
                href="https://calendly.com/andymoreno208/30min"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-white/70 transition-colors hover:text-white"
              >
                Agendar Auditoría de Escalamiento
              </a>
            </li>
          </ul>

          <div className="text-sm text-white/70">
            &copy; {new Date().getFullYear()} Vanguard Scale. Todos los derechos
            reservados.
          </div>
        </div>
      </div>
    </footer>
  );
}
