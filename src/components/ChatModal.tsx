"use client";

import { useState, useEffect, useRef } from "react";

interface Message {
  from: "max" | "user";
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

  // Reset on open
  useEffect(() => {
    if (open) {
      setMessages([]);
      setStep(0);
      setInput("");
      setName("");
      // Show first message with typing effect
      setTyping(true);
      const timer = setTimeout(() => {
        setMessages([
          {
            from: "max",
            text: "¡Hola! Soy Max. Para analizar cómo puedo reducir tus costos operativos, ¿cuál es tu nombre?",
          },
        ]);
        setTyping(false);
      }, 800);
      return () => clearTimeout(timer);
    }
  }, [open]);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  function addMaxMessage(text: string) {
    setTyping(true);
    setTimeout(() => {
      setMessages((prev) => [...prev, { from: "max", text }]);
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
      addMaxMessage(
        `¡Mucho gusto, ${userMsg}! ¿Cuál es el correo de tu empresa para enviarte el análisis?`
      );
    } else if (step === 1) {
      setStep(2);
      addMaxMessage(
        `Perfecto, ${name}. ¿A qué se dedica tu empresa y cuál es su mayor reto operativo?`
      );
    } else if (step === 2) {
      setStep(3);
      addMaxMessage(
        `¡Excelente, ${name}! Ya tengo lo que necesito. Mi equipo te contactará en menos de 24 horas con un plan para reducir tus costos operativos. ¡Prepárate para ganar más! 🚀`
      );
    }
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative flex h-[520px] w-full max-w-md flex-col overflow-hidden rounded-2xl border border-white/10 bg-[#0f0f1a] shadow-2xl shadow-cyan-500/10">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/5 bg-gradient-to-r from-blue-600/10 to-cyan-500/10 px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-cyan-500 text-sm font-bold text-white">
              M
            </div>
            <div>
              <div className="font-semibold text-white">Max</div>
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

            {/* Typing indicator */}
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

        {/* Input */}
        {step < 3 ? (
          <form
            onSubmit={handleSubmit}
            className="flex items-center gap-2 border-t border-white/5 bg-[#0a0a14] px-4 py-3"
          >
            <input
              type={step === 1 ? "email" : "text"}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                step === 0
                  ? "Escribe tu nombre..."
                  : step === 1
                    ? "tu@empresa.com"
                    : "Cuéntale a Max..."
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
          <div className="border-t border-white/5 bg-[#0a0a14] px-4 py-3 text-center text-sm text-text-secondary">
            Max te contactará pronto ✨
          </div>
        )}
      </div>
    </div>
  );
}
