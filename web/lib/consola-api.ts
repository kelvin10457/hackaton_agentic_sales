/**
 * consola-api.ts — Capa de comunicación con el backend FastAPI para la consola.
 *
 * Responsabilidades:
 * 1. Autenticación JWT (login + almacenamiento del token)
 * 2. Fetch de leads enriquecidos (ensamblando datos de múltiples endpoints)
 * 3. Transformación de LeadV2Read del backend → Lead del frontend
 * 4. Operaciones de escritura (aprobar/rechazar acciones)
 *
 * Los componentes NO llaman fetch directamente — usan estas funciones.
 */

import type {
  Lead,
  ScoreLead,
  ConsentimientoDetalle,
  AccionPropuesta,
  Banda,
  TipoAccion,
  EstadoAccion,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

// ──────────────────────────────────────────────────────────────────────────────
// Auth: JWT Bearer para /api/consola/*
// ──────────────────────────────────────────────────────────────────────────────

const TOKEN_KEY = "fa_consola_jwt";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

export function clearToken() {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
  }
}

function authHeaders(): HeadersInit {
  const token = getToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

/**
 * Login del ejecutivo. Usa el formulario OAuth2 de FastAPI.
 * El backend espera `username` (email) y `password` como form-data.
 */
export async function login(email: string, password: string): Promise<void> {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);

  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? "Credenciales incorrectas");
  }

  const data = await res.json();
  setToken(data.access_token);
}

/**
 * Registro rápido para demo. Crea usuario y hace login automáticamente.
 */
export async function registrarYLogin(
  name: string,
  email: string,
  password: string
): Promise<void> {
  // Intenta registrar; si ya existe, solo hace login.
  const resReg = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password }),
  });

  if (!resReg.ok) {
    const err = await resReg.json().catch(() => null);
    // Si ya existe, intentar login directamente
    if (resReg.status === 400 && err?.detail?.includes("ya está registrado")) {
      await login(email, password);
      return;
    }
    throw new Error(err?.detail ?? "Error al registrar");
  }

  // Si el registro fue exitoso, hacer login
  await login(email, password);
}

// ──────────────────────────────────────────────────────────────────────────────
// Helpers genéricos
// ──────────────────────────────────────────────────────────────────────────────

/**
 * FastAPI devuelve `detail` como string (HTTPException) o como ARRAY de objetos
 * (error 422 de validación). Sin esto, el toast mostraba "[object Object]".
 */
function formatearDetalle(
  detail: unknown,
  status: number,
  path: string
): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const msgs = detail
      .map((d) => (d && typeof d === "object" && "msg" in d ? String(d.msg) : JSON.stringify(d)))
      .join(" · ");
    if (msgs) return msgs;
  }
  if (detail && typeof detail === "object") return JSON.stringify(detail);
  return `Error ${status} en ${path}`;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { ...authHeaders(), ...init?.headers },
  });

  if (res.status === 401) {
    clearToken();
    throw new Error("Sesión expirada. Vuelve a iniciar sesión.");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(formatearDetalle(body?.detail, res.status, path));
  }

  if (res.status === 204) {
    return {} as T;
  }

  return res.json() as Promise<T>;
}

// ──────────────────────────────────────────────────────────────────────────────
// Tipos crudos del backend (solo los campos que necesitamos)
// ──────────────────────────────────────────────────────────────────────────────

interface LeadV2ReadRaw {
  id: number;
  nombre: string;
  email: string | null;
  email_normalizado: string | null;
  telefono: string | null;
  cedula: string | null;
  empresa: string | null;
  cargo: string | null;
  estado_identificacion: string;
  etapa_embudo: string;
  segmento: "b2c" | "b2b";
  necesidad: string | null;
  objeciones: string[];
  created_at: string;
  updated_at: string | null;
}

interface ScoreRaw {
  lead_id: number;
  dimension_interes: number;
  dimension_capacidad: number;
  dimension_urgencia: number;
  dimension_fit: number;
  total: number;
  banda: string;
  justificacion: string;
  calculado_en: string;
}

interface SenalesRaw {
  objetivo: string | null;
  horizonte: string | null;
  pidio_asesor: boolean | null;
  mensajes_intercambiados: number | null;
  completo_quiz: boolean | null;
  monto_declarado_usd: number | null;
  experiencia_inversion: string | null;
  perfil_riesgo: string | null;
  num_colaboradores: number | null;
  presupuesto_capacitacion_usd: number | null;
  es_decisor: boolean | null;
  solicito_propuesta: boolean | null;
}

interface OtorgamientoRaw {
  otorgado: boolean;
  fecha: string | null;
  ip_origen: string | null;
  canal: string | null;
  texto_mostrado: string | null;
}

interface ConsentimientoRaw {
  id: number;
  lead_id: number;
  tratamiento_datos: OtorgamientoRaw;
  comunicaciones_comerciales: OtorgamientoRaw;
  version_politica: string | null;
  updated_at: string | null;
}

