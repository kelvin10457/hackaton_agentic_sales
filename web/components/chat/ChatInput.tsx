"use client";
import { useState } from "react";
import { Send } from "lucide-react";

import { Input } from "@/components/shared/input";
import { Button } from "@/components/shared/button";

export function ChatInput({
  onSend,
  disabled,
  conectando,
}: {
  onSend: (texto: string) => void;
  disabled?: boolean;
  conectando?: boolean;
}) {
  const [valor, setValor] = useState("");

  function enviar(e: React.FormEvent) {
    e.preventDefault();
    if (!valor.trim() || disabled) return;
    onSend(valor.trim());
    setValor("");
  }

  return (
    <form onSubmit={enviar} className="flex items-center gap-2 p-3">
      <label htmlFor="chat-mensaje" className="sr-only">
        Escribe tu mensaje
      </label>
      <Input
        id="chat-mensaje"
        value={valor}
        onChange={(e) => setValor(e.target.value)}
        placeholder={conectando ? "Conectando con el asistente…" : "Escribe un mensaje…"}
        disabled={disabled}
        autoComplete="off"
        maxLength={500}
        className="h-10 rounded-full px-4"
      />
      <Button
        type="submit"
        variant="accent"
        size="icon"
        className="size-10 rounded-full"
        disabled={disabled || !valor.trim()}
        aria-label="Enviar mensaje"
      >
        <Send className="size-4" aria-hidden="true" />
      </Button>
    </form>
  );
}
