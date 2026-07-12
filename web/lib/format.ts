import { formatDistanceToNowStrict } from "date-fns";
import { es } from "date-fns/locale";

/**
 * Formatos compartidos entre chat y consola (regla de consistencia #6):
 * moneda USD $10,000 · fechas es-EC · etiquetas de enums.
 * Nadie formatea a mano fuera de este archivo.
 */

export function formatUSD(monto: number): string {
  return `USD $${monto.toLocaleString("en-US")}`;
}

/** "12 jul 2026, 22:47" */
export function formatFechaLarga(iso: string): string {
  const fecha = new Date(iso);
  if (isNaN(fecha.getTime())) return iso;
  return new Intl.DateTimeFormat("es-EC", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(fecha);
}

/** "22:47" */
export function formatHora(iso: string): string {
  const fecha = new Date(iso);
  if (isNaN(fecha.getTime())) return "";
  return new Intl.DateTimeFormat("es-EC", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(fecha);
}

/** "hace 2 horas" — siempre acompañado del absoluto en el tooltip */
export function formatRelativo(iso: string): string {
  const fecha = new Date(iso);
  if (isNaN(fecha.getTime())) return "";
  return formatDistanceToNowStrict(fecha, { addSuffix: true, locale: es });
}

/** Etiquetas legibles para los enums del backend */
const ETIQUETAS: Record<string, string> = {
  // etapa_embudo
  nutricion: "Nutrición",
  calificacion: "Calificación",
  educacion: "Educación",
  listo_para_asesor: "Listo para asesor",
  derivado: "Derivado",
  // ruta_sugerida
  asesoria_inversion: "Asesoría de inversión",
  programa_inicial: "Programa inicial",
  ventas_corporativas: "Ventas corporativas",
  // tipo de acción propuesta
  agendar_reunion: "Agendar reunión",
  enviar_material: "Enviar material educativo",
  derivar_especialista: "Derivar a especialista",
  derivar_a_ventas_corporativas: "Derivar a ventas corporativas",
  // estado de la acción
  pendiente: "Pendiente",
  aprobada: "Aprobada",
  editada_y_aprobada: "Editada y aprobada",
  rechazada: "Rechazada",
  obsoleta: "Obsoleta",
  // banda
  caliente: "Caliente",
  tibio: "Tibio",
  frio: "Frío",
  // perfil de riesgo
  conservador: "Conservador",
  moderado: "Moderado",
  agresivo: "Agresivo",
};

export function etiqueta(valor?: string | null): string {
  if (!valor) return "—";
  return (
    ETIQUETAS[valor] ??
    valor.replaceAll("_", " ").replace(/^\w/, (c) => c.toUpperCase())
  );
}
