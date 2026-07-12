import type { Metadata } from "next";
import { ChatWindow } from "@/components/chat/ChatWindow";

export const metadata: Metadata = {
    title: "Asistente",
    description:
        "Aprende finanzas con contenido verificado y descubre tu perfil de inversionista.",
};

export default function ChatPage() {
    return (
        <main className="flex min-h-dvh items-center justify-center bg-futuro-bg sm:p-6">
            {/* Pantalla completa en móvil; tarjeta centrada en escritorio */}
            <div className="flex h-dvh w-full max-w-2xl flex-col sm:h-[min(860px,94dvh)]">
                <ChatWindow />
            </div>
        </main>
    );
}
