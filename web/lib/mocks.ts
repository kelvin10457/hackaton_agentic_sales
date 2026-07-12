export const USE_MOCKS = true; // flag global

import type { RespuestaAgente } from "./types";

export const mockRespuestaAgente: RespuestaAgente = {
  mensaje: "Entiendo. ¿Con qué monto estarías pensando empezar?",
  fuentes: [],
  estado_flujo: "calificacion",
  badge_tipo: "B2C",
};

export const mockRespuestaTutor: RespuestaAgente = {
  mensaje: "Un ETF es un fondo que cotiza en bolsa y replica un índice...",
  fuentes: [{ cita_visible: "Futuro Academy - ETFs: qué son y qué no son §2" }],
  estado_flujo: "educacion",
};

export const mockNegativaHonesta: RespuestaAgente = {
  mensaje: "Eso no está cubierto en el material aprobado de Futuro Academy, y prefiero no darte un dato que no pueda respaldar.",
  fuentes: [],
  estado_flujo: "educacion",
  guardrail: "G2",
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