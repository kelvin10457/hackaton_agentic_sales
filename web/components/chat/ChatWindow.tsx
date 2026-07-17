"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { ClipboardList, RefreshCw, WifiOff } from "lucide-react";

import { MessageBubble } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";
import { ChatInput } from "./ChatInput";
import { Bienvenida } from "./SuggestionChips";
import { QuizCard } from "./QuizCard";
import { EmailCaptureCard } from "./EmailCaptureCard";
import { ConsentimientoModal } from "./ConsentimientoModal";
import { Badge } from "@/components/shared/badge";
import { Button } from "@/components/shared/button";
import { Skeleton } from "@/components/shared/skeleton";
import { LogoMark } from "@/components/shared/logo";
import {
  enviarMensaje,
  enviarRespuestasQuiz,
  iniciarConversacion,
  obtenerConversacion,
  obtenerQuiz,
  registrarConsentimiento,
} from "@/lib/api-client";
import { USE_MOCKS, escribirStoreMock } from "@/lib/mocks";
import type { MensajeChat, PerfilRiesgo, Quiz, TipoLead } from "@/lib/types";

type FlujoGuiado = "inactivo" | "quiz" | "email" | "consentimiento";

// Detecta un correo dentro de un mensaje de texto libre (en cualquier momento
// del chat), para poder disparar el consentimiento aunque no venga por la tarjeta.
const RE_EMAIL = /[^\s@]+@[^\s@]+\.[^\s@]{2,}/;
function detectarEmail(texto: string): string | null {
  const m = texto.match(RE_EMAIL);
  return m ? m[0].replace(/[.,;:]+$/, "") : null;
}

