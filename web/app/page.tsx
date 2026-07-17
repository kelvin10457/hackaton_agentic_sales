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
      {/* ── Fondo Desktop: mockup mantiene aspecto ──── */}
      <div
        className="relative hidden sm:block shadow-2xl"
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

        {/* Botón fantasma montado sobre «Ingresar» → consola del ejecutivo */}
        <button
          type="button"
          onClick={abrirCrm}
          aria-label="Ingresar — Consola del ejecutivo"
          title="Ingresar — Consola del ejecutivo"
          className="absolute cursor-pointer rounded-full ring-white/40 transition duration-150 hover:bg-white/10 hover:ring-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
          style={{ left: "81.3%", top: "4.1%", width: "8.1%", height: "5.4%" }}
        />
      </div>

      {/* ── Fondo Móvil: ocupa toda la pantalla ──── */}
      <div className="relative block h-dvh w-full sm:hidden">
        <Image
          src="/landing-futuro-mobile.png"
          alt="Futuro — Casa de Valores · La guía paso a paso para tu futuro financiero"
          fill
          priority
          sizes="100vw"
          className="select-none object-cover object-top"
        />
        {/* Botón fantasma visible de ingreso en móvil (esquina superior derecha, ajustado con %) */}
        <button
          type="button"
          onClick={abrirCrm}
          aria-label="Ingresar — Consola del ejecutivo"
          className="absolute z-10 cursor-pointer rounded-full ring-white/40 transition duration-150 active:bg-white/10 active:ring-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
          style={{ right: "4%", top: "3%", width: "30%", height: "7%" }}
        />
      </div>

      {/* ── Chat del agente ─── */}
      {chatAbierto && (
        <div className="fixed bottom-24 right-3 z-50 w-[calc(100vw-24px)] max-w-[400px] sm:inset-x-auto sm:bottom-24 sm:right-12 sm:w-[440px] sm:max-w-none">
          <div className="animate-fade-up relative h-[min(600px,72dvh)] w-full sm:h-[min(720px,78dvh)]">
            {/* X circular de cierre (solo desktop, en móvil se integra en el ChatWindow) */}
            <button
              type="button"
              onClick={() => setChatAbierto(false)}
              aria-label="Cerrar chat"
              title="Cerrar chat"
              className="absolute -right-2 -top-2 z-10 hidden sm:flex size-8 items-center justify-center rounded-full border border-border bg-card text-futuro-base shadow-lg transition-transform duration-150 hover:scale-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-futuro-sky focus-visible:ring-offset-2"
            >
              <X className="size-4" aria-hidden="true" />
            </button>
            <div className="h-full w-full overflow-hidden shadow-2xl rounded-2xl ring-1 ring-black/10">
              {/* Le pasamos onClose para que en móvil el botón de cerrar esté dentro del header del chat */}
              <ChatWindow onClose={() => setChatAbierto(false)} />
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
