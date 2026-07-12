"use client"

import { ConsentimientoModal } from "@/components/shared/ConsentimientoModal"

export default function ChatPage() {
  const manejarConsentimiento = (aceptaDatos: boolean, aceptaComercial: boolean) => {
    console.log("Consentimiento Datos:", aceptaDatos)
    console.log("Consentimiento Comercial:", aceptaComercial)
    // Aquí luego enviaremos esto al backend de R2
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-[#F4F5F6] p-4">
      {/* Tu contenedor principal del chat */}
      <div className="w-full max-w-2xl bg-white min-h-[600px] shadow-lg rounded-xl flex flex-col p-4 border border-gray-200">
        
        {/* Cabecera del Chat */}
        <header className="bg-[#031B4E] text-white p-4 rounded-t-lg mb-4 flex justify-between items-center">
          <h1 className="font-bold">Futuro Academy Asistente</h1>
          {/* Badge B2C/B2B */}
          <span className="bg-[#5A17F5] text-white text-xs px-2 py-1 rounded">B2C</span>
        </header>

        {/* Área de mensajes (Aquí irán las burbujas luego) */}
        <div className="flex-1 overflow-y-auto mb-4 p-2">
           <p className="text-center text-sm text-gray-400">Simulación del Chat...</p>
           {/* Invocamos el Modal para probarlo visualmente */}
           <ConsentimientoModal onComplete={manejarConsentimiento} />
        </div>

        {/* Input falso por ahora */}
        <div className="mt-auto flex gap-2">
          <input disabled type="text" placeholder="Escribe un mensaje..." className="flex-1 border rounded p-2" />
          <button disabled className="bg-[#D900C7] text-white px-4 py-2 rounded">Enviar</button>
        </div>

      </div>
    </main>
  )
}