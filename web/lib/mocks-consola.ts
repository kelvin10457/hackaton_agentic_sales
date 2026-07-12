export const mockLeads = [
  {
    id: "lead_001",
    identidad: { nombre: "María Villacis" },
    tipo: "B2C",
    score: {
      interes: 25,
      presupuesto: 20,
      perfil: 25,
      urgencia: 18,
      total: 88,
      banda: "caliente",
      justificacion: "Interés alto: pidió hablar con un asesor..."
    },
    ruta_sugerida: "asesoria_inversion",
    consentimiento: {
      tratamiento_datos: { otorgado: true },
      comunicaciones_comerciales: { otorgado: true }
    }
  },
  {
    id: "lead_002",
    identidad: { nombre: "Sofía Andrade" },
    tipo: "B2C",
    score: { total: 72, banda: "caliente" },
    // Sofía es tu caso de prueba para el bloqueo (Línea roja)
    consentimiento: {
      comunicaciones_comerciales: { otorgado: false } 
    }
  },
  {
    id: "lead_003",
    identidad: { nombre: "Andrés C." },
    tipo: "B2B",
    score: { total: 65, banda: "tibio" },
    consentimiento: { comunicaciones_comerciales: { otorgado: true } }
  }
];
