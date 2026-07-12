import { Badge } from "@/components/shared/badge";
import type { MensajeChat } from "@/lib/types";

export function MessageBubble({ mensaje }: { mensaje: MensajeChat }) {
  const esAgente = mensaje.rol === "agente";
  return (
    <div className={`flex ${esAgente ? "justify-start" : "justify-end"} mb-3`}>
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-2 text-sm ${
          esAgente ? "bg-slate-100 text-slate-900" : "bg-blue-600 text-white"
        }`}
      >
        <p>{mensaje.texto}</p>
        {mensaje.fuentes && mensaje.fuentes.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {mensaje.fuentes.map((f, i) => (
              <Badge key={i} variant="outline" className="text-xs font-normal">
                {f.cita_visible}
              </Badge>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}