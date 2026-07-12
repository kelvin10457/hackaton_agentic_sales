export const USE_MOCKS = true; // flag global

import type {
  MensajeChat,
  PerfilRiesgo,
  RespuestaAgente,
  TipoLead,
} from "./types";

export const mockRespuestaAgente: RespuestaAgente = {
  mensaje: "Entiendo. ¿Con qué monto estarías pensando empezar?",
  fuentes: [],
  estado_flujo: "calificacion",
  badge_tipo: "B2C",
};

export const mockRespuestaTutor: RespuestaAgente = {
  mensaje:
    "Un ETF es un fondo que cotiza en bolsa y replica un índice. En lugar de comprar una sola acción, compras una canasta diversificada en una sola operación. ¿Te gustaría descubrir qué perfil de inversionista tienes? Tengo un quiz corto de 3 preguntas.",
  fuentes: [{ cita_visible: "Futuro Academy · ETFs: qué son y qué no son · §2" }],
  estado_flujo: "educacion",
  accion: "proponer_quiz",
};

export const mockNegativaHonesta: RespuestaAgente = {
  mensaje:
    "Eso no está cubierto en el material aprobado de Futuro Academy, y prefiero no darte un dato que no pueda respaldar.",
  fuentes: [],
  estado_flujo: "educacion",
  guardrail: "G2",
};

export const mockInvitacionQuiz: RespuestaAgente = {
  mensaje:
    "¡Claro! Son 3 preguntas rápidas con una rúbrica fija aprobada por cumplimiento — la IA no las improvisa. Al final te digo tu perfil de inversionista.",
  fuentes: [],
  estado_flujo: "educacion",
  accion: "proponer_quiz",
};

export const mockQuiz = {
  preguntas: [
    {
      id: "q1",
      texto: "Si tu inversión bajara un 20% en un mes, ¿qué harías?",
      opciones: ["Vender todo para no perder más", "Esperar y no hacer nada", "Comprar más, está barato"]
    },
    {
      id: "q2",
      texto: "¿En cuánto tiempo necesitarías recuperar este dinero?",
      opciones: ["En menos de un año", "Entre 1 y 5 años", "Más de 5 años"]
    },
    {
      id: "q3",
      texto: "¿Qué prefieres?",
      opciones: ["Ganar poco, pero seguro", "Un equilibrio entre riesgo y retorno", "Máximo retorno, aunque haya riesgo"]
    }
  ]
};

/**
 * Réplica SOLO PARA MODO MOCK del cálculo determinista del backend.
 * La rúbrica real vive en el servidor (principio 5: un instrumento
 * diagnóstico no lo improvisa una IA). Cada opción suma 0/1/2 puntos.
 */
export function calcularPerfilMock(respuestas: number[]): PerfilRiesgo {
  const puntos = respuestas.reduce((acc, r) => acc + r, 0);
  if (puntos <= 1) return "conservador";
  if (puntos <= 4) return "moderado";
  return "agresivo";
}

/* ------------------------------------------------------------------ */
/* Persistencia local del modo mock.                                    */
/* Con backend real la conversación se recupera con el token de sesión  */
/* (GET /api/chat/conversacion); este almacén solo emula esa memoria    */
/* para que la escena de continuidad funcione sin servidor.             */
/* ------------------------------------------------------------------ */

export interface StoreMockConversacion {
  historial: MensajeChat[];
  badge: TipoLead;
  perfil?: PerfilRiesgo;
  email?: string;
  consentimiento?: { datos: boolean; comercial: boolean };
}

const STORE_KEY = "fa_mock_conversacion";

export function leerStoreMock(): StoreMockConversacion | null {
  if (typeof window === "undefined") return null;
  try {
    const crudo = window.localStorage.getItem(STORE_KEY);
    return crudo ? (JSON.parse(crudo) as StoreMockConversacion) : null;
  } catch {
    return null;
  }
}

export function escribirStoreMock(patch: Partial<StoreMockConversacion>) {
  if (typeof window === "undefined") return;
  try {
    const actual = leerStoreMock() ?? { historial: [], badge: null };
    window.localStorage.setItem(
      STORE_KEY,
      JSON.stringify({ ...actual, ...patch })
    );
  } catch {
    // almacenamiento no disponible: la conversación seguirá en memoria
  }
}
