"use client";

import { useState, useEffect, useRef } from "react";

interface Message {
  from: "vanguard" | "user";
  text: string;
}

interface ChatModalProps {
  open: boolean;
  onClose: () => void;
}

export default function ChatModal({ open, onClose }: ChatModalProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [step, setStep] = useState(0);
  const [input, setInput] = useState("");
  const [name, setName] = useState("");
  const [typing, setTyping] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) {
      setMessages([]);
      setStep(0);
      setInput("");
      setName("");
      setTyping(true);
      const timer = setTimeout(() => {
        setMessages([
          {
            from: "vanguard",
            text: "Bienvenido a Vanguard Scale. Para diagnosticar cuánto revenue estás perdiendo por lentitud operativa, necesito tu nombre.",
          },
        ]);
        setTyping(false);
      }, 800);
      return () => clearTimeout(timer);
    }
  }, [open]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  function addVanguardMessage(text: string) {
    setTyping(true);
    setTimeout(() => {
      setMessages((prev) => [...prev, { from: "vanguard", text }]);
      setTyping(false);
    }, 600);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input.trim();
    setMessages((prev) => [...prev, { from: "user", text: userMsg }]);
    setInput("");

    if (step === 0) {
      setName(userMsg);
      setStep(1);
      addVanguardMessage(
        `${userMsg}, registrado. ¿Cuál es tu vertical? (ej: clínica dental, inmobiliaria, agencia de marketing)`
      );
    } else if (step === 1) {
      setStep(2);
      addVanguardMessage(
        `Copiado, ${name}. ¿Cuántos leads recibes al mes y cuántos se quedan sin respuesta?`
      );
    } else if (step === 2) {
      setStep(3);
      addVanguardMessage(
        `Diagnóstico listo, ${name}. Con esos números hay revenue recuperable desde el día uno. Agenda tu auditoría abajo.`
      );
    }
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      <div className="relative flex h-[520px] w-full max-w-md flex-col overflow-hidden rounded-2xl border border-white/10 bg-[#0f0f1a] shadow-2xl shadow-cyan-500/10">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/5 bg-gradient-to-r from-blue-600/10 to-cyan-500/10 px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-cyan-500 text-sm font-bold text-white">
              V
            </div>
            <div>
              <div className="font-semibold text-white">Vanguard</div>
              <div className="flex items-center gap-1.5 text-xs text-cyan-400">
                <span className="h-2 w-2 rounded-full bg-cyan-400" />
                En línea
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-text-secondary transition-colors hover:bg-white/5 hover:text-white"
            aria-label="Cerrar chat"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-5 py-4">
          <div className="flex flex-col gap-3">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.from === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                    msg.from === "user"
                      ? "rounded-br-md bg-gradient-to-r from-blue-600 to-cyan-500 text-white"
                      : "rounded-bl-md border border-white/5 bg-white/5 text-white"
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}

            {typing && (
              <div className="flex justify-start">
                <div className="flex gap-1.5 rounded-2xl rounded-bl-md border border-white/5 bg-white/5 px-4 py-3">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-cyan-400 [animation-delay:0ms]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-cyan-400 [animation-delay:150ms]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-cyan-400 [animation-delay:300ms]" />
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        </div>

        {/* Input / WhatsApp CTA */}
        {step < 3 ? (
          <form
            onSubmit={handleSubmit}
            className="flex items-center gap-2 border-t border-white/5 bg-[#0a0a14] px-4 py-3"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                step === 0
                  ? "Escribe tu nombre..."
                  : step === 1
                    ? "Ej: Clínica dental..."
                    : "Ej: 200 leads, 50 sin respuesta..."
              }
              className="flex-1 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder:text-text-secondary focus:border-cyan-500/50 focus:outline-none"
              autoFocus
            />
            <button
              type="submit"
              className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-r from-blue-600 to-cyan-500 text-white transition-transform hover:scale-105"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </form>
        ) : (
          <div className="flex items-center justify-center border-t border-white/5 bg-[#0a0a14] px-4 py-3">
            <a
              href="https://wa.me/593959915414?text=Hola%20Andy,%20quiero%20escalar%20mi%20facturación%20con%20IA."
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 rounded-full bg-[#25D366] px-6 py-2.5 text-sm font-semibold text-white transition-transform hover:scale-105"
            >
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
              </svg>
              Hablar con Vanguard en WhatsApp
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
