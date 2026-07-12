"use client";
import { useEffect, useRef, useState } from "react";
import { MessageBubble } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";
import { ChatInput } from "./ChatInput";
import { Badge } from "@/components/shared/badge";
import { enviarMensaje, iniciarConversacion } from "@/lib/api-client";
import type { MensajeChat, TipoLead } from "@/lib/types";

export function ChatWindow() {
  const [mensajes, setMensajes] = useState<MensajeChat[]>([]);
  const [escribiendo, setEscribiendo] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [badgeTipo, setBadgeTipo] = useState<TipoLead>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    iniciarConversacion().then((r) => setToken(r.token_sesion));
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensajes, escribiendo]);

  async function handleSend(texto: string) {
    if (!token) return;
    setMensajes((prev) => [
      ...prev,
      { id: crypto.randomUUID(), rol: "usuario", texto, ts: new Date().toISOString() },
    ]);
    setEscribiendo(true);

    try {
      const respuesta = await enviarMensaje(token, texto);
      if (respuesta.badge_tipo) setBadgeTipo(respuesta.badge_tipo);
      setMensajes((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          rol: "agente",
          texto: respuesta.mensaje,
          ts: new Date().toISOString(),
          fuentes: respuesta.fuentes,
        },
      ]);
    } catch {
      setMensajes((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          rol: "agente",
          texto: "Hubo un problema de conexión. Intenta de nuevo en un momento.",
          ts: new Date().toISOString(),
        },
      ]);
    } finally {
      setEscribiendo(false);
    }
  }

  return (
    <div className="flex flex-col h-[600px] max-w-2xl mx-auto border rounded-xl overflow-hidden bg-white">
      <div className="bg-slate-900 text-white px-4 py-3 flex justify-between items-center">
        <span className="font-semibold">Futuro Academy Asistente</span>
        {badgeTipo && <Badge>{badgeTipo}</Badge>}
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        {mensajes.map((m) => (
          <MessageBubble key={m.id} mensaje={m} />
        ))}
        {escribiendo && <TypingIndicator />}
        <div ref={scrollRef} />
      </div>
      <ChatInput onSend={handleSend} disabled={!token || escribiendo} />
    </div>
  );
}