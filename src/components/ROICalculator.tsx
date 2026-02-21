"use client";

import { useState } from "react";

export default function ROICalculator() {
  const [messages, setMessages] = useState(100);
  const [serviceValue, setServiceValue] = useState(500);

  const lostLeads = Math.round(messages * 0.3);
  const monthlyLoss = lostLeads * serviceValue;

  return (
    <section className="px-6 py-24">
      <div className="mx-auto max-w-3xl">
        <div className="rounded-2xl border border-card-border bg-card-bg p-8 sm:p-12">
          <div className="mb-10 text-center">
            <h2 className="mb-3 text-3xl font-bold sm:text-4xl">
              Calculadora de{" "}
              <span className="bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
                Pérdidas
              </span>
            </h2>
            <p className="text-text-secondary">
              Descubre cuánto dinero estás dejando sobre la mesa cada mes.
            </p>
          </div>

          <div className="space-y-8">
            {/* Messages slider */}
            <div>
              <div className="mb-3 flex items-center justify-between">
                <label
                  htmlFor="messages"
                  className="text-sm font-medium sm:text-base"
                >
                  Mensajes de prospectos al mes
                </label>
                <span className="rounded-lg bg-white/5 px-3 py-1 text-lg font-bold text-cyan-400">
                  {messages}
                </span>
              </div>
              <input
                id="messages"
                type="range"
                min={10}
                max={1000}
                step={10}
                value={messages}
                onChange={(e) => setMessages(Number(e.target.value))}
                className="h-2 w-full cursor-pointer appearance-none rounded-full bg-white/10 accent-cyan-500"
              />
              <div className="mt-1 flex justify-between text-xs text-text-secondary">
                <span>10</span>
                <span>1,000</span>
              </div>
            </div>

            {/* Service value slider */}
            <div>
              <div className="mb-3 flex items-center justify-between">
                <label
                  htmlFor="serviceValue"
                  className="text-sm font-medium sm:text-base"
                >
                  Valor promedio de tu servicio
                </label>
                <span className="rounded-lg bg-white/5 px-3 py-1 text-lg font-bold text-cyan-400">
                  ${serviceValue.toLocaleString("en-US")} USD
                </span>
              </div>
              <input
                id="serviceValue"
                type="range"
                min={50}
                max={5000}
                step={50}
                value={serviceValue}
                onChange={(e) => setServiceValue(Number(e.target.value))}
                className="h-2 w-full cursor-pointer appearance-none rounded-full bg-white/10 accent-cyan-500"
              />
              <div className="mt-1 flex justify-between text-xs text-text-secondary">
                <span>$50</span>
                <span>$5,000</span>
              </div>
            </div>
          </div>

          {/* Result */}
          <div className="mt-10 rounded-xl border border-red-500/20 bg-red-500/5 p-6 text-center">
            <p className="mb-1 text-sm text-text-secondary">
              Pierdes aprox. <span className="text-white font-medium">{lostLeads} leads</span> al mes por lentitud operativa
            </p>
            <p className="text-3xl font-bold text-red-400 sm:text-4xl">
              Estás perdiendo aproximadamente $
              {monthlyLoss.toLocaleString("en-US")} USD cada mes
            </p>
            <p className="mt-2 text-sm text-red-400/70">
              por lentitud operativa
            </p>
          </div>

          {/* CTA */}
          <div className="mt-8 text-center">
            <a
              href="https://wa.me/593959916032?text=Hola,%20quiero%20ver%20como%20Vanguard%20califica%20leads"
              target="_blank"
              rel="noopener noreferrer"
              className="animate-glow inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-blue-600 to-cyan-500 px-8 py-4 text-base font-semibold text-white transition-transform hover:scale-105"
            >
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
              </svg>
              Detener esta pérdida hoy (Probar Vanguard en WhatsApp)
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
