"use client";
import { useState } from "react";
import { Mail } from "lucide-react";

import { Input } from "@/components/shared/input";
import { Button } from "@/components/shared/button";

/**
 * El momento donde se cierra el embudo: la prospecto QUIERE dar su correo
 * porque recibe algo a cambio (su resultado + ruta de 3 pasos).
 * No es un formulario: es un intercambio de valor.
 */
export function EmailCaptureCard({
  onSubmit,
}: {
  onSubmit: (email: string) => void;
}) {
  const [valor, setValor] = useState("");
  const [error, setError] = useState<string | null>(null);

  function enviar(e: React.FormEvent) {
    e.preventDefault();
    const correo = valor.trim();
    const valido = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(correo);
    if (!valido) {
      setError("Escribe un correo válido, por ejemplo nombre@correo.com");
      return;
    }
    onSubmit(correo);
  }

  return (
    <form
      onSubmit={enviar}
      noValidate
      className="my-2 w-full max-w-md animate-fade-up rounded-2xl border border-border bg-card p-4 shadow-sm sm:ml-9"
    >
      <p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-futuro-corp">
        <Mail className="size-3.5" aria-hidden="true" />
        Tu resultado, a tu correo
      </p>
      <p className="mt-1 text-[13px] leading-snug text-muted-foreground">
        Te enviaremos tu perfil y una ruta de aprendizaje de 3 pasos.
      </p>
      <div className="mt-3 flex gap-2">
        <label htmlFor="email-resultado" className="sr-only">
          Correo electrónico
        </label>
        <Input
          id="email-resultado"
          type="email"
          inputMode="email"
          autoComplete="email"
          placeholder="nombre@correo.com"
          value={valor}
          onChange={(e) => {
            setValor(e.target.value);
            setError(null);
          }}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? "email-error" : undefined}
        />
        <Button type="submit" variant="accent" disabled={!valor.trim()}>
          Enviar
        </Button>
      </div>
      {error && (
        <p id="email-error" role="alert" className="mt-1.5 text-xs font-medium text-destructive">
          {error}
        </p>
      )}
    </form>
  );
}
