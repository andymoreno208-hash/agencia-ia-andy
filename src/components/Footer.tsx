export default function Footer() {
  return (
    <footer className="border-t border-white/5 px-6 py-12">
      <div className="mx-auto max-w-7xl">
        <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
          <a href="#" className="text-xl font-bold tracking-tight">
            <span className="bg-gradient-to-r from-accent-blue to-accent-purple bg-clip-text text-transparent">
              Agencia
            </span>{" "}
            IA
          </a>

          <ul className="flex gap-6">
            <li>
              <a
                href="#servicios"
                className="text-sm text-text-secondary transition-colors hover:text-white"
              >
                Servicios
              </a>
            </li>
            <li>
              <a
                href="#nosotros"
                className="text-sm text-text-secondary transition-colors hover:text-white"
              >
                Nosotros
              </a>
            </li>
            <li>
              <a
                href="#portfolio"
                className="text-sm text-text-secondary transition-colors hover:text-white"
              >
                Portfolio
              </a>
            </li>
            <li>
              <a
                href="#contacto"
                className="text-sm text-text-secondary transition-colors hover:text-white"
              >
                Contacto
              </a>
            </li>
          </ul>

          <div className="text-sm text-text-secondary">
            &copy; {new Date().getFullYear()} Agencia IA. Todos los derechos
            reservados.
          </div>
        </div>
      </div>
    </footer>
  );
}