interface AccionPropuestaRaw {
  id: number;
  lead_id: number;
  tipo: string;
  destinatario: { email: string; nombre: string };
  asunto: string | null;
  mensaje_sugerido: string;
  razonamiento: string | null;
  fuentes_consultadas: string[];
  snapshot_senales: Record<string, unknown>;
  generado_por: string;
  estado: string;
  revisado_por: string | null;
  revisado_en: string | null;
  motivo_rechazo: string | null;
  borrador_final: { asunto: string; cuerpo: string } | null;
  editado_por_humano: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface EventoAuditoriaRaw {
  id: number;
  actor: string;
  actor_id: string;
  tipo_evento: string;
  lead_id: number | null;
  payload: Record<string, unknown> | null;
  timestamp: string;
}

// ──────────────────────────────────────────────────────────────────────────────
// Transformaciones: Backend → Frontend
// ──────────────────────────────────────────────────────────────────────────────

function mapScore(raw: ScoreRaw): ScoreLead {
  return {
    interes: Math.round(raw.dimension_interes),
    presupuesto: Math.round(raw.dimension_capacidad),
    perfil: Math.round(raw.dimension_fit),
    urgencia: Math.round(raw.dimension_urgencia),
    total: Math.round(raw.total),
    banda: raw.banda as Banda,
    justificacion: raw.justificacion,
  };
}

const SCORE_VACIO: ScoreLead = {
  interes: 0,
  presupuesto: 0,
  perfil: 0,
  urgencia: 0,
  total: 0,
  banda: "frio",
  justificacion: "Score pendiente de cálculo.",
};

function mapConsentimiento(raw: ConsentimientoRaw): {
  tratamiento_datos: ConsentimientoDetalle;
  comunicaciones_comerciales: ConsentimientoDetalle;
} {
  return {
    tratamiento_datos: {
      otorgado: raw.tratamiento_datos.otorgado,
      timestamp: raw.tratamiento_datos.fecha ?? undefined,
    },
    comunicaciones_comerciales: {
      otorgado: raw.comunicaciones_comerciales.otorgado,
      timestamp: raw.comunicaciones_comerciales.fecha ?? undefined,
    },
  };
}

function mapAccion(raw: AccionPropuestaRaw): AccionPropuesta {
  return {
    id: String(raw.id),
    lead_id: String(raw.lead_id),
    tipo: raw.tipo as TipoAccion,
    destinatario: raw.destinatario,
    // Si un humano ya lo editó, se muestra lo que REALMENTE salió, no el
    // borrador original del agente.
    borrador: {
      canal: "email",
      asunto:
        raw.borrador_final?.asunto ??
        raw.asunto ??
        "Comunicación de Futuro Academy",
      cuerpo: raw.borrador_final?.cuerpo ?? raw.mensaje_sugerido,
    },
    // El razonamiento del agente es lo que Carlos lee antes de aprobar (criterio 3.2).
    razonamiento:
      raw.razonamiento ??
      "El agente no registró un razonamiento para esta propuesta.",
    fuentes_consultadas: raw.fuentes_consultadas ?? [],
    estado: raw.estado as EstadoAccion,
    revisado_por: raw.revisado_por,
    editado_por_humano: raw.editado_por_humano ?? false,
    motivo_rechazo: raw.motivo_rechazo ?? null,
  };
}

function mapLead(
  raw: LeadV2ReadRaw,
  score: ScoreLead,
  consentimiento: {
    tratamiento_datos: ConsentimientoDetalle;
    comunicaciones_comerciales: ConsentimientoDetalle;
  },
  accion: AccionPropuesta | undefined,
  senales?: SenalesRaw | null,
  rutaSugerida?: string | null,
): Lead {
  return {
    id: String(raw.id),
    tipo: raw.segmento === "b2b" ? "B2B" : "B2C",
    estado_identificacion: raw.estado_identificacion,
    etapa_embudo: raw.etapa_embudo,
    identidad: {
      nombre: raw.nombre,
      email: raw.email ?? undefined,
      documento: raw.cedula ?? undefined,
      documento_valido: raw.cedula ? true : undefined,
      empresa: raw.empresa ?? undefined,
    },
    // El brief que lee Carlos antes de llamar (criterio 3.1).
    necesidad: raw.necesidad ?? undefined,
    objeciones: raw.objeciones ?? [],
    senales: senales
      ? {
          perfil_riesgo: senales.perfil_riesgo ?? undefined,
          monto_declarado_usd: senales.monto_declarado_usd ?? undefined,
          horizonte: senales.horizonte ?? undefined,
        }
      : undefined,
    score,
    // El "para que" de la HU1: lo calcula el backend (T12), nunca el frontend.
    ruta_sugerida: rutaSugerida ?? undefined,
    consentimiento,
    ultima_actividad: raw.updated_at ?? raw.created_at,
    accion_propuesta: accion,
  };
}

// ──────────────────────────────────────────────────────────────────────────────
// Funciones públicas de la Consola
// ──────────────────────────────────────────────────────────────────────────────

/**
 * Carga todos los leads con su score y consentimiento enriquecido.
 * Las llamadas de enriquecimiento se hacen en paralelo por lead.
 */
export async function fetchLeadsEnriquecidos(): Promise<Lead[]> {
  const rawLeads = await apiFetch<LeadV2ReadRaw[]>("/api/consola/leads");

  // Enriquecer cada lead en paralelo (score + consentimiento + acciones)
  const enriched = await Promise.all(
    rawLeads.map(async (raw) => {
      const [scoreRaw, consentimientoRaw, accionesRaw] = await Promise.all([
        apiFetch<ScoreRaw>(`/api/consola/leads/${raw.id}/score`).catch(
          () => null
        ),
        apiFetch<ConsentimientoRaw>(
          `/api/consola/leads/${raw.id}/consentimiento`
        ).catch(() => null),
        apiFetch<AccionPropuestaRaw[]>(
          `/api/consola/leads/${raw.id}/acciones`
        ).catch(() => [] as AccionPropuestaRaw[]),
      ]);

      const score = scoreRaw ? mapScore(scoreRaw) : SCORE_VACIO;
      const consentimiento = consentimientoRaw
        ? mapConsentimiento(consentimientoRaw)
        : {
            tratamiento_datos: { otorgado: false },
            comunicaciones_comerciales: { otorgado: false },
          };
      const accionReciente =
        accionesRaw.length > 0 ? mapAccion(accionesRaw[0]) : undefined;

      return mapLead(raw, score, consentimiento, accionReciente);
    })
  );

  return enriched;
}

/**
 * Elimina un lead y todos sus datos relacionados del CRM de forma dura.
 */
export async function eliminarLead(leadId: number): Promise<void> {
  await apiFetch(`/api/consola/leads/${leadId}`, {
    method: 'DELETE',
  });
}

/**
 * Carga un lead individual con detalle completo (incluye señales y auditoría).
 */
export async function fetchLeadDetalle(leadId: number): Promise<{
  lead: Lead;
  auditoria: EventoAuditoriaRaw[];
}> {
  const [
    raw,
    scoreRaw,
    senalesRaw,
    consentimientoRaw,
    accionesRaw,
    auditoria,
    oportunidadRaw,
  ] = await Promise.all([
    apiFetch<LeadV2ReadRaw>(`/api/consola/leads/${leadId}`),
    apiFetch<ScoreRaw>(`/api/consola/leads/${leadId}/score`).catch(() => null),
    apiFetch<SenalesRaw>(`/api/consola/leads/${leadId}/senales`).catch(
      () => null
    ),
    apiFetch<ConsentimientoRaw>(
      `/api/consola/leads/${leadId}/consentimiento`
    ).catch(() => null),
    apiFetch<AccionPropuestaRaw[]>(
      `/api/consola/leads/${leadId}/acciones`
    ).catch(() => [] as AccionPropuestaRaw[]),
    apiFetch<EventoAuditoriaRaw[]>(
      `/api/consola/leads/${leadId}/auditoria`
    ).catch(() => [] as EventoAuditoriaRaw[]),
    apiFetch<{ ruta_sugerida: string | null }>(
      `/api/consola/leads/${leadId}/oportunidad`
    ).catch(() => null),
  ]);

  const score = scoreRaw ? mapScore(scoreRaw) : SCORE_VACIO;
  const consentimiento = consentimientoRaw
    ? mapConsentimiento(consentimientoRaw)
    : {
        tratamiento_datos: { otorgado: false },
        comunicaciones_comerciales: { otorgado: false },
      };
  const accionReciente =
    accionesRaw.length > 0 ? mapAccion(accionesRaw[0]) : undefined;

  return {
    lead: mapLead(
      raw,
      score,
      consentimiento,
      accionReciente,
      senalesRaw,
      oportunidadRaw?.ruta_sugerida
    ),
    auditoria,
  };
}

/**
 * Aprueba una acción propuesta. El backend verifica consentimiento (403 si no).
 *
 * Si se pasa `borrador`, el backend compara con lo que redactó el agente: si
 * cambió, la acción queda como `editada_y_aprobada` con `editado_por_humano`,
 * y la bitácora registra que la última palabra fue de un humano (criterio 3.3).
 */
export async function aprobarAccion(
  accionId: number,
  borrador?: { asunto: string; cuerpo: string }
): Promise<void> {
  await apiFetch(`/api/consola/acciones/${accionId}/aprobar`, {
    method: "POST",
    body: JSON.stringify(borrador ?? {}),
  });
}

/**
 * Rechaza una acción propuesta. El lead vuelve a nutrición.
 */
export async function rechazarAccion(
  accionId: number,
  motivo: string
): Promise<void> {
  await apiFetch(`/api/consola/acciones/${accionId}/rechazar`, {
    method: "POST",
    body: JSON.stringify({ motivo_rechazo: motivo }),
  });
}

/**
 * Obtiene la auditoría de un lead.
 */
export async function fetchAuditoria(
  leadId: number
): Promise<EventoAuditoriaRaw[]> {
  return apiFetch<EventoAuditoriaRaw[]>(
    `/api/consola/leads/${leadId}/auditoria`
  );
}