export function ChatWindow() {
  const [mensajes, setMensajes] = useState<MensajeChat[]>([]);
  const [escribiendo, setEscribiendo] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [badgeTipo, setBadgeTipo] = useState<TipoLead>(null);
  const [cargandoInicial, setCargandoInicial] = useState(true);
  const [errorInicial, setErrorInicial] = useState(false);
  const [flujo, setFlujo] = useState<FlujoGuiado>("inactivo");
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [perfil, setPerfil] = useState<PerfilRiesgo | null>(null);
  const [email, setEmail] = useState("");
  const [emailEnviado, setEmailEnviado] = useState(false);
  const [solicitudCorreoFinalizada, setSolicitudCorreoFinalizada] = useState(false);
  const [ofertaQuiz, setOfertaQuiz] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // CONTRATO 1: el token vive en localStorage. Cerrar y reabrir el
  // navegador recupera la conversación completa desde el backend.
  const inicializar = useCallback(async () => {
    setCargandoInicial(true);
    setErrorInicial(false);
    try {
      let t = localStorage.getItem("token_sesion");
      if (!t) {
        const r = await iniciarConversacion();
        t = r.token_sesion;
        localStorage.setItem("token_sesion", t);
      }
      setToken(t);
      const conv = await obtenerConversacion(t);
      setMensajes(conv.historial ?? []);
      if (conv.badge_tipo) setBadgeTipo(conv.badge_tipo);
      // CONTRATO 4: si el quiz ya se hizo, no se vuelve a mostrar
      if (conv.quiz?.perfil_resultante) setPerfil(conv.quiz.perfil_resultante);
      // Si ya dejó su correo, la tarjeta de email no vuelve a aparecer.
      if (conv.email_capturado) {
        setEmailEnviado(true);
        setSolicitudCorreoFinalizada(true);
      }
    } catch {
      setErrorInicial(true);
      localStorage.removeItem("token_sesion");
    } finally {
      setCargandoInicial(false);
    }
  }, []);

  useEffect(() => {
    inicializar();
  }, [inicializar]);

  // En modo mock, el "backend" es localStorage: así la escena de
  // continuidad funciona sin servidor. Con API real, esto no se ejecuta.
  useEffect(() => {
    if (!USE_MOCKS || cargandoInicial) return;
    escribirStoreMock({ historial: mensajes, badge: badgeTipo });
  }, [mensajes, badgeTipo, cargandoInicial]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [mensajes, escribiendo, flujo, ofertaQuiz]);

  function agregarMensaje(
    rol: MensajeChat["rol"],
    texto: string,
    extra?: Partial<MensajeChat>
  ) {
    setMensajes((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        rol,
        texto,
        ts: new Date().toISOString(),
        ...extra,
      },
    ]);
  }

  async function handleSend(texto: string) {
    if (!token || !texto.trim()) return;

    // Si la tarjeta de correo estaba abierta y el usuario prefirió escribir,
    // se cierra: nada de recuadros persistentes que nadie pidió.
    if (flujo === "email" || flujo === "consentimiento") {
      setFlujo("inactivo");
      setSolicitudCorreoFinalizada(true);
    }
    agregarMensaje("usuario", texto);

    // ¿El usuario entregó su correo por texto (en cualquier momento)? Igual se
    // manda el turno al backend para que capture el nombre/señales, pero el
    // siguiente paso SIEMPRE será el consentimiento.
    const correoLibre = !emailEnviado ? detectarEmail(texto) : null;

    setEscribiendo(true);
    try {
      const respuesta = await enviarMensaje(token, texto);
      if (respuesta.badge_tipo) setBadgeTipo(respuesta.badge_tipo);

      if (correoLibre) {
        // Correo recibido → se omite la respuesta de embudo del agente (que solo
        // volvería a pedir el correo) y se pasa directo a pedir el consentimiento.
        // Sin esto, un correo por texto libre nunca disparaba el consentimiento.
        abrirConsentimiento(correoLibre);
        return;
      }

      agregarMensaje("agente", respuesta.mensaje, {
        fuentes: respuesta.fuentes,
        guardrail: respuesta.guardrail,
      });
      if (respuesta.accion === "proponer_quiz" && !perfil) {
        setOfertaQuiz(true);
      }
      // El prospecto pidió el quiz por texto → se abre el REAL de inmediato
      // (jamás lo improvisa el LLM: es el cuestionario fijo de cumplimiento).
      if (respuesta.accion === "abrir_quiz" && !perfil) {
        void comenzarQuiz();
      }
      // B2B no tiene quiz (es de perfil de riesgo personal): el agente pide el
      // correo directamente. También ocurre en B2C si ya completó el quiz.
      // Nunca se re-pide un correo ya entregado.
      if (respuesta.accion === "pedir_email" && !emailEnviado && !solicitudCorreoFinalizada) {
        setFlujo("email");
      }
    } catch {
      agregarMensaje(
        "agente",
        "Hubo un problema de conexión. Intenta de nuevo en un momento."
      );
    } finally {
      setEscribiendo(false);
    }
  }

  async function comenzarQuiz() {
    setOfertaQuiz(false);
    try {
      const q = await obtenerQuiz();
      setQuiz(q);
      setFlujo("quiz");
    } catch {
      agregarMensaje(
        "agente",
        "No pude cargar el quiz en este momento. Intenta de nuevo más tarde."
      );
    }
  }

  async function completarQuiz(respuestas: number[]) {
    setFlujo("inactivo");
    setQuiz(null);
    setEscribiendo(true);
    try {
      const resultado = await enviarRespuestasQuiz(token!, respuestas);
      setPerfil(resultado.perfil);
      agregarMensaje("agente", resultado.mensaje);
      setFlujo("email");
    } catch {
      agregarMensaje(
        "agente",
        "No pude calcular tu perfil. ¿Intentamos de nuevo en un momento?"
      );
    } finally {
      setEscribiendo(false);
    }
  }

  // Paso único de consentimiento: se llega aquí tanto por la tarjeta de correo
  // como al detectar el correo en texto libre. Siempre pide autorización antes
  // de convertir el chat en un lead (nombre + correo + consentimiento).
  function abrirConsentimiento(correo: string) {
    setEmail(correo);
    setFlujo("inactivo");
    setSolicitudCorreoFinalizada(true);
    setEscribiendo(true);
    window.setTimeout(() => {
      agregarMensaje(
        "agente",
        "Gracias. Antes de enviarte nada necesito tu autorización expresa — puedes elegir una, ambas o ninguna:"
      );
      setEscribiendo(false);
      setFlujo("consentimiento");
    }, 700);
  }

  function confirmarEmail(correo: string) {
    agregarMensaje("usuario", `Mi correo es ${correo}`);
    abrirConsentimiento(correo);
  }

  async function completarConsentimiento(datos: boolean, comercial: boolean) {
    setFlujo("inactivo");
    setEscribiendo(true);
    try {
      const r = await registrarConsentimiento(token!, {
        email: datos ? email : undefined,
        tratamiento_datos: datos,
        comunicaciones_comerciales: comercial,
      });
      agregarMensaje("agente", r.mensaje);
      if (datos) setEmailEnviado(true);
    } catch {
      agregarMensaje(
        "agente",
        "No pude registrar tu elección. El tutor sigue disponible con normalidad."
      );
    } finally {
      setEscribiendo(false);
    }
  }

  const ocupado = !token || escribiendo || cargandoInicial || flujo === "quiz";

  return (
    <div className="flex h-full w-full flex-col overflow-hidden bg-card sm:rounded-2xl sm:border sm:border-border sm:shadow-xl">
      {/* Cabecera de marca */}
      <header className="flex items-center justify-between gap-3 bg-futuro-base px-4 py-3 text-white">
        <div className="flex items-center gap-3">
          <LogoMark claro />
          <div>
            <p className="text-sm font-semibold leading-tight">Futuro Academy</p>
            <p className="mt-0.5 flex items-center gap-1.5 text-[11px] leading-none text-white/70">
              <span className="size-1.5 rounded-full bg-emerald-400" aria-hidden="true" />
              En línea · Tutor con fuentes verificadas
            </p>
          </div>
        </div>
        {badgeTipo && (
          <Badge
            className="animate-scale-in border border-white/25 bg-white/10 text-white"
            title={
              badgeTipo === "B2C"
                ? "Conversación clasificada: persona"
                : "Conversación clasificada: empresa"
            }
          >
            {badgeTipo}
          </Badge>
        )}
      </header>

      {/* Cuerpo de la conversación */}
      {cargandoInicial ? (
        <div className="flex-1 space-y-4 bg-futuro-bg/60 px-4 py-5" aria-hidden="true">
          <div className="flex gap-2.5">
            <Skeleton className="size-7 rounded-full" />
            <Skeleton className="h-14 w-3/5 rounded-2xl" />
          </div>
          <div className="flex justify-end">
            <Skeleton className="h-9 w-2/5 rounded-2xl" />
          </div>
          <div className="flex gap-2.5">
            <Skeleton className="size-7 rounded-full" />
            <Skeleton className="h-20 w-4/6 rounded-2xl" />
          </div>
        </div>
      ) : errorInicial ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 bg-futuro-bg/60 p-8 text-center">
          <span className="flex size-12 items-center justify-center rounded-full bg-muted">
            <WifiOff className="size-5 text-muted-foreground" aria-hidden="true" />
          </span>
          <div>
            <p className="text-sm font-semibold text-foreground">
              No pudimos conectar con el asistente
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              Revisa tu conexión e intenta de nuevo.
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={inicializar}>
            <RefreshCw aria-hidden="true" /> Reintentar
          </Button>
        </div>
      ) : (
        <div
          role="log"
          aria-live="polite"
          aria-label="Conversación con el asistente"
          className="scrollbar-thin flex-1 overflow-y-auto bg-futuro-bg/60 px-3 py-4 sm:px-4"
        >
          {mensajes.length === 0 && (
            <Bienvenida onSelect={handleSend} deshabilitado={ocupado} />
          )}
          {mensajes.map((m) => (
            <MessageBubble key={m.id} mensaje={m} />
          ))}

          {/* Invitación al quiz (HU2): aparece cuando el agente la propone */}
          {ofertaQuiz && !perfil && flujo === "inactivo" && (
            <div className="flex animate-fade-up py-1.5 sm:pl-9">
              <button
                type="button"
                onClick={comenzarQuiz}
                className="flex items-center gap-2 rounded-full border border-futuro-accent/40 bg-accent px-4 py-2 text-[13px] font-semibold text-futuro-corp shadow-sm transition-all duration-150 hover:border-futuro-accent hover:bg-futuro-accent hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 active:translate-y-px"
              >
                <ClipboardList className="size-4" aria-hidden="true" />
                Comenzar el quiz · 3 preguntas
              </button>
            </div>
          )}

          {flujo === "quiz" && quiz && (
            <QuizCard quiz={quiz} onComplete={completarQuiz} />
          )}
          {flujo === "email" && !emailEnviado && !solicitudCorreoFinalizada && (
            <EmailCaptureCard
              onSubmit={confirmarEmail}
              onDismiss={() => {
                setFlujo("inactivo");
                setSolicitudCorreoFinalizada(true);
              }}
            />
          )}
          {flujo === "consentimiento" && (
            <ConsentimientoModal email={email} onComplete={completarConsentimiento} />
          )}

          {escribiendo && <TypingIndicator />}
          <div ref={scrollRef} />
        </div>
      )}

      {/* Entrada + declaración de transparencia */}
      <div className="border-t border-border bg-card">
        <ChatInput
          onSend={handleSend}
          disabled={ocupado || errorInicial}
          conectando={!token && !errorInicial}
        />
        <p className="px-4 pb-2.5 text-center text-[10px] leading-snug text-muted-foreground">
          Contenido educativo con fuentes verificadas — no constituye asesoría de
          inversión. Cualquier contacto comercial lo aprueba un asesor humano.
        </p>
      </div>
    </div>
  );
}
