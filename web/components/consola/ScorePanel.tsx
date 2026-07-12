import React from 'react';

// Interfaz para asegurar los tipos de TypeScript
interface ScoreProps {
  score: {
    interes: number;
    presupuesto: number;
    perfil: number;
    urgencia: number;
    total: number;
    banda: string;
    justificacion?: string;
  };
}

export default function ScorePanel({ score }: ScoreProps) {
  // Configuración semántica de las bandas (Rojo/Ámbar/Azul) según la Regla 4
  const colorBanda = 
    score.banda === 'caliente' ? 'bg-red-500' : 
    score.banda === 'tibio' ? 'bg-amber-400' : 'bg-blue-500';

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6 font-sans">
      
      {/* Cabecera del Score */}
      <div className="flex justify-between items-end mb-6">
        <div>
          <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest">Score Dinámico</h2>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-3xl font-bold tabular-nums text-futuro-base">{score.total}</span>
            <span className={`text-xs font-bold px-2 py-1 rounded-md uppercase ${colorBanda} text-white shadow-sm`}>
              {score.banda}
            </span>
          </div>
        </div>
      </div>

      {/* Las 4 Barras de Dimensiones (Máximo 25 puntos c/u) */}
      <div className="space-y-4 mb-6">
        <ScoreBar label="Interés" value={score.interes} max={25} />
        <ScoreBar label="Presupuesto" value={score.presupuesto} max={25} />
        <ScoreBar label="Perfil" value={score.perfil} max={25} />
        <ScoreBar label="Urgencia" value={score.urgencia} max={25} />
      </div>

      {/* El texto que "sostiene" la tesis del producto */}
      <div className={`p-4 rounded-lg bg-gray-50 border-l-4 ${
        score.banda === 'caliente' ? 'border-red-500' : 
        score.banda === 'tibio' ? 'border-amber-400' : 'border-blue-500'
      }`}>
        <p className="text-xs font-semibold text-gray-700 mb-1 uppercase tracking-wider">Razonamiento del Modelo</p>
        <p className="text-sm text-gray-600 leading-relaxed italic">
          &quot;{score.justificacion || 'Sin justificación disponible para este lead.'}&quot;
        </p>
      </div>

    </div>
  );
}

// Subcomponente interno para cada barra
function ScoreBar({ label, value, max }: { label: string, value: number, max: number }) {
  const percentage = (value / max) * 100;
  
  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="text-xs font-medium text-gray-500 tabular-nums">{value}/{max}</span>
      </div>
      <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
        <div 
          className="h-full bg-futuro-corp transition-all duration-500 rounded-full" 
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
    </div>
  );
}
