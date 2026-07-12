// TODO: Reemplazar por lib/api-types.ts generado con `npm run types`
// cuando R2 publique /openapi.json. No editar a mano después de eso.

export type TipoLead = "B2C" | "B2B" | null;

export type PerfilRiesgo = "conservador" | "moderado" | "agresivo";

export interface Fuente {
  cita_visible: string;
}

export interface RespuestaAgente {
  mensaje: string;
  fuentes: Fuente[];
  estado_flujo: string; // "clasificacion" | "calificacion" | "educacion" | ...
  badge_tipo?: TipoLead;
  guardrail?: string;
  /** El backend puede sugerir una acción de UI (p. ej. ofrecer el quiz) */
  // Siguiente paso que debe ofrecer la UI:
  //   proponer_quiz → tarjeta del quiz de perfil de riesgo (solo B2C)
  //   pedir_email   → captura del correo (B2B, o B2C que ya hizo el quiz)
  accion?: "proponer_quiz" | "pedir_email";
}

export interface PreguntaQuiz {
  id: string;
  texto: string;
  opciones: string[];
}

export interface Quiz {
  preguntas: PreguntaQuiz[];
}

export interface ResultadoQuiz {
  perfil: PerfilRiesgo;
  mensaje: string;
}

export interface MensajeChat {
  id: string;
  rol: "usuario" | "agente";
  texto: string;
  ts: string;
  fuentes?: Fuente[];
  guardrail?: string;
}

export interface IniciarConversacionResponse {
  token_sesion: string;
  conversacion_id: string;
}

export interface ConversacionRecuperada {
  historial: MensajeChat[];
  preguntas_respondidas: string[];
  quiz?: { iniciado: boolean; perfil_resultante?: PerfilRiesgo };
  estado_flujo: string;
  badge_tipo?: TipoLead;
}

/* ------------------------------------------------------------------ */
/* Tipos de la consola (espejo de la Sección 5 del manual R4).         */
/* También se reemplazan por los tipos generados cuando R2 publique.   */
/* ------------------------------------------------------------------ */

export type Banda = "caliente" | "tibio" | "frio" | "critico";

export interface ScoreLead {
  interes: number;
  presupuesto: number;
  perfil: number;
  urgencia: number;
  total: number;
  banda: Banda;
  justificacion: string;
}

export interface ConsentimientoDetalle {
  otorgado: boolean;
  timestamp?: string;
}

export type TipoAccion =
  | "agendar_reunion"
  | "enviar_material"
  | "derivar_especialista"
  | "derivar_a_ventas_corporativas"
  // Valores del backend (TipoAccion enum en schemas.py)
  | "llamada"
  | "email"
  | "whatsapp"
  | "reunion"
  | "demo"
  | "propuesta_formal"
  | "descuento";

export type EstadoAccion =
  | "pendiente"
  | "aprobada"
  | "editada_y_aprobada"
  | "rechazada"
  | "obsoleta"
  // Valor del backend
  | "ejecutada";

export interface AccionPropuesta {
  id: string;
  lead_id?: string;
  tipo: TipoAccion;
  destinatario?: { email?: string; nombre?: string };
  borrador: { canal: string; asunto: string; cuerpo: string };
  razonamiento: string;
  fuentes_consultadas: string[];
  estado: EstadoAccion;
  revisado_por?: string | null;
  editado_por_humano?: boolean;
}

export interface Lead {
  id: string;
  tipo: "B2C" | "B2B";
  estado_identificacion?: string;
  etapa_embudo: string;
  identidad: {
    nombre: string;
    email?: string;
    documento?: string;
    documento_valido?: boolean;
    empresa?: string;
  };
  necesidad?: string;
  objeciones?: string[];
  senales?: {
    perfil_riesgo?: PerfilRiesgo | string;
    monto_declarado_usd?: number;
    horizonte?: string;
  };
  score: ScoreLead;
  ruta_sugerida?: string;
  consentimiento: {
    tratamiento_datos: ConsentimientoDetalle;
    comunicaciones_comerciales: ConsentimientoDetalle;
  };
  ultima_actividad?: string;
  accion_propuesta?: AccionPropuesta;
}
