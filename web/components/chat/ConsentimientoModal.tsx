"use client"

import { useState } from "react"
import { Checkbox } from "@/components/ui/checkbox"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"

export function ConsentimientoModal({ onComplete }: { onComplete: (datos: boolean, comercial: boolean) => void }) {
  const [datos, setDatos] = useState(false)
  const [comercial, setComercial] = useState(false)

  return (
    <Card className="w-full max-w-md mx-auto my-4 border-2 border-[#003E6B]">
      <CardHeader className="bg-[#F4F5F6] rounded-t-lg">
        <CardTitle className="text-[#031B4E]">Antes de enviarte los resultados...</CardTitle>
        <CardDescription className="text-gray-600">
          Tu perfil salió moderado. ¿A qué correo te envío tu resultado y una ruta de aprendizaje de 3 pasos?
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6 pt-6">
        
        {/* Casilla 1: Tratamiento de Datos */}
        <div className="flex items-start space-x-3">
          <Checkbox 
            id="datos" 
            checked={datos} 
            onCheckedChange={(c) => setDatos(c as boolean)} 
            className="mt-1 border-[#0084FF] text-[#0084FF]"
          />
          <label htmlFor="datos" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 text-[#031B4E]">
            Autorizo a Futuro Academy a tratar mis datos para enviarme mi resultado y material educativo.
          </label>
        </div>

        {/* Casilla 2: Comunicaciones Comerciales */}
        <div className="flex items-start space-x-3">
          <Checkbox 
            id="comercial" 
            checked={comercial} 
            onCheckedChange={(c) => setComercial(c as boolean)} 
            className="mt-1 border-[#0084FF] text-[#0084FF]"
          />
          <label htmlFor="comercial" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 text-[#031B4E]">
            Autorizo que un asesor de Futuro Academy me contacte con información comercial.
          </label>
        </div>

        {/* Botón CTA */}
        <Button
          onClick={() => onComplete(datos, comercial)}
          className="w-full bg-[#0084FF] hover:bg-[#003E6B] text-white font-bold py-2 rounded transition-colors"
        >
          Enviar resultados
        </Button>
      </CardContent>
    </Card>
  )
}