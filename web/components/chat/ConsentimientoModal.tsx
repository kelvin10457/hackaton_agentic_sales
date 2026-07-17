"use client";

import { useState } from "react";
import { ShieldCheck } from "lucide-react";

import { Checkbox } from "@/components/shared/checkbox";
import { Button } from "@/components/shared/button";
import { cn } from "@/lib/utils";

/**
 * CONTRATO 3 — Consentimiento POR FINALIDAD (LOPDP):
 * 1. DOS casillas, no una: tratamiento de datos ≠ comunicaciones comerciales.
 * 2. NUNCA premarcadas.
 * 3. Rechazar ambas NO degrada el servicio: el tutor sigue funcionando igual.
 */
export function ConsentimientoModal({
  email,
  onComplete,
}: {
  email?: string;
  onComplete: (datos: boolean, comercial: boolean) => void;
}) {
  const [datos, setDatos] = useState(false);
  const [comercial, setComercial] = useState(false);

  const opciones = [
    {
      id: "consent-datos",
      checked: datos,
      set: setDatos,
      texto:
        "Autorizo a Futuro Academy a tratar mis datos para enviarme mi resultado y material educativo.",
    },
    {
      id: "consent-comercial",
      checked: comercial,
      set: setComercial,
      texto:
        "Autorizo que un asesor de Futuro Academy me contacte con información comercial.",
    },
  ];

  return (
    <div className="my-2 w-full animate-fade-up rounded-2xl border border-border bg-card p-3 shadow-sm sm:p-4">
      <p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-futuro-corp">
        <ShieldCheck className="size-3.5" aria-hidden="true" />
        Tu autorización, por finalidad
      </p>
      <p className="mt-1 text-[13px] leading-snug text-muted-foreground">
        Son dos permisos distintos{email ? ` para ${email}` : ""}. Ninguno viene
        marcado.
      </p>

      <fieldset className="mt-3 flex flex-col gap-2">
        <legend className="sr-only">Consentimientos</legend>
        {opciones.map((op) => (
          <label
            key={op.id}
            htmlFor={op.id}
            className={cn(
              "flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-colors duration-150",
              op.checked
                ? "border-futuro-accent bg-accent"
                : "border-border hover:border-futuro-accent/40"
            )}
          >
            <Checkbox
              id={op.id}
              checked={op.checked}
              onCheckedChange={(c) => op.set(c === true)}
              className="mt-0.5"
            />
            <span className="text-[13px] leading-snug text-foreground">
              {op.texto}
            </span>
          </label>
        ))}
      </fieldset>

      <Button
        onClick={() => onComplete(datos, comercial)}
        variant="accent"
        className="mt-3 w-full"
      >
        Confirmar elección
      </Button>
      <p className="mt-2 text-center text-[11px] leading-snug text-muted-foreground">
        Puedes aceptar una, ambas o ninguna — el tutor seguirá disponible igual.
      </p>
    </div>
  );
}
