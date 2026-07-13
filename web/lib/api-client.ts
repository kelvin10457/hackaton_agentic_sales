import {
  USE_MOCKS,
  mockRespuestaAgente,
  mockRespuestaTutor,
  mockNegativaHonesta,
  mockInvitacionQuiz,
  mockQuiz,
  calcularPerfilMock,
  leerStoreMock,
  escribirStoreMock,
} from "./mocks";
import type {
  RespuestaAgente,
  IniciarConversacionResponse,
  ConversacionRecuperada,
  Quiz,
  ResultadoQuiz,
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
    const store = leerStoreMock();
    return {
      historial: store?.historial ?? [],
      preguntas_respondidas: [],
      quiz: store?.perfil
        ? { iniciado: true, perfil_resultante: store.perfil }
        : { iniciado: false },
      estado_flujo: "saludo",
      badge_tipo: store?.badge ?? null,
    };
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
    if (/quiz|perfil de riesgo|perfil de inversi/i.test(mensaje)) return mockInvitacionQuiz;
    if (/etf|fondo|invertir en qu[eé]|qu[eé] es/i.test(mensaje)) return mockRespuestaTutor;
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
  const res = await fetch(`${API_URL}/api/chat/quiz`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("No se pudo obtener el quiz");
  return res.json();
}

/**
 * Envía las respuestas del quiz. El PERFIL LO CALCULA EL BACKEND con la
 * rúbrica fija (principio 5); el mock replica ese cálculo solo para la demo.
 */
export async function enviarRespuestasQuiz(
  token: string,
  respuestas: number[]
): Promise<ResultadoQuiz> {
  if (USE_MOCKS) {
    await delay(700);
    const perfil = calcularPerfilMock(respuestas);
    escribirStoreMock({ perfil });
    return {
      perfil,
      mensaje: `Tu perfil salió ${perfil}. ¿A qué correo te envío tu resultado y una ruta de aprendizaje de 3 pasos?`,
    };
  }
  const res = await fetch(`${API_URL}/api/chat/quiz/respuestas`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ respuestas }),
  });
  if (!res.ok) throw new Error("No se pudo calcular el perfil");
  return res.json();
}

/**
 * Registra el consentimiento POR FINALIDAD (LOPDP): tratamiento de datos y
 * comunicaciones comerciales son autorizaciones distintas. Rechazar ambas
 * NO degrada el servicio del tutor.
 */
export async function registrarConsentimiento(
  token: string,
  datos: { email?: string; tratamiento_datos: boolean; comunicaciones_comerciales: boolean }
): Promise<{ mensaje: string }> {
  if (USE_MOCKS) {
    await delay(500);
    escribirStoreMock({
      email: datos.email,
      consentimiento: {
        datos: datos.tratamiento_datos,
        comercial: datos.comunicaciones_comerciales,
      },
    });
    if (datos.tratamiento_datos && datos.comunicaciones_comerciales) {
      return {
        mensaje: `¡Listo! Te envié tu resultado y la ruta de aprendizaje a ${datos.email}. Un asesor podrá contactarte, y cualquier comunicación la aprueba primero un humano — así trabajamos.`,
      };
    }
    if (datos.tratamiento_datos) {
      return {
        mensaje: `¡Listo! Te envié tu resultado y la ruta de aprendizaje a ${datos.email}. No recibirás comunicaciones comerciales: solo el material que pediste.`,
      };
    }
    return {
      mensaje:
        "Sin problema — no registraré tus datos. Podemos seguir aprendiendo aquí en el chat con total normalidad.",
    };
  }
  const res = await fetch(`${API_URL}/api/chat/consentimiento`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(datos),
  });
  if (!res.ok) throw new Error("No se pudo registrar el consentimiento");
  return res.json();
}
