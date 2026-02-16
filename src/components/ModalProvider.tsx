"use client";

import { createContext, useContext, useState, useCallback } from "react";
import ChatModal from "./ChatModal";

const ModalContext = createContext<() => void>(() => {});

export function useOpenChat() {
  return useContext(ModalContext);
}

export default function ModalProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const openChat = useCallback(() => setOpen(true), []);

  return (
    <ModalContext.Provider value={openChat}>
      {children}
      <ChatModal open={open} onClose={() => setOpen(false)} />
    </ModalContext.Provider>
  );
}
