export default function Footer() {
  return (
    <footer className="border-t border-white/5 px-6 py-12">
      <div className="mx-auto max-w-7xl">
        <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
          <a href="#" className="text-xl font-bold tracking-tight">
            <span className="bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
              Alex
            </span>{" "}
            IA
          </a>

          <ul className="flex gap-6">
            <li>
              <a
                href="#alex"
                className="text-sm text-text-secondary transition-colors hover:text-white"
              >
                Alex
              </a>
            </li>
            <li>
              <a
                href="#planes"
                className="text-sm text-text-secondary transition-colors hover:text-white"
              >
                Planes
              </a>
            </li>
            <li>
              <a
                href="#agendar"
                className="text-sm text-text-secondary transition-colors hover:text-white"
              >
                Agendar
              </a>
            </li>
          </ul>

          <div className="text-sm text-text-secondary">
            &copy; {new Date().getFullYear()} Alex IA. Todos los derechos
            reservados.
          </div>
        </div>
      </div>
    </footer>
  );
}
