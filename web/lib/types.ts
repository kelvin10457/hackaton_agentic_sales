// TODO: Reemplazar por lib/api-types.ts generado con `npm run types`
// cuando R2 publique /openapi.json. No editar a mano después de eso.

export type TipoLead = "B2C" | "B2B" | null;

export interface Fuente {
  cita_visible: string;
}

export interface RespuestaAgente {
  mensaje: string;
  fuentes: Fuente[];
  estado_flujo: string; // "clasificacion" | "calificacion" | "educacion" | ...
  badge_tipo?: TipoLead;
  guardrail?: string;
}

export interface PreguntaQuiz {
  id: string;
  texto: string;
  opciones: string[];
}

export interface Quiz {
  preguntas: PreguntaQuiz[];
}

export interface MensajeChat {
  id: string;
  rol: "usuario" | "agente";
  texto: string;
  ts: string;
  fuentes?: Fuente[];
}

export interface IniciarConversacionResponse {
  token_sesion: string;
  conversacion_id: string;
}

export interface ConversacionRecuperada {
  historial: MensajeChat[];
  preguntas_respondidas: string[];
  quiz?: { iniciado: boolean; perfil_resultante?: string };
  estado_flujo: string;
}