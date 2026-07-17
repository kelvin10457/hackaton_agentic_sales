"use client";

import { useState } from "react";
import Image from "next/image";
import { MessageCircle, X } from "lucide-react";

import { ChatWindow } from "@/components/chat/ChatWindow";
import { ConsolaApp } from "@/components/consola/ConsolaApp";

// Dimensiones reales del mockup de fondo (public/landing-futuro.png).
const IMG_W = 2688;
const IMG_H = 1598;

export default function HomePage() {
  const [chatAbierto, setChatAbierto] = useState(false);
  const [crmAbierto, setCrmAbierto] = useState(false);

  // Abrir el CRM cierra el chat: ambos comparten el mismo espacio simulado.
  function abrirCrm() {
    setChatAbierto(false);
    setCrmAbierto(true);
  }

  return (
    <main className="relative flex h-dvh w-screen items-center justify-center overflow-hidden bg-futuro-base">
      {/* ── Fondo: el mockup se ajusta al viewport manteniendo su aspecto ────
          La caja toma el máximo tamaño que cabe en pantalla sin recortar ni
          generar scroll (ni horizontal ni vertical). Como conserva el aspecto
          exacto de la imagen, los botones montados en % quedan siempre
          alineados a los elementos del mockup. */}
      <div
        className="relative shadow-2xl"
        style={{
          width: `min(100vw, calc(100dvh * ${IMG_W} / ${IMG_H}))`,
          height: `min(100dvh, calc(100vw * ${IMG_H} / ${IMG_W}))`,
        }}
      >
        <Image
          src="/landing-futuro.png"
          alt="Futuro — Casa de Valores · La guía paso a paso para tu futuro financiero"
          fill
          priority
          sizes="100vw"
          className="select-none object-cover"
        />

        {/* Botón fantasma montado sobre «Ingresar» → consola del ejecutivo.
            Invisible en reposo; revela un aro sutil al pasar el cursor. */}
        <button
          type="button"
          onClick={abrirCrm}
          aria-label="Ingresar — Consola del ejecutivo"
          title="Ingresar — Consola del ejecutivo"
          className="absolute cursor-pointer rounded-full ring-white/40 transition duration-150 hover:bg-white/10 hover:ring-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
          style={{ left: "81.3%", top: "4.1%", width: "8.1%", height: "5.4%" }}
        />
      </div>

      {/* ── Chat del agente: se monta sobre el fondo, alineado a la derecha ─── */}
      {chatAbierto && (
        <div className="fixed inset-x-3 bottom-24 z-50 sm:inset-x-auto sm:bottom-24 sm:right-12 sm:w-[440px]">
          <div className="animate-fade-up relative h-[min(720px,78dvh)]">
            {/* X circular de cierre (como en el ejemplo) */}
            <button
              type="button"
              onClick={() => setChatAbierto(false)}
              aria-label="Cerrar chat"
              title="Cerrar chat"
              className="absolute -right-2 -top-2 z-10 flex size-8 items-center justify-center rounded-full border border-border bg-card text-futuro-base shadow-lg transition-transform duration-150 hover:scale-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-futuro-sky focus-visible:ring-offset-2"
            >
              <X className="size-4" aria-hidden="true" />
            </button>
            <div className="h-full overflow-hidden rounded-2xl shadow-2xl ring-1 ring-black/10">
              <ChatWindow />
            </div>
          </div>
        </div>
      )}

      {/* ── Botón circular flotante para abrir/cerrar el agente ─────────────── */}
      <button
        type="button"
        onClick={() => setChatAbierto((v) => !v)}
        aria-label={chatAbierto ? "Cerrar el asistente" : "Abrir el asistente"}
        aria-expanded={chatAbierto}
        title={chatAbierto ? "Cerrar el asistente" : "Habla con el asistente"}
        className="fixed bottom-6 right-6 z-50 flex size-16 items-center justify-center rounded-full bg-futuro-accent text-white shadow-2xl ring-2 ring-white/80 transition-transform duration-150 hover:scale-110 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-white sm:size-20"
      >
        {chatAbierto ? (
          <X className="size-7 sm:size-9" aria-hidden="true" />
        ) : (
          <MessageCircle className="size-7 sm:size-9" aria-hidden="true" />
        )}
      </button>

      {/* ── CRM del ejecutivo: overlay a pantalla completa sobre el landing ─── */}
      {crmAbierto && (
        <div className="fixed inset-0 z-[60] overflow-y-auto bg-background">
          <ConsolaApp onClose={() => setCrmAbierto(false)} />
        </div>
      )}
    </main>
  );
}
