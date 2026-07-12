import {
  USE_MOCKS,
  mockRespuestaAgente,
  mockRespuestaTutor,
  mockNegativaHonesta,
  mockQuiz,
} from "./mocks";
import type {
  RespuestaAgente,
  IniciarConversacionResponse,
  ConversacionRecuperada,
  Quiz,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function iniciarConversacion(): Promise<IniciarConversacionResponse> {
  if (USE_MOCKS) {
    await delay(300);
    return { token_sesion: "tok_mock_" + Date.now(), conversacion_id: "conv_mock_1" };
  }
  const res = await fetch(`${API_URL}/api/chat/iniciar`, { method: "POST" });
  if (!res.ok) throw new Error("No se pudo iniciar la conversación");
  return res.json();
}

export async function obtenerConversacion(token: string): Promise<ConversacionRecuperada> {
  if (USE_MOCKS) {
    await delay(300);
    return { historial: [], preguntas_respondidas: [], estado_flujo: "saludo" };
  }
  const res = await fetch(`${API_URL}/api/chat/conversacion`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("No se pudo recuperar la conversación");
  return res.json();
}

export async function enviarMensaje(token: string, mensaje: string): Promise<RespuestaAgente> {
  if (USE_MOCKS) {
    await delay(1200); // simula la latencia real del LLM (2–4s en producción)
    if (/bitcoin|cripto/i.test(mensaje)) return mockNegativaHonesta;
    if (/etf|fondo|invertir en qu[eé]/i.test(mensaje)) return mockRespuestaTutor;
    return mockRespuestaAgente;
  }
  const res = await fetch(`${API_URL}/api/chat/mensaje`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ mensaje }),
  });
  if (!res.ok) throw new Error("Error al enviar el mensaje");
  return res.json();
}

export async function obtenerQuiz(): Promise<Quiz> {
  if (USE_MOCKS) {
    await delay(200);
    return mockQuiz;
  }
  const res = await fetch(`${API_URL}/api/chat/quiz`);
  if (!res.ok) throw new Error("No se pudo obtener el quiz");
  return res.json();
}