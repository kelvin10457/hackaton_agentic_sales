"use client";
import { useState } from "react";
import { Input } from "@/components/shared/input";
import { Button } from "@/components/shared/button";

export function ChatInput({
  onSend,
  disabled,
}: {
  onSend: (texto: string) => void;
  disabled?: boolean;
}) {
  const [valor, setValor] = useState("");

  function enviar() {
    if (!valor.trim() || disabled) return;
    onSend(valor.trim());
    setValor("");
  }

  return (
    <div className="flex gap-2 p-4 border-t">
      <Input
        value={valor}
        onChange={(e) => setValor(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && enviar()}
        placeholder="Escribe un mensaje..."
        disabled={disabled}
      />
      <Button onClick={enviar} disabled={disabled}>
        Enviar
      </Button>
    </div>
  );
}